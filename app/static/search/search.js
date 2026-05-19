(function () {
  var form = document.getElementById("search-form");
  var input = document.getElementById("search-query");
  var status = document.getElementById("status");
  var results = document.getElementById("results");
  var resultsActions = document.getElementById("results-actions");
  var showMore = document.getElementById("show-more");
  var latestSearchId = 0;
  var currentQuery = "";
  var currentLimit = 10;
  // RRF scores are small, so expand top matches into visible meter widths.
  var MATCH_METER_SCORE_SCALE = 1800;
  var INITIAL_LIMIT = 10;
  var LIMIT_STEP = 10;

  function escapeHtml(value) {
    return String(value || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function escapeRegExp(value) {
    return String(value).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  }

  function createHighlighter(query) {
    var terms = String(query || "")
      .trim()
      .split(/\s+/)
      .filter(Boolean);
    if (!terms.length) {
      return escapeHtml;
    }

    var pattern = terms.map(escapeRegExp).join("|");
    var splitter = new RegExp("(" + pattern + ")", "gi");
    var matcher = new RegExp("^(" + pattern + ")$", "i");
    return function (value) {
      return String(value || "")
        .split(splitter)
        .map(function (part) {
          if (!part) {
            return "";
          }
          if (matcher.test(part)) {
            return "<mark>" + escapeHtml(part) + "</mark>";
          }
          return escapeHtml(part);
        })
        .join("");
    };
  }

  function stripExtension(fileName) {
    return String(fileName || "").replace(/\.[^/.]+$/, "");
  }

  function isFileDerivedTitle(title, fileName) {
    if (!fileName) {
      return false;
    }
    var rawTitle = String(title || "");
    return rawTitle === fileName || rawTitle === stripExtension(fileName);
  }

  function prettyFileTitle(title) {
    var fallback = stripExtension(title);
    var match = fallback.match(/^(\d{3})_(.+)$/);
    return (match ? match[2] : fallback).replace(/_/g, " ");
  }

  function displayTitle(result) {
    var rawTitle = result.title || "Document " + result.id;
    return isFileDerivedTitle(rawTitle, result.original_file_name)
      ? prettyFileTitle(rawTitle)
      : rawTitle;
  }

  function formatDate(value) {
    if (!value) {
      return "";
    }
    var dateValue = String(value);
    var dateParts = dateValue.match(/^(\d{4})-(\d{2})-(\d{2})/);
    var date = dateParts
      ? new Date(
          Date.UTC(
            Number(dateParts[1]),
            Number(dateParts[2]) - 1,
            Number(dateParts[3]),
          ),
        )
      : new Date(dateValue);
    if (Number.isNaN(date.getTime())) {
      return dateValue;
    }
    return date.toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      timeZone: "UTC",
    });
  }

  function pageLabel(pageCount) {
    if (!pageCount) {
      return "";
    }
    return pageCount + (pageCount === 1 ? " page" : " pages");
  }

  function scoreWidth(score) {
    if (score === null || score === undefined || score === "") {
      return 40;
    }
    var numeric = Number(score);
    if (!Number.isFinite(numeric)) {
      return 40;
    }
    return Math.max(
      12,
      Math.min(100, Math.round(numeric * MATCH_METER_SCORE_SCALE)),
    );
  }

  function loginRedirect() {
    var target = window.location.pathname + window.location.search;
    window.location.href =
      "/accounts/login/?next=" + encodeURIComponent(target || "/search");
  }

  function setStatus(message) {
    status.textContent = message || "";
  }

  function setShowMore(payload) {
    var maxLimit = Number(payload.max_limit || 50);
    var canAskForMore =
      Boolean(payload.has_more_possible) && currentLimit < maxLimit;
    resultsActions.hidden = !canAskForMore;
    showMore.disabled = !canAskForMore;
  }

  function errorMessage(code, fallback) {
    var messages = {
      paperless_api_error: "Paperless is unavailable right now.",
      search_failed: "Search failed. Try again in a moment.",
      not_authenticated: "Your Paperless session expired.",
      "q is required": "Enter a search query.",
      "q is too long": "Search query is too long.",
    };
    return messages[code] || fallback || "Something went wrong.";
  }

  function parseJsonResponse(response, fallback) {
    var contentType = response.headers.get("content-type") || "";
    if (contentType.indexOf("application/json") === -1) {
      throw new Error(fallback);
    }
    return response.json().catch(function () {
      throw new Error(fallback);
    });
  }

  function renderEmpty(message) {
    results.innerHTML =
      '<div class="empty-state">' + escapeHtml(message) + "</div>";
    resultsActions.hidden = true;
  }

  function meta(label, value) {
    if (value === null || value === undefined || value === "") {
      return "";
    }
    return "<span>" + escapeHtml(label + ": " + value) + "</span>";
  }

  function resultCard(result, highlight, index) {
    var snippet = result.matched_chunk || "";
    var created = formatDate(result.created);
    var titleText = displayTitle(result);
    var resultRank = String(index + 1).padStart(2, "0");
    var pageCount = pageLabel(result.page_count);
    var score =
      result.relevance_score !== null && result.relevance_score !== undefined
        ? result.relevance_score
        : result.similarity;
    var hasScore = score !== null && score !== undefined && score !== "";

    return [
      '<article class="result-card">',
      '<div class="result-rail" aria-hidden="true">',
      '<span class="rail-number">' + escapeHtml(resultRank) + "</span>",
      '<span class="rail-label">result</span>',
      "</div>",
      '<div class="result-body">',
      '<div class="result-band">',
      "<span>",
      created ? escapeHtml(created) : "Undated",
      "</span>",
      "</div>",
      '<a class="result-title" href="' +
        escapeHtml(result.document_url) +
        '">' +
        highlight(titleText) +
        "</a>",
      snippet ? '<p class="snippet">' + highlight(snippet) + "</p>" : "",
      '<div class="result-footer">',
      '<div class="meta">',
      pageCount ? "<span>" + escapeHtml(pageCount) + "</span>" : "",
      meta("Score", score),
      result.original_file_name
        ? meta("File", result.original_file_name)
        : meta("Document", result.id),
      "</div>",
      '<div class="match-group">',
      '<div class="match-meter" aria-label="' +
        escapeHtml(
          hasScore ? "Match score " + score : "Match score unavailable",
        ) +
        '">',
      "<span>Match</span>",
      '<b class="scorebar"><i style="--score-width: ' +
        scoreWidth(score) +
        '%"></i></b>',
      "</div>",
      "</div>",
      "</div>",
      "</div>",
      "</article>",
    ].join("");
  }

  function renderResults(payload) {
    if (!payload.results || payload.results.length === 0) {
      renderEmpty("No matching documents found.");
      setStatus("No results");
      resultsActions.hidden = true;
      return;
    }

    var highlight = createHighlighter(payload.query);
    results.innerHTML = payload.results
      .map(function (result, index) {
        return resultCard(result, highlight, index);
      })
      .join("");
    setStatus(
      payload.count +
        (payload.count === 1 ? " result" : " results") +
        ' for "' +
        payload.query +
        '"',
    );
    setShowMore(payload);
  }

  function runSearch(query, requestedLimit) {
    latestSearchId += 1;
    var searchId = latestSearchId;
    var trimmed = query.trim();
    var limit = requestedLimit || INITIAL_LIMIT;
    if (!trimmed) {
      input.focus();
      setStatus("Enter a search query.");
      results.innerHTML = "";
      resultsActions.hidden = true;
      return;
    }

    currentQuery = trimmed;
    currentLimit = limit;
    setStatus("Searching...");
    showMore.disabled = true;
    resultsActions.hidden = true;
    results.innerHTML = "";
    fetch(
      "/search/api/documents?q=" +
        encodeURIComponent(trimmed) +
        "&limit=" +
        encodeURIComponent(limit),
      {
        headers: { Accept: "application/json" },
      },
    )
      .then(function (response) {
        if (searchId !== latestSearchId) {
          return null;
        }
        if (response.status === 401) {
          loginRedirect();
          return null;
        }
        return parseJsonResponse(response, "Search failed").then(
          function (body) {
            if (!response.ok) {
              throw new Error(errorMessage(body.error, "Search failed"));
            }
            return body;
          },
        );
      })
      .then(function (payload) {
        if (searchId !== latestSearchId) {
          return;
        }
        if (payload) {
          renderResults(payload);
          window.history.replaceState(
            null,
            "",
            "/search?q=" + encodeURIComponent(trimmed),
          );
        }
      })
      .catch(function (error) {
        if (searchId !== latestSearchId) {
          return;
        }
        var message = error.message || "Search failed";
        setStatus(message);
        renderEmpty(message);
      });
  }

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    runSearch(input.value, INITIAL_LIMIT);
  });

  showMore.addEventListener("click", function () {
    if (!currentQuery) {
      return;
    }
    runSearch(currentQuery, currentLimit + LIMIT_STEP);
  });

  var params = new URLSearchParams(window.location.search);
  var initialQuery = params.get("q");
  if (initialQuery) {
    input.value = initialQuery;
    runSearch(initialQuery);
  } else {
    input.focus();
  }
})();
