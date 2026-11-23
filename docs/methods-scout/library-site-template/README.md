# Library site template

The human-facing GitHub Pages site every agent-ready library ships with (finish-line item 7 in [../FEEDBACK.md](../FEEDBACK.md)). The look follows the [Google Research blog](https://research.google/blog/): a white page with plenty of space, a narrow reading column, blue accents, big hero headings, figure captions and simple cards. **Only the style is borrowed.** The template has no Google logos, wordmarks or names, and nothing on a library site may present itself as Google's.

It is plain static HTML and CSS with a little vanilla JS. There is no build step and nothing to install. Fonts fall back from Google Sans and Product Sans, which load only if the visitor already has them, to Inter (from Google Fonts) and then system fonts. Math is rendered with KaTeX from jsDelivr.

## What's in it

| File | Page | What goes on it |
|---|---|---|
| `index.html` | Overview | What it does, why it matters, a hero figure, three headline cards (parity, speed, backend) and links to the other pages |
| `how-it-works.html` | How it works | The intuition first, then the math in KaTeX (`\( … \)` inline, `$$ … $$` display), the null, and the assumptions |
| `quickstart.html` | Quickstart | Install from source, `examples/agent_quickstart.py` (at most 15 lines) and its expected output |
| `example.html` | Worked example | One real run on public or SYNTHETIC data, with its real output plots |
| `judging.html` | How to judge the output | What `.diagnostics()` and `.null_test()` check, how pass, warn and fail are decided, failure modes, the minimum data size from the power study, and when not to use the method |
| `benchmarks.html` | Benchmarks | Parity against the original, and speed charts drawn from `bench/results.json` |
| `api.html` | API reference | The public functions, mirroring `docs/api.md` |
| `provenance.html` | Provenance | Built by AI coding agents from the papers, benchmarked against the original code, an independent implementation. **Facts only, no legal analysis.** |
| `cite.html` | Cite and changelog | Citations for the papers and the software, plus recent CHANGELOG entries |
| `assets/site.css` | Theme | Every style. Change colours with the variables in `:root` |
| `assets/site.js` | Helpers | Highlights the current nav link, adds copy buttons to code blocks, runs KaTeX auto-render, and draws the data-driven charts |
| `fill.py`, `site.example.json` | Filler | Copies the template into `docs/` and fills in the `{{TOKENS}}` |

Every page links agents to `AGENTS.md`, `llms.txt`, `docs/api.md` and `docs/HOW_TO_JUDGE.md` from the footer, and the index links them again under the cards. Keep those links.

## How to fill it in

1. **Copy and fill the tokens.** Start from `site.example.json`, add a value for each `{{TOKEN}}` used in the pages, then run:
   ```bash
   python3 docs/methods-scout/library-site-template/fill.py --config site.json --out ../<lib-repo>/docs
   ```
   `fill.py` copies `site.css` and `site.js`, writes the nine pages and `.nojekyll`, and exits with code 1, listing what's missing, while any token is unfilled. Values can contain HTML. Tables that need more than one row (diagnostics, API arguments, parity rows) are easier to finish by hand after the fill.
2. **Add the images** to `docs/assets/`:
   - `logo.png` (512 px), `logo-192.png`, `favicon-32.png` and `docs/favicon.ico`.
   - `hero.jpg` for the Overview figure.
   - **The logo and any illustration come from Grok Imagine. Never hand-draw an SVG logo or illustration.** Charts and plots come from the package's real output: commit PNGs written by `examples/`, or use the data-driven charts below.
   - Replace each `<div class="ph">` placeholder with `<img src="assets/…" alt="…">` and keep the `<figcaption>`.
3. **Charts without a plotting library.** `site.js` draws two chart types from data attributes. Copy the numbers from the results files; never type in made-up numbers.
   ```html
   <!-- bars: [label, value, colour 1-4]; data-scale="log" for timings -->
   <div class="chart bars" data-unit="s" data-scale="log" data-title="Median wall time"
        data-groups='[{"label":"62 × 14","bars":[["Original",98.8,1],["This library",0.593,3]]}]'></div>
   <!-- lines: power curves and similar; data-ref draws a dashed reference line -->
   <div class="chart lines" data-x='[0.025,0.05,0.075,0.1]' data-ref="0.8" data-xlabel="Effect size" data-ylabel="Power"
        data-series='[{"name":"T = 62","y":[0.15,0.50,0.90,1.0]}]'></div>
   ```
4. **Verdict chips.** Use `<span class="chip pass">pass</span>`, `chip warn` and `chip fail` wherever the site reports a check. In tables, `td.ok`, `td.warn` and `td.bad` colour a result.
5. **Turn on Pages.** Go to Settings → Pages and pick "Deploy from a branch" with `main` and `/docs`, or run `gh api -X POST repos/jgridifier/<repo>/pages -f 'source[branch]=main' -f 'source[path]=/docs'`. Check that `https://jgridifier.github.io/<repo>/` returns 200.
6. **Before merging,** make sure there are no `{{` left (`grep -R "{{" docs/*.html`), every page loads, the math renders, and the page reads well at 375 px wide.

## Rules

- **Data:** public or SYNTHETIC only. Never publish private rows.
- **Wording:** never mention banks or any industry.
- **Legal:** no legal write-ups. The provenance page states facts only; any legal review stays off GitHub.
- **Publishing:** don't publish to PyPI or crates.io without Jared's explicit go. The quickstart installs from source.
- **Images:** visuals come from Grok Imagine; don't hand-draw logos.

Reference build: [ecotraj-py](https://jgridifier.github.io/ecotraj-py/) uses this theme. Its content predates the full page set, so it has a teaching page and a results page rather than all nine.
