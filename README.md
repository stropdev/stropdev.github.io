# stropdev.github.io

The strop.dev site. Placeholder stage (plan 0004 §2): pure static — `index.html`,
`assets/`, `img/` — deployed as-is by `.github/workflows/pages.yml`. No build step
until real docs exist, then adopt the rootle/gripsack `build.py` pattern.

- Demo GIFs land in `img/` from the app repo's demo workflow (`stropdev/strop`),
  which then pings this repo with a `rebuild` dispatch.
- The hero and footer version chips share one releases API response client-side
  until the build step exists. Keep both hidden if the API is unavailable;
  do not duplicate a fixed version in the hero's feature description.
- DNS (manual, Porkbun): apex A records → 185.199.108/109/110/111.153,
  `www` → CNAME `stropdev.github.io`. The `CNAME` file here is the Pages half.
