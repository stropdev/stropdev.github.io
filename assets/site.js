// Paper is the website default; editor configuration and recordings are untouched.
document.documentElement.classList.add("js");
(function () {
  var KEY = "strop-palette";
  var PALETTES = ["paper", "paper-dark", "strop", "catppuccin-mocha", "tokyo-night", "gruvbox-dark", "nord", "dracula", "one-dark", "solarized-dark", "catppuccin-latte", "github-light", "one-light", "solarized-light"];
  var buttons = Array.from(document.querySelectorAll("[data-set-palette]"));

  function setPalette(name) {
    if (PALETTES.indexOf(name) === -1) {
      name = "paper";
    }
    document.documentElement.dataset.palette = name;
    try { localStorage.setItem(KEY, name); } catch (_) {}
    buttons.forEach(function (button) {
      var active = button.dataset.setPalette === name;
      button.classList.toggle("active", active);
      button.setAttribute("aria-pressed", active ? "true" : "false");
    });
  }

  buttons.forEach(function (button) {
    button.addEventListener("click", function () { setPalette(button.dataset.setPalette); });
  });

  var saved = null;
  try { saved = localStorage.getItem(KEY); } catch (_) {}
  setPalette(saved || "paper");
})();

// End-of-body scripts run after the source examples have been parsed.
if (window.Prism) {
  window.Prism.highlightAll();
  // Keep the surrounding prompt, copy control and command hook intact.
  var installCommand = document.querySelector("[data-install-cmd]");
  if (installCommand) window.Prism.highlightElement(installCommand);
}

// Copy the exact displayed installation command.
(function () {

  function fallbackCopy(text) {
    var field = document.createElement("textarea");
    field.value = text;
    field.setAttribute("readonly", "");
    field.style.position = "fixed";
    field.style.opacity = "0";
    document.body.appendChild(field);
    field.select();
    var copied = document.execCommand("copy");
    field.remove();
    if (!copied) throw new Error("Copy unavailable");
  }

  document.addEventListener("click", function (event) {
    var button = event.target.closest ? event.target.closest("[data-install-copy]") : null;
    if (!button) return;
    var text = button.dataset.copy || "";
    var status = document.querySelector("[data-copy-status]");
    var write = navigator.clipboard && window.isSecureContext
      ? navigator.clipboard.writeText(text)
      : Promise.reject(new Error("Clipboard API unavailable"));

    write.catch(function () { fallbackCopy(text); }).then(function () {
      button.classList.add("copied");
      button.textContent = "Copied";
      if (status) status.textContent = "Command copied to clipboard.";
      window.setTimeout(function () {
        button.classList.remove("copied");
        button.textContent = "Copy";
        if (status) status.textContent = "";
      }, 1600);
    }).catch(function () {
      if (status) status.textContent = "Copy unavailable; select the command manually.";
    });
  });
})();

// Latest release links retain GitHub's releases/latest URL if the API is unavailable.
(function () {
  var KEY = "strop-latest-release";
  var links = document.querySelectorAll("[data-latest-release]");
  if (!links.length) return;

  function show(release) {
    if (!release || !release.tag_name) return;
    links.forEach(function (link) {
      link.textContent = release.tag_name + " · latest release";
      if (release.html_url) link.href = release.html_url;
    });
  }

  try { show(JSON.parse(sessionStorage.getItem(KEY))); } catch (_) {}
  if (!window.fetch) return;
  fetch("https://api.github.com/repos/stropdev/strop/releases/latest", {
    headers: { Accept: "application/vnd.github+json" }
  }).then(function (response) {
    return response.ok ? response.json() : null;
  }).then(function (release) {
    if (!release || !release.tag_name) return;
    show(release);
    try {
      sessionStorage.setItem(KEY, JSON.stringify({ tag_name: release.tag_name, html_url: release.html_url }));
    } catch (_) {}
  }).catch(function () {});
})();
