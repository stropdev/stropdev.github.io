# stropdev.github.io

The strop.dev site. Static HTML, one stylesheet, one small script, deployed
as-is by `.github/workflows/pages.yml` on every push to `main`. Everything the
site says about the editor is read from the editor repository
(`stropdev/strop`) by `build.py`; the generated pages are committed.

## Layout

| Path | What it is |
|---|---|
| `index.html` | Hand-written landing page with build-stamped regions (`<!-- build:NAME -->…<!-- /build:NAME -->`): version, release date, language count, the Lean claim list, the Status table |
| `docs/*.html` | Generated from the editor repo's `docs/*.md`, one page each, plus `docs/index.html` |
| `changelog.html` | Generated from the editor repo's `CHANGELOG.md` |
| `CHANGELOG.md`, `install.sh` | Vendored copies from the editor repo at the released tag (`install.sh` is what `curl -fsSL https://strop.dev/install.sh` serves) |
| `img/hero.svg` | The hero: a real terminal frame of the editor, converted from a tmux capture by `tools/ansi2svg.py` |
| `img/demo.gif`, `img/demo-poster.png` | The recording the editor repo's demo workflow pushes here, and a still frame shown until it is opened |
| `assets/site.css`, `assets/site.js`, `assets/favicon.svg` | The editor's six palettes as CSS custom properties, the palette switcher and copy button, the icon |
| `roadmap.html`, `docs.html` | Meta-refresh stubs for old links (`/#status` and `/docs/`) |
| `build.py`, `tools/` | The build, the frame converter and the site checker; Python 3.8+, standard library only |

## Rebuilding for a release

From a checkout of `stropdev/strop` at the released tag (the build refuses a
tree whose `Cargo.toml` version has no `CHANGELOG.md` entry):

```sh
python3 build.py /path/to/strop
python3 tools/check_site.py .
git add -A && git commit -m "Publish strop X.Y.Z"
```

This vendors `CHANGELOG.md` and `install.sh`, regenerates `docs/` and
`changelog.html`, and stamps `index.html`. The output is deterministic for a
given source tree; the pages record the `git describe` of the source they
were built from. Then refresh the hero (below), check locally with
`python3 -m http.server` and push `main`; Pages deploys every file.

The Markdown converter in `build.py` handles exactly the subset the repo's
documents use — ATX headings, paragraphs, `-`/`1.` lists with wrapped lines,
fenced code, pipe tables, inline code, links, reference links, bold, italic —
and fails the build on anything else rather than guessing. Relative `*.md`
links become `*.html`; `../plans/…` links point at GitHub.

`tools/check_site.py` parses every page with the stdlib HTML parser (balanced
tags, unique ids), resolves every internal link and anchor, and prints the
contrast ratios of each palette's text tokens.

## Regenerating the hero

`img/hero.svg` must be a frame of the released binary — never a drawing. The
frame shows an operator-pending preview: `d/width` composing in a Rust file,
so the search card counts matches and the statusline names the pending delete
and its exact range before Enter. Capture it at 140×40 in the Hone palette
with tmux, then convert:

```sh
cd /path/to/strop
tmux -L hero -f /dev/null new-session -d -s hero -x 140 -y 40 \
  'strop --theme hone crates/strop/src/render/statusline.rs'
sleep 2                                      # let the editor start and paint
tmux -L hero send-keys -t hero -l '24G'      # a line below where the search card sits
sleep 0.3
tmux -L hero send-keys -t hero -l 'd/width'  # compose; do not press Enter
sleep 0.5
tmux -L hero capture-pane -e -p -t hero > /tmp/hero.ansi
tmux -L hero kill-server

cd /path/to/stropdev.github.io
python3 tools/ansi2svg.py /tmp/hero.ansi img/hero.svg --cols 140 --rows 40 \
  --default-bg '#15171c' --default-fg '#e6e1d6' \
  --title 'strop: d/width composing in statusline.rs' \
  --desc 'A 140 by 40 terminal frame of the strop editor with a search card and the pending delete named in the statusline.'
```

`--default-bg`/`--default-fg` are the theme's `bg.base` and `fg.text`, used
for cells the editor left at the terminal default. After regenerating,
update the `alt` text and `<figcaption>` of the hero in `index.html` so they
describe the new frame exactly (match count, the range in the statusline),
and delete the PLACEHOLDER comment above the figure.

The converter reads 24-bit, 256- and 16-colour SGR, bold, italic and
underline; it emits one rect per background run and one text run per style
run, each pinned to its cell span with `textLength`, so the grid holds in
whatever monospace font the viewer has. A capture of a different size takes
`--cols`/`--rows`.

## The recording

`img/demo.gif` arrives from the editor repo's demo workflow, which then sends
a `rebuild` dispatch. It is 7.5 MB, so the page shows `img/demo-poster.png`
(one frame of the GIF) inside a `<details>` and loads the GIF only when
opened. When the tape changes, refresh the poster from the new GIF with
Pillow, picking a frame that shows the editor rather than the shell, and
update the poster's `alt` text in `index.html`:

```sh
python3 -c "from PIL import Image; im=Image.open('img/demo.gif'); im.seek(662); \
im.convert('RGB').quantize(128).save('img/demo-poster.png', optimize=True)"
```

If `ffmpeg` is available, a WebM of the same tape would be far smaller than
the GIF; the markup is ready to take a `<video>` in place of the inner
`<img class="recording">`.

## Palettes

`assets/site.css` defines the editor's six palettes — Hone (default), Slate,
Carbide, Vellum, Paper, Paper Dark — as CSS custom properties with the hex
values from `plans/0087 §4.3`, `plans/0088 §3` and
`crates/strop-core/src/theme/paper.rs`. Hone applies by default, Vellum under
`prefers-color-scheme: light`; the switcher on `/` stores an explicit choice
in `localStorage` (`strop-palette`) and a one-line script in each `<head>`
applies it before first paint. Pressing the applied palette again returns to
automatic. When the editor's palettes change, change the tokens here — the
site must never show a colour the binary does not ship.

## DNS (manual, Porkbun)

Apex A records → 185.199.108/109/110/111.153; `www` → CNAME
`stropdev.github.io`. The `CNAME` file here is the Pages half.
