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
