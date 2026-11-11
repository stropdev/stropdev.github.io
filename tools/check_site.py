#!/usr/bin/env python3
"""Check the built site: python3 tools/check_site.py .

Fails (exit 1) when:

- a page does not parse (unbalanced tags, duplicate ids, a raw `<` in text)
  or an internal link or `#anchor` does not resolve;
- a page loads anything from another origin (no trackers, no CDNs);
- a page written in this repository contains a retired phrase (STALE). Pages
  generated from the strop repository's own documents carry a
  `strop-source` meta and are exempt: they are that repository's record;
- a key named on the landing page or in the walkthrough is not in the
  keymap listing the binary generates (`docs/vim-compat.html`). While the
  site is built from a tree older than the release it describes, such keys
  are reported as pending instead; from that release on they fail;
- the frames were captured from a different version than the site is built
  from.

It also prints the contrast ratio of each palette's text tokens.
Python 3.8+, standard library only.
"""

from __future__ import annotations

import html
import html.entities
import html.parser
import json
import pathlib
import re
import sys
import urllib.parse
from typing import Dict, List, Optional, Set

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source",
        "track", "wbr"}

# Copy the site no longer carries: features that were cut, the old demo, the
# plan ledger, and the coined phrases. Matched case-insensitively.
STALE = ["container", "docker", "worker", "catppuccin", "plans in force", "neovim's hands",
         "helix's spine", "rootle", "gitlens", "see the cut", "the soul"]

# Pages whose keys must exist in the binary.
KEY_PAGES = ["index.html", "start.html"]
KEYMAP_PAGE = "docs/vim-compat.html"


class Page(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.stack: List[str] = []
        self.ids: Set[str] = set()
        self.links: List[str] = []
        self.loads: List[str] = []       # URLs the browser fetches without a click
        self.meta: Dict[str, str] = {}
        self.errors: List[str] = []
        self.chords: List[str] = []      # runs of adjacent <kbd>, e.g. "space g g"
        self.codes: List[str] = []       # text of every <code>
        self._chord: Optional[List[str]] = None
        self._text: Optional[List[str]] = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            if a["id"] in self.ids:
                self.errors.append(f"duplicate id {a['id']}")
            self.ids.add(a["id"])
        if tag == "meta" and a.get("name"):
            self.meta[a["name"]] = a.get("content") or ""
        if a.get("href"):
            self.links.append(a["href"])
            if tag == "link" and a.get("rel") != "canonical":
                self.loads.append(a["href"])
        if a.get("src"):
            self.links.append(a["src"])
            self.loads.append(a["src"])
        if tag in ("kbd", "code"):
            self._text = []
        elif self._chord is not None:
            self._end_chord()        # another element between two keys ends the chord
        if tag not in VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if tag == "kbd" and self._text is not None:
            self._chord = (self._chord or []) + ["".join(self._text)]
            self._text = None
        elif tag == "code" and self._text is not None:
            self.codes.append("".join(self._text))
            self._text = None
        if not self.stack or self.stack[-1] != tag:
            self.errors.append(f"mismatched </{tag}> (open: {self.stack[-3:]}) at line {self.getpos()[0]}")
            while tag in self.stack and self.stack[-1] != tag:
                self.stack.pop()
        if self.stack:
            self.stack.pop()

    def handle_data(self, data):
        if self._text is not None:
            self._text.append(data)
        elif self._chord is not None and data.strip():
            self._end_chord()        # words between two keys: they are separate keys
        if "<" in data and self.stack and self.stack[-1] not in ("script", "style"):
            self.errors.append(f"raw < in text near line {self.getpos()[0]}: {data.strip()[:40]!r}")

    def handle_entityref(self, name):
        if name not in html.entities.html5 and name + ";" not in html.entities.html5:
            self.errors.append(f"entity &{name};")
        elif self._text is not None:
            self._text.append(html.unescape(f"&{name};"))

    def handle_charref(self, name):
        if self._text is not None:
            self._text.append(html.unescape(f"&#{name};"))

    def _end_chord(self):
        self.chords.append(" ".join(key_token(k) for k in self._chord))
        self._chord = None

    def close(self):
        super().close()
        if self._chord is not None:
            self._end_chord()
        if self.stack:
            self.errors.append(f"unclosed {self.stack}")


def key_token(key: str) -> str:
    """`Space` and `Ctrl-O` as the keymap writes them: `space`, `ctrl-o`. One letter keeps its case."""
    key = key.strip()
    return key if len(key) == 1 else key.lower()


def keymap_rows(page: Page) -> List[List[str]]:
    """Each `✓ keys…` cell of the generated keymap, as tokens."""
    return [code.split()[1:] for code in page.codes if code.startswith("✓")]


def in_keymap(chord: str, rows: List[List[str]]) -> bool:
    want = chord.split()
    return any(row[i:i + len(want)] == want for row in rows for i in range(len(row) - len(want) + 1))


def version_tuple(text: str):
    return tuple(int(n) for n in text.split(".")[:2])


def main() -> int:
    root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    # `src/` holds page bodies for build.py, not pages.
    paths = [p for p in sorted(root.rglob("*.html"))
             if ".git" not in p.parts and p.relative_to(root).parts[0] != "src"]
    pages: Dict[pathlib.Path, Page] = {}
    problems: List[str] = []
    for path in paths:
        page = Page()
        text = path.read_text(encoding="utf-8")
        page.feed(text)
        page.close()
        pages[path] = page
        rel = path.relative_to(root)
        problems += [f"{rel}: {e}" for e in page.errors]
        problems += [f"{rel}: loads {url} from another origin" for url in page.loads
                     if url.startswith(("http:", "https:", "//"))]
        if "strop-source" not in page.meta:
            low = text.lower()
            problems += [f"{rel}: retired phrase {phrase!r}" for phrase in STALE if phrase in low]

    for path, page in pages.items():
        rel = path.relative_to(root)
        for link in page.links:
            if link.startswith(("http:", "https:", "mailto:")):
                continue
            url = urllib.parse.urlsplit(link)
            if url.path == "":
                target = path
            else:
                target = (root / url.path.lstrip("/")) if url.path.startswith("/") else (path.parent / url.path)
                target = target.resolve()
                if target.is_dir():
                    target = target / "index.html"
            if not target.exists():
                problems.append(f"{rel}: broken link {link}")
            elif url.fragment and target.suffix == ".html" and url.fragment not in pages[target].ids:
                problems.append(f"{rel}: missing anchor {link}")

    # Keys named on the landing page and in the walkthrough exist in the binary.
    home = pages.get(root / "index.html")
    keymap = pages.get(root / KEYMAP_PAGE)
    pending: List[str] = []
    if home is None or keymap is None:
        problems.append(f"index.html or {KEYMAP_PAGE} is missing")
    else:
        rows = keymap_rows(keymap)
        if not rows:
            problems.append(f"{KEYMAP_PAGE}: no keymap rows found")
        built = home.meta.get("strop-version", "")
        describes = home.meta.get("strop-describes", "")
        if not built or not describes:
            problems.append("index.html: no strop-version / strop-describes meta")
        else:
            preview = version_tuple(built) < version_tuple(describes)
            for name in KEY_PAGES:
                page = pages.get(root / name)
                if page is None:
                    problems.append(f"{name} is missing")
                    continue
                for chord in sorted(set(page.chords)):
                    if in_keymap(chord, rows):
                        continue
                    if preview:
                        pending.append(f"{name}: {chord}")
                    else:
                        problems.append(f"{name}: key {chord!r} is not in the keymap of strop {built}")
            frames = root / "img" / "frames.json"
            if not frames.exists():
                problems.append("img/frames.json is missing; run tools/frames.py")
            else:
                captured = json.loads(frames.read_text(encoding="utf-8"))["version"]
                if captured != built:
                    problems.append(f"frames are of strop {captured}, the site is built from {built}; "
                                    f"rerun tools/frames.py")
            if pending:
                print(f"pending until strop {describes} (built from {built}); these keys are not in its keymap yet:")
                for line in pending:
                    print(f"  {line}")

    for line in problems:
        print(line)
    print(f"{len(pages)} pages, {len(problems)} problems")
    print_contrast(root)
    return 1 if problems else 0


def luminance(colour: str) -> float:
    def channel(c: float) -> float:
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (int(colour[i:i + 2], 16) / 255 for i in (1, 3, 5))
    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)


def ratio(a: str, b: str) -> float:
    la, lb = luminance(a), luminance(b)
    return round((max(la, lb) + 0.05) / (min(la, lb) + 0.05), 2)


def print_contrast(root: pathlib.Path) -> None:
    css = (root / "assets/site.css").read_text(encoding="utf-8")
    pairs = [("text/base", "fg-text", "bg-base"), ("secondary/base", "fg-secondary", "bg-base"),
             ("secondary/surface", "fg-secondary", "bg-surface"), ("muted/base", "fg-muted", "bg-base"),
             ("muted/surface", "fg-muted", "bg-surface"), ("accent/base", "accent", "bg-base"),
             ("accent/raised", "accent", "bg-raised"), ("on-accent/accent", "on-accent", "accent"),
             ("text/selection", "fg-text", "bg-selection")]
    for m in re.finditer(r"(:root[^{]*|\[data-palette=\"([a-z-]+)\"\])\s*\{([^}]*)\}", css):
        body = m.group(3)
        if "--bg-base" not in body:
            continue
        tokens = dict(re.findall(r"--([a-z-]+):\s*(#[0-9a-f]{6})", body))
        name = m.group(2) or m.group(1).strip()[:40]
        print(f"{name:28}", "  ".join(f"{label}={ratio(tokens[a], tokens[b])}" for label, a, b in pairs))


if __name__ == "__main__":
    sys.exit(main())
