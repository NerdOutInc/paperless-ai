(function () {
  var LINK_MARKER = "paperlessAgSemanticSearch";
  var LINK_MARKER_ATTRIBUTE = "data-paperless-ag-semantic-search";
  var SEARCH_HOST_MARKER_ATTRIBUTE = "data-paperless-ag-search-host";
  var SEARCH_INPUT_SELECTOR = 'pngx-global-search input[name="query"]';
  var COMPACT_MEDIA_QUERY = "(max-width: 900px)";
  var activeButton = null;
  var activeMetricsCleanup = null;
  var attachScheduled = false;
  var styleApplied = false;

  function addStyles() {
    if (styleApplied || document.getElementById("paperless-ag-ui-link-style")) {
      styleApplied = true;
      return;
    }

    var style = document.createElement("style");
    style.id = "paperless-ag-ui-link-style";
    style.textContent = [
      ".paperless-ag-semantic-search-btn {",
      "  --paperless-ag-button-border: rgba(255, 255, 255, 0.34);",
      "  --paperless-ag-button-bg: rgba(255, 255, 255, 0.12);",
      "  --paperless-ag-button-bg-hover: rgba(255, 255, 255, 0.2);",
      "  align-items: center;",
      "  background: var(--paperless-ag-button-bg);",
      "  border: 1px solid var(--paperless-ag-button-border);",
      "  border-bottom-left-radius: 0;",
      "  border-bottom-right-radius: var(",
      "    --paperless-ag-search-border-bottom-right-radius,",
      "    var(--bs-border-radius-sm, 0.25rem)",
      "  );",
      "  border-top-left-radius: 0;",
      "  border-top-right-radius: var(",
      "    --paperless-ag-search-border-top-right-radius,",
      "    var(--bs-border-radius-sm, 0.25rem)",
      "  );",
      "  box-sizing: border-box;",
      "  color: var(--pngx-primary-text-contrast, #ffffff);",
      "  cursor: pointer;",
      "  display: inline-flex;",
      "  flex: 0 0 auto;",
      "  font: inherit;",
      "  font-size: 0.8125rem;",
      "  font-weight: 600;",
      "  gap: 0.35rem;",
      "  height: var(--paperless-ag-search-control-height, auto);",
      "  line-height: 1;",
      "  margin-left: calc(var(--bs-border-width, 1px) * -1);",
      "  min-height: var(--paperless-ag-search-control-height, auto);",
      "  padding: 0 0.72rem;",
      "  text-decoration: none;",
      "  transition: background-color 0.15s ease, border-color 0.15s ease, box-shadow 0.15s ease, transform 0.15s ease;",
      "  white-space: nowrap;",
      "}",
      "[" + SEARCH_HOST_MARKER_ATTRIBUTE + "] {",
      "  flex: 1 1 auto !important;",
      "  max-width: none !important;",
      "  min-width: 0 !important;",
      "  width: 100% !important;",
      "}",
      "[" + SEARCH_HOST_MARKER_ATTRIBUTE + "] > pngx-global-search {",
      "  display: block;",
      "  min-width: 0;",
      "  width: 100%;",
      "}",
      "[" + SEARCH_HOST_MARKER_ATTRIBUTE + "] .dropdown,",
      "[" + SEARCH_HOST_MARKER_ATTRIBUTE + "] .form-inline,",
      "[" + SEARCH_HOST_MARKER_ATTRIBUTE + "] .input-group {",
      "  min-width: 0;",
      "  width: 100%;",
      "}",
      "[" + SEARCH_HOST_MARKER_ATTRIBUTE + "] .input-group {",
      "  flex-wrap: nowrap;",
      "}",
      "[" + SEARCH_HOST_MARKER_ATTRIBUTE + "] .input-group > .form-control {",
      "  min-width: 0;",
      "}",
      ".paperless-ag-semantic-search-btn:hover {",
      "  background: var(--paperless-ag-button-bg-hover);",
      "  border-color: rgba(255, 255, 255, 0.55);",
      "  color: var(--pngx-primary-text-contrast, #ffffff);",
      "}",
      ".paperless-ag-semantic-search-btn:focus-visible {",
      "  box-shadow: 0 0 0 0.16rem rgba(255, 255, 255, 0.26);",
      "  outline: 0;",
      "}",
      ".paperless-ag-semantic-search-btn:active {",
      "  transform: translateY(1px);",
      "}",
      ".paperless-ag-semantic-search-btn svg {",
      "  flex: 0 0 auto;",
      "  height: 1em;",
      "  width: 1em;",
      "}",
      "@media " + COMPACT_MEDIA_QUERY + " {",
      "  .paperless-ag-semantic-search-btn {",
      "    gap: 0;",
      "    padding: 0 0.48rem;",
      "  }",
      "  .paperless-ag-semantic-search-btn span {",
      "    clip: rect(0 0 0 0);",
      "    clip-path: inset(50%);",
      "    height: 1px;",
      "    overflow: hidden;",
      "    position: absolute;",
      "    white-space: nowrap;",
      "    width: 1px;",
      "  }",
      "}",
    ].join("\n");
    document.head.appendChild(style);
    styleApplied = true;
  }

  function searchUrlFor(input) {
    var query = (input.value || "").trim();
    if (!query) {
      return "/search";
    }
    return "/search?q=" + encodeURIComponent(query);
  }

  function searchControlFor(input) {
    return input.closest(".form-control") || input;
  }

  function cssVariable(element, name) {
    var value = window.getComputedStyle(element).getPropertyValue(name).trim();
    return value || "";
  }

  function usableRadius(value) {
    return value && value !== "0px" ? value : "";
  }

  function captureRightEdge(inputGroup, input) {
    var control = searchControlFor(input);
    var source = inputGroup.lastElementChild || control;
    var sourceStyle = window.getComputedStyle(source);
    var controlStyle = window.getComputedStyle(control);
    var fallbackRadius =
      cssVariable(control, "--bs-border-radius-sm") ||
      cssVariable(control, "--bs-border-radius") ||
      "0.25rem";

    return {
      borderTopRightRadius:
        usableRadius(sourceStyle.borderTopRightRadius) ||
        usableRadius(controlStyle.borderTopRightRadius) ||
        usableRadius(controlStyle.borderTopLeftRadius) ||
        fallbackRadius,
      borderBottomRightRadius:
        usableRadius(sourceStyle.borderBottomRightRadius) ||
        usableRadius(controlStyle.borderBottomRightRadius) ||
        usableRadius(controlStyle.borderBottomLeftRadius) ||
        fallbackRadius,
    };
  }

  function syncButtonMetrics(input, button, rightEdge) {
    var controlHeight = searchControlFor(input).getBoundingClientRect().height;
    if (controlHeight > 0) {
      button.style.setProperty(
        "--paperless-ag-search-control-height",
        controlHeight + "px",
      );
    }
    button.style.setProperty(
      "--paperless-ag-search-border-top-right-radius",
      rightEdge.borderTopRightRadius,
    );
    button.style.setProperty(
      "--paperless-ag-search-border-bottom-right-radius",
      rightEdge.borderBottomRightRadius,
    );
  }

  function watchButtonMetrics(input, button, rightEdge) {
    var control = searchControlFor(input);
    var resizeObserver = null;
    var disposed = false;
    var update = function () {
      syncButtonMetrics(input, button, rightEdge);
    };

    update();
    if ("ResizeObserver" in window) {
      resizeObserver = new ResizeObserver(update);
      resizeObserver.observe(control);
    }
    window.addEventListener("resize", update, { passive: true });

    return function () {
      if (disposed) {
        return;
      }
      disposed = true;
      if (resizeObserver) {
        resizeObserver.disconnect();
      }
      window.removeEventListener("resize", update);
    };
  }

  function createButton(input) {
    var button = document.createElement("button");
    button.type = "button";
    button.className = "paperless-ag-semantic-search-btn";
    button.dataset[LINK_MARKER] = "true";
    button.setAttribute("aria-label", "Smart Search");
    button.title = "Smart Search";
    button.innerHTML = [
      '<svg aria-hidden="true" viewBox="0 0 24 24" fill="none"',
      ' stroke="currentColor" stroke-width="2" stroke-linecap="round"',
      ' stroke-linejoin="round">',
      '<path d="M15 4V2" />',
      '<path d="M15 16v-2" />',
      '<path d="M8 9h2" />',
      '<path d="M20 9h2" />',
      '<path d="m17.8 11.8 1.4 1.4" />',
      '<path d="m17.8 6.2 1.4-1.4" />',
      '<path d="M3 21 14.5 9.5" />',
      '<path d="m7 17 3-3" />',
      "</svg>",
      "<span>Smart Search</span>",
    ].join("");
    button.addEventListener("click", function () {
      window.location.assign(searchUrlFor(input));
    });
    return button;
  }

  function activeButtonIsConnected() {
    return activeButton && document.documentElement.contains(activeButton);
  }

  function clearActiveMetrics() {
    if (activeMetricsCleanup) {
      activeMetricsCleanup();
      activeMetricsCleanup = null;
    }
    activeButton = null;
  }

  function markSearchLayout(inputGroup) {
    var host = inputGroup.closest(".col-12") || inputGroup.parentElement;
    if (host) {
      host.setAttribute(SEARCH_HOST_MARKER_ATTRIBUTE, "true");
    }
  }

  function attachButton() {
    if (activeButtonIsConnected()) {
      return true;
    }

    clearActiveMetrics();

    var input = document.querySelector(SEARCH_INPUT_SELECTOR);
    if (!input) {
      return false;
    }

    var inputGroup = input.closest(".input-group");
    if (!inputGroup || inputGroup.querySelector("[" + LINK_MARKER_ATTRIBUTE + "]")) {
      return false;
    }

    addStyles();
    markSearchLayout(inputGroup);
    var rightEdge = captureRightEdge(inputGroup, input);
    activeButton = createButton(input);
    inputGroup.appendChild(activeButton);
    activeMetricsCleanup = watchButtonMetrics(input, activeButton, rightEdge);
    return true;
  }

  function scheduleAttachButton() {
    if (attachScheduled || activeButtonIsConnected()) {
      return;
    }

    attachScheduled = true;
    var run = function () {
      attachScheduled = false;
      attachButton();
    };
    if (window.requestAnimationFrame) {
      window.requestAnimationFrame(run);
    } else {
      window.setTimeout(run, 0);
    }
  }

  attachButton();

  var observer = new MutationObserver(function () {
    scheduleAttachButton();
  });
  observer.observe(document.documentElement, {
    childList: true,
    subtree: true,
  });
})();
