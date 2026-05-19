import psycopg2
from contextlib import contextmanager
from pgvector.psycopg2 import register_vector
import config


@contextmanager
def get_cursor(need_vector=True):
    conn = psycopg2.connect(config.DATABASE_URL)
    try:
        if need_vector:
            register_vector(conn)
        cur = conn.cursor()
        yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def init_db():
    # First create extension with a raw connection (no register_vector yet)
    with get_cursor(need_vector=False) as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Now that the extension exists, register and create table
    with get_cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS document_embeddings (
                id SERIAL PRIMARY KEY,
                document_id INTEGER NOT NULL,
                chunk_index INTEGER NOT NULL,
                chunk_text TEXT NOT NULL,
                embedding vector(384),
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
                UNIQUE(document_id, chunk_index)
            )
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_doc_embeddings_doc_id
            ON document_embeddings (document_id)
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_doc_embeddings_embedding_hnsw
            ON document_embeddings
            USING hnsw (embedding vector_cosine_ops)
        """)


def store_embeddings(doc_id, chunks):
    """chunks: list of (chunk_index, chunk_text, embedding_list)"""
    with get_cursor() as cur:
        cur.execute("DELETE FROM document_embeddings WHERE document_id = %s", (doc_id,))
        for chunk_idx, chunk_text, embedding in chunks:
            vec_str = "[" + ",".join(str(x) for x in embedding) + "]"
            cur.execute(
                """INSERT INTO document_embeddings
                   (document_id, chunk_index, chunk_text, embedding)
                   VALUES (%s, %s, %s, %s::vector)""",
                (doc_id, chunk_idx, chunk_text, vec_str)
            )


def get_embedded_doc_ids():
    with get_cursor() as cur:
        cur.execute("SELECT DISTINCT document_id FROM document_embeddings")
        return {row[0] for row in cur.fetchall()}


def search_similar(query_embedding, limit=20):
    with get_cursor() as cur:
        # Convert to pgvector string format: [0.1, 0.2, ...]
        vec_str = "[" + ",".join(str(x) for x in query_embedding) + "]"
        cur.execute(
            """SELECT document_id, chunk_index, chunk_text,
                      1 - (embedding <=> %s::vector) as similarity
               FROM document_embeddings
               ORDER BY embedding <=> %s::vector
               LIMIT %s""",
            (vec_str, vec_str, limit)
        )
        return [
            {"document_id": row[0], "chunk_index": row[1],
             "chunk_text": row[2], "similarity": float(row[3])}
            for row in cur.fetchall()
        ]


def search_similar_documents(query_embedding, limit=20, chunk_limit=None):
    with get_cursor() as cur:
        vec_str = "[" + ",".join(str(x) for x in query_embedding) + "]"
        chunk_limit = chunk_limit or max(limit * 8, limit)
        cur.execute(
            """WITH nearest_chunks AS (
                   SELECT id, document_id, chunk_index,
                          1 - (embedding <=> %s::vector) as similarity,
                          embedding <=> %s::vector as distance
                   FROM document_embeddings
                   ORDER BY embedding <=> %s::vector
                   LIMIT %s
               ),
               best_document_chunks AS (
                   SELECT DISTINCT ON (document_id)
                          id, document_id, chunk_index, similarity, distance
                   FROM nearest_chunks
                   ORDER BY document_id, distance
               ),
               ranked_documents AS (
                   SELECT id, document_id, chunk_index, similarity, distance
                   FROM best_document_chunks
                   ORDER BY distance
                   LIMIT %s
               )
               SELECT ranked_documents.document_id,
                      ranked_documents.chunk_index,
                      document_embeddings.chunk_text,
                      ranked_documents.similarity
               FROM ranked_documents
               JOIN document_embeddings
                 ON document_embeddings.id = ranked_documents.id
               ORDER BY ranked_documents.distance""",
            (vec_str, vec_str, vec_str, chunk_limit, limit)
        )
        return [
            {"document_id": row[0], "chunk_index": row[1],
             "chunk_text": row[2], "similarity": float(row[3])}
            for row in cur.fetchall()
        ]


def get_embedding_stats():
    with get_cursor() as cur:
        cur.execute("""
            SELECT COUNT(*), COUNT(DISTINCT document_id)
            FROM document_embeddings
        """)
        total_chunks, total_docs = cur.fetchone()
        return {"total_chunks": total_chunks, "total_docs": total_docs}
