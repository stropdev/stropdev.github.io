#!/usr/bin/env python3
"""Render the vendored CHANGELOG.md into changelog.html.

The changelog's markdown is a fixed subset: # title, ## release,
### section, - bullets (wrapped lines continue the bullet), blank-line
paragraphs, **bold**, `code`. The previous hand conversion split every
wrapped source line into its own paragraph and produced nested
<ul><li></ul> garbage — this script joins continuations first, then
emits. Regenerate: python3 build_changelog.py
"""

import html
import pathlib
import re

ROOT = pathlib.Path(__file__).parent
SRC = ROOT / "CHANGELOG.md"
OUT = ROOT / "changelog.html"

HEAD = """<!doctype html>
<html lang="en" data-palette="strop">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>strop — changelog</title>
<meta name="description" content="strop release changelog.">
<link rel="icon" href="./assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="assets/site.css?v=5">
</head>
<body>
<a class="skip-link" href="#main-content">Skip to content</a>
<header class="topbar">
  <div class="shell nav-inner">
    <a class="brand-mini" href="/" aria-label="strop home">strop</a>
    <nav aria-label="Primary navigation">
      <a href="./docs.html">Docs</a>
      <a href="./roadmap.html">Roadmap</a>
      <a href="./changelog.html" aria-current="page">Changelog</a>
      <a href="https://github.com/stropdev/strop">GitHub</a>
    </nav>
  </div>
</header>
<main class="page-shell changelog" id="main-content">
<div class="page-intro">
  <p class="eyebrow">Release history</p>
  <h1>Changelog</h1>
  <p>Release notes and development history. Browse <a href="https://github.com/stropdev/strop/releases">all published releases on GitHub</a>.</p>
</div>
<div class="prose">
"""

FOOT = """</div>
</main>
<footer class="foot">
  <div class="shell footer-inner">
    <p><span class="caret-dot"></span>© 2026 <a href="https://github.com/tknawara">Tarek Nawara</a> · MIT license</p>
    <nav class="footer-links" aria-label="Footer navigation">
      <a href="https://github.com/stropdev">stropdev</a>
      <a href="https://github.com/stropdev/strop">Source</a>
    </nav>
    <p class="footer-right"><a class="version" data-latest-release href="https://github.com/stropdev/strop/releases/latest">Latest release</a></p>
  </div>
</footer>
<script src="assets/site.js?v=3"></script>
</body>
</html>
"""


def inline(text: str) -> str:
    text = html.escape(text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    return text


def render(md: str) -> str:
    out: list[str] = []
    in_list = False
    para: list[str] = []

    def flush_para():
        nonlocal para
        if para:
            out.append(f"<p>{inline(' '.join(para))}</p>")
            para = []

    def close_list():
        nonlocal in_list
        if in_list:
            out.append("</ul>")
            in_list = False

    lines = md.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("# "):
            i += 1  # the page has its own h1
            continue
        if line.startswith("## "):
            flush_para()
            close_list()
            heading = line[3:]
            anchor = re.sub(r"[^a-z0-9]+", "-", heading.lower()).strip("-")
            out.append(f'<h2 id="release-{anchor}">{inline(heading)}</h2>')
        elif line.startswith("### "):
            flush_para()
            close_list()
            out.append(f"<h3>{inline(line[4:])}</h3>")
        elif line.startswith("- "):
            flush_para()
            if not in_list:
                out.append("<ul>")
                in_list = True
            # wrapped lines belong to this bullet, not their own tag
            parts = [line[2:]]
            while i + 1 < len(lines) and lines[i + 1].startswith("  "):
                i += 1
                parts.append(lines[i].strip())
            out.append(f"<li>{inline(' '.join(parts))}</li>")
        elif not line.strip():
            flush_para()
            close_list()
        else:
            para.append(line.strip())
        i += 1
    flush_para()
    close_list()
    return "\n".join(out)


def main() -> None:
    body = render(SRC.read_text())
    OUT.write_text(HEAD + body + "\n" + FOOT)
    print(f"wrote {OUT.name} ({len(body)} bytes)")


if __name__ == "__main__":
    main()
