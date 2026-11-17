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
