#!/usr/bin/env python3
"""Turn a `tmux capture-pane -e -p` dump into a self-contained SVG.

The capture is a fixed-size terminal: one line per row, cells painted with
SGR sequences (24-bit `38;2;r;g;b` / `48;2;r;g;b`, the 16- and 256-colour
forms, bold `1`, italic `3`, underline `4`, and the resets). The SVG is a
cell grid: one rect per background run, one text element per style run,
each run pinned to its exact cell span with `textLength`, so the grid holds
in any monospace font the viewer has. Nothing is redrawn or retouched — the
output is the frame the terminal showed.

    python3 tools/ansi2svg.py frame.ansi frame.svg --cols 100 --rows 30 \
        --default-bg '#15171c' --default-fg '#e6e1d6' --title '...'

Cells the editor left at the terminal default (`\\e[39m` / `\\e[49m`) take
`--default-fg` / `--default-bg`; pass the editor theme's `fg.text` and
`bg.base`. `tools/frames.py` calls this module for the landing page's frames.
Python 3.8+, standard library only.
"""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from dataclasses import dataclass, replace
from pathlib import Path
from typing import List, Optional, Tuple
from xml.sax.saxutils import escape

SGR = re.compile(r"\x1b\[([0-9;]*)m")
OTHER_ESCAPE = re.compile(r"\x1b(?:\[[0-?]*[ -/]*[@-~]|[@-Z\\-_])")

# The 16 ANSI colours a capture may use by index; Hone's ansi16 (0087 §4.3).
ANSI16 = [
    "#101217", "#e8707c", "#8fc48a", "#d9a85a", "#7fb2d4", "#c99ce0", "#8ecdb8", "#cfcac0",
    "#4a5160", "#f08a94", "#a6d6a0", "#e8a848", "#9ccbe8", "#d9b2f0", "#a8e0d0", "#e6e1d6",
]


def xterm256(index: int) -> str:
    if index < 16:
        return ANSI16[index]
    if index < 232:
        index -= 16
        steps = (0, 95, 135, 175, 215, 255)
        r, g, b = steps[index // 36], steps[index // 6 % 6], steps[index % 6]
        return f"#{r:02x}{g:02x}{b:02x}"
    grey = 8 + (index - 232) * 10
    return f"#{grey:02x}{grey:02x}{grey:02x}"


@dataclass(frozen=True)
class Style:
    fg: Optional[str] = None  # None = terminal default
    bg: Optional[str] = None
    bold: bool = False
    italic: bool = False
    underline: bool = False


@dataclass
class Cell:
    char: str
    style: Style
    width: int  # 1, 2 (wide), or 0 (the continuation of a wide glyph)


def cell_width(ch: str) -> int:
    if unicodedata.combining(ch):
        return 0
    return 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1


def apply_sgr(style: Style, params: str) -> Style:
    codes = [int(p) if p else 0 for p in params.split(";")] if params else [0]
    i = 0
    while i < len(codes):
        c = codes[i]
        if c == 0:
            style = Style()
        elif c == 1:
            style = replace(style, bold=True)
        elif c == 3:
            style = replace(style, italic=True)
        elif c == 4:
            style = replace(style, underline=True)
        elif c == 22:
            style = replace(style, bold=False)
        elif c == 23:
            style = replace(style, italic=False)
        elif c == 24:
            style = replace(style, underline=False)
        elif c == 39:
            style = replace(style, fg=None)
        elif c == 49:
            style = replace(style, bg=None)
        elif 30 <= c <= 37:
            style = replace(style, fg=ANSI16[c - 30])
        elif 90 <= c <= 97:
            style = replace(style, fg=ANSI16[c - 90 + 8])
        elif 40 <= c <= 47:
            style = replace(style, bg=ANSI16[c - 40])
        elif 100 <= c <= 107:
            style = replace(style, bg=ANSI16[c - 100 + 8])
        elif c in (38, 48) and i + 1 < len(codes):
            mode = codes[i + 1]
            colour = None
            if mode == 2 and i + 4 < len(codes):
                r, g, b = codes[i + 2 : i + 5]
                colour = f"#{r:02x}{g:02x}{b:02x}"
                i += 4
            elif mode == 5 and i + 2 < len(codes):
                colour = xterm256(codes[i + 2])
                i += 2
            else:
                i += 1
            if colour is not None:
                style = replace(style, fg=colour) if c == 38 else replace(style, bg=colour)
        i += 1
    return style


def parse_row(line: str, cols: int) -> List[Cell]:
    cells: List[Cell] = []
    style = Style()
    pos = 0
    for match in SGR.finditer(line):
        for ch in line[pos : match.start()]:
            emit(cells, ch, style)
        style = apply_sgr(style, match.group(1))
        pos = match.end()
    for ch in line[pos:]:
        emit(cells, ch, style)
    # tmux trims trailing default cells; pad to the grid width in the last style.
    while len(cells) < cols:
        cells.append(Cell(" ", replace(style, fg=None), 1))
    if len(cells) > cols:
        raise SystemExit(f"row is {len(cells)} cells wide, more than --cols {cols}")
    return cells


def emit(cells: List[Cell], ch: str, style: Style) -> None:
    if ch in "\r\n":
        return
    if ch == "\t":
        ch = " "
    width = cell_width(ch)
    if width == 0:
        if cells:
            cells[-1].char += ch  # a combining mark joins its base glyph
        return
    cells.append(Cell(ch, style, width))
    if width == 2:
        cells.append(Cell("", style, 0))


def parse(text: str, cols: int, rows: int) -> List[List[Cell]]:
    text = OTHER_ESCAPE.sub(lambda m: m.group(0) if SGR.fullmatch(m.group(0)) else "", text)
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    if len(lines) > rows:
        raise SystemExit(f"capture has {len(lines)} rows, more than --rows {rows}")
    grid = [parse_row(line, cols) for line in lines]
    while len(grid) < rows:
        grid.append([Cell(" ", Style(), 1) for _ in range(cols)])
    return grid


def runs(cells: List[Cell], key) -> List[Tuple[int, int, Cell]]:
    """Group consecutive cells by `key(cell)`; yields (start_col, cell_count, first_cell)."""
    out: List[Tuple[int, int, Cell]] = []
    start = 0
    while start < len(cells):
        end = start + 1
        while end < len(cells) and key(cells[end]) == key(cells[start]):
            end += 1
        out.append((start, end - start, cells[start]))
        start = end
    return out


def render(grid: List[List[Cell]], *, cols: int, font_size: float, default_fg: str,
           default_bg: str, title: str, desc: str, pad: float) -> str:
    cw = round(font_size * 0.6, 3)  # the advance of every common monospace face is ~0.6em
    ch = round(font_size * 1.25, 3)
    width = round(cols * cw + 2 * pad, 2)
    height = round(len(grid) * ch + 2 * pad, 2)
    baseline = round(ch * 0.76, 3)
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}" role="img" aria-labelledby="t d">',
        f"<title id=\"t\">{escape(title)}</title>",
        f"<desc id=\"d\">{escape(desc)}</desc>",
        f'<rect width="{width}" height="{height}" rx="6" fill="{default_bg}"/>',
        f'<g font-family="ui-monospace, &quot;DejaVu Sans Mono&quot;, Menlo, Consolas, '
        f'&quot;Liberation Mono&quot;, monospace" font-size="{font_size}" fill="{default_fg}" xml:space="preserve">',
    ]
    for r, row in enumerate(grid):
        y = pad + r * ch
        for col, count, cell in runs(row, lambda c: c.style.bg):
            bg = cell.style.bg or default_bg
            if bg == default_bg:
                continue
            out.append(
                f'<rect x="{pad + col * cw:.2f}" y="{y:.2f}" width="{count * cw:.2f}" '
                f'height="{ch}" fill="{bg}"/>'
            )
        for col, count, cell in runs(row, lambda c: c.style):
            # Trim blank cells off both ends so textLength only spans glyphs.
            run = row[col : col + count]
            a, b = 0, len(run)
            while a < b and run[a].char == " ":
                a += 1
            while b > a and run[b - 1].char == " ":
                b -= 1
            if a == b:
                continue
            # Browsers collapse runs of spaces in SVG text whatever xml:space says, and
            # textLength would then stretch the glyphs; a no-break space keeps each cell.
            text = "".join(c.char for c in run[a:b]).replace(" ", "\u00a0")
            span = sum(c.width for c in run[a:b])
            attrs = [f'x="{pad + (col + a) * cw:.2f}"', f'y="{y + baseline:.2f}"',
                     f'textLength="{span * cw:.2f}"', 'lengthAdjust="spacingAndGlyphs"']
            fg = cell.style.fg or default_fg
            if fg != default_fg:
                attrs.append(f'fill="{fg}"')
            if cell.style.bold:
                attrs.append('font-weight="bold"')
            if cell.style.italic:
                attrs.append('font-style="italic"')
            if cell.style.underline:
                attrs.append('text-decoration="underline"')
            out.append(f"<text {' '.join(attrs)}>{escape(text)}</text>")
    out.append("</g></svg>")
    return "\n".join(out) + "\n"


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source", type=Path, help="tmux capture-pane -e -p output")
    ap.add_argument("output", type=Path, help="SVG to write")
    ap.add_argument("--cols", type=int, default=140)
    ap.add_argument("--rows", type=int, default=40)
    ap.add_argument("--font-size", type=float, default=14.0)
    ap.add_argument("--pad", type=float, default=12.0, help="margin around the grid, in px")
    ap.add_argument("--default-fg", default="#e6e1d6", help="colour of cells at the terminal default foreground")
    ap.add_argument("--default-bg", default="#15171c", help="colour of cells at the terminal default background")
    ap.add_argument("--title", default="A strop terminal frame")
    ap.add_argument("--desc", default="A captured terminal frame of the strop editor, rendered cell for cell.")
    args = ap.parse_args(argv)

    grid = parse(args.source.read_text(encoding="utf-8"), args.cols, args.rows)
    svg = render(grid, cols=args.cols, font_size=args.font_size, default_fg=args.default_fg.lower(),
                 default_bg=args.default_bg.lower(), title=args.title, desc=args.desc, pad=args.pad)
    args.output.write_text(svg, encoding="utf-8")
    print(f"wrote {args.output} ({len(svg)} bytes, {args.cols}x{args.rows} cells)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
