# stropdev.github.io

The strop.dev site: static HTML, shared CSS/JavaScript and images, deployed as-is by
`.github/workflows/pages.yml`.

- `index.html`, `docs.html`, `roadmap.html` and `changelog.html` share the responsive
  design system in `assets/site.css` and the interactions in `assets/site.js`.
- `CHANGELOG.md` and `install.sh` are vendored from `stropdev/strop`; synchronize
  them from current main rather than editing release policy only on the website.
  The changelog is generated from that source: run `python3 build_changelog.py`
  after synchronization and commit both changelog files.
- Latest-release links use GitHub's `releases/latest` URL and add the current tag
  client-side when the releases API is available.
- Demo GIFs land in `img/` from the app repo's demo workflow (`stropdev/strop`),
  which then pings this repo with a `rebuild` dispatch.
- The hero and footer version chips share one releases API response client-side
  until the build step exists. Keep both hidden if the API is unavailable;
  do not duplicate a fixed version in the hero's feature description.
- For local browser checks, run `python3 -m http.server` in this directory.
- DNS (manual, Porkbun): apex A records → 185.199.108/109/110/111.153,
  `www` → CNAME `stropdev.github.io`. The `CNAME` file here is the Pages half.
