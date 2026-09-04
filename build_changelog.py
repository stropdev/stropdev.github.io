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
<link rel="stylesheet" href="assets/site.css?v=2">
<style>
  main.changelog { max-width: 52rem; margin: 0 auto; padding: 5.5rem 1.25rem 4rem; }
  .changelog h1 { color: var(--accent); font-size: 1.6rem; margin: 0 0 .5rem; }
  .changelog h2 { color: var(--text); font-size: 1.15rem; margin: 2.5rem 0 .5rem; border-bottom: 1px solid var(--border); padding-bottom: .4rem; }
  .changelog h3 { color: var(--accent); font-size: .95rem; margin: 1.5rem 0 .25rem; }
  .changelog p, .changelog li { color: var(--muted); line-height: 1.65; }
  .changelog code { color: var(--syn-str); }
  .changelog strong { color: var(--text); }
  .changelog ul { padding-left: 1.25rem; }
</style>
</head>
<body>
<header class="topbar">
  <a class="brand-mini" href="/">strop</a>
  <nav>
    <a href="./docs.html">docs</a>
    <a href="./roadmap.html">roadmap</a>
    <a href="./changelog.html">changelog</a>
    <a href="https://github.com/stropdev/strop">github</a>
  </nav>
</header>
<main class="changelog">
<h1>changelog</h1>
"""

FOOT = """</main>
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
            out.append(f"<h2>{inline(line[3:])}</h2>")
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
