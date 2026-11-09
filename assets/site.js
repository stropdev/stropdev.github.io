// strop.dev — two behaviours, no framework: the palette switcher and the copy
// button. Every page works without this file; the <head> applies a stored
// palette before first paint so there is no flash.
document.documentElement.classList.add("js");

(function () {
  var KEY = "strop-palette";
  var PALETTES = ["hone", "slate", "carbide", "vellum", "paper", "paper-dark"];
  var buttons = Array.prototype.slice.call(document.querySelectorAll("[data-set-palette]"));

  function current() {
    return document.documentElement.dataset.palette || null;
  }

  function reflect() {
    var name = current();
    buttons.forEach(function (button) {
      button.setAttribute("aria-pressed", button.dataset.setPalette === name ? "true" : "false");
    });
  }

  function set(name) {
    if (name && PALETTES.indexOf(name) === -1) name = null;
    if (name) {
      document.documentElement.dataset.palette = name;
    } else {
      delete document.documentElement.dataset.palette;
    }
    try {
      if (name) localStorage.setItem(KEY, name); else localStorage.removeItem(KEY);
    } catch (_) {}
    reflect();
  }

  buttons.forEach(function (button) {
    button.addEventListener("click", function () {
      // Pressing the applied palette again returns to automatic (Hone, or Vellum in light mode).
      set(button.dataset.setPalette === current() ? null : button.dataset.setPalette);
    });
  });

  if (current() && PALETTES.indexOf(current()) === -1) set(null);
  reflect();
})();

(function () {
  var button = document.querySelector("[data-copy]");
  var status = document.querySelector("[data-copy-status]");
  if (!button) return;
  button.addEventListener("click", function () {
    var text = button.getAttribute("data-copy");
    var done = function () {
      if (status) status.textContent = "copied";
      window.setTimeout(function () { if (status) status.textContent = ""; }, 1800);
    };
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(text).then(done, function () {
        if (status) status.textContent = "select the command and copy it";
      });
    } else if (status) {
      status.textContent = "select the command and copy it";
    }
  });
})();
