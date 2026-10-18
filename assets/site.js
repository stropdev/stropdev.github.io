// Palette picker: swaps the var set on <html>, persists across visits.
// The inline logo SVG is painted from those vars, so it re-themes with
// the page — no rebuild, no per-palette assets.
(function () {
  var KEY = "strop-palette";
  var buttons = document.querySelectorAll("[data-set-palette]");

  function setPalette(name) {
    document.documentElement.dataset.palette = name;
    try { localStorage.setItem(KEY, name); } catch (_) {}
    buttons.forEach(function (b) {
      b.classList.toggle("active", b.dataset.setPalette === name);
    });
  }

  buttons.forEach(function (b) {
    b.addEventListener("click", function () { setPalette(b.dataset.setPalette); });
  });

  var saved = null;
  try { saved = localStorage.getItem(KEY); } catch (_) {}
  setPalette(saved || "strop");
})();

// Install tabs (rootle pattern): pills swap command, note, and update line.
(function () {
  var BREW = "brew install stropdev/tap/strop";
  var BREW_UP = "brew upgrade stropdev/tap/strop";
  var INSTALLS = {
    curl: {
      cmd: "curl -fsSL https://strop.dev/install.sh | sh",
      note: 'prebuilt static binary · Linux / WSL x86_64 only · sha256-verified · <a href="https://github.com/stropdev/strop/releases">tarballs ↗</a>',
      update: "strop update",
    },
    brew: {
      cmd: BREW,
      note: "Linux / WSL x86_64 only · Homebrew source formula · requires Zig 0.16.0",
      update: BREW_UP,
    },
    cargo: {
      cmd: "cargo install strop-editor --locked",
      note: "Linux / WSL x86_64 only · crates.io source build · requires Rust and Zig 0.16.0",
      update: "cargo install strop-editor --locked",
    },
    mise: {
      cmd: "mise use cargo:strop-editor",
      note: "Linux / WSL x86_64 only · mise Cargo backend · requires Rust and Zig 0.16.0",
      update: "mise up strop-editor",
    },
  };

  function setInstall(name) {
    var data = INSTALLS[name];
    if (!data) return;
    var pills = document.querySelectorAll("[data-install]");
    for (var i = 0; i < pills.length; i++) {
      var on = pills[i].getAttribute("data-install") === name;
      pills[i].classList.toggle("active", on);
      pills[i].setAttribute("aria-pressed", on ? "true" : "false");
    }
    var cmd = document.querySelector("[data-install-cmd]");
    if (cmd) cmd.textContent = data.cmd;
    var copy = document.querySelector("[data-install-copy]");
    if (copy) copy.setAttribute("data-copy", data.cmd);
    var note = document.querySelector("[data-install-note]");
    if (note) note.innerHTML = data.note;
    var upd = document.querySelector("[data-install-update]");
    if (upd) upd.textContent = data.update;
  }

  document.addEventListener("click", function (ev) {
    var pill = ev.target.closest ? ev.target.closest("[data-install]") : null;
    if (pill) setInstall(pill.getAttribute("data-install"));
    var copyBtn = ev.target.closest ? ev.target.closest("[data-install-copy]") : null;
    if (copyBtn) {
      var text = copyBtn.getAttribute("data-copy") || "";
      if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(function () {
          copyBtn.classList.add("copied");
          copyBtn.textContent = "copied";
          setTimeout(function () {
            copyBtn.classList.remove("copied");
            copyBtn.textContent = "copy";
          }, 1200);
        });
      }
    }
  });
})();
