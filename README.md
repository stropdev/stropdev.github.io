# stropdev.github.io

The strop.dev site. Static HTML, one stylesheet, one small script, no
trackers and nothing loaded from another origin. `.github/workflows/pages.yml`
deploys every file on every push to `main`. What the site says about the
editor is read from the editor repository (`stropdev/strop`) by `build.py`,
and the frames on the front page are captured from the binary by
`tools/frames.py`; the generated pages are committed.

## Layout

| Path | What it is |
|---|---|
| `src/*.html` | The hand-written pages as page bodies: `index` (landing), `start` (First ten minutes), `neovim` (Coming from Neovim), `engineering`. Each starts with a `key: value` header comment (`title`, `description`, optional `nav`, `class`) and takes `{{slots}}` that `build.py` fills |
| `index.html`, `start.html`, `neovim.html`, `engineering.html` | Generated from `src/` |
| `docs/*.html` | Generated from the editor repo's `docs/*.md`, one page each, plus `docs/index.html`, which groups them by task (`DOC_GROUPS` in `build.py` holds the site's titles and one-liners) |
| `changelog.html`, `changelog-all.html` | The last three releases, and all of them, from the editor repo's `CHANGELOG.md` |
| `CHANGELOG.md`, `install.sh` | Vendored copies from the editor repo at the released tag (`install.sh` is what `curl -fsSL https://strop.dev/install.sh` serves) |
| `img/frame-*.svg`, `img/frames.json` | The landing page's frames and their manifest (version, captions), written by `tools/frames.py` |
| `assets/site.css`, `assets/site.js`, `assets/favicon.svg` | The editor's six palettes as CSS custom properties, the palette switcher and copy button, the icon |
| `docs.html` | Meta-refresh stub for an old link |
| `build.py`, `tools/` | The build (`tools/md.py` is its Markdown converter), the frame capture (`frames.py`, `ansi2svg.py`, `fixture/`) and the site checker; Python 3.8+, standard library only |
| `notes/` | Working notes, not part of the site's content |

## Publishing a release

From a checkout of `stropdev/strop` at the released tag (the build refuses a
tree whose `Cargo.toml` version has no `CHANGELOG.md` entry), with the
released binary:

```sh
python3 tools/frames.py /path/to/strop-binary \
    --paths /path/to/strop/crates/strop-picker/fixtures/linux-7.4-rc2-paths.txt.gz
python3 build.py /path/to/strop
python3 tools/check_site.py .
git add -A && git commit -m "Publish strop X.Y.Z"
```

Frames first: `build.py` writes the captions from `img/frames.json`, and
`check_site.py` fails when the frames are of a different version than the
site. Check locally with `python3 -m http.server`, then push `main`.

`build.py` vendors `CHANGELOG.md` and `install.sh`, regenerates every page
and syncs the palette values in `assets/site.css` from
`crates/strop-core/src/theme/*.rs`. The output is deterministic for a given
source tree and set of frames.

### The site describes one release

The copy in `src/` describes strop as of `SITE_DESCRIBES` in `build.py`
(0.62). Built from an older tree, every page carries a "Preview" line, and
`check_site.py` reports keys that tree does not have yet as pending instead
of failing. From 0.62 on the line is gone and a missing key fails. When the
copy is next rewritten ahead of a release, raise `SITE_DESCRIBES`.

### What the checker checks

`tools/check_site.py` fails when:

- a page does not parse (balanced tags, unique ids), or an internal link or
  anchor does not resolve;
- a page loads anything from another origin;
- a page written here contains a retired phrase (`STALE` in the script:
  features that were cut, the old demo, the plan ledger, the coined
  phrases). Pages generated from the editor repo's own documents are exempt
  and say so with a `strop-source` meta;
- a key named in `<kbd>` on the landing page or in the walkthrough is not in
  the keymap the binary generates (`docs/vim-compat.html`). Adjacent `<kbd>`
  elements are one chord (`Space` `g` `g`); put a word between keys that are
  separate;
- the frames are of another version than the site.

It also prints the contrast ratios of each palette's text tokens.

## The frames

The three frames on the landing page (find, search and replace, git) are the
released binary's own screens, never drawings. One command makes them:

```sh
python3 tools/frames.py /path/to/strop-binary --paths PATHS.txt.gz
```

It needs `tmux` and `git`, takes about fifteen seconds, and is
byte-reproducible for a given binary.

How it works, and why it is honest:

- `strop headless SCRIPT FILE` is the editor's scripted driver. Its `frame`
  directive prints the cell grid as plain text, with no colour. So each
  scenario's script is run twice over the same fixture: once headless, for
  the settled text, and once in the interactive binary inside a detached
  tmux pane, with the same keys. The pane is captured with colour
  (`tmux capture-pane -e`) only once its text equals the headless frame cell
  for cell; if the two never agree the run fails.
- `tools/ansi2svg.py` turns the capture into an SVG: one rect per background
  run, one text run per style run, each pinned to its cells.
- The editor runs with an empty `HOME` and a `PATH` of `/usr/bin:/bin`, in
  the Hone palette, at 100×30 cells.

Fixtures, built fresh in a temporary directory on every run:

- the large tree: one two-line stub file per line of `--paths`. Use the
  Linux kernel file list the editor's ranking tests use
  (`crates/strop-picker/fixtures/linux-*-paths.txt.gz`, in the strop repo
  from 0.60). The stubs say they are stubs, and so does the caption;
- `tools/fixture/project`, a small Rust crate, committed to a git repository
  at a fixed date, then `tools/fixture/changes` copied over it: one file
  staged, two modified, one untracked.

Each scenario in `frames.py` lists candidates, newest surface first, and
uses the first whose frame contains its `expect` strings. On 0.62 the git
frame is the status buffer (`Space g g`); on an older binary it falls back
to the hunk preview. `img/frames.json` records which candidate each frame
is, with its caption and alt text. To change what a frame shows, edit its
`script` (headless directives: `keys`, `settle`, `wait`), `expect` and
`caption` together.

## Palettes

`assets/site.css` defines the editor's six palettes — Hone (default), Slate,
Carbide, Vellum, Paper, Paper Dark — as CSS custom properties. `build.py`
rewrites their values, and the swatches of the switcher on `/`, from the
theme sources on every build, so the site never shows a colour the binary
does not ship. Hone applies by default, Vellum under
`prefers-color-scheme: light`; the switcher stores an explicit choice in
`localStorage` (`strop-palette`) and a one-line script in each `<head>`
applies it before first paint. Pressing the applied palette again returns to
automatic.

## The Markdown converter

`tools/md.py` handles exactly the subset the editor repo's documents use —
ATX headings, paragraphs, `-`/`1.` lists with wrapped lines, fenced code,
pipe tables, inline code, links, reference links, bold, italic — and fails
the build on anything else rather than guessing. Relative `*.md` links
become `*.html`; `../plans/…` links point at GitHub.

## DNS (manual, Porkbun)

Apex A records → 185.199.108/109/110/111.153; `www` → CNAME
`stropdev.github.io`. The `CNAME` file here is the Pages half.
