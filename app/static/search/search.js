(function () {
  var form = document.getElementById("search-form");
  var input = document.getElementById("search-query");
  var status = document.getElementById("status");
  var profileStatus = document.getElementById("profile-status");
  var results = document.getElementById("results");
  var latestSearchId = 0;

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

  function highlightHtml(value, query) {
    var terms = String(query || "")
      .trim()
      .split(/\s+/)
      .filter(Boolean);
    if (!terms.length) {
      return escapeHtml(value);
    }

    var pattern = terms.map(escapeRegExp).join("|");
    var splitter = new RegExp("(" + pattern + ")", "gi");
    var matcher = new RegExp("^(" + pattern + ")$", "i");
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
  }

  function prettyTitle(title) {
    var fallback = String(title || "");
    var match = fallback.match(/^(\d{3})_(.+)$/);
    if (!match) {
      return {
        number: null,
        name: fallback.replace(/_/g, " "),
      };
    }
    return {
      number: match[1],
      name: match[2].replace(/_/g, " "),
    };
  }

  function formatDate(value) {
    if (!value) {
      return "";
    }
    var dateValue = String(value);
    var date = new Date(
      dateValue.length === 10 ? dateValue + "T00:00:00" : dateValue,
    );
    if (Number.isNaN(date.getTime())) {
      return dateValue;
    }
    return date.toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  }

  function pageLabel(pageCount) {
    if (!pageCount) {
      return "";
    }
    return pageCount + (pageCount === 1 ? " page" : " pages");
  }

  function scoreWidth(score) {
    var numeric = Number(score);
    if (!Number.isFinite(numeric)) {
      return 40;
    }
    return Math.max(12, Math.min(100, Math.round(numeric * 1800)));
  }

  function loginRedirect() {
    var target = window.location.pathname + window.location.search;
    window.location.href =
      "/accounts/login/?next=" + encodeURIComponent(target || "/search");
  }

  function setStatus(message) {
    status.textContent = message || "";
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
  }

  function meta(label, value) {
    if (value === null || value === undefined || value === "") {
      return "";
    }
    return "<span>" + escapeHtml(label + ": " + value) + "</span>";
  }

  function resultCard(result, query, index) {
    var rawTitle = result.title || "Document " + result.id;
    var title = prettyTitle(rawTitle);
    var snippet = result.matched_chunk || "";
    var created = formatDate(result.created);
    var titleText = title.name || rawTitle;
    var resultRank = String(index + 1).padStart(2, "0");
    var pageCount = pageLabel(result.page_count);
    var score = result.relevance_score || result.similarity || "";

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
        highlightHtml(titleText, query) +
        "</a>",
      snippet
        ? '<p class="snippet">' + highlightHtml(snippet, query) + "</p>"
        : "",
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
        escapeHtml(score ? "Match score " + score : "Match score unavailable") +
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
      return;
    }

    results.innerHTML = payload.results
      .map(function (result, index) {
        return resultCard(result, payload.query, index);
      })
      .join("");
    setStatus(
      payload.count +
        (payload.count === 1 ? " result" : " results") +
        ' for "' +
        payload.query +
        '"',
    );
  }

  function runSearch(query) {
    latestSearchId += 1;
    var searchId = latestSearchId;
    var trimmed = query.trim();
    if (!trimmed) {
      input.focus();
      setStatus("Enter a search query.");
      results.innerHTML = "";
      return;
    }

    setStatus("Searching...");
    results.innerHTML = "";
    fetch(
      "/search/api/documents?q=" + encodeURIComponent(trimmed) + "&limit=10",
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

  fetch("/search/api/me", { headers: { Accept: "application/json" } })
    .then(function (response) {
      if (response.status === 401) {
        loginRedirect();
        return null;
      }
      return parseJsonResponse(response, "Profile unavailable").then(
        function (body) {
          if (!response.ok) {
            throw new Error(errorMessage(body.error, "Profile unavailable"));
          }
          return body;
        },
      );
    })
    .then(function (payload) {
      if (!payload) {
        return;
      }
      if (!profileStatus) {
        return;
      }
      var profile = payload.profile || {};
      var name =
        [profile.first_name, profile.last_name].filter(Boolean).join(" ") ||
        profile.email ||
        profile.username ||
        "Paperless";
      profileStatus.textContent = "Signed in as " + name;
    })
    .catch(function () {
      if (profileStatus) {
        profileStatus.textContent = "Sign-in status unavailable";
      }
    });

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    runSearch(input.value);
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
