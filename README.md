# research-lab

Ad-hoc quant research Pages — bank fundamentals forecasting, Y-9C panels, DFM × Sinkhorn nowcasting.

**Site:** https://jgridifier.github.io/research-lab/

> Independent research lab · Not affiliated with any employer or financial institution · Not investment advice.

---

## What is here

| Track | Description |
|-------|-------------|
| [Statement Forecast](docs/tracks/statement-forecast/index.html) | Non-embedding methods for joint multi-item forecasting of bank holding company statements on the FR Y-9C panel |
| [Y-9C / Yahoo Bank Panel](docs/tracks/y9c-panel/index.html) | Research data path: FFIEC NIC FR Y-9C bulk downloads + Yahoo Finance quarterly smoke |
| [DFM × Sinkhorn](docs/tracks/dfm-sinkhorn/index.html) | Literature at the intersection of dynamic factor models and Sinkhorn / entropic OT as observation loss |

Each track has:
- An **overview** page (`index.html`)
- One or more **teaching pages** (method intuition, worked sketches)
- **Lit memos** (structured literature synthesis)

---

## Adding a new track

### 1. Create the directory

```bash
mkdir -p docs/tracks/<track-slug>
```

Use a short, kebab-case slug (e.g. `credit-spread`, `macro-nowcast`).

### 2. Copy the page template

Each track needs at minimum one `index.html`. Start from an existing track:

```bash
cp docs/tracks/dfm-sinkhorn/index.html docs/tracks/<track-slug>/index.html
```

Edit the copy:
- Update `<title>` and `<meta name="description">`.
- Update the `<header>` eyebrow, `<h1>`, and sub-text.
- Update the `active` class on the `<nav>` link (or add a new nav item — see step 4).
- Update breadcrumb `<nav>`.
- Replace track resource list and overview prose.

### 3. Add teaching and lit-memo pages (optional)

For a teaching page, copy `docs/tracks/dfm-sinkhorn/teaching.html` and edit the body content.

For a lit memo, copy `docs/tracks/dfm-sinkhorn/lit-memo.html`.

Both files reference `../../assets/site.css` — keep that relative path intact.

### 4. Wire the nav

Add the new track to the top `<nav>` in **every existing page** and the new pages:

```html
<li><a href="../../tracks/<track-slug>/index.html">Track Name</a></li>
```

Also add a card to `docs/index.html`:

```html
<a class="track-card" href="tracks/<track-slug>/index.html">
  <div class="track-card__label">Track N</div>
  <div class="track-card__title">Track display name</div>
  <p class="track-card__desc">One-paragraph description.</p>
</a>
```

### 5. Commit and push

```bash
git add docs/
git commit -m "feat: add <track-slug> track"
git push origin main
```

GitHub Actions will deploy to Pages automatically (see `.github/workflows/pages.yml`).

---

## Local preview

No build step needed — this is plain HTML/CSS. Open any file directly in a browser, or
serve with Python:

```bash
cd docs
python -m http.server 8000
# open http://localhost:8000
```

---

## Theme

The site uses the `docs/assets/site.css` stylesheet. Key design tokens:

| Token | Value | Role |
|-------|-------|------|
| `--nav-bg` | `#0a2540` | Top nav background |
| `--text-primary` | `#0c1a27` | Body text |
| `--surface` | `#ffffff` | Card / content background |
| `--accent` | `#0a4080` | Links, callout borders |
| `--font-sans` | Inter | UI + body |
| `--font-mono` | IBM Plex Mono | Code blocks |

**Theme constraints (locked):**
- No gold or amber accents.
- No rounded corners (use `border-radius: 0` or at most `2px` for subtle detail).
- No GS logos, wordmarks, "Goldman Sachs", firm product names, or copied GS assets/CSS.

---

## What is excluded

- `forma-release/`, `proforma-20q/`, HF checkpoints
- Raw panels / CSVs
- Secrets or credentials
- Gated licenses or paywalled assets

---

## Hosting

GitHub Pages deploys from the `docs/` folder on `main` via
`.github/workflows/pages.yml`. The workflow runs on every push to `main`
and on manual dispatch.
