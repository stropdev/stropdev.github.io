# stropdev.github.io

The strop.dev site. Placeholder stage (plan 0004 §2): pure static — `index.html`,
`assets/`, `img/` — deployed as-is by `.github/workflows/pages.yml`. No build step
until real docs exist, then adopt the rootle/gripsack `build.py` pattern.

- Demo GIFs land in `img/` from the app repo's demo workflow (`stropdev/strop`),
  which then pings this repo with a `rebuild` dispatch.
- The version chip reads the releases API client-side until the build step exists.
- DNS (manual, Porkbun): apex A records → 185.199.108/109/110/111.153,
  `www` → CNAME `stropdev.github.io`. The `CNAME` file here is the Pages half.
