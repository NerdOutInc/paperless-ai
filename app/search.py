import math
import re

import requests

import auth
import config
import db
import embeddings


SEMANTIC_MIN_CANDIDATES = 20
SEMANTIC_MAX_CANDIDATES = 500
PAPERLESS_DOCUMENT_BATCH_SIZE = 100
PAPERLESS_DOCUMENT_CARD_FIELDS = (
    "id,title,created,created_date,added,original_file_name,page_count,mime_type"
)
PAPERLESS_KEYWORD_DOCUMENT_FIELDS = f"{PAPERLESS_DOCUMENT_CARD_FIELDS},content"
QUERY_STOP_WORDS = {
    "about",
    "after",
    "also",
    "and",
    "any",
    "are",
    "but",
    "can",
    "for",
    "from",
    "has",
    "have",
    "how",
    "into",
    "not",
    "our",
    "out",
    "show",
    "that",
    "the",
    "their",
    "then",
    "there",
    "these",
    "this",
    "those",
    "was",
    "were",
    "what",
    "when",
    "where",
    "with",
    "you",
}


def _semantic_similarity(result):
    try:
        return float(result.get("similarity") or 0)
    except (TypeError, ValueError):
        return 0.0


def _passes_semantic_threshold(result):
    return _semantic_similarity(result) >= config.SEMANTIC_MIN_SIMILARITY


def _query_terms(query):
    terms = []
    for term in re.findall(r"[a-z0-9]+", query.lower()):
        if len(term) < 3 or term in QUERY_STOP_WORDS:
            continue
        terms.append(term)
    return terms


def _term_variants(term):
    variants = {term}
    if len(term) > 3 and term.endswith("s"):
        variants.add(term[:-1])
    if len(term) > 4 and term.endswith("ies"):
        variants.add(f"{term[:-3]}y")
    return variants


def _topic_text_matches_query(query, result):
    terms = _query_terms(query)
    if not terms:
        return False

    topic_text = " ".join(
        str(result.get(field) or "")
        for field in ("title", "original_file_name")
    ).lower()
    if not topic_text:
        return False

    matches = 0
    for term in terms:
        if any(variant in topic_text for variant in _term_variants(term)):
            matches += 1

    required_matches = 1
    if len(terms) > 1:
        required_matches = max(2, math.ceil(len(terms) * 0.6))
    return matches >= required_matches


def _semantic_elbow_index(candidates):
    """Find the first rank where semantic scores fall out of the match cluster."""
    if len(candidates) <= config.SEMANTIC_ELBOW_MIN_RESULTS:
        return len(candidates)

    top_similarity = _semantic_similarity(candidates[0])
    if top_similarity <= 0:
        return len(candidates)

    min_results = max(1, config.SEMANTIC_ELBOW_MIN_RESULTS)
    for index in range(min_results, len(candidates)):
        previous_similarity = _semantic_similarity(candidates[index - 1])
        current_similarity = _semantic_similarity(candidates[index])
        gap = previous_similarity - current_similarity
        if (
            gap >= config.SEMANTIC_ELBOW_MIN_GAP
            and current_similarity <= top_similarity * config.SEMANTIC_ELBOW_DROP_RATIO
        ):
            return index

    return len(candidates)


def _apply_semantic_cutoff(candidates):
    cutoff_index = _semantic_elbow_index(candidates)
    return candidates[:cutoff_index], cutoff_index < len(candidates)


def get_document_metadata(doc_id):
    resp = auth.api_request(
        "GET", f"{config.PAPERLESS_API_URL}/api/documents/{doc_id}/",
    )
    doc = resp.json()
    return {
        "id": doc["id"],
        "title": doc.get("title", ""),
        "correspondent": doc.get("correspondent"),
        "document_type": doc.get("document_type"),
        "tags": doc.get("tags", []),
        "created": doc.get("created", ""),
        "content": doc.get("content", "")[:500],
    }


def paperless_session_request(method, path, cookie_header, **kwargs):
    """Call Paperless as the browser user identified by the session cookie."""
    headers = dict(kwargs.pop("headers", {}) or {})
    headers.setdefault("Accept", "application/json")
    if cookie_header:
        headers["Cookie"] = cookie_header

    url = path if path.startswith("http") else f"{config.PAPERLESS_API_URL}{path}"
    kwargs.setdefault("timeout", 30)
    return requests.request(method, url, headers=headers, **kwargs)


def _document_payload(doc, matched_chunk="", similarity=None, sources=None):
    doc_id = doc["id"]
    content = doc.get("content") or ""
    snippet = matched_chunk or content[:300]
    payload = {
        "id": doc_id,
        "title": doc.get("title") or doc.get("original_file_name") or f"Document {doc_id}",
        "created": doc.get("created_date") or doc.get("created", ""),
        "added": doc.get("added", ""),
        "original_file_name": doc.get("original_file_name", ""),
        "page_count": doc.get("page_count"),
        "mime_type": doc.get("mime_type", ""),
        "document_url": f"/documents/{doc_id}",
        "matched_chunk": snippet[:500] if snippet else "",
        "sources": sources or [],
    }
    if similarity is not None:
        payload["similarity"] = round(similarity, 4)
    return payload


def get_documents_for_session(doc_ids, cookie_header):
    if not doc_ids:
        return {}

    documents = {}
    for offset in range(0, len(doc_ids), PAPERLESS_DOCUMENT_BATCH_SIZE):
        batch = doc_ids[offset:offset + PAPERLESS_DOCUMENT_BATCH_SIZE]
        resp = paperless_session_request(
            "GET",
            "/api/documents/",
            cookie_header,
            params={
                "id__in": ",".join(str(doc_id) for doc_id in batch),
                "page_size": len(batch),
                "fields": PAPERLESS_DOCUMENT_CARD_FIELDS,
            },
        )
        resp.raise_for_status()
        documents.update(
            {
                doc["id"]: doc
                for doc in resp.json().get("results", [])
            }
        )
    return documents


def semantic_search(query, limit=10):
    query_embedding = embeddings.get_embedding(query)
    raw_results = db.search_similar(query_embedding, limit=limit * 2)

    # Deduplicate by document_id, keeping highest similarity
    seen = {}
    for result in raw_results:
        if not _passes_semantic_threshold(result):
            continue
        doc_id = result["document_id"]
        if (
            doc_id not in seen
            or _semantic_similarity(result) > _semantic_similarity(seen[doc_id])
        ):
            seen[doc_id] = result

    candidates = sorted(seen.values(), key=_semantic_similarity, reverse=True)
    candidates, _cutoff_applied = _apply_semantic_cutoff(candidates)
    results = candidates[:limit]

    enriched = []
    for r in results:
        try:
            meta = get_document_metadata(r["document_id"])
            enriched.append({
                **meta,
                "similarity": round(_semantic_similarity(r), 4),
                "matched_chunk": r["chunk_text"][:300],
            })
        except Exception:
            continue

    return enriched


def semantic_search_for_session(query, limit=10, cookie_header=""):
    query_embedding = embeddings.get_embedding(query)
    candidate_limit = min(
        max(limit * 8, SEMANTIC_MIN_CANDIDATES),
        SEMANTIC_MAX_CANDIDATES,
    )
    authorized_docs = {}
    checked_doc_ids = set()

    while True:
        raw_results = db.search_similar_documents(query_embedding, limit=candidate_limit)
        seen = {}
        for result in raw_results:
            if not _passes_semantic_threshold(result):
                continue
            doc_id = result["document_id"]
            if (
                doc_id not in seen
                or _semantic_similarity(result) > _semantic_similarity(seen[doc_id])
            ):
                seen[doc_id] = result

        candidates = sorted(seen.values(), key=_semantic_similarity, reverse=True)
        if not candidates:
            return []

        candidate_doc_ids = [result["document_id"] for result in candidates]
        unchecked_doc_ids = [
            doc_id
            for doc_id in candidate_doc_ids
            if doc_id not in checked_doc_ids
        ]
        if unchecked_doc_ids:
            authorized_docs.update(
                get_documents_for_session(unchecked_doc_ids, cookie_header)
            )
            checked_doc_ids.update(unchecked_doc_ids)

        visible_candidates = [
            result
            for result in candidates
            if result["document_id"] in authorized_docs
        ]
        visible_candidates, cutoff_applied = _apply_semantic_cutoff(visible_candidates)

        results = []
        for result in visible_candidates:
            doc = authorized_docs.get(result["document_id"])
            results.append(
                _document_payload(
                    doc,
                    matched_chunk=result["chunk_text"],
                    similarity=_semantic_similarity(result),
                    sources=["semantic"],
                )
            )
            if len(results) >= limit:
                break

        if (
            len(results) >= limit
            or cutoff_applied
            or not raw_results
            or candidate_limit >= SEMANTIC_MAX_CANDIDATES
        ):
            return results

        candidate_limit = min(candidate_limit * 2, SEMANTIC_MAX_CANDIDATES)


def keyword_search(query, limit=10):
    resp = auth.api_request(
        "GET", f"{config.PAPERLESS_API_URL}/api/documents/",
        params={"query": query, "page_size": limit},
    )
    return [
        {
            "id": doc["id"],
            "title": doc.get("title", ""),
            "correspondent": doc.get("correspondent"),
            "document_type": doc.get("document_type"),
            "tags": doc.get("tags", []),
            "created": doc.get("created", ""),
        }
        for doc in resp.json().get("results", [])
    ]


def keyword_search_for_session(query, limit=10, cookie_header=""):
    resp = paperless_session_request(
        "GET",
        "/api/documents/",
        cookie_header,
        params={
            "query": query,
            "page_size": limit,
            "fields": PAPERLESS_KEYWORD_DOCUMENT_FIELDS,
            "truncate_content": "true",
        },
    )
    resp.raise_for_status()
    return [
        _document_payload(doc, sources=["keyword"])
        for doc in resp.json().get("results", [])
    ]


def hybrid_search(query, limit=10):
    semantic_results = semantic_search(query, limit=limit)
    keyword_results = keyword_search(query, limit=limit)

    k = 60
    scores = {}
    doc_data = {}

    for rank, result in enumerate(semantic_results):
        doc_id = result["id"]
        scores[doc_id] = scores.get(doc_id, 0) + 1.0 / (k + rank)
        doc_data[doc_id] = result

    for rank, result in enumerate(keyword_results):
        doc_id = result["id"]
        if doc_id not in doc_data and not _topic_text_matches_query(query, result):
            continue
        scores[doc_id] = scores.get(doc_id, 0) + 1.0 / (k + rank)
        if doc_id not in doc_data:
            doc_data[doc_id] = result

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:limit]

    results = []
    for doc_id, score in ranked:
        entry = doc_data[doc_id].copy()
        entry["relevance_score"] = round(score, 6)
        results.append(entry)

    return results


def hybrid_search_for_session(query, limit=10, cookie_header=""):
    semantic_results = semantic_search_for_session(
        query,
        limit=limit,
        cookie_header=cookie_header,
    )
    keyword_results = keyword_search_for_session(
        query,
        limit=limit,
        cookie_header=cookie_header,
    )

    k = 60
    scores = {}
    doc_data = {}
    sources = {}

    for rank, result in enumerate(semantic_results):
        doc_id = result["id"]
        scores[doc_id] = scores.get(doc_id, 0) + 1.0 / (k + rank)
        doc_data[doc_id] = result
        sources.setdefault(doc_id, set()).update(result.get("sources", []))

    for rank, result in enumerate(keyword_results):
        doc_id = result["id"]
        if doc_id not in doc_data and not _topic_text_matches_query(query, result):
            continue
        scores[doc_id] = scores.get(doc_id, 0) + 1.0 / (k + rank)
        if doc_id not in doc_data:
            doc_data[doc_id] = result
        sources.setdefault(doc_id, set()).update(result.get("sources", []))

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:limit]

    results = []
    for doc_id, score in ranked:
        entry = doc_data[doc_id].copy()
        entry["sources"] = sorted(sources.get(doc_id, []))
        entry["relevance_score"] = round(score, 6)
        results.append(entry)

    return results


def get_document(doc_id):
    resp = auth.api_request(
        "GET", f"{config.PAPERLESS_API_URL}/api/documents/{doc_id}/",
    )
    doc = resp.json()
    return {
        "id": doc["id"],
        "title": doc.get("title", ""),
        "correspondent": doc.get("correspondent"),
        "document_type": doc.get("document_type"),
        "tags": doc.get("tags", []),
        "created": doc.get("created", ""),
        "added": doc.get("added", ""),
        "content": doc.get("content", ""),
    }


def _get_paginated_results(url):
    results = []
    while url:
        resp = auth.api_request("GET", url)
        data = resp.json()
        results.extend(data.get("results", []))
        url = data.get("next")
    return results


def list_tags():
    results = _get_paginated_results(
        f"{config.PAPERLESS_API_URL}/api/tags/?page_size=100"
    )
    return [{"id": t["id"], "name": t["name"]} for t in results]


def list_document_types():
    results = _get_paginated_results(
        f"{config.PAPERLESS_API_URL}/api/document_types/?page_size=100"
    )
    return [{"id": t["id"], "name": t["name"]} for t in results]


def search_by_tag(tag_name, limit=20):
    tags = list_tags()
    tag_id = next((t["id"] for t in tags if t["name"].lower() == tag_name.lower()), None)
    if tag_id is None:
        return []

    resp = auth.api_request(
        "GET", f"{config.PAPERLESS_API_URL}/api/documents/",
        params={"tags__id": tag_id, "page_size": limit},
    )
    return [
        {"id": d["id"], "title": d.get("title", ""), "created": d.get("created", "")}
        for d in resp.json().get("results", [])
    ]


def search_by_date_range(start, end, limit=20):
    resp = auth.api_request(
        "GET", f"{config.PAPERLESS_API_URL}/api/documents/",
        params={"created__date__gte": start, "created__date__lte": end, "page_size": limit},
    )
    return [
        {"id": d["id"], "title": d.get("title", ""), "created": d.get("created", "")}
        for d in resp.json().get("results", [])
    ]
