# Methods-scout feedback loop

Jared reviews each scouted method the same way he reviews Nitro XML proposals: open a card, tap through to one GitHub issue, react or leave a short comment. A daily scanner reads new signals and proceeds, parks, drops, or refines the work.

Live board: [board.html](board.html) (also linked from the [scout index](index.html)).
State file (this folder): [`feedback-state.json`](feedback-state.json).

This document is the contract the daily methods-scout run and the daily scanner both follow. Use the names, title pattern, labels, marker, and response vocabulary exactly.

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

React on this issue (do not comment just to vote):

- 👍 = go ahead with the top pick
- 👎 = drop it
- 👀 = park for later

Or comment one of:

- `go engineering` · `go math` · `go new use` · `go all`
- `refine: <what to change>`
- `promote` (move into analysis-skills)
- `park`
- `drop`

Free-text comments are read as refinement notes. A daily scanner picks this up; you do not need to @-mention anyone.
```

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

`signal` is `thumbs_up`, `thumbs_down`, `eyes`, a comment command (`go math`, `park`, `refine: …`, `promote`, …), or `free_text`. `source` is `reaction` or `comment`. `ref` is a comment id when the source is a comment, else `null`. `actor` is the GitHub login. Do not record signals from comments that contain `<!-- quant-scout-bot -->`.

`updated_at` is the last time this file was written (ISO-8601 UTC).

## Buttons on scout pages

Every method card (the method's `<h2>` section, including backfilled past editions and any new edition the daily scout writes) gets, immediately after the section heading / Found-via line:

- A visible **Respond on GitHub** button linking to that method's issue.
- A status chip: Proposed, Approved, Refine, In progress, Parked, Dropped, or Done, rendered from `feedback-state.json` **at build time** (static HTML; no live JS required).
- A short hint line of the reaction and comment options.

Shared styles: [`feedback.css`](feedback.css). Shared renderer: `tools/scout_feedback.py` (`respond_block(entry)`). Include the stylesheet on every scout edition and on the board:

```html
<link rel="stylesheet" href="feedback.css">
```

Give the method section a stable `id` matching `page_anchor` (for example `id="crqa"` on the method's `.sec-head` or `<h2>`). Mobile-first: the button should be easy to tap on a phone.

There is no shared HTML generator for daily pages today (each edition is written as a page). The daily scout copies the same block the renderer emits, or calls it. Do not invent a different button label or a different hint.

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
6. Rebuild `board.html`.
7. Commit the page, the state file, and the board together.

## What the daily scanner does

A routine (not this file) scans once a day. Its job:

1. Pull main. Load `feedback-state.json`.
2. For each issue, fetch reactions and comments newer than `last_processed_at`. Ignore anything whose body contains `<!-- quant-scout-bot -->`. Ignore reactions left by a bot account if one is ever used; Jared's own reactions count, agent-added reactions must not exist.
3. Apply the first new actionable signal (later ones stay queued until the next scan, unless they clearly confirm the same action):

   | Signal | New status | Notes |
   |---|---|---|
   | 👍 | `approved` | Go ahead with the current top pick |
   | 👎 | `dropped` | |
   | 👀 | `parked` | |
   | `go engineering` / `go math` / `go new use` | `approved` | Switch `top_pick` and the `pick:*` label |
   | `go all` | `approved` | `top_pick` becomes `all`; keep all three `pick:*` labels |
   | `refine: …` or free-text | `refine` | Record the text in `notes` and in `history` |
   | `promote` | `approved` | Note that a move into analysis-skills was requested; do **not** write an `APPROVAL.md` or promote until Jared's own dated approval exists |
   | `park` | `parked` | |
   | `drop` | `dropped` | |

4. Update the issue's `status:*` (and `pick:*` if the avenue changed). Append a short marked comment confirming what was recorded, then set `last_processed_at` to now (UTC) and append a `history` entry.
5. Rebuild `board.html`. If the matching scout page's status chip is stale, refresh that chip from the state file.
6. Open a PR for the state + board (and any chip edits) and merge once CI is green, rebasing onto main first.

Promotion into `analysis-skills` still requires Jared's own dated approval in `methods/<method>/APPROVAL.md`. A `promote` comment is a request, not that approval.
