#!/usr/bin/env python3
"""Build strop.dev from the strop repository.

    python3 build.py /path/to/strop

Reads the editor repo and writes, deterministically:

- `docs/index.html` and `docs/<name>.html` from `docs/*.md`;
- `changelog.html` from `CHANGELOG.md`;
- the build-stamped regions of `index.html` (version chip, release date,
  language count, the Status table from `plans/STATUS.md`);
- vendored copies of `CHANGELOG.md` and `install.sh`.

Standard library only. The Markdown converter covers exactly the subset the
repo's documents use (ATX headings, paragraphs, `-`/`1.` lists with wrapped
lines, fenced code, pipe tables, inline code, links, reference links, bold,
italic) and refuses anything it does not understand rather than guessing.
The generated files are committed; the deploy is static.
"""

from __future__ import annotations

import argparse
import html
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

SITE = Path(__file__).resolve().parent
REPO_URL = "https://github.com/stropdev/strop"

# Reading order of the docs index; anything else in docs/ follows alphabetically.
USER_DOCS = ["cli", "editor", "search", "filesystem", "remote", "terminal-and-scripting", "vim-compat"]
DESIGN_DOCS = ["worker-protocol", "nucleo-decision"]


# --------------------------------------------------------------------------- markdown

@dataclass
class Heading:
    level: int
    text: str  # rendered inline HTML
    plain: str
    anchor: str


@dataclass
class Document:
    title: str
    body: str
    headings: List[Heading]
    lead: str = ""  # first paragraph, rendered inline (for indexes)


def slugify(text: str) -> str:
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "section"


class Markdown:
    """A small, strict converter for the repository's Markdown subset."""

    FENCE = re.compile(r"^(```+)\s*([A-Za-z0-9_+.-]*)\s*$")
    HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
    BULLET = re.compile(r"^- (.*)$")
    ORDERED = re.compile(r"^(\d+)\. (.*)$")
    TABLE_SEP = re.compile(r"^\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?\s*$")
    REF_DEF = re.compile(r"^\[([^\]]+)\]:\s+(\S+)\s*$")
    UNSUPPORTED = re.compile(r"^(>|\s*[*+] |\d+\) |!\[|---\s*$|\*\*\*|<[a-zA-Z/!])")

    def __init__(self, link: Callable[[str], str], heading_id: Optional[Callable[[int, str], str]] = None):
        self.link = link
        self.heading_id = heading_id or (lambda level, text: slugify(text))
        self.refs: Dict[str, str] = {}
        self.anchors: Dict[str, int] = {}
        self.headings: List[Heading] = []
        self.lead = ""

    # -- inline -------------------------------------------------------------

    def inline(self, text: str) -> str:
        codes: List[str] = []

        def stash(m: re.Match) -> str:
            codes.append(f"<code>{html.escape(m.group(2))}</code>")
            return f"\x00{len(codes) - 1}\x00"

        text = re.sub(r"(`+)(.+?)\1", stash, text)
        text = html.escape(text, quote=False)
        text = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", lambda m: self.anchor_tag(m.group(1), m.group(2)), text)
        text = re.sub(r"\[([^\]\x00]+)\](?![\(\[:])", self.ref_link, text)
        text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
        text = re.sub(r"(?<![\w*])\*([^*\n]+?)\*(?![\w*])", r"<em>\1</em>", text)
        text = re.sub(r"\x00(\d+)\x00", lambda m: codes[int(m.group(1))], text)
        return text

    def ref_link(self, m: re.Match) -> str:
        label = m.group(1)
        url = self.refs.get(html.unescape(label).lower())
        if url is None:
            return m.group(0)
        return self.anchor_tag(label, url)

    def anchor_tag(self, label: str, url: str) -> str:
        href = html.escape(self.link(html.unescape(url)), quote=True)
        return f'<a href="{href}">{label}</a>'

    # -- blocks -------------------------------------------------------------

    def convert(self, source: str) -> str:
        lines = source.splitlines()
        body: List[str] = []
        for line in lines:
            m = self.REF_DEF.match(line)
            if m:
                self.refs[m.group(1).lower()] = m.group(2)
            else:
                body.append(line)
        out: List[str] = []
        i = 0
        while i < len(body):
            line = body[i]
            if not line.strip():
                i += 1
                continue
            m = self.FENCE.match(line)
            if m:
                fence, lang = m.group(1), m.group(2)
                code: List[str] = []
                i += 1
                while i < len(body) and body[i].strip() != fence:
                    code.append(body[i])
                    i += 1
                if i >= len(body):
                    raise ValueError("unterminated code fence")
                i += 1
                attr = f' class="language-{html.escape(lang)}"' if lang else ""
                out.append(f"<pre><code{attr}>{html.escape(chr(10).join(code))}</code></pre>")
                continue
            m = self.HEADING.match(line)
            if m:
                out.append(self.heading(len(m.group(1)), m.group(2)))
                i += 1
                continue
            if self.BULLET.match(line) or self.ORDERED.match(line):
                i = self.list(body, i, out)
                continue
            if line.lstrip().startswith("|") and i + 1 < len(body) and self.TABLE_SEP.match(body[i + 1]):
                i = self.table(body, i, out)
                continue
            if self.UNSUPPORTED.match(line):
                raise ValueError(f"unsupported Markdown construct: {line!r}")
            para: List[str] = []
            while i < len(body) and body[i].strip() and not self.block_start(body[i]):
                para.append(body[i].strip())
                i += 1
            rendered = self.inline(" ".join(para))
            if not self.lead:
                self.lead = rendered
            out.append(f"<p>{rendered}</p>")
        return "\n".join(out)

    def block_start(self, line: str) -> bool:
        return bool(self.FENCE.match(line) or self.HEADING.match(line) or self.BULLET.match(line)
                    or self.ORDERED.match(line) or line.lstrip().startswith("|"))

    def heading(self, level: int, text: str) -> str:
        anchor = self.heading_id(level, text)
        n = self.anchors.get(anchor, 0)
        self.anchors[anchor] = n + 1
        if n:
            anchor = f"{anchor}-{n + 1}"
        rendered = self.inline(text)
        self.headings.append(Heading(level, rendered, html.unescape(re.sub(r"<[^>]+>", "", rendered)), anchor))
        return f'<h{level} id="{anchor}">{rendered}</h{level}>'

    def list(self, body: List[str], i: int, out: List[str]) -> int:
        ordered = bool(self.ORDERED.match(body[i]))
        pattern = self.ORDERED if ordered else self.BULLET
        indent = 3 if ordered else 2
        items: List[str] = []
        while i < len(body):
            m = pattern.match(body[i])
            if not m:
                break
            parts = [m.group(2) if ordered else m.group(1)]
            i += 1
            while i < len(body) and body[i].startswith(" " * indent) and body[i].strip():
                parts.append(body[i].strip())
                i += 1
            items.append(f"<li>{self.inline(' '.join(parts))}</li>")
        tag = "ol" if ordered else "ul"
        out.append(f"<{tag}>\n" + "\n".join(items) + f"\n</{tag}>")
        return i

    @staticmethod
    def cells(row: str) -> List[str]:
        row = row.strip()
        if row.startswith("|"):
            row = row[1:]
        if row.endswith("|") and not row.endswith("\\|"):
            row = row[:-1]
        cells, current, in_code = [], [], False
        for ch in row:
            if ch == "`":
                in_code = not in_code
            if ch == "|" and not in_code:
                cells.append("".join(current).strip())
                current = []
            else:
                current.append(ch)
        cells.append("".join(current).strip())
        return cells

    def table(self, body: List[str], i: int, out: List[str]) -> int:
        header = self.cells(body[i])
        i += 2
        rows: List[List[str]] = []
        while i < len(body) and body[i].lstrip().startswith("|"):
            rows.append(self.cells(body[i]))
            i += 1
        head = "".join(f"<th>{self.inline(c)}</th>" for c in header)
        parts = [f"<table>\n<thead><tr>{head}</tr></thead>\n<tbody>"]
        for row in rows:
            row = row + [""] * (len(header) - len(row))
            parts.append("<tr>" + "".join(f"<td>{self.inline(c)}</td>" for c in row[: len(header)]) + "</tr>")
        parts.append("</tbody>\n</table>")
        out.append("\n".join(parts))
        return i


def convert(source: str, link: Callable[[str], str], heading_id=None) -> Document:
    md = Markdown(link, heading_id)
    body = md.convert(source)
    title = next((h.plain for h in md.headings if h.level == 1), "")
    # The page supplies its own title element; drop the first H1 from the body.
    body = re.sub(r'^<h1 id="[^"]*">.*?</h1>\n?', "", body, count=1, flags=re.S)
    headings = [h for h in md.headings[1:]] if md.headings and md.headings[0].level == 1 else md.headings
    return Document(title, body, headings, md.lead)


# --------------------------------------------------------------------------- repo facts

@dataclass
class Facts:
    version: str
    date: str
    describe: str
    languages: int
    status_rows: List[Tuple[str, str, str]] = field(default_factory=list)  # (plan, url, contract)
    claims: List[str] = field(default_factory=list)  # required theorems, from proofs/Audit.lean


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
    status = parse_status(repo / "plans/STATUS.md")
    claims = parse_claims(repo / "proofs/Audit.lean")
    return Facts(version, date, describe, languages, status, claims)


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


def parse_status(path: Path) -> List[Tuple[str, str, str]]:
    text = path.read_text(encoding="utf-8")
    m = re.search(r"^## In force.*?\n(.*?)(?=^## )", text, re.S | re.M)
    if not m:
        raise SystemExit("STATUS.md: no 'In force' section")
    rows = []
    for line in m.group(1).splitlines():
        if not line.startswith("|") or re.match(r"^\|\s*-", line) or line.startswith("| Plan"):
            continue
        plan, contract = Markdown.cells(line)[:2]
        lm = re.match(r"\[([^\]]+)\]\(([^)]+)\)", plan)
        if not lm:
            raise SystemExit(f"STATUS.md: unexpected plan cell {plan!r}")
        rows.append((lm.group(1), f"{REPO_URL}/blob/main/plans/{lm.group(2)}", contract))
    if not rows:
        raise SystemExit("STATUS.md: empty 'In force' table")
    return rows


# --------------------------------------------------------------------------- page chrome

def page(*, title: str, description: str, body: str, root: str, current: str, facts: Facts,
         head_extra: str = "", body_class: str = "") -> str:
    def nav(href: str, label: str, key: str) -> str:
        cur = ' aria-current="page"' if key == current else ""
        return f'<a href="{href}"{cur}>{label}</a>'

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(description, quote=True)}">
<meta name="color-scheme" content="dark light">
<link rel="icon" href="{root}assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="{root}assets/site.css">
<script>try{{var p=localStorage.getItem("strop-palette");if(p)document.documentElement.dataset.palette=p}}catch(e){{}}</script>
{head_extra}</head>
<body class="{body_class}">
<a class="skip" href="#main">Skip to content</a>
<header class="top">
  <div class="shell top-inner">
    <a class="brand" href="{root}">strop</a>
    <nav aria-label="Site">
      {nav(root + "docs/", "Docs", "docs")}
      {nav(root + "changelog.html", "Changelog", "changelog")}
      {nav(root + "#status", "Status", "status")}
      <a href="{REPO_URL}">GitHub</a>
    </nav>
  </div>
</header>
<main id="main">
{body}
</main>
<footer class="foot">
  <div class="shell foot-inner">
    <p>MIT license · © 2026 <a href="https://github.com/tknawara">Tarek Nawara</a></p>
    <p><a href="{REPO_URL}">Source</a> · <a href="{REPO_URL}/releases/latest">Release v{facts.version}</a> · <a href="{root}#palette">Palette</a></p>
  </div>
</footer>
<script src="{root}assets/site.js"></script>
</body>
</html>
"""


# --------------------------------------------------------------------------- outputs

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
    names = sorted(p.stem for p in (repo / "docs").glob("*.md"))
    for required in USER_DOCS + DESIGN_DOCS:
        if required not in names:
            raise SystemExit(f"docs/{required}.md is missing from the repo")
    extra = [n for n in names if n not in USER_DOCS + DESIGN_DOCS]
    order = USER_DOCS + DESIGN_DOCS + extra
    docs: Dict[str, Document] = {}
    for name in order:
        source = (repo / "docs" / f"{name}.md").read_text(encoding="utf-8")
        try:
            docs[name] = convert(source, docs_link)
        except ValueError as e:
            raise SystemExit(f"docs/{name}.md: {e}")
    out_dir = SITE / "docs"
    out_dir.mkdir(exist_ok=True)
    written = []
    for idx, name in enumerate(order):
        doc = docs[name]
        prev_name = order[idx - 1] if idx > 0 else None
        next_name = order[idx + 1] if idx + 1 < len(order) else None
        toc = "".join(
            f'<li><a href="#{h.anchor}">{h.text}</a></li>'
            for h in doc.headings if h.level <= 2
        )
        pager = ""
        if prev_name:
            pager += f'<a class="pager-prev" href="{prev_name}.html">← {html.escape(docs[prev_name].title)}</a>'
        if next_name:
            pager += f'<a class="pager-next" href="{next_name}.html">{html.escape(docs[next_name].title)} →</a>'
        body = f"""<div class="shell doc-layout">
  <aside class="doc-side">
    <p class="side-title"><a href="./">Docs</a></p>
    <ol class="side-docs">
      {''.join(f'<li><a href="{n}.html"{" aria-current=&quot;page&quot;" if n == name else ""}>{html.escape(docs[n].title)}</a></li>' for n in order)}
    </ol>
    {"<p class='side-title'>On this page</p><ol class='side-toc'>" + toc + "</ol>" if toc else ""}
  </aside>
  <article class="doc">
    <p class="eyebrow">Docs</p>
    <h1>{html.escape(doc.title)}</h1>
    <div class="prose">
{doc.body}
    </div>
    <nav class="pager" aria-label="Documents">{pager}</nav>
    <p class="provenance">Generated from <a href="{REPO_URL}/blob/main/docs/{name}.md"><code>docs/{name}.md</code></a> at <code>{html.escape(facts.describe)}</code>. The repository file is the source of truth; edit it there.</p>
  </article>
</div>"""
        text = page(title=f"{doc.title} — strop docs", description=strip_tags(doc.lead)[:200],
                    body=body, root="../", current="docs", facts=facts, body_class="docs-page")
        (out_dir / f"{name}.html").write_text(text, encoding="utf-8")
        written.append(f"docs/{name}.html")

    def card(n: str) -> str:
        return f'<li><a href="{n}.html"><strong>{html.escape(docs[n].title)}</strong><span>{docs[n].lead}</span></a></li>'

    index_body = f"""<div class="shell page">
  <p class="eyebrow">Docs</p>
  <h1>The reference</h1>
  <p class="lede">Every page here is generated from the editor repository's <a href="{REPO_URL}/tree/main/docs"><code>docs/</code></a> directory at <code>{html.escape(facts.describe)}</code>, so the site cannot say something the repository does not. For the input grammar, see <kbd>Space</kbd> <kbd>?</kbd> inside the editor or the <a href="{REPO_URL}#the-grammar-in-one-card">README card</a>.</p>
  <h2>Using strop</h2>
  <ul class="doc-cards">
    {''.join(card(n) for n in USER_DOCS)}
  </ul>
  <h2>Design records</h2>
  <ul class="doc-cards">
    {''.join(card(n) for n in DESIGN_DOCS + extra)}
  </ul>
  <p class="aside">Design contracts — the numbered plans every behaviour answers to — live in <a href="{REPO_URL}/tree/main/plans"><code>plans/</code></a>; the <a href="../#status">Status</a> section lists the ones in force.</p>
</div>"""
    text = page(title="Docs — strop", description="strop reference documentation, generated from the repository's docs directory.",
                body=index_body, root="../", current="docs", facts=facts, body_class="docs-page")
    (out_dir / "index.html").write_text(text, encoding="utf-8")
    written.append("docs/index.html")
    return written


def strip_tags(text: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", text))


def build_changelog(repo: Path, facts: Facts) -> str:
    source = (repo / "CHANGELOG.md").read_text(encoding="utf-8")

    def heading_id(level: int, text: str) -> str:
        return ("release-" if level == 2 else "") + slugify(text)

    def link(url: str) -> str:
        return url if url.startswith(("http://", "https://", "#")) else f"{REPO_URL}/blob/main/{url}"

    try:
        doc = convert(source, link, heading_id)
    except ValueError as e:
        raise SystemExit(f"CHANGELOG.md: {e}")
    releases = [h for h in doc.headings if h.level == 2]
    body = f"""<div class="shell page changelog">
  <p class="eyebrow">Changelog</p>
  <h1>Every release</h1>
  <p class="lede">{len(releases)} releases, newest first. Generated from <a href="{REPO_URL}/blob/main/CHANGELOG.md"><code>CHANGELOG.md</code></a> at <code>{html.escape(facts.describe)}</code>; tarballs and checksums are on <a href="{REPO_URL}/releases">GitHub releases</a>.</p>
  <div class="prose">
{doc.body}
  </div>
</div>"""
    text = page(title="Changelog — strop", description="strop release history, generated from CHANGELOG.md.",
                body=body, root="./", current="changelog", facts=facts)
    (SITE / "changelog.html").write_text(text, encoding="utf-8")
    return "changelog.html"


def stamp_index(facts: Facts) -> str:
    path = SITE / "index.html"
    text = path.read_text(encoding="utf-8")

    def region(name: str, value: str) -> None:
        nonlocal text
        pattern = re.compile(rf"(<!-- build:{name} -->).*?(<!-- /build:{name} -->)", re.S)
        if not pattern.search(text):
            raise SystemExit(f"index.html: missing build region {name!r}")
        text = pattern.sub(lambda m: m.group(1) + value + m.group(2), text)

    status = "\n".join(
        f'<tr><th scope="row"><a href="{url}">{html.escape(plan)}</a></th><td>{Markdown(lambda u: u).inline(contract)}</td></tr>'
        for plan, url, contract in facts.status_rows
    )
    region("version", html.escape(facts.version))
    region("date", html.escape(facts.date))
    region("describe", html.escape(facts.describe))
    region("languages", str(facts.languages))
    region("status", "\n" + status + "\n")
    region("claims", "".join(f"<li>{html.escape(c)}</li>" for c in facts.claims))
    path.write_text(text, encoding="utf-8")
    return "index.html"


def vendor(repo: Path) -> List[str]:
    written = []
    for name in ("CHANGELOG.md", "install.sh"):
        shutil.copyfile(repo / name, SITE / name)
        written.append(name)
    return written


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("repo", type=Path, help="path to a checkout of stropdev/strop at the released tag")
    args = ap.parse_args(argv)
    repo = args.repo.resolve()
    if not (repo / "Cargo.toml").exists():
        raise SystemExit(f"{repo} is not the strop repository")
    facts = read_facts(repo)
    written = vendor(repo) + build_docs(repo, facts) + [build_changelog(repo, facts), stamp_index(facts)]
    print(f"strop {facts.version} ({facts.describe}), released {facts.date}, {facts.languages} languages, "
          f"{len(facts.status_rows)} plans in force")
    for w in written:
        print(f"  wrote {w}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
