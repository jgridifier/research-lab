# Contributing to the Research Lab site

## To add a story, add one entry

The lab home — https://jgridifier.github.io/research-lab/ — is rendered from a single data file, [`docs/stories.json`](docs/stories.json).

1. Open `docs/stories.json`.
2. Add one object to the `stories` array. Copy an existing entry that is close (an internal track page, an external Pages site, or a GitHub-only repo) and change the fields.
3. Use a unique `id`. Keep existing URLs unchanged.
4. Set `external` to `true` and use an absolute `url` for anything outside this repository’s Pages site. Mark GitHub-only repositories with `"kind": "repo"` and Pages sites with `"kind": "site"`.
5. Use `"featured": "lead"` for at most one story, `"secondary"` for a handful of front-page pieces, or `null` to appear only in the Index and the Latest rail.
6. Preview: `cd docs && python -m http.server 8000`, then open http://localhost:8000/.

Fields are documented in the [README](README.md#the-front-page). Adding a new research track still follows the checklist in the README (directory, template, teaching page); the front-page step is the `stories.json` entry, not a hand-edited card in `index.html`.

Do not edit `.github/workflows` for a routine story or track update. Pages deploys from `docs/` on `main` automatically.
