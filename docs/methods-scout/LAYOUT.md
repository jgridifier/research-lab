# Methods-scout page contract

How the methods scout is laid out on the site, and what every research card must contain. The daily scout run follows this file; `tools/build_cards.py` enforces the parts a script can check.

## Files

| Path | What it is | Written by |
|---|---|---|
| `index.html` | **Home: the ranked queue**, including the research-to-production tracker | `tools/build_cards.py` (do not edit by hand) |
| `m/<slug>.html` | One **research card** per method | `tools/build_cards.py` |
| `production-links.json` | Build repo, docs site, published-package and engineering-ticket URLs, keyed by slug | by hand, when a repo, package or ticket exists |
| `cards/<slug>/card.json` | Summary box, one picture, findings | the daily scout |
| `cards/<slug>/{math,applied,robust,sauce,questions}.html` | The five tab bodies (HTML fragments, KaTeX allowed) | the daily scout |
| `cards/<slug>/deep.html` | Optional deep dive (HTML fragment, KaTeX allowed), rendered to `m/<slug>-deep.html` and linked under the card's summary box | the daily scout or scanner, when Jared asks for more depth |
| `cards/_toys/toys.py` | Every toy-example number on every card, reproducible | the daily scout |
| `YYYY-MM-DD.html` | Dated edition (full tables, code notes) | the daily scout |
| `archive.html` | List of dated editions | the daily scout (add each new edition) |
| `board.html` | Issues grouped by status | `tools/build_board.py` |
| `status.js` | Refreshes status chips from GitHub labels on load | `tools/build_cards.py` |
| `scout-cards.css` | Card and queue styles, on top of `../assets/brief.css` | by hand |

`<slug>` is the `slug` in `feedback-state.json`. Every issue in the state file must have a `cards/<slug>/card.json`, or the build fails. A method without a full card yet gets a stub: `{"issue": N, "stub": true, "verdict": "...", "one": "..."}`; its queue row links to its dated edition instead.

Build, from the repo root:

```bash
python3 docs/methods-scout/tools/build_cards.py
python3 docs/methods-scout/tools/build_board.py
```

## The queue (home page)

Sections, in this order, each shown only if non-empty:

1. **Waiting on you**: any method whose `card.json` has a `your_call` line (a decision only Jared can make), unless dropped or done.
2. **Undecided, ranked**: status `proposed`, ranked by the rule below, with the rule printed above the list.
3. **Moving**: `approved`, `in-progress`, `refine`.
4. **Parked**, then **Closed** (`dropped`, `done`).
5. **Research to production**: every method whose status is `approved` (Go) or `in-progress` (Building). Each row shows the stage along `research → go → building → released`, then the lineage: originating and later edition pages, the research card, the GitHub issue, then the engineering ticket, the build plan (steps done and the next step, expandable), the build repo, docs site, and published package. Missing build artifacts are written in plain words, never as a broken link.

Each queue row: rank (or status icon), method name, the `one` line, chips (status, question, verdict, "Research card"). Tapping opens a drawer with the rank-score arithmetic, top pick, the Respond button, a link to the card, and the response line.

**Research-to-production links.** Status and the originating edition come from `feedback-state.json`. Later editions are picked up automatically when a dated page (`YYYY-MM-DD.html` or `YYYY-MM-DD-adhoc.html`) has `id="<slug>"`. Repos, docs sites, and packages live in `production-links.json`, keyed by slug, with optional notes:

| Field | What it is |
|---|---|
| `repo` | URL of the build repository (only if it exists) |
| `repo_note` | Plain-language stand-in when there is no repo yet (default: "repo not yet created") |
| `source` | Optional URL of research code in this lab, shown next to a missing repo |
| `docs` | URL of the docs site (only if it exists) |
| `docs_note` | Stand-in when there is no docs site (default: "docs site not yet published") |
| `package` | URL of a published package (only after the URL returns 200; never invent one) |
| `package_label` | Link text for a published package |
| `package_note` | Stand-in when nothing is published (default: "not on PyPI yet") |
| `ticket` | URL of the engineering ticket (a GitHub issue labelled `engineering`). If absent, the tracker falls back to `build_plan.ticket` in the state file |

A Go or Building method with no entry in the file still appears, with the default missing notes. Stage is `released` when `package` is set, otherwise `building` if the status is `in-progress`, otherwise `go`. A future scout run that changes a status, or a new edition page that carries the slug, updates the tracker on the next `build_cards.py` run. When a repo, docs site, or package comes into being, add the verified URL to `production-links.json`.

**Ranking rule.** `score = verdict × question fit`. Verdict: Recommend or Adopt-candidate = 3, Interesting = 2, Watchlist = 0. Question fit: live Q1/Q2/Q3 = 2, old Q1 (`Q1-retired`) or none = 1, `watchlist` = 0. Ties go to the newest edition, then slug. Both inputs are printed in each drawer.

**Status icons** (one icon and one word, everywhere):

| Status | Icon | Word |
|---|---|---|
| `proposed` | ○ | New |
| `approved` | ✓ | Go |
| `in-progress` | ▶ | Building |
| `refine` | ✎ | Needs direction |
| `parked` | ❚❚ | Parked |
| `dropped` | ✕ | Dropped |
| `done` | ★ | Done |

## The research card

### Top of the page (the 3-second read)

- Chips: question, status, verdict, scout date. Kicker: method name · home field. Title (`title`, ≤ 12 words).
- **Summary box**, four rows: What it is (`what`, ≤ 22 words) · Verdict + home-field grade · Top pick (from `top_pick` in the state file, plus `pick_eff` and `pick_line`, ≤ 22 words) · Data (say SYNTHETIC when it is).
- **The one picture**: a before/after pair of numbers (`picture.type = "numbers"`) or of images (`"images"`). The left side is the usual tool, the right side is this method, on the same data.
- **Respond button** and the response line.
- **Build plan** (`id="build-plan"`), only for Go and Building methods: rendered by `build_cards.py` from `build_plan` in `feedback-state.json` (never hand-written in the card folder). It shows the library name, repo, ticket, and each step with its status, what to do, the acceptance test ("Pass when") and any kill rule. It ends in the agent-ready library defined in [FEEDBACK.md](FEEDBACK.md#finish-line-agent-ready-library). **The build fails** if a Go or Building method has no `build_plan`, has fewer than 3 or more than 6 steps, has a step without `title`, `do`, `accept` or a valid `status`, or does not end in the agent-ready library. A stub card shows its plan in the production tracker instead.

Word caps apply **only** to the summary box and the queue row (`one`, ≤ 20 words). The build fails if they are exceeded. The tabs have no word cap: depth comes first, plain language always.

### Tabs (all five required for a non-stub card)

**1. The math** (`math.html`). Must contain, in this order:

1. **Notation table**: symbol, meaning, what it is in our data.
2. **Assumptions** the method needs.
3. **The estimator or statistic**, as KaTeX display math (`$$…$$`; inline `\( … \)`).
4. **Why it works, step by step** (`<div class="step">`), with at least one or two derivation steps actually shown, not just stated.
5. **The null or inference**: how significance or uncertainty is judged, including any multiple-testing control.
6. **A tiny worked toy** (`<div class="toy">`) with real numbers small enough to check by hand. Every number comes from `cards/_toys/toys.py`, never typed from memory.
7. **How it differs mathematically from the standard tool** (`<div class="diff">`): what the usual method assumes, and what this one assumes instead.
8. **Citation** (`<p class="cite">`): the paper and the equation or section followed. If the numbers were not checked against the paper, say "section and equation numbers not checked".

**2. On our data** (`applied.html`). The build puts the findings from `card.json` on top under "What we found" (one chart each, an honest miss marked `"miss": true`). The fragment must then contain:

1. **Who plays what**: a mapping table from the home field to our data.
2. **Inputs and preprocessing**: sources, period, transforms, anything dropped or interpolated.
3. **What we ran**: the steps, in order.
4. **How to read the main chart** (`<div class="callouts">`): numbered call-outs for the axes, the marks, and what pattern means what.
5. **What it means for a decision-maker** (`<div class="plain">`): plain language, no symbols.
6. **Where it breaks**: limitations seen in our runs.
7. **What we'd do next**.

**3. Robust at home** (`robust.html`): the home-field grade and its evidence (papers, replications, package maturity). Methods scouted before grading began say "Not graded" and list only sourced facts.

**4. Secret sauce** (`sauce.html`): exactly three cards (Engineering, Math, New use on our data), each with effort, what it is, a **math sketch**, and a **test** with a pass bar stated in advance. The top pick gets `class="sauce top"` and "★ Top pick", and must match `top_pick` in the state file.

**5. Questions** (`questions.html`): which Q1/Q2/Q3 sub-questions this answers and how, what is still missing, a link to `QUESTIONS.md`.

### Rules for content

- Only numbers from the dated edition, the run scripts in `runs/`, the paper, or `toys.py`. **Never invent a number.** A number derived from published ones (a conversion, a ratio) is labelled "computed".
- No raw private rows. Q2 work uses SYNTHETIC mocks and says so.
- Descriptive only where the edition says so; no trading signals.

## Responding

Everywhere (cards, queue drawers, edition pages, board, issue bodies) the only instruction is:

> 👍 go ahead · 👎 drop · or just comment what you think

It lives in one place, `RESPOND_HINT` in `tools/scout_feedback.py`. How the scanner reads replies, and the promotion rule, are in [FEEDBACK.md](FEEDBACK.md).

## Daily scout checklist

1. Write the dated edition page and open or adopt the issue (FEEDBACK.md).
2. Add the toy to `cards/_toys/toys.py`, run it, and update `toys_output.txt`.
3. Write `cards/<slug>/card.json` and the five tab fragments.
4. Run `build_cards.py` (writes `m/<slug>.html`, the queue, the production tracker and `status.js`) and `build_board.py`.
5. Add the edition to `archive.html`. If a Go or Building method now has a repo, docs site, published package or engineering ticket, add the verified URL to `production-links.json`. When a method becomes Go, write its `build_plan` in `feedback-state.json` before rebuilding (the build fails without it).
6. Check the card on a 390-px-wide screen: the math scrolls sideways inside its box, the tabs wrap.
