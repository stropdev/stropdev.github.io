# stropdev.github.io

The strop.dev site. Placeholder stage (plan 0004 §2): pure static — `index.html`,
`assets/`, `img/` — deployed as-is by `.github/workflows/pages.yml`. No build step
until real docs exist, then adopt the rootle/gripsack `build.py` pattern.

- Demo GIFs land in `img/` from the app repo's demo workflow (`stropdev/strop`),
  which then pings this repo with a `rebuild` dispatch.
- The version chip reads the releases API client-side until the build step exists.
- DNS (manual, Porkbun): apex A records → 185.199.108/109/110/111.153,
  `www` → CNAME `stropdev.github.io`. The `CNAME` file here is the Pages half.

## Active platform and installer sources

The current support boundary is Linux x86_64 only, including Linux x86_64
distributions inside WSL. macOS, ARM/aarch64 and native Windows expansion
require an explicit decision and fresh target-specific qualification.
`index.html`, `docs.html`, `roadmap.html` and `assets/site.js` present that policy.
The Homebrew route is the Linux x86_64 source formula, not a macOS cask.

`install.sh` is vendored verbatim from `stropdev/strop`'s installer source;
update it only after the source installer is finalized. It retains release
catalog/checksum verification, atomic installation and ownership receipts.
Historical `CHANGELOG.md`, `changelog.html`, release summaries and demo assets
are preserved rather than rewritten as evidence for this policy change.
This source update does not publish, deploy or claim new qualification.
