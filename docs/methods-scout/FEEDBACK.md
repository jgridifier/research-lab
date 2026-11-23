# Methods-scout feedback loop

Jared reviews each scouted method the same way he reviews Nitro XML proposals: open a research card, tap through to one GitHub issue, and give a thumbs up, a thumbs down, or a comment in his own words. A daily scanner reads new signals and proceeds, parks, drops, or refines the work.

Home page: the [ranked queue](index.html). Each method has a research card at `m/<slug>.html`; the page contract is [LAYOUT.md](LAYOUT.md). Board by status: [board.html](board.html). Dated editions: [archive.html](archive.html).
State file (this folder): [`feedback-state.json`](feedback-state.json).

This document is the contract the daily methods-scout run and the daily scanner both follow. Use the names, title pattern, labels, marker, and response line exactly.

## One GitHub issue per scout method

Issues live in `jgridifier/research-lab`. **Never open a second issue for the same method.** Before creating one, check:

1. `docs/methods-scout/feedback-state.json` (key = issue number, value has `slug` + `scout_date`).
2. Open issues labelled `scout` (`gh issue list -R jgridifier/research-lab --label scout --state all --limit 100`).
3. A title search for `[Scout YYYY-MM-DD] <Method name>`.

If today's (or any day's) scout run already opened the issue, **adopt it**: do not open a duplicate. Add any missing labels, and if the body is missing the "How to respond" block, add that block in a comment that contains the agent marker below.

### Title

```
[Scout YYYY-MM-DD] <Method name> — Q<n>
```

Examples: `[Scout 2026-11-15] Convergent cross mapping — Q1`, `[Scout 2026-11-13] ebnm — Q2`, `[Scout 2026-11-14] IDR — Q3`.

- Retired prime-broker Q1 methods still use `Q1` in the title (the `scout:Q1-retired` label carries the retirement).
- Watchlist items that are not a full scout pick (MaxLIPO+TR is the standing example; it was the MD's pick, not ours) use `watchlist` instead of `Q<n>`:

```
[Scout YYYY-MM-DD] MaxLIPO+TR — watchlist
```

The date in the title is the scout edition the method was first presented on, not the date the issue was opened.

Methods scouted before the Q framing (partykit and changeforest, 2026-11-10) omit the `— Q<n>` suffix and have no `scout:Q*` label.

### Labels (create if missing; names are exact)

| Label | Use |
|---|---|
| `scout` | Every scout feedback issue |
| `scout:Q1` | Aimed at current Q1 |
| `scout:Q2` | Aimed at Q2 |
| `scout:Q3` | Aimed at Q3 |
| `scout:Q1-retired` | Aimed at the retired 2026-11-10 prime-broker Q1 |
| `status:proposed` | Awaiting Jared's response (default for a new issue) |
| `status:approved` | Approved to move forward |
| `status:refine` | Needs a change or a decision |
| `status:in-progress` | Work is underway |
| `status:parked` | Parked for later |
| `status:dropped` | Dropped |
| `status:done` | Finished |
| `pick:engineering` | Top pick, or the avenue Jared chose, is Engineering |
| `pick:math` | Top pick, or the avenue Jared chose, is Math |
| `pick:new-use` | Top pick, or the avenue Jared chose, is New use |
| `watchlist` | Watchlist item, not a full scout method pick |

Exactly one `status:*` label at a time. Exactly one `scout:Q*` label when the method maps to a question (watchlist items may omit it). Add the matching `pick:*` for the current top pick or chosen avenue.

### Issue body

Plain language, short, phone-friendly. Include, in this order:

1. The hidden agent marker on its own line: `<!-- quant-scout-bot -->`
2. Two or three sentence summary of what the method is and what the scout run actually found.
3. A **Found via** line with a link (same source as the scout page).
4. A **Home-field robustness** line, if the page has a verdict; otherwise omit it.
5. The three secret-sauce cards, each one line: **Engineering**, **Math**, **New use** — effort and the test. Mark which is the **top pick**.
6. A link to the scout page section (edition HTML + anchor).
7. A **How to respond** block, verbatim:

```markdown
## How to respond

👍 go ahead · 👎 drop · or just comment what you think.

A daily scanner reads this issue; you do not need to @-mention anyone.
```

The same one line (`RESPOND_HINT` in `tools/scout_feedback.py`) is the only response instruction on research cards, queue drawers, edition pages and the board. There is no command vocabulary for Jared to learn.

## Agent marker and reactions

Every issue body or comment written by an agent **must** contain the hidden HTML comment:

```
<!-- quant-scout-bot -->
```

The scanner uses this to tell agent writing apart from Jared. Agents post through Jared's own GitHub account, so the author login is not a signal.

**Agents must never add reactions to scout issues.** Only Jared's reactions count.

## State file

Path: `docs/methods-scout/feedback-state.json`

```json
{
  "version": 1,
  "repo": "jgridifier/research-lab",
  "updated_at": "2026-11-16T18:00:00Z",
  "issues": {
    "42": {
      "issue": 42,
      "slug": "crqa",
      "method": "CRQA",
      "scout_date": "2026-11-14",
      "page": "2026-11-14.html",
      "page_anchor": "#crqa",
      "question": "Q1",
      "status": "proposed",
      "top_pick": "engineering",
      "labels": ["scout", "scout:Q1", "status:proposed", "pick:engineering"],
      "last_processed_at": "2026-11-16T18:00:00Z",
      "notes": "",
      "history": []
    }
  }
}
```

Field rules:

- The object key and the `issue` field are the issue number, as a string key and an integer value.
- `slug` is lowercase, hyphenated, stable (`crqa`, `denselines`, `lovell-proportionality`, `maxlipo-tr`).
- `page` is the edition filename under this folder. `page_anchor` starts with `#`.
- `question` is `Q1`, `Q2`, `Q3`, `Q1-retired`, or `watchlist`.
- `status` is one of: `proposed`, `approved`, `refine`, `in-progress`, `parked`, `dropped`, `done`.
- `top_pick` is `engineering`, `math`, `new-use`, `all`, or `null` (watchlist items).
- `last_processed_at` is ISO-8601 UTC. **Initialize it to the issue's `created_at`**, so the scanner does not replay the opening comment as a new signal.
- `history` is a list of acted-on signals, oldest first. Each entry:

```json
{
  "at": "2026-11-17T14:00:00Z",
  "signal": "thumbs_up",
  "source": "reaction",
  "actor": "jgridifier",
  "action": "status:approved",
  "ref": null
}
```

`signal` is `thumbs_up`, `thumbs_down`, `eyes`, or `free_text` (the scanner's plain-language reading goes in `action` and the comment id in `ref`). `source` is `reaction` or `comment`. `ref` is a comment id when the source is a comment, else `null`. `actor` is the GitHub login. Do not record signals from comments that contain `<!-- quant-scout-bot -->`.

`updated_at` is the last time this file was written (ISO-8601 UTC).

## Finish line: agent-ready library

Jared's goal (2026-11-23): build Python and Rust libraries, very fast and very agent-friendly, so the analytical coding agent has a portfolio of exotic analysis skills it can call **without writing or re-validating the method each time**. So part of the job is making each method easy to use and easy to judge. "It doesn't have to have a Rust core, it just needs to be ultra optimized, which usually means a Rust core."

Every approved method ends as an **agent-ready library**. Reference model: [jgridifier/ecotraj-py](https://github.com/jgridifier/ecotraj-py) (AGENTS.md, llms.txt, docs/api.md, research/). The library is done when it has all of these:

1. **Its own repo** under `jgridifier`, MIT unless decided otherwise. No neural nets.
2. **Ultra-optimized, backend chosen by benchmark.** Usually a Rust core with thin Python bindings (PyO3/maturin). Vectorized NumPy or Numba is fine when Rust shows no material gain; default rule: keep Rust only if it is at least 5× faster than the best Python path at the target size. Timings against the original go in `bench/results.json` either way.
3. **A small typed API** with sensible defaults.
4. **Parity tests** with the original implementation as a black-box oracle, run as a separate program; fixtures come from scripts under `oracle/`.
5. **A judging layer:** library functions such as `.diagnostics()` and `.null_test()` that return **pass / warn / fail** with a reason, plus `docs/HOW_TO_JUDGE.md` covering what good output looks like, which null to read, failure modes, when not to use it, and the **minimum data size from a power study**.
6. **Examples** on public or SYNTHETIC data only, including `examples/agent_quickstart.py` (at most 15 lines), and README code blocks that run in CI.
7. **Docs:** AGENTS.md, llms.txt, docs/api.md, the library's **own repo + human Pages site in the Google Research style built from the template** ([library-site-template/](library-site-template/README.md); style only, no Google branding): overview with a hero figure, how it works (intuition + KaTeX math), quickstart, worked example with real output plots, how to judge the output, benchmarks (parity + speed charts), API reference, provenance, and citation + changelog, linking AGENTS.md and llms.txt for agents. Plus CHANGELOG, CITATION.cff, and a **provenance note** (NOTICE / README): built by AI coding agents from the papers, benchmarked against the original, an independent implementation. Legal analysis never goes on GitHub.
8. **Release-ready metadata** for PyPI and, for a Rust core, crates.io. Wheels build in CI. **Nothing is published** without Jared's explicit go.
9. **A skill card** (`SKILL.md`) for the analytical coding agent: when to use it, the call, how to judge the output, when not to use it. Promotion into analysis-skills still needs Jared's own dated `methods/<method>/APPROVAL.md` (see below).

Logos and illustrations only via Grok Imagine; agents do not draw them. Charts and plots come from the package's real output. (Jared, 2026-11-23: "each of these packages should be a repo with a beautiful pages site that explains it and everything for humans - let's use google research theme".)

### Build plan (`build_plan` in the state file)

When a method becomes `approved` or `in-progress`, the scanner writes a `build_plan` on its state entry, using 3–6 steps that end in the agent-ready library. Every step names a specific dataset, metric, null and, where a test can fail, a kill rule. "Validate on the real panel" is not a step. If real data is missing, the step uses SYNTHETIC or public data, and the real-data rerun is an optional extra once Jared provides it.

```json
"build_plan": {
  "library": "proprlite",
  "repo": "jgridifier/proprlite (not created yet)",
  "ticket": 90,
  "finish": "Agent-ready library (finish-line spec in FEEDBACK.md)",
  "updated_at": "2026-11-23T17:30:00Z",
  "steps": [
    {"n": 1, "title": "Repo plus core, with parity", "status": "todo",
     "do": "what to build or run",
     "accept": "the test, with numbers, that decides pass",
     "kill": "optional: what happens if it fails"}
  ]
}
```

`status` is `todo`, `doing`, `done`, or `blocked` (waiting on Jared or on data). Optional `result` records what the acceptance test actually measured (dated, with the numbers, including misses); the card shows it under the step. `ticket` is the engineering issue number, or `null`. `build_cards.py` renders the plan on the research card (`#build-plan`) and in the production tracker, and fails the build if a Go or Building method has no valid plan.

**How the scanner moves a plan.** Each run moves an approved or in-progress method through as many steps as it can finish in that run. It runs each step's acceptance test, sets the step to `done` (or records a miss and applies the kill rule), and comments on the issue. When a step needs a new repo or other engineering work, the scanner files the **engineering ticket** itself.

### Engineering tickets

An engineering ticket is a GitHub issue in this repo titled `[Eng] <method>: <library> — agent-ready optimized library`. It is labelled `engineering` and `scout`, and it carries the agent marker. It is **not** a scout method: do not add it to `issues` in the state file, and do not open a research card for it. Link it from the method's scout issue with a marked comment, from `build_plan.ticket`, and from `ticket` in `production-links.json`. The ticket holds the known results, scope and testable acceptance criteria. The build plan holds the step order.

## Buttons on scout pages

Every method card (the method's `<h2>` section, including backfilled past editions and any new edition the daily scout writes) gets, immediately after the section heading / Found-via line:

- A visible **Respond on GitHub** button linking to that method's issue.
- A status chip: Proposed, Approved, Refine, In progress, Parked, Dropped, or Done, rendered from `feedback-state.json` **at build time** (static HTML; no live JS required).
- The one response line: 👍 go ahead · 👎 drop · or just comment what you think.

Shared styles: [`feedback.css`](feedback.css). Shared renderer: `tools/scout_feedback.py` (`respond_block(entry)`). Include the stylesheet on every scout edition and on the board:

```html
<link rel="stylesheet" href="feedback.css">
```

Give the method section a stable `id` matching `page_anchor` (for example `id="crqa"` on the method's `.sec-head` or `<h2>`). Mobile-first: the button should be easy to tap on a phone.

Research cards and the queue are generated by `tools/build_cards.py` (see [LAYOUT.md](LAYOUT.md)). Dated edition pages are still written by hand; the daily scout copies the block the renderer emits, or calls it. Do not invent a different button label or a different hint.

## Board

[`board.html`](board.html) lists every scout issue, grouped by status, with links to the issue and to the scout page section. It is generated from `feedback-state.json` by:

```bash
python3 docs/methods-scout/tools/build_board.py
```

Run from the repo root. The script overwrites `docs/methods-scout/board.html`. The daily scanner reruns it after it updates the state file, and the daily scout reruns it after opening or adopting issues. Link the board from the scout index nav.

## What the daily scout run does

1. `git pull` / rebase onto `origin/main` before committing or merging. Do not merge a stale branch over a newer main (the scanner or a conventions PR may have edited `feedback-state.json`).
2. After choosing the day's methods, **check for existing issues** as above. If a  today's-date issue already exists for that method, adopt it; do not open a second one.
3. Open one issue per new method with the title, labels, body, and marker specified here. A helper: `python3 docs/methods-scout/tools/open_scout_issue.py --help`.
4. Add the method to `feedback-state.json`, setting `last_processed_at` to the issue's `created_at`.
5. Put the Respond button, status chip, and hint on the day's page, and a stable section `id`.
6. Write `cards/<slug>/card.json` and the five tab fragments for each new method, following [LAYOUT.md](LAYOUT.md), then run `python3 docs/methods-scout/tools/build_cards.py`. This writes `m/<slug>.html` and adds the method to the queue (`index.html`). Add the new edition to `archive.html`.
7. Rebuild `board.html`.
8. Commit the page, the cards, the queue, the state file, and the board together.

## What the daily scanner does

A routine (not this file) scans once a day. Its job:

1. Pull main. Load `feedback-state.json`.
2. For each issue, fetch reactions and comments newer than `last_processed_at`. Ignore anything whose body contains `<!-- quant-scout-bot -->`. Ignore reactions left by a bot account if one is ever used; Jared's own reactions count, agent-added reactions must not exist.
3. Read the signals. 👍 and 👎 count the same whether they are **reactions on the issue** or **emoji inside a comment**. Every other comment is read in plain language, the way a colleague would read it. Apply the first new actionable signal (later ones stay queued until the next scan, unless they clearly confirm the same action):

   | What Jared does | New status | Notes |
   |---|---|---|
   | 👍 (reaction, or 👍 in a comment with nothing that changes it) | `approved` | Go ahead with the current top pick |
   | 👎 (reaction, or 👎 in a comment) | `dropped` | |
   | 👀 reaction | `parked` | Kept for compatibility; not advertised |
   | A comment that names an avenue ("do the math one", "engineering first", "all three") | `approved` | Switch `top_pick` (`engineering`, `math`, `new-use`, `all`) and the `pick:*` labels |
   | A comment asking for a change ("try it on weekly data", "redo with X") | `refine` | Record his words in `notes` and in `history` |
   | A comment saying later / not now / park it | `parked` | |
   | A comment saying drop it / not useful | `dropped` | |
   | A comment that clearly says to promote it or move it into analysis-skills | `approved` | Promotion request; see below |
   | A question, or anything ambiguous | unchanged | Reply with a short marked comment that asks him which he means. **Do not guess.** |

   A 👍 or 👎 combined with text is read as a whole ("👍 but do the new-use one" = approved, top pick New use). When the reading is not obvious, ask.

4. Update the issue's `status:*` (and `pick:*` if the avenue changed). Append a short marked comment confirming what was recorded, then set `last_processed_at` to now (UTC) and append a `history` entry.
5. Rebuild `board.html`. If the matching scout page's status chip is stale, refresh that chip from the state file.
6. Open a PR for the state + board (and any chip edits) and merge once CI is green, rebasing onto main first.

### Promotion into analysis-skills

Promotion still requires Jared's own dated approval in `methods/<method>/APPROVAL.md`. The only thing that counts is a comment **from Jared** (no `<!-- quant-scout-bot -->` marker) that clearly says to promote the method or move it into analysis-skills. `APPROVAL.md` quotes that comment **verbatim**, with its date (ISO-8601 UTC) and a link to the comment. A 👍, a general "looks good", or an agent saying Jared agreed is never approval. If it is unclear whether a comment asks for promotion, the scanner asks him in a marked comment and promotes nothing.
