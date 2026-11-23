#!/usr/bin/env python3
"""Build the methods-scout home (ranked queue) and one research card per method.

    python3 docs/methods-scout/tools/build_cards.py

Inputs (contract: docs/methods-scout/LAYOUT.md)
  feedback-state.json                 status, question, issue, edition page per method
  cards/<slug>/card.json              summary box, picture, findings, queue one-liner, verdict
  cards/<slug>/{math,applied,robust,sauce,questions}.html   tab bodies (full research cards)
  production-links.json               optional repo / docs / package URLs, keyed by slug
  A card.json with "stub": true has no tabs; its queue row links to the dated edition.

Outputs
  index.html          the ranked queue (scout home), including the research-to-production tracker
  m/<slug>.html       one research card per non-stub method
"""
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scout_feedback import RESPOND_HINT, load_state  # noqa: E402

SCOUT = Path(__file__).resolve().parent.parent
CARDS = SCOUT / "cards"
LINKS_PATH = SCOUT / "production-links.json"
REPO = "https://github.com/jgridifier/research-lab"
ICON_HEAD = (SCOUT / "icons" / "head.html").read_text()
e = html.escape

STATUS = {  # one icon + one plain word per status, everywhere (LAYOUT.md)
    "proposed": ("○", "New"),
    "approved": ("✓", "Go"),
    "in-progress": ("▶", "Building"),
    "refine": ("✎", "Needs direction"),
    "parked": ("❚❚", "Parked"),
    "dropped": ("✕", "Dropped"),
    "done": ("★", "Done"),
}
PICK = {"math": "Math", "engineering": "Engineering", "new-use": "New use", "all": "All three", None: "—"}
VERDICT_PTS = {"Recommend": 3, "Adopt-candidate": 3, "Interesting": 2, "Watchlist": 0, "Skip": 1}
TABS = [("math", "The math"), ("applied", "On our data"), ("robust", "Robust at home"),
        ("sauce", "Secret sauce"), ("questions", "Questions")]
BUDGET = {"what": 22, "pick_line": 22, "one": 20, "title": 12}   # summary box + queue rows only


def words(s: str) -> int:
    return len(re.sub(r"<[^>]+>", " ", s).split())


def check_budget(card: dict) -> None:
    for k, n in BUDGET.items():
        if k in card and card[k]:
            w = words(card[k])
            if w > n:
                raise SystemExit(f"{card['slug']}: '{k}' is {w} words (limit {n}): {card[k]}")


PLAN_STATUS = {"todo": ("○", "To do"), "doing": ("▶", "Doing"), "done": ("✓", "Done"), "blocked": ("❚❚", "Waiting")}


def check_build_plan(c: dict) -> None:
    """Every Go / Building method needs a build plan of 3-6 steps, each with an acceptance test (FEEDBACK.md)."""
    bp = c.get("build_plan")
    if c["status"] not in ("approved", "in-progress"):
        return
    if not bp:
        raise SystemExit(f"{c['slug']}: status {c['status']} needs a build_plan in feedback-state.json (FEEDBACK.md)")
    steps = bp.get("steps") or []
    if not 3 <= len(steps) <= 6:
        raise SystemExit(f"{c['slug']}: build_plan needs 3-6 steps, has {len(steps)}")
    for i, st in enumerate(steps, 1):
        for k in ("title", "do", "accept", "status"):
            if not st.get(k):
                raise SystemExit(f"{c['slug']}: build_plan step {i} is missing '{k}'")
        if st["status"] not in PLAN_STATUS:
            raise SystemExit(f"{c['slug']}: build_plan step {i} status '{st['status']}' not in {list(PLAN_STATUS)}")
    if "agent-ready" not in (bp.get("finish") or "").lower() and "agent-ready" not in steps[-1]["title"].lower():
        raise SystemExit(f"{c['slug']}: build_plan must end in the agent-ready library (FEEDBACK.md finish line)")


def ticket_url(c: dict, links: dict | None = None) -> str | None:
    if links and links.get("ticket"):
        return links["ticket"]
    bp = c.get("build_plan") or {}
    return f"{REPO}/issues/{bp['ticket']}" if bp.get("ticket") else None


def plan_steps_html(bp: dict) -> str:
    rows = []
    for st in bp["steps"]:
        ic, lab = PLAN_STATUS[st["status"]]
        kill = f'<p class="kill"><b>Kill rule:</b> {e(st["kill"])}</p>' if st.get("kill") else ""
        rows.append(f'<li class="bp-step bp-{e(st["status"])}"><div class="bp-head"><span class="bp-n">{st.get("n", "")}</span>'
                    f'<span class="bp-t">{e(st["title"])}</span><span class="chip bp-st">{ic} {lab}</span></div>'
                    f'<p><b>Do:</b> {e(st["do"])}</p><p><b>Pass when:</b> {e(st["accept"])}</p>{kill}</li>')
    return f'<ol class="bp-steps">{"".join(rows)}</ol>'


def build_plan_section(c: dict) -> str:
    bp = c.get("build_plan")
    if not bp:
        return ""
    t = ticket_url(c)
    tk = f' · Engineering ticket: <a href="{e(t, quote=True)}">#{e(str(bp["ticket"]))}</a>' if t else ""
    done = sum(1 for st in bp["steps"] if st["status"] == "done")
    return (f'<section class="bplan" id="build-plan"><h2 class="sect">Build plan <span class="cnt">{done}/{len(bp["steps"])} done</span></h2>'
            f'<p class="rule">Ends in an <b>agent-ready library</b>: fast (backend chosen by benchmark, usually a Rust core), '
            f'parity-tested against the original, with diagnostics and null tests that say pass / warn / fail, a how-to-judge guide '
            f'and a skill card. Library: <b>{e(bp.get("library") or "TBD")}</b> · repo: {e(bp.get("repo") or "not created yet")}{tk}. '
            f'Finish-line spec: <a href="{REPO}/blob/main/docs/methods-scout/FEEDBACK.md#finish-line-agent-ready-library">FEEDBACK.md</a>.</p>'
            f'{plan_steps_html(bp)}</section>\n')


def fit_pts(q):
    return 2 if q in ("Q1", "Q2", "Q3") else (0 if q == "watchlist" else 1)


def chip_status(st, issue):
    ic, lab = STATUS.get(st, ("?", st))
    return f'<span class="chip st-{st}" data-issue="{issue}">{ic} {lab}</span>'


def chip_q(q):
    lab = {"Q1-retired": "Old Q1", "watchlist": "Watchlist", None: "No question"}.get(q, q)
    return f'<span class="chip q">{e(lab)}</span>'


def chip_v(v):
    if v == "Watchlist":
        return ""
    return f'<span class="chip {"v-rec" if VERDICT_PTS.get(v, 0) >= 3 else "v-int"}">{e(v)}</span>'


def respond(issue, big=False):
    return (f'<a class="btn{" big" if big else ""}" href="{REPO}/issues/{issue}">Respond on #{issue}</a>'
            f'<p class="howto">{RESPOND_HINT}</p>')


# ------------------------------------------------------------------ phone-first SVG charts
INK, MUT, LINE, RED = "#1c150d", "#6f5f46", "#d9c8a6", "#df5236"
COL = {"amber": "#e8902e", "teal": "#1f9e8e", "green": "#54b441", "red": "#df5236", "muted": "#6f5f46"}
MONO = 'font-family="JetBrains Mono, monospace"'
HEAD = 'font-family="Bricolage Grotesque, sans-serif" font-weight="800"'


def _title(s, t):
    if t:
        s.append(f'<text x="6" y="16" {MONO} font-size="11" fill="{MUT}" letter-spacing="1">{e(t.upper())}</text>')


def svg_hbars(c, W=360):
    rows, vmax, ref = c["rows"], c["max"], c.get("ref")
    top = 26 if c.get("title") else 6
    H = top + 40 * len(rows) + (22 if ref else 8)
    x0, x1 = 6, W - 70
    sc = lambda v: x0 + (x1 - x0) * v / vmax
    s = [f'<svg viewBox="0 0 {W} {H}" role="img" xmlns="http://www.w3.org/2000/svg">']
    _title(s, c.get("title"))
    if ref:
        xr = sc(ref[0])
        s.append(f'<line x1="{xr:.1f}" x2="{xr:.1f}" y1="{top+14}" y2="{H-16}" stroke="{RED}" stroke-width="2" stroke-dasharray="4 3" opacity=".75"/>')
        s.append(f'<text x="{min(xr+4, W-160):.1f}" y="{H-4}" {MONO} font-size="10.5" fill="{RED}">{e(ref[1])}</text>')
    for i, (lab, v, col, vt) in enumerate(rows):
        y = top + i * 40
        s.append(f'<text x="{x0}" y="{y+12}" {MONO} font-size="12" fill="{INK}">{e(lab)}</text>')
        s.append(f'<rect x="{x0}" y="{y+17}" width="{max(sc(v)-x0, 2):.1f}" height="16" fill="{COL[col]}" stroke="{INK}" stroke-width="1.5"/>')
        s.append(f'<text x="{sc(v)+6:.1f}" y="{y+30}" {HEAD} font-size="15" fill="{INK}">{e(vt)}</text>')
    s.append("</svg>")
    return "".join(s)


def svg_dots(c, W=360):
    rows, lo, hi, ref, rl = c["rows"], c["lo"], c["hi"], c["ref"], c["ref_label"]
    top = 26 if c.get("title") else 6
    H = top + 38 * len(rows) + 30
    x0, x1 = 10, W - 14
    sc = lambda v: x0 + (x1 - x0) * (v - lo) / (hi - lo)
    s = [f'<svg viewBox="0 0 {W} {H}" role="img" xmlns="http://www.w3.org/2000/svg">']
    _title(s, c.get("title"))
    xr = sc(ref)
    s.append(f'<line x1="{xr:.1f}" x2="{xr:.1f}" y1="{top}" y2="{H-24}" stroke="{RED}" stroke-width="2" stroke-dasharray="4 3"/>')
    for i, (lab, v, col, vt) in enumerate(rows):
        y = top + i * 38
        s.append(f'<text x="{x0}" y="{y+12}" {MONO} font-size="11.5" fill="{INK}">{e(lab)}</text>')
        s.append(f'<text x="{W-6}" y="{y+12}" text-anchor="end" {HEAD} font-size="14" fill="{INK}">{e(vt)}</text>')
        s.append(f'<line x1="{x0}" x2="{x1}" y1="{y+25}" y2="{y+25}" stroke="{LINE}" stroke-width="2"/>')
        s.append(f'<line x1="{xr:.1f}" x2="{sc(v):.1f}" y1="{y+25}" y2="{y+25}" stroke="{COL[col]}" stroke-width="4"/>')
        s.append(f'<circle cx="{sc(v):.1f}" cy="{y+25}" r="7.5" fill="{COL[col]}" stroke="{INK}" stroke-width="2"/>')
    s.append(f'<text x="{xr:.1f}" y="{H-12}" text-anchor="middle" {MONO} font-size="10" fill="{RED}">{e(rl)}</text>')
    s.append("</svg>")
    return "".join(s)


def svg_strip(c, W=360):
    groups = c["groups"]
    top = 26 if c.get("title") else 6
    H = top + 46 * len(groups) + 22
    x0, x1 = 10, W - 14
    sc = lambda v: x0 + (x1 - x0) * v / 100
    s = [f'<svg viewBox="0 0 {W} {H}" role="img" xmlns="http://www.w3.org/2000/svg">']
    _title(s, c.get("title"))
    for i, (lab, vals, col) in enumerate(groups):
        y = top + i * 46
        s.append(f'<text x="{x0}" y="{y+12}" {MONO} font-size="11.5" fill="{INK}">{e(lab)}</text>')
        s.append(f'<line x1="{x0}" x2="{x1}" y1="{y+28}" y2="{y+28}" stroke="{LINE}" stroke-width="2"/>')
        for j, v in enumerate(vals):
            s.append(f'<circle cx="{sc(v):.1f}" cy="{y+28+(j%3-1)*3}" r="6" fill="{COL[col]}" fill-opacity=".8" stroke="{INK}" stroke-width="1.5"/>')
    for t in (0, 50, 100):
        s.append(f'<text x="{sc(t):.1f}" y="{H-6}" text-anchor="middle" {MONO} font-size="10" fill="{MUT}">{t}th pct</text>')
    s.append("</svg>")
    return "".join(s)


def img_pair(c, prefix=""):
    return (f'<div class="pair"><div><span class="lab">{e(c["la"])}</span><img src="{prefix}{c["a"]}" alt="{e(c["la"])}"></div>'
            f'<div class="new"><span class="lab">{e(c["lb"])}</span><img src="{prefix}{c["b"]}" alt="{e(c["lb"])}"></div></div>')


def chart(c):
    return {"hbars": svg_hbars, "dots": svg_dots, "strip": svg_strip, "images": img_pair}[c["type"]](c)


def picture(p):
    if p["type"] == "numbers":
        L, R = p["left"], p["right"]
        return (f'<div class="pair"><div><span class="lab">{e(L["lab"])}</span><div class="big">{e(L["big"])}</div><div class="sub">{e(L["sub"])}</div></div>'
                f'<div class="new"><span class="lab">{e(R["lab"])}</span><div class="big">{e(R["big"])}</div><div class="sub">{e(R["sub"])}</div></div></div>')
    return chart(p)


# ------------------------------------------------------------------ page shell
FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,400..800'
         '&family=Newsreader:ital,opsz,wght@0,6..72,400..600;1,6..72,400..500&family=JetBrains+Mono:wght@400;500;700&display=swap">')
KATEX = ('<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css">'
         '<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"></script>'
         '<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js" '
         'onload="renderMathInElement(document.body,{delimiters:[{left:\'$$\',right:\'$$\',display:true},{left:\'\\\\(\',right:\'\\\\)\',display:false}]})"></script>')


def page(title, body, depth, math=False, sources="feedback-state.json</code> and <code>cards/"):
    up = "../" * depth
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title>
{FONTS}
<link rel="stylesheet" href="{up}../assets/brief.css">
<link rel="stylesheet" href="{up}scout-cards.css">
{KATEX if math else ''}
{ICON_HEAD}
</head><body>
<header class="topbar"><a class="brand" href="{up}index.html">Methods scout</a>
<span><a href="{up}index.html">Queue</a> · <a href="{up}archive.html">Archive</a></span></header>
<div class="pz">
{body}
</div>
<footer class="pf">Generated by <code>tools/build_cards.py</code> from <code>{sources}</code>; page contract in <a href="{REPO}/blob/main/docs/methods-scout/LAYOUT.md">LAYOUT.md</a>.
Status chips are baked in at build time and refreshed from the GitHub issue labels on load. Q2 work so far uses SYNTHETIC mock budgets; no private rows are published.</footer>
<script src="{up}status.js"></script>
</body></html>"""


def load_cards(state):
    cards = {}
    for d in sorted(CARDS.iterdir()):
        f = d / "card.json"
        if not f.exists():
            continue
        c = json.loads(f.read_text())
        c["slug"] = d.name
        st = state["issues"].get(str(c["issue"]))
        if not st:
            raise SystemExit(f"{d.name}: issue #{c['issue']} is not in feedback-state.json")
        c["status"], c["q"], c["date"] = st["status"], st["question"], st["scout_date"]
        c["page"] = st["page"]
        c["page_anchor"] = st.get("page_anchor") or ""
        c["edition"] = c["page"] + c["page_anchor"]
        c["pick_key"] = st["top_pick"]
        c.setdefault("method", st["method"])
        c["build_plan"] = st.get("build_plan")
        check_budget(c)
        check_build_plan(c)
        if not c.get("stub"):
            for k, _ in TABS:
                if not (d / f"{k}.html").exists():
                    raise SystemExit(f"{d.name}: missing {k}.html (LAYOUT.md requires all five tabs)")
            c["tabs"] = {k: (d / f"{k}.html").read_text() for k, _ in TABS}
            if (d / "deep.html").exists():  # optional deep dive (LAYOUT.md), rendered to m/<slug>-deep.html
                c["deep"] = (d / "deep.html").read_text()
        cards[d.name] = c
    return cards


def card_page(c):
    finds = []
    for i, f in enumerate(c.get("findings", []), 1):
        note = f'<p class="small">{f["note"]}</p>' if f.get("note") else ""
        fig = (f'<p class="small"><a href="../{f["fig"]}">Original chart from the {c["date"]} edition →</a></p>' if f.get("fig") else "")
        finds.append(f'<article class="fcard{" red" if f.get("miss") else ""}"><div class="viz">{chart(f["chart"]) if f["chart"]["type"]!="images" else img_pair(f["chart"])}</div>'
                     f'<div class="body"><span class="chip">Finding {i}</span><h3>{e(f["h"])}</h3><p class="take">{f["t"]}</p>{note}{fig}</div></article>')
    findings = f'<h4>What we found</h4>{"".join(finds)}' if finds else ""
    radios = "".join(f'<input type="radio" name="tab" id="t{i}"{" checked" if i == 1 else ""}>' for i in range(1, 6))
    labels = "".join(f'<label for="t{i}">{e(lab)}</label>' for i, (_, lab) in enumerate(TABS, 1))
    panels = []
    for i, (k, _) in enumerate(TABS, 1):
        body = c["tabs"][k]
        if k == "applied":
            body = findings + body
        panels.append(f'<div class="panel p{i}" id="{k}">{body}</div>')
    body = f"""<p class="crumb"><a href="../index.html">← Queue</a></p>
<div class="chips">{chip_q(c['q'])}{chip_status(c['status'], c['issue'])}{chip_v(c['verdict'])}<span class="date">Scouted {c['date']}</span></div>
<section class="hero" style="padding-top:.5rem"><p class="kicker">{e(c['name'])} · from {e(c['field'])}</p>
<h1>{e(c['title'])}</h1></section>
<div class="sum">
<div class="row"><span class="k">What it is</span><span class="v">{e(c['what'])}</span></div>
<div class="row"><span class="k">Verdict</span><span class="v"><b>{e(c['verdict'])}.</b> Home field: {e(c['grade'])}.</span></div>
<div class="row"><span class="k">Top pick</span><span class="v"><b>{e(PICK[c['pick_key']])}</b> (effort {e(c['pick_eff'])}): {e(c['pick_line'])}</span></div>
<div class="row"><span class="k">Data</span><span class="v">{e(c['data'])}</span></div>
</div>
{deep_link(c)}<p class="kicker" style="margin-top:1rem">The one picture</p>
{picture(c['picture'])}
<div style="margin:1rem 0 .4rem">{respond(c['issue'], big=True)}</div>
{build_plan_section(c)}<div class="tabs">{radios}<div class="tabbar">{labels}</div><div class="panels">{''.join(panels)}</div></div>
<p class="cite">Full tables, code and data notes: <a href="../{c['edition']}">the {c['date']} edition</a> · scripts in <code>runs/{c['date']}/</code> · card sources in <code>cards/{c['slug']}/</code>.</p>
<div style="margin:1.4rem 0">{respond(c['issue'])}</div>
<script>(function(){{var m={{"math":1,"applied":2,"robust":3,"sauce":4,"questions":5}};var h=location.hash.slice(1);var i=m[h]||(/^t[1-5]$/.test(h)?+h[1]:0);if(i)document.getElementById("t"+i).checked=true;}})();</script>"""
    return page(f"{c['name']} · research card · methods scout", body, depth=1, math=True)



def deep_link(c):
    if not c.get("deep"):
        return ""
    return (f'<p class="small" style="margin:.8rem 0 0"><b>Deep dive:</b> <a href="{e(c["slug"])}-deep.html">scope, causality line, '
            f'comparison, extensions and the next pre-registered step →</a></p>')


def deep_page(c):
    body = f"""<p class="crumb"><a href="../index.html">← Queue</a> · <a href="{e(c['slug'])}.html">← Research card</a></p>
<div class="chips">{chip_q(c['q'])}{chip_status(c['status'], c['issue'])}{chip_v(c['verdict'])}<span class="date">Scouted {c['date']}</span></div>
<section class="hero" style="padding-top:.5rem"><p class="kicker">{e(c['name'])} · deep dive</p>
<h1>{e(c.get('deep_title') or 'Deep dive')}</h1></section>
{c['deep']}
<div style="margin:1.4rem 0">{respond(c['issue'])}</div>"""
    return page(f"{c['name']} · deep dive · methods scout", body, depth=1, math=True)


EDITION_PAGE = re.compile(r"^\d{4}-\d{2}-\d{2}(?:-[\w]+)?\.html$")
GO_BUILDING = ("approved", "in-progress")
STAGES = ("research", "go", "building", "released")


def load_links() -> dict:
    """Repo / docs / package URLs keyed by slug. Missing slugs are fine: the tracker still lists them."""
    if not LINKS_PATH.exists():
        return {}
    data = json.loads(LINKS_PATH.read_text())
    methods = data.get("methods") or {}
    if not isinstance(methods, dict):
        raise SystemExit("production-links.json: 'methods' must be an object keyed by slug")
    return methods


def stage_of(status: str, links: dict) -> str:
    if links.get("package"):
        return "released"
    if status == "in-progress":
        return "building"
    return "go"


def editions_for(c: dict) -> list[tuple[str, str, str]]:
    """(page, anchor, date) for the originating edition plus later pages that carry id=slug."""
    slug = c["slug"]
    found: list[tuple[str, str, str]] = []
    seen: set[str] = set()
    page = c.get("page") or ""
    if page:
        anchor = c.get("page_anchor") or f"#{slug}"
        found.append((page, anchor, c.get("date") or ""))
        seen.add(page)
    for p in sorted(SCOUT.glob("*.html")):
        if not EDITION_PAGE.match(p.name) or p.name in seen:
            continue
        text = p.read_text(encoding="utf-8")
        if re.search(rf'\bid=["\']{re.escape(slug)}["\']', text):
            date = re.match(r"(\d{4}-\d{2}-\d{2})", p.name).group(1)
            found.append((p.name, f"#{slug}", date))
            seen.add(p.name)
    return found


def edition_label(page: str, date: str) -> str:
    extra = page.removesuffix(".html")[len(date):].replace("-", " ").strip()
    extra = extra.replace("adhoc", "ad hoc")
    return f"{date} {extra}".strip() if extra else date


def repo_label(url: str) -> str:
    m = re.search(r"github\.com/([^/]+/[^/]+)", url)
    return m.group(1).rstrip("/") if m else url


def docs_label(url: str) -> str:
    return re.sub(r"^https?://", "", url).rstrip("/")


def _li(label: str, value: str) -> str:
    return f'<li><span class="k">{label}</span><span>{value}</span></li>'


def prod_row(c: dict, links: dict) -> str:
    slug = c["slug"]
    stage = stage_of(c["status"], links)
    bits = []
    reached = True
    for s in STAGES:
        if s == stage:
            bits.append(f'<span class="now {e(s)}">{e(s)}</span>')
            reached = False
        elif reached:
            bits.append(f'<span class="done">{e(s)}</span>')
        else:
            bits.append(f'<span class="todo">{e(s)}</span>')
    pipe = '<span class="arrow">→</span>'.join(bits)

    ed_html = ", ".join(
        f'<a href="{e(page, quote=True)}{e(anchor, quote=True)}">{e(edition_label(page, date))}</a>'
        for page, anchor, date in editions_for(c)
    ) or '<span class="missing">edition page not recorded</span>'
    if c.get("stub"):
        card_html = '<span class="missing">research card not yet written</span>'
    else:
        card_html = f'<a href="m/{e(slug)}.html">research card</a>'
    issue_html = f'<a href="{REPO}/issues/{c["issue"]}">#{c["issue"]}</a>'
    t = ticket_url(c, links)
    if t:
        m = re.search(r"/issues/(\d+)", t)
        ticket_html = f'<a href="{e(t, quote=True)}">{"#" + m.group(1) if m else e(t)}</a> (engineering)'
    else:
        ticket_html = '<span class="missing">no engineering ticket yet</span>'
    bp = c.get("build_plan")
    if bp:
        done = sum(1 for st in bp["steps"] if st["status"] == "done")
        nxt = next((st for st in bp["steps"] if st["status"] != "done"), None)
        where = (f' · <a href="m/{e(slug)}.html#build-plan">on the card</a>' if not c.get("stub") else "")
        plan_html = (f'<details class="bp-mini"><summary>{done}/{len(bp["steps"])} steps done'
                     f'{" · next: " + e(nxt["title"]) if nxt else ""}</summary>{plan_steps_html(bp)}</details>{where}')
    else:
        plan_html = '<span class="missing">no build plan yet</span>'

    if links.get("repo"):
        url = links["repo"]
        repo_html = f'<a href="{e(url, quote=True)}">{e(repo_label(url))}</a>'
    else:
        repo_html = f'<span class="missing">{e(links.get("repo_note") or "repo not yet created")}</span>'
        if links.get("source"):
            src = links["source"]
            repo_html += f' · research code: <a href="{e(src, quote=True)}">in this lab</a>'

    if links.get("docs"):
        url = links["docs"]
        docs_html = f'<a href="{e(url, quote=True)}">{e(docs_label(url))}</a>'
    else:
        docs_html = f'<span class="missing">{e(links.get("docs_note") or "docs site not yet published")}</span>'

    if links.get("package"):
        url = links["package"]
        pkg_lab = links.get("package_label") or url
        pkg_html = f'<a href="{e(url, quote=True)}">{e(pkg_lab)}</a>'
    else:
        pkg_html = f'<span class="missing">{e(links.get("package_note") or "not on PyPI yet")}</span>'

    return f"""<article class="prod-card">
<div class="prod-head"><span class="nm">{e(c["method"])}</span>{chip_status(c["status"], c["issue"])}</div>
<p class="stage-pipe" aria-label="Stage: {e(stage)}">{pipe}</p>
<ul class="prod-links">
{_li("Editions", ed_html)}
{_li("Card", card_html)}
{_li("Issue", issue_html)}
{_li("Ticket", ticket_html)}
{_li("Plan", plan_html)}
{_li("Repo", repo_html)}
{_li("Docs", docs_html)}
{_li("Package", pkg_html)}
</ul>
</article>
"""


def prod_section(allc: list, linkmap: dict) -> str:
    rows = [c for c in allc if c["status"] in GO_BUILDING]
    if not rows:
        return ""

    def sort_key(c):
        st = stage_of(c["status"], linkmap.get(c["slug"]) or {})
        return ({"released": 0, "building": 1, "go": 2}[st], -int(c["date"].replace("-", "")), c["slug"])

    rows = sorted(rows, key=sort_key)
    intro = ('<p class="rule">Methods that are a go or already being built, from the scout edition '
             'they came from through a build repo or published package when one exists. '
             'Missing links are marked in words, not as a broken URL.</p>')
    cards = "".join(prod_row(c, linkmap.get(c["slug"]) or {}) for c in rows)
    return (f'<h2 class="sect" id="production">Research to production <span class="cnt">{len(rows)}</span></h2>'
            f"{intro}{cards}")


def qrow(c, rank=None):
    ic, _ = STATUS[c["status"]]
    has_card = not c.get("stub")
    link = f"m/{c['slug']}.html" if has_card else c["edition"]
    linklab = "Open research card →" if has_card else f"Open {c['date']} edition →"
    vp, fp = VERDICT_PTS.get(c["verdict"], 0), fit_pts(c["q"])
    why = f'<span class="score">Rank score {vp * fp} = verdict {vp} × question fit {fp}</span>' if rank else ""
    ask = f'<p><b>Your call:</b> {e(c["your_call"])}</p>' if c.get("your_call") else ""
    rk = rank if rank else ic
    return f"""<details class="qrow{' wait' if c.get('your_call') else ''}"><summary><span class="rk">{rk}</span>
<span><span class="nm">{e(c['method'])}</span><p class="one">{e(c['one'])}</p>
<span class="chips">{chip_status(c['status'], c['issue'])}{chip_q(c['q'])}{chip_v(c['verdict'])}{'<span class="chip">Research card</span>' if has_card else ''}</span></span><span class="chev">›</span></summary>
<div class="drawer">{ask}{why}<p><b>Top pick:</b> {e(PICK[c['pick_key']])} · scouted {c['date']}</p>
<p><a class="btn" href="{REPO}/issues/{c['issue']}">Respond #{c['issue']}</a> <a class="btn ghost" href="{link}">{linklab}</a></p>
<p class="howto">{RESPOND_HINT}</p></div></details>"""


def rank_key(c):
    return (-VERDICT_PTS.get(c["verdict"], 0) * fit_pts(c["q"]), -int(c["date"].replace("-", "")), c["slug"])


def queue_page(cards):
    allc = list(cards.values())
    waiting = [c for c in allc if c.get("your_call") and c["status"] not in ("dropped", "done")]
    todo = sorted([c for c in allc if c["status"] == "proposed" and c not in waiting], key=rank_key)
    moving = sorted([c for c in allc if c["status"] in ("approved", "in-progress", "refine") and c not in waiting], key=rank_key)
    parked = [c for c in allc if c["status"] == "parked"]
    closed = [c for c in allc if c["status"] in ("dropped", "done")]
    legend = "".join(f'<span class="chip st-{s}">{i} {l}</span>' for s, (i, l) in STATUS.items())
    sect = lambda t, rows, extra="": (f'<h2 class="sect">{t} <span class="cnt">{len(rows)}</span></h2>{extra}' + "".join(rows)) if rows else ""
    prod = prod_section(allc, load_links())
    prod_nav = '<a class="chip" href="#production">Research to production</a>' if prod else ""
    body = f"""<section class="hero"><p class="kicker">Methods scout · ranked queue</p>
<h1>Work down the list</h1>
<p class="lede">Every scouted method in one order. First what is waiting on you, then undecided methods, best first. Tap a row for the drawer; open the research card for the math and how it plays on our data.</p>
<div class="legend">{legend}</div>
<div class="navrow"><a class="chip" href="archive.html">Dated editions</a><a class="chip" href="board.html">Board by status</a><a class="chip" href="secret-sauce.html">Secret sauce</a><a class="chip" href="{REPO}/blob/main/docs/methods-scout/QUESTIONS.md">Questions</a><a class="chip" href="{REPO}/blob/main/docs/methods-scout/watchlist.md">Watchlist</a>{prod_nav}</div></section>
{sect("Waiting on you", [qrow(c) for c in waiting])}
{sect("Undecided, ranked", [qrow(c, i) for i, c in enumerate(todo, 1)], RULE)}
{sect("Moving", [qrow(c) for c in moving])}
{sect("Parked", [qrow(c) for c in parked])}
{sect("Closed", [qrow(c) for c in closed])}
{prod}"""
    return page("Methods scout · ranked queue · research-lab", body, depth=0,
                sources="feedback-state.json</code>, <code>cards/</code>, and <code>production-links.json")


RULE = """<div class="rule"><b>How the ranking works.</b> <code>score = verdict × question fit</code>.
Verdict: recommend or adopt-candidate = 3, interesting = 2. Question fit: a live question (Q1, Q2, Q3) = 2, the old Q1 or none = 1, watchlist = 0.
Ties go to the newest edition. Both inputs are printed on each card, so the order can be checked by hand.</div>"""

STATUS_JS = """// Refresh status chips from the live GitHub issue labels (one API call). Static chips stay if offline.
(function(){
  var els=document.querySelectorAll("[data-issue]"); if(!els.length) return;
  var MAP=%s;
  fetch("https://api.github.com/repos/jgridifier/research-lab/issues?labels=scout&state=all&per_page=100",{headers:{Accept:"application/vnd.github+json"}})
    .then(function(r){return r.ok?r.json():null}).then(function(list){
      if(!list) return; var by={};
      list.forEach(function(i){var s=null;(i.labels||[]).forEach(function(l){var n=l.name||"";if(n.indexOf("status:")===0)s=n.slice(7);});
        if(s&&MAP[s])by[i.number]=s;});
      els.forEach(function(el){var s=by[el.getAttribute("data-issue")]; if(!s) return;
        el.className="chip st-"+s; el.textContent=MAP[s][0]+" "+MAP[s][1];});
    }).catch(function(){});
})();
"""


def main():
    state = load_state()
    cards = load_cards(state)
    missing = [v["slug"] for v in state["issues"].values() if v["slug"] not in cards]
    if missing:
        raise SystemExit(f"no cards/<slug>/card.json for: {missing} (add a full card or a stub)")
    (SCOUT / "m").mkdir(exist_ok=True)
    (SCOUT / "status.js").write_text(STATUS_JS % json.dumps(STATUS, ensure_ascii=False))
    for c in cards.values():
        if not c.get("stub"):
            (SCOUT / "m" / f"{c['slug']}.html").write_text(card_page(c))
            if c.get("deep"):
                (SCOUT / "m" / f"{c['slug']}-deep.html").write_text(deep_page(c))
    (SCOUT / "index.html").write_text(queue_page(cards))
    print("cards:", sorted(k for k, c in cards.items() if not c.get("stub")))
    print("stubs:", sorted(k for k, c in cards.items() if c.get("stub")))


if __name__ == "__main__":
    main()
