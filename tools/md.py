"""The Markdown subset the strop repository's documents use.

ATX headings, paragraphs, `-`/`1.` lists with wrapped lines, fenced code,
pipe tables, inline code, links, reference links, bold, italic. Anything
else raises `ValueError` rather than being guessed at.
"""

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

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
            if self.FENCE.match(line):
                i = self.fenced(body, i, 0, out)
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
            if not para:
                # a line that looks like a block start no branch takes (a
                # `|` row with no table separator): fail, never spin
                raise ValueError(f"unsupported Markdown construct: {line!r}")
            rendered = self.inline(" ".join(para))
            if not self.lead:
                self.lead = rendered
            out.append(f"<p>{rendered}</p>")
        return "\n".join(out)

    def fenced(self, body: List[str], i: int, indent: int, out: List[str]) -> int:
        """A fenced code block at `body[i]`, its lines `indent` cells in
        (a fence inside a list item is indented with the item's text)."""
        m = self.FENCE.match(body[i][indent:])
        fence, lang = m.group(1), m.group(2)
        code: List[str] = []
        i += 1
        while i < len(body) and body[i].strip() != fence:
            line = body[i]
            code.append(line[indent:] if line[:indent].strip() == "" else line)
            i += 1
        if i >= len(body):
            raise ValueError("unterminated code fence")
        attr = f' class="language-{html.escape(lang)}"' if lang else ""
        out.append(f"<pre><code{attr}>{html.escape(chr(10).join(code))}</code></pre>")
        return i + 1

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
            blocks: List[str] = []
            i += 1
            while i < len(body):
                line = body[i]
                if line.startswith(" " * indent) and self.FENCE.match(line[indent:]):
                    i = self.fenced(body, i, indent, blocks)
                    continue
                if not line.strip():
                    # a blank line inside an item continues it only when an
                    # indented code fence follows
                    if i + 1 < len(body) and body[i + 1].startswith(" " * indent) \
                            and self.FENCE.match(body[i + 1][indent:]):
                        i += 1
                        continue
                    break
                if not line.startswith(" " * indent):
                    break
                if blocks:
                    break
                parts.append(line.strip())
                i += 1
            items.append(f"<li>{self.inline(' '.join(parts))}{''.join(chr(10) + b for b in blocks)}</li>")
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
