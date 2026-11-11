#!/usr/bin/env python3
"""Build strop.dev from the strop repository.

    python3 build.py /path/to/strop

Reads the editor repo and writes, deterministically:

- `index.html`, `start.html`, `engineering.html` and `neovim.html` from the
  hand-written fragments in `src/`, with the facts below filled in;
- `docs/<name>.html` from `docs/*.md`, and `docs/index.html`;
- `changelog.html` (the last three releases) and `changelog-all.html` from
  `CHANGELOG.md`;
- vendored copies of `CHANGELOG.md` and `install.sh`;
- the palette values in `assets/site.css`, from the theme sources.

Facts come from the repo (version, release date, language count, the proved
claims in `proofs/Audit.lean`, the Missing and Reassigned lists in
`docs/vim-compat.md`) and from `img/frames.json`, which `tools/frames.py`
writes next to the frames it captures.

The site describes strop as of SITE_DESCRIBES. Built from an older tree,
every page carries a line saying so, and `tools/check_site.py` lets keys
that tree does not have yet pass as pending; from that release on, the line
is gone and a missing key fails the check.

Standard library only. The generated files are committed; the deploy is
static.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

SITE = Path(__file__).resolve().parent
sys.path.insert(0, str(SITE / "tools"))
from md import Document, Markdown, convert, slugify  # noqa: E402

REPO_URL = "https://github.com/stropdev/strop"
SITE_DESCRIBES = (0, 62)
RECENT_RELEASES = 3

# The docs index, by what the reader wants to do. Each entry is
# (doc name, title on the site, one line on the site). The repository's own
# titles and lead paragraphs are written for maintainers; these are not.
DOC_GROUPS: List[Tuple[str, List[Tuple[str, str, str]]]] = [
    ("Find and change", [
        ("search", "Find files, search and replace",
         "The file finder, project search and replace, and the words that narrow them: "
         "<code>path:</code>, <code>language:</code>, <code>regex:</code>."),
        ("filesystem", "Create, rename, move and delete files",
         "The directory buffer and its file operations. Each one is shown for review before it happens."),
    ]),
    ("Git", [
        ("git", "Git", "Status, commit, branches, blame, log, history and hunks."),
    ]),
    ("Code", [
        ("editor", "Completion, indentation, language servers and themes",
         "What the editor does as you type, how language servers start and report, the six palettes."),
    ]),
    ("Terminals and other machines", [
        ("terminal-and-scripting", "Terminals and scripting",
         "A shell in a split, driving the editor from a script, and recording a bug report."),
        ("remote", "Edit over SSH", "Open files and directories on another machine with plain OpenSSH."),
    ]),
    ("Reference", [
        ("cli", "The command line", "Every subcommand and flag of <code>strop</code>."),
        ("vim-compat", "Every key", "The whole keymap, generated from the binary's command table."),
    ]),
    ("Background", [
        ("nucleo-decision", "Why the fuzzy matcher is nucleo", "A design record."),
    ]),
]
OPTIONAL_DOCS = {"git"}  # arrives in 0.62; an older tree is built without it

PALETTE_NAMES = [  # (data-palette, name, kind), in the switcher's order
    ("hone", "Hone", "dark · default"), ("slate", "Slate", "low-chroma dark"),
    ("carbide", "Carbide", "high-contrast dark"), ("vellum", "Vellum", "light"),
    ("paper", "Paper", "light"), ("paper-dark", "Paper Dark", "dark"),
]


# --------------------------------------------------------------------------- repo facts

@dataclass
class Facts:
    version: str
    date: str
    describe: str
    languages: int
    claims: List[str] = field(default_factory=list)  # required theorems, from proofs/Audit.lean

    @property
    def preview(self) -> bool:
        """True when the tree is older than the release the site's copy describes."""
        return tuple(int(n) for n in self.version.split(".")[:2]) < SITE_DESCRIBES


def read_facts(repo: Path) -> Facts:
    cargo = (repo / "Cargo.toml").read_text(encoding="utf-8")
    m = re.search(r"^\[workspace\.package\](?:.*\n)*?version\s*=\s*\"([^\"]+)\"", cargo, re.M)
    if not m:
        raise SystemExit("Cargo.toml: no [workspace.package] version")
    version = m.group(1)
    changelog = (repo / "CHANGELOG.md").read_text(encoding="utf-8")
    m = re.search(rf"^## {re.escape(version)} — (\d{{4}}-\d{{2}}-\d{{2}})\s*$", changelog, re.M)
    if not m:
        raise SystemExit(f"CHANGELOG.md has no entry for {version}; build from a released tree")
    date = m.group(1)
    try:
        describe = subprocess.run(["git", "-C", str(repo), "describe", "--tags", "--always", "--dirty"],
                                  check=True, capture_output=True, text=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        describe = f"v{version}"
    languages = count_languages(repo / "crates/strop-syntax/src/languages.rs")
    claims = parse_claims(repo / "proofs/Audit.lean")
    return Facts(version, date, describe, languages, claims)


def parse_claims(path: Path) -> List[str]:
    """The headline theorems the axiom audit requires (``claims`` in Audit.lean)."""
    text = path.read_text(encoding="utf-8")
    m = re.search(r"def claims : List Name := \[(.*?)\]", text, re.S)
    if not m:
        raise SystemExit("Audit.lean: no claims list")
    names = re.findall(r"``Strop\.Kernel\.([A-Za-z0-9_]+)", m.group(1))
    if not names:
        raise SystemExit("Audit.lean: claims list is empty")
    return names


def count_languages(path: Path) -> int:
    """Languages a file can open as: registry entries with an extension, filename or interpreter.

    Injection-only grammars (Markdown's inline and rustdoc variants) have none and are not counted.
    """
    text = path.read_text(encoding="utf-8")
    m = re.search(r"static LANGUAGES: &\[Entry\] = &\[(.*?)\n\];", text, re.S)
    if not m:
        raise SystemExit("languages.rs: LANGUAGES table not found")
    count = 0
    for entry in re.findall(r"Entry \{(.*?)\n    \}", m.group(1), re.S):
        openers = re.findall(r"(?:extensions|filenames|interpreters): &\[([^\]]*)\]", entry)
        if any(o.strip() for o in openers):
            count += 1
    if count == 0:
        raise SystemExit("languages.rs: no openable languages parsed")
    return count


# --------------------------------------------------------------------------- page chrome

def page(*, title: str, description: str, body: str, root: str, current: str, facts: Facts,
         source: str = "", body_class: str = "") -> str:
    def nav(href: str, label: str, key: str) -> str:
        cur = ' aria-current="page"' if key == current else ""
        return f'<a href="{href}"{cur}>{label}</a>'

    describes = ".".join(str(n) for n in SITE_DESCRIBES)
    preview = (f'<p class="preview-note">Preview: this site describes strop {describes}. It was built from '
               f'{html.escape(facts.version)}, which does not have all of it yet.</p>\n' if facts.preview else "")
    # A page generated from a repository document says which; check_site.py holds
    # only the pages written here to the site's own wording rules.
    source_meta = f'<meta name="strop-source" content="{html.escape(source, quote=True)}">\n' if source else ""
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(description, quote=True)}">
<meta name="color-scheme" content="dark light">
<meta name="strop-version" content="{html.escape(facts.version, quote=True)}">
<meta name="strop-describes" content="{describes}">
{source_meta}<link rel="icon" href="{root}assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="{root}assets/site.css">
<script>try{{var p=localStorage.getItem("strop-palette");if(p)document.documentElement.dataset.palette=p}}catch(e){{}}</script>
</head>
<body class="{body_class}">
<a class="skip" href="#main">Skip to content</a>
<header class="top">
  <div class="shell top-inner">
    <a class="brand" href="{root}">strop</a>
    <nav aria-label="Site">
      {nav(root + "docs/", "Docs", "docs")}
      {nav(root + "neovim.html", "From Neovim", "neovim")}
      {nav(root + "changelog.html", "Changelog", "changelog")}
      <a href="{REPO_URL}">GitHub</a>
    </nav>
  </div>
</header>
<main id="main">
{preview}{body}
</main>
<footer class="foot">
  <div class="shell foot-inner">
    <p>MIT license · © 2026 <a href="https://github.com/tknawara">Tarek Nawara</a></p>
    <p><a href="{root}start.html">First ten minutes</a> · <a href="{root}engineering.html">Engineering</a> · <a href="{REPO_URL}/releases/latest">Release v{html.escape(facts.version)}</a> · <a href="{root}#palette">Palette</a></p>
  </div>
</footer>
<script src="{root}assets/site.js"></script>
</body>
</html>
"""


def strip_tags(text: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", text))


# --------------------------------------------------------------------------- hand-written pages

HEADER = re.compile(r"\A<!--\n(.*?)\n-->\n", re.S)


def build_fragment(name: str, values: Dict[str, str], facts: Facts) -> str:
    """`src/NAME.html` is a page body with a `key: value` header comment and `{{slots}}`."""
    source = (SITE / "src" / f"{name}.html").read_text(encoding="utf-8")
    m = HEADER.match(source)
    if not m:
        raise SystemExit(f"src/{name}.html: no header comment")
    meta = dict(line.split(": ", 1) for line in m.group(1).splitlines())
    for key in ("title", "description"):
        if key not in meta:
            raise SystemExit(f"src/{name}.html: header has no {key}")

    def slot(match: re.Match) -> str:
        if match.group(1) not in values:
            raise SystemExit(f"src/{name}.html: unknown slot {{{{{match.group(1)}}}}}")
        return values[match.group(1)]

    body = re.sub(r"\{\{([a-z_]+)\}\}", slot, source[m.end():])
    text = page(title=meta["title"], description=meta["description"], body=body.rstrip("\n"), root="./",
                current=meta.get("nav", ""), facts=facts, body_class=meta.get("class", ""))
    (SITE / f"{name}.html").write_text(text, encoding="utf-8")
    return f"{name}.html"


def frames_html() -> str:
    """The landing page's frames: radio-button tabs, so they work without script."""
    path = SITE / "img" / "frames.json"
    if not path.exists():
        raise SystemExit("img/frames.json is missing; run tools/frames.py (see README)")
    manifest = json.loads(path.read_text(encoding="utf-8"))
    frames = list(manifest["frames"].items())
    if not 1 <= len(frames) <= 4:
        raise SystemExit("the frame tabs are styled for one to four frames")
    picks, tabs, figures = [], [], []
    for i, (name, frame) in enumerate(frames):
        picks.append(f'<input class="frame-pick" type="radio" name="frame" id="pick-{name}"'
                     f'{" checked" if i == 0 else ""}>')
        tabs.append(f'<label for="pick-{name}">{html.escape(frame["tab"])}</label>')
        lazy = "" if i == 0 else ' loading="lazy"'
        figures.append(
            f'<figure class="frame">\n'
            f'    <div class="frame-scroll"><img src="{frame["file"]}" width="{frame["width"]}" '
            f'height="{frame["height"]}" alt="{html.escape(frame["alt"], quote=True)}"{lazy}></div>\n'
            f'    <figcaption>{frame["caption"]}</figcaption>\n'
            f'  </figure>')
    note = (f'<p class="frames-note">Each frame is the screen of strop {html.escape(manifest["version"])}, '
            f'{manifest["cols"]} by {manifest["rows"]} cells, captured from the binary and converted to SVG. '
            f'Nothing is drawn by hand.</p>')
    return ("\n  ".join(picks) + '\n  <div class="frame-tabs">' + "".join(tabs) + "</div>\n  "
            + "\n  ".join(figures) + "\n  " + note)


def palettes_html(repo: Path) -> str:
    buttons = []
    for palette, name, kind in PALETTE_NAMES:
        file, const = next((f, c) for f, c, selector in PALETTES if f'data-palette="{palette}"' in selector)
        values = read_palette(repo / "crates/strop-core/src/theme" / file, const)
        buttons.append(
            f'<button type="button" data-set-palette="{palette}" aria-pressed="false">'
            f'<span class="sw" style="--sw-base:{values[("bg", "base")]};--sw-accent:{values[(None, "accent")]}"></span>'
            f'<span><span class="name">{name}</span><span class="kind">{kind}</span></span></button>')
    return "\n    ".join(buttons)


# --------------------------------------------------------------------------- docs

def docs_link(url: str) -> str:
    if url.startswith(("http://", "https://", "#", "mailto:")):
        return url
    if url.startswith("../plans/"):
        return f"{REPO_URL}/blob/main/plans/{url[len('../plans/'):]}"
    if url.startswith("../"):
        return f"{REPO_URL}/blob/main/{url[3:]}"
    m = re.match(r"^([A-Za-z0-9_-]+)\.md(#.*)?$", url)
    if m:
        return f"{m.group(1)}.html{m.group(2) or ''}"
    raise ValueError(f"docs link I cannot rewrite: {url!r}")


def build_docs(repo: Path, facts: Facts) -> List[str]:
    present = sorted(p.stem for p in (repo / "docs").glob("*.md"))
    groups: List[Tuple[str, List[Tuple[str, str, str]]]] = []
    listed = set()
    for group, entries in DOC_GROUPS:
        kept = []
        for name, title, blurb in entries:
            listed.add(name)
            if name in present:
                kept.append((name, title, blurb))
            elif name not in OPTIONAL_DOCS:
                raise SystemExit(f"docs/{name}.md is missing from the repo")
        if kept:
            groups.append((group, kept))
    docs: Dict[str, Document] = {}
    for name in present:
        source = (repo / "docs" / f"{name}.md").read_text(encoding="utf-8")
        try:
            docs[name] = convert(source, docs_link)
        except ValueError as e:
            raise SystemExit(f"docs/{name}.md: {e}")
    # A document the table above does not know keeps the repository's own title and lead.
    extra = [(n, html.escape(docs[n].title), docs[n].lead) for n in present if n not in listed]
    if extra:
        groups.append(("More", extra))
    order = [entry for _, entries in groups for entry in entries]

    out_dir = SITE / "docs"
    out_dir.mkdir(exist_ok=True)
    for stale in out_dir.glob("*.html"):
        stale.unlink()
    written = []
    for idx, (name, title, _) in enumerate(order):
        doc = docs[name]
        toc = "".join(f'<li><a href="#{h.anchor}">{h.text}</a></li>' for h in doc.headings if h.level <= 2)
        pager = ""
        if idx > 0:
            pager += f'<a class="pager-prev" href="{order[idx - 1][0]}.html">← {order[idx - 1][1]}</a>'
        if idx + 1 < len(order):
            pager += f'<a class="pager-next" href="{order[idx + 1][0]}.html">{order[idx + 1][1]} →</a>'
        side = "".join(
            f'<p class="side-title">{group}</p><ol class="side-docs">'
            + "".join(f'<li><a href="{n}.html"{" aria-current=" + chr(34) + "page" + chr(34) if n == name else ""}>{t}</a></li>'
                      for n, t, _ in entries)
            + "</ol>"
            for group, entries in groups)
        body = f"""<div class="shell doc-layout">
  <aside class="doc-side">
    <p class="side-title"><a href="./">All docs</a></p>
    {side}
    {"<p class='side-title side-toc-title'>On this page</p><ol class='side-toc'>" + toc + "</ol>" if toc else ""}
  </aside>
  <article class="doc">
    <p class="eyebrow">Docs</p>
    <h1>{title}</h1>
    <div class="prose">
{doc.body}
    </div>
    <nav class="pager" aria-label="Documents">{pager}</nav>
    <p class="provenance">This page is <a href="{REPO_URL}/blob/main/docs/{name}.md"><code>docs/{name}.md</code></a> from the strop repository at <code>{html.escape(facts.describe)}</code>.</p>
  </article>
</div>"""
        text = page(title=f"{strip_tags(title)} — strop docs", description=strip_tags(doc.lead)[:200], body=body,
                    root="../", current="docs", facts=facts, source=f"docs/{name}.md", body_class="docs-page")
        (out_dir / f"{name}.html").write_text(text, encoding="utf-8")
        written.append(f"docs/{name}.html")

    def card(href: str, title: str, blurb: str) -> str:
        return f'<li><a href="{href}"><strong>{title}</strong><span>{blurb}</span></a></li>'

    sections = "".join(
        f'\n  <h2>{group}</h2>\n  <ul class="doc-cards">\n    '
        + "\n    ".join(card(f"{n}.html", t, b) for n, t, b in entries) + "\n  </ul>"
        for group, entries in groups)
    index_body = f"""<div class="shell page">
  <p class="eyebrow">Docs</p>
  <h1>Docs</h1>
  <p class="lede">Pick what you want to do. Inside the editor, <kbd>Space</kbd> <kbd>?</kbd> lists every key and <code>:help</code> opens the same reference.</p>
  <h2>Start</h2>
  <ul class="doc-cards">
    {card("../start.html", "First ten minutes", "Install, open a project, find a file, search, replace, commit.")}
    {card("../neovim.html", "Coming from Neovim", "What works the same, what differs, and what is missing.")}
  </ul>{sections}
  <p class="aside">The reference pages are the files in the repository's <a href="{REPO_URL}/tree/main/docs"><code>docs/</code></a> directory at <code>{html.escape(facts.describe)}</code>, shown as they are.</p>
</div>"""
    text = page(title="Docs — strop", description="strop documentation, by what you want to do.",
                body=index_body, root="../", current="docs", facts=facts, body_class="docs-page")
    (out_dir / "index.html").write_text(text, encoding="utf-8")
    written.append("docs/index.html")
    return written


# --------------------------------------------------------------------------- coming from Neovim

def compat_slots(repo: Path) -> Dict[str, str]:
    """The parts of `docs/vim-compat.md` the Neovim page shows.

    The file is generated from the keymap (`strop compat`). Its sections are
    the binary's own: one per mode or surface, then Missing and Reassigned.
    """
    source = (repo / "docs" / "vim-compat.md").read_text(encoding="utf-8")
    sections: Dict[str, str] = {}
    order: List[str] = []
    for part in re.split(r"^## ", source, flags=re.M)[1:]:
        title, _, body = part.partition("\n")
        sections[title.strip()] = body.strip()
        order.append(title.strip())

    def rendered(title: str, since: str) -> str:
        if title not in sections:
            return (f'<p class="pending">The keymap listing of this build has no {title} list; '
                    f'the binary prints one from strop {since} on.</p>')
        # The page introduces each list in its own words; take the rows only.
        rows_only = sections[title][sections[title].index("\n- ") + 1:] if "\n- " in sections[title] else sections[title]
        try:
            return Markdown(docs_link).convert(rows_only)
        except ValueError as e:
            raise SystemExit(f"docs/vim-compat.md, {title}: {e}")

    rows = []
    for title in order:
        if title in ("Missing", "Reassigned"):
            continue
        count = len(re.findall(r"^- `✓", sections[title], flags=re.M))
        rows.append(f'<li><a href="docs/vim-compat.html#{slugify(title)}">{html.escape(title)}</a>'
                    f'<span>{count} rows</span></li>')
    return {
        "compat_sections": "\n      ".join(rows),
        "compat_missing": rendered("Missing", "0.59"),
        "compat_reassigned": rendered("Reassigned", "0.59"),
    }


# --------------------------------------------------------------------------- changelog

def build_changelog(repo: Path, facts: Facts) -> List[str]:
    source = (repo / "CHANGELOG.md").read_text(encoding="utf-8")
    parts = re.split(r"^(?=## )", source, flags=re.M)
    # A tree between releases has an Unreleased section; the site lists releases.
    releases = [p for p in parts[1:] if not p.startswith("## Unreleased")]

    def heading_id(level: int, text: str) -> str:
        return ("release-" if level == 2 else "") + slugify(text)

    def link(url: str) -> str:
        return url if url.startswith(("http://", "https://", "#")) else f"{REPO_URL}/blob/main/{url}"

    def render(chunk: List[str]) -> str:
        try:
            return convert("".join(chunk), link, heading_id).body
        except ValueError as e:
            raise SystemExit(f"CHANGELOG.md: {e}")

    def write(name: str, heading: str, lede: str, chunk: List[str], tail: str) -> str:
        body = f"""<div class="shell page changelog">
  <p class="eyebrow">Changelog</p>
  <h1>{heading}</h1>
  <p class="lede">{lede}</p>
  <div class="prose">
{render(chunk)}
  </div>{tail}
</div>"""
        text = page(title=f"{heading} — strop", description="What changed in strop, release by release.",
                    body=body, root="./", current="changelog", facts=facts, source="CHANGELOG.md")
        (SITE / name).write_text(text, encoding="utf-8")
        return name

    older = len(releases) - RECENT_RELEASES
    return [
        write("changelog.html", "What changed",
              f'The last {RECENT_RELEASES} releases, newest first. Tarballs and checksums are on '
              f'<a href="{REPO_URL}/releases">GitHub releases</a>.',
              releases[:RECENT_RELEASES],
              f'\n  <p class="more"><a href="changelog-all.html">All {len(releases)} releases →</a></p>'
              if older > 0 else ""),
        write("changelog-all.html", "Every release",
              f'{len(releases)} releases, newest first, from <a href="{REPO_URL}/blob/main/CHANGELOG.md">'
              f'<code>CHANGELOG.md</code></a> at <code>{html.escape(facts.describe)}</code>. '
              f'<a href="changelog.html">The last {RECENT_RELEASES} only</a>.',
              releases, ""),
    ]


def vendor(repo: Path) -> List[str]:
    written = []
    for name in ("CHANGELOG.md", "install.sh"):
        shutil.copyfile(repo / name, SITE / name)
        written.append(name)
    return written


# --------------------------------------------------------------------------- palettes
# The site's six palettes are the editor's, read from the compiled-in theme
# sources so the two can never disagree. Each CSS block is located by its
# selector; only the token values inside it are rewritten.
PALETTES = [  # (theme file, Rust const, CSS selector that opens the block)
    ("hone.rs", "HONE", ':root, :root[data-palette="hone"] {'),
    ("vellum.rs", "VELLUM", ":root:not([data-palette]) {"),
    ("vellum.rs", "VELLUM", ':root[data-palette="vellum"] {'),
    ("slate.rs", "SLATE", ':root[data-palette="slate"] {'),
    ("carbide.rs", "CARBIDE", ':root[data-palette="carbide"] {'),
    ("paper.rs", "PAPER", ':root[data-palette="paper"] {'),
    ("paper.rs", "PAPER_DARK", ':root[data-palette="paper-dark"] {'),
]
TOKENS = {  # CSS custom property -> (Rust group, field); group None = top level
    "--bg-base": ("bg", "base"), "--bg-surface": ("bg", "surface"),
    "--bg-raised": ("bg", "raised"), "--bg-selection": ("bg", "selection"),
    "--fg-text": ("fg", "text"), "--fg-secondary": ("fg", "secondary"),
    "--fg-muted": ("fg", "muted"), "--fg-faint": ("fg", "faint"),
    "--accent": (None, "accent"), "--on-accent": ("fg", "on_accent"),
}


def read_palette(path: Path, const: str) -> dict:
    text = path.read_text(encoding="utf-8")
    start = text.find(f"pub const {const}: Theme = Theme {{")
    if start < 0:
        raise SystemExit(f"{path}: no theme const {const}")
    body = text[start:text.find("\n};", start)]
    values, group = {}, None
    for line in body.splitlines()[1:]:
        stripped = line.strip()
        opened = re.match(r"(\w+): \w+ \{$", stripped)
        if opened:
            group = opened.group(1)
            continue
        if stripped.startswith("}"):
            group = None
            continue
        entry = re.match(r"(?:r#)?(\w+): hex\(0x([0-9a-fA-F]{6})\),$", stripped)
        if entry:
            values[(group, entry.group(1))] = "#" + entry.group(2).lower()
    return values


def sync_palettes(repo: Path) -> str:
    css_path = SITE / "assets" / "site.css"
    css = css_path.read_text(encoding="utf-8")
    themes = repo / "crates/strop-core/src/theme"
    for file, const, selector in PALETTES:
        values = read_palette(themes / file, const)
        open_at = css.find(selector)
        if open_at < 0:
            raise SystemExit(f"site.css has no block {selector}")
        close_at = css.find("}", open_at + len(selector))
        block = css[open_at:close_at]
        for prop, key in TOKENS.items():
            if key not in values:
                raise SystemExit(f"{file}:{const} has no {key}")
            block, n = re.subn(re.escape(prop) + r": #[0-9a-fA-F]{6};", f"{prop}: {values[key]};", block)
            if n != 1:
                raise SystemExit(f"site.css block {selector} must set {prop} exactly once")
        css = css[:open_at] + block + css[close_at:]
    css_path.write_text(css, encoding="utf-8")
    return "assets/site.css"


# --------------------------------------------------------------------------- main

def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("repo", type=Path, help="path to a checkout of stropdev/strop at the released tag")
    args = ap.parse_args(argv)
    repo = args.repo.resolve()
    if not (repo / "Cargo.toml").exists():
        raise SystemExit(f"{repo} is not the strop repository")
    facts = read_facts(repo)
    values = {
        "version": html.escape(facts.version),
        "date": html.escape(facts.date),
        "describe": html.escape(facts.describe),
        "languages": str(facts.languages),
        "claims": "".join(f"<li>{html.escape(c)}</li>" for c in facts.claims),
        "frames": frames_html(),
        "palettes": palettes_html(repo),
        "git_doc": "docs/git.html" if (repo / "docs" / "git.md").exists() else "docs/vim-compat.html#git",
        **compat_slots(repo),
    }
    written = vendor(repo) + build_docs(repo, facts) + build_changelog(repo, facts)
    written += [build_fragment(name, values, facts) for name in ("index", "start", "neovim", "engineering")]
    written.append(sync_palettes(repo))
    print(f"strop {facts.version} ({facts.describe}), released {facts.date}, {facts.languages} languages")
    for w in written:
        print(f"  wrote {w}")
    frames_version = json.loads((SITE / "img" / "frames.json").read_text(encoding="utf-8"))["version"]
    if frames_version != facts.version:
        print(f"  note: the frames are of strop {frames_version}; rerun tools/frames.py with the "
              f"{facts.version} binary (tools/check_site.py fails until then)")
    if facts.preview:
        print(f"  note: preview build; the copy describes {'.'.join(map(str, SITE_DESCRIBES))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
