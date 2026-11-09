# stropdev.github.io

The strop.dev site: static HTML, shared CSS/JavaScript and images, deployed as-is by
`.github/workflows/pages.yml`.

- `index.html`, `docs.html`, `roadmap.html` and `changelog.html` share the responsive
  design system in `assets/site.css` and the interactions in `assets/site.js`.
- Paper is the default website palette, including without JavaScript. The landing
  page's **Website palette** chooser adds Paper Dark and retains the twelve original
  optional palettes (including `strop`). It stores supported selections in `strop-palette` in
  localStorage. The selection applies to docs, roadmap and generated changelog
  pages; unavailable storage or an unsupported selection falls back to Paper.
- The hero is a labelled, palette-aware brand illustration, not an editor
  screenshot. Website choices do not configure the editor; Paper and Paper Dark
  are also compiled-in editor themes as of 0.47.3. The real demo GIF keeps its recorded colors and is
  revealed with a native disclosure, so animation requires an explicit action.
- Current releases are GitHub-only, for Linux/WSL x86_64. The homepage offers the
  official curl installer and direct release downloads with checksum verification.
  macOS/Linux aarch64 artifacts and crates.io/Homebrew updates are retired;
  historical packages are not advertised as current installation methods.
  The command remains selectable without JavaScript; clipboard feedback uses the
  shared script. Keep its `data-copy` value identical to the visible command.
- Example boxes declare their language explicitly (`toml`, `bash`, `strop` or
  `javascript`); prose filenames and keys remain plain inline code. The JavaScript
  documentation-comment example stays a JavaScript comment, including its fence.
  `assets/syntax.js` bundles Prism 1.30.0 locally, with its license in
  `assets/SYNTAX-LICENSE`; no CDN or language auto-loader is used. Load it with
  `data-manual` before `assets/site.js` on every page and in the changelog template.
  Palette-aware semantic token styles live in `assets/site.css`. Install and
  update commands are highlighted without changing their source; clipboard data
  remains the exact plain command, and missing JavaScript leaves readable source.
  The bundle's local additions preserve literal source whitespace, recognize
  arbitrary shell executable names, and cover Strop command/headless syntax.
  Keep those additions and the upstream notice when refreshing pinned components.
- `CHANGELOG.md` and `install.sh` are vendored from `stropdev/strop`; synchronize
  them from the latest public release tag (currently `v0.53.0`), not unreleased main.
  The changelog is generated from that source: run `python3 build_changelog.py`
  after synchronization and commit both changelog files.
- Latest-release links use GitHub's `releases/latest` URL and add the current tag
  client-side when the releases API is available.
- Demo GIFs land in `img/` from the app repo's demo workflow (`stropdev/strop`),
  which then pings this repo with a `rebuild` dispatch.
- Hero and footer release links share one releases API response client-side.
  On API failure they retain the functional GitHub `releases/latest` fallback;
  do not duplicate a fixed version in the hero's feature description.
- For local browser checks, run `python3 -m http.server` in this directory.
- DNS (manual, Porkbun): apex A records → 185.199.108/109/110/111.153,
  `www` → CNAME `stropdev.github.io`. The `CNAME` file here is the Pages half.
