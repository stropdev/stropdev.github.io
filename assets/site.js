// Palette picker: swap CSS variables and remember a supported palette.
(function () {
  var KEY = "strop-palette";
  var PALETTES = ["strop", "catppuccin-mocha", "tokyo-night", "gruvbox-dark", "nord", "dracula", "one-dark", "solarized-dark", "catppuccin-latte", "github-light", "one-light", "solarized-light"];
  var buttons = Array.from(document.querySelectorAll("[data-set-palette]"));

  function setPalette(name) {
    if (PALETTES.indexOf(name) === -1) {
      name = "strop";
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
  setPalette(saved || "strop");
})();

// Install method tabs and copy feedback.
(function () {
  var BREW = "brew install stropdev/tap/strop";
  var BREW_UP = "brew upgrade stropdev/tap/strop";
  var INSTALLS = {
    curl: {
      cmd: "curl -fsSL https://strop.dev/install.sh | sh",
      note: 'Prebuilt static binary · Linux x86_64/aarch64 · macOS arm64 · SHA-256 verified · <a href="https://github.com/stropdev/strop/releases">download tarballs</a>',
      update: "strop update"
    },
    brew: {
      cmd: BREW,
      note: "Homebrew formula — builds from source · macOS cask is prebuilt",
      update: BREW_UP
    },
    cargo: {
      cmd: "cargo install strop-editor --locked",
      note: "From crates.io — builds from source · requires a Rust toolchain",
      update: "cargo install strop-editor --locked"
    },
    mise: {
      cmd: "mise use cargo:strop-editor",
      note: "Pinned per-project via mise's cargo backend",
      update: "mise up strop-editor"
    }
  };

  function setInstall(name) {
    var data = INSTALLS[name];
    if (!data) return;
    document.querySelectorAll("[data-install]").forEach(function (button) {
      var active = button.dataset.install === name;
      button.classList.toggle("active", active);
      button.setAttribute("aria-pressed", active ? "true" : "false");
    });
    var command = document.querySelector("[data-install-cmd]");
    if (command) command.textContent = data.cmd;
    var copy = document.querySelector("[data-install-copy]");
    if (copy) copy.dataset.copy = data.cmd;
    var note = document.querySelector("[data-install-note]");
    if (note) note.innerHTML = data.note;
    var update = document.querySelector("[data-install-update]");
    if (update) update.textContent = data.update;
  }

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
    var method = event.target.closest ? event.target.closest("[data-install]") : null;
    if (method) setInstall(method.dataset.install);

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
