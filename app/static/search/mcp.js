(function () {
  var status = document.getElementById("mcp-status");
  var values = {
    SERVER_NAME: "paperless-ag",
    MCP_URL: window.location.origin + "/mcp",
    MCP_TOKEN: "YOUR_MCP_AUTH_TOKEN",
    AUTH_HEADER: "Bearer YOUR_MCP_AUTH_TOKEN",
  };
  var TOKEN_UNAVAILABLE_MESSAGE =
    "Ask a Paperless administrator for the MCP token";

  function setStatus(message) {
    status.textContent = message || "";
  }

  function loginRedirect() {
    var target = window.location.pathname + window.location.search;
    window.location.href =
      "/accounts/login/?next=" + encodeURIComponent(target || "/search/mcp");
  }

  function escapeTemplate(value) {
    return String(value || "");
  }

  function fillText(selector, value) {
    Array.prototype.forEach.call(
      document.querySelectorAll(selector),
      function (node) {
        node.textContent = value;
      },
    );
  }

  function renderTemplates() {
    fillText("[data-server-name]", values.SERVER_NAME);
    fillText("[data-mcp-url]", values.MCP_URL);
    fillText("[data-mcp-token]", values.MCP_TOKEN);
    fillText("[data-auth-header]", values.AUTH_HEADER);

    Array.prototype.forEach.call(
      document.querySelectorAll("[data-template]"),
      function (node) {
        var template = node.getAttribute("data-raw-template");
        if (!template) {
          template = node.textContent;
          node.setAttribute("data-raw-template", template);
        }

        node.textContent = template
          .replace(/\{\{SERVER_NAME\}\}/g, escapeTemplate(values.SERVER_NAME))
          .replace(/\{\{MCP_URL\}\}/g, escapeTemplate(values.MCP_URL))
          .replace(/\{\{MCP_TOKEN\}\}/g, escapeTemplate(values.MCP_TOKEN))
          .replace(/\{\{AUTH_HEADER\}\}/g, escapeTemplate(values.AUTH_HEADER));
      },
    );
  }

  function writeClipboard(value) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      return navigator.clipboard.writeText(value);
    }

    return new Promise(function (resolve, reject) {
      var textarea = document.createElement("textarea");
      textarea.value = value;
      textarea.setAttribute("readonly", "");
      textarea.style.position = "fixed";
      textarea.style.left = "-9999px";
      document.body.appendChild(textarea);
      textarea.select();
      try {
        if (document.execCommand("copy")) {
          resolve();
        } else {
          reject(new Error("Copy failed"));
        }
      } catch (error) {
        reject(error);
      } finally {
        document.body.removeChild(textarea);
      }
    });
  }

  function copyText(button) {
    var targetSelector = button.getAttribute("data-copy-target");
    var target = targetSelector ? document.querySelector(targetSelector) : null;
    var value = target
      ? target.textContent
      : button.getAttribute("data-copy-value");
    if (!value) {
      return;
    }

    writeClipboard(value)
      .then(function () {
        var previous = button.textContent;
        button.textContent = "Copied";
        window.setTimeout(function () {
          button.textContent = previous;
        }, 1500);
      })
      .catch(function () {
        setStatus("Could not copy to clipboard.");
      });
  }

  function loadConfig() {
    fetch("/search/api/mcp-config", {
      headers: { Accept: "application/json" },
    })
      .then(function (response) {
        if (response.status === 401) {
          loginRedirect();
          return null;
        }
        return response.json().then(function (body) {
          if (!response.ok) {
            throw new Error(body.error || "Could not load MCP details.");
          }
          return body;
        });
      })
      .then(function (payload) {
        if (!payload) {
          return;
        }

        values.SERVER_NAME = payload.server_name || values.SERVER_NAME;
        values.MCP_URL =
          window.location.origin + (payload.endpoint_path || "/mcp");
        if (payload.auth_token) {
          values.MCP_TOKEN = payload.auth_token;
          values.AUTH_HEADER = "Bearer " + payload.auth_token;
        } else {
          values.MCP_TOKEN = TOKEN_UNAVAILABLE_MESSAGE;
          values.AUTH_HEADER = "Bearer YOUR_MCP_AUTH_TOKEN";
        }
        renderTemplates();
        if (!payload.token_configured) {
          setStatus("MCP_AUTH_TOKEN is not configured yet.");
        } else if (!payload.can_view_token) {
          setStatus(
            "MCP token is configured. Only Paperless admins can view it here.",
          );
        } else {
          setStatus("MCP connection details loaded.");
        }
      })
      .catch(function (error) {
        renderTemplates();
        setStatus(error.message || "Could not load MCP details.");
      });
  }

  Array.prototype.forEach.call(
    document.querySelectorAll("[data-copy-target], [data-copy-value]"),
    function (button) {
      button.addEventListener("click", function () {
        copyText(button);
      });
    },
  );

  renderTemplates();
  loadConfig();
})();
