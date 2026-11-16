#!/usr/bin/env python3
"""Rebuild docs/methods-scout/board.html from feedback-state.json.

Run from the repo root (or anywhere):

    python3 docs/methods-scout/tools/build_board.py

The daily scanner and the daily scout both rerun this after they
update feedback-state.json. The page is static; status chips are
baked in at build time.
"""
from __future__ import annotations

import html
import sys
from collections import OrderedDict
from pathlib import Path

# Allow running as a script from any cwd.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from scout_feedback import (  # noqa: E402
    BOARD_PATH,
    PAGES_BASE,
    STATE_PATH,
    STATUSES,
    STATUS_LABEL,
    issue_url,
    load_state,
    page_url,
    stylesheet_tag,
)

GROUP_ORDER = STATUSES  # already the display order
GROUP_BLURB = {
    "proposed": "Waiting for a reaction or a short comment.",
    "approved": "Approved to move forward (validation or build still may be owed).",
    "refine": "Needs a change, or a decision on direction.",
    "in-progress": "Work is underway.",
    "parked": "Parked for later, including watchlist items.",
    "dropped": "Dropped.",
    "done": "Finished.",
}


def _head() -> str:
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Methods scout · feedback board · research-lab</title>
<meta name="description" content="All methods-scout feedback issues, grouped by status. Tap through to react or comment on GitHub.">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,400..800&family=Newsreader:ital,opsz,wght@0,6..72,400..600;1,6..72,400..500&family=JetBrains+Mono:wght@400;500;700&display=swap">
<link rel="stylesheet" href="../assets/brief.css">
{stylesheet_tag()}
<link rel="apple-touch-icon" sizes="180x180" href="/research-lab/methods-scout/icons/apple-touch-icon.png">
<link rel="icon" type="image/png" sizes="32x32" href="/research-lab/methods-scout/icons/favicon-32.png">
<link rel="icon" type="image/png" sizes="192x192" href="/research-lab/methods-scout/icons/icon-192.png">
<link rel="manifest" href="/research-lab/methods-scout/manifest.webmanifest">
<meta name="apple-mobile-web-app-title" content="Methods Scout">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="theme-color" content="#0F2A23">
</head><body><main>
<header class="mast">
  <div class="date">Methods scout · feedback</div>
  <h1>Feedback board</h1>
  <p class="dek">One GitHub issue per scouted method. Tap a card, then react or leave a short comment. A daily scan reads the replies.</p>
  <nav><a href="index.html">All editions</a><a href="secret-sauce.html">Secret sauce</a><a href="https://github.com/jgridifier/research-lab/blob/main/docs/methods-scout/QUESTIONS.md">Research questions</a><a href="https://github.com/jgridifier/research-lab/blob/main/docs/methods-scout/FEEDBACK.md">How this works</a></nav>
</header>
"""


def _card(entry: dict) -> str:
    n = entry["issue"]
    method = html.escape(entry.get("method", entry.get("slug", "")))
    question = html.escape(str(entry.get("question", "")))
    date = html.escape(str(entry.get("scout_date", "")))
    status = entry.get("status", "proposed")
    chip = html.escape(STATUS_LABEL.get(status, status))
    notes = (entry.get("notes") or "").strip()
    notes_html = f"<p>{html.escape(notes)}</p>" if notes else ""
    page = entry.get("page") or ""
    anchor = entry.get("page_anchor") or ""
    page_href = html.escape(page_url(page, anchor), quote=True) if page else ""
    page_link = (
        f'<a href="{page_href}">Scout page</a> · ' if page else ""
    )
    issue_href = html.escape(issue_url(n), quote=True)
    top = entry.get("top_pick")
    top_bit = f" · top pick: {html.escape(top)}" if top else ""
    return f"""<li>
  <span class="scout-chip status-{html.escape(status)}">{chip}</span>
  <h3><a href="{issue_href}">{method}</a></h3>
  <p class="board-meta">{date} · {question} · issue #{n}{top_bit}</p>
  {notes_html}
  <p class="board-meta">{page_link}<a href="{issue_href}">Respond on GitHub</a></p>
</li>
"""


def _counts(by_status: dict) -> str:
    chips = []
    for status in GROUP_ORDER:
        n = len(by_status.get(status, []))
        if not n:
            continue
        label = html.escape(STATUS_LABEL[status])
        chips.append(f'<span class="scout-chip status-{status}">{label} · {n}</span>')
    if not chips:
        return '<p class="board-empty">No scout issues yet. The daily scout and the backfill will add them.</p>'
    return '<div class="board-counts">' + "".join(chips) + "</div>"


def build() -> str:
    state = load_state()
    issues = list(state.get("issues", {}).values())
    issues.sort(key=lambda e: (e.get("scout_date") or "", e.get("slug") or ""), reverse=True)
    by_status: dict[str, list] = OrderedDict((s, []) for s in GROUP_ORDER)
    unknown = []
    for entry in issues:
        status = entry.get("status", "proposed")
        if status in by_status:
            by_status[status].append(entry)
        else:
            unknown.append(entry)

    parts = [_head(), _counts(by_status)]
    if not issues:
        parts.append(
            '<p class="lede">The conventions are in place. Issues and status chips land in a follow-up once each past method has an issue, and on each new daily scout page.</p>'
        )
    parts.append('<div class="board-groups">')
    for status in GROUP_ORDER:
        entries = by_status[status]
        if not entries and issues:
            continue
        if not entries and not issues:
            continue
        label = html.escape(STATUS_LABEL[status])
        blurb = html.escape(GROUP_BLURB[status])
        cards = "".join(_card(e) for e in entries) or '<p class="board-empty">None.</p>'
        parts.append(
            f'<section class="board-group" id="{status}">'
            f'<div class="sec-head"><span class="n">{len(entries):02d}</span>'
            f"<h2>{label}</h2><span class=\"line\"></span></div>"
            f"<p class=\"meta\">{blurb}</p>"
            f'<ul class="board-list">{cards}</ul></section>'
        )
    if unknown:
        parts.append(
            '<section class="board-group"><h2>Unrecognised status</h2>'
            f'<ul class="board-list">{"".join(_card(e) for e in unknown)}</ul></section>'
        )
    parts.append("</div>")
    updated = html.escape(str(state.get("updated_at") or "not yet"))
    parts.append(
        f'<footer><p>Built from <code>feedback-state.json</code> · last write {updated} · '
        f'<a href="FEEDBACK.md">conventions</a> · source state at '
        f'<a href="https://github.com/jgridifier/research-lab/blob/main/docs/methods-scout/feedback-state.json">GitHub</a>.</p>'
        f'<p>Status chips are static, refreshed when the board is rebuilt. Live issue threads are on GitHub.</p></footer>\n'
        f"</main></body></html>\n"
    )
    # silence unused
    _ = PAGES_BASE
    return "".join(parts)


def main() -> int:
    html_out = build()
    BOARD_PATH.write_text(html_out, encoding="utf-8")
    state = load_state()
    n = len(state.get("issues", {}))
    print(f"wrote {BOARD_PATH.relative_to(SCOUT_ROOT_PRINT())} ({n} issue(s))")
    return 0


def SCOUT_ROOT_PRINT() -> Path:
    # Pretty path: prefer repo-relative if we can find it.
    here = BOARD_PATH
    for parent in here.parents:
        if (parent / ".git").exists() or (parent / "Makefile").exists():
            return parent
    return here.parent


if __name__ == "__main__":
    raise SystemExit(main())
