"""SEL and B* schedules (PREREG v2 7e and 8; v1 GATE_THRESHOLDS 5). Written to disk before anything is scored."""
import json
from pathlib import Path
import pandas as pd
from .candidates import ENTRIES, NON_OT

WINDOW = 156     # most recent usable all-4 target weeks
TIE_BAND = 0.01  # ties within 1% relative go to the earlier (simpler) entry
MIN_SEL_WEEKS = 52  # IMPL: no selection (hence no SEL/B* forecast) before this many windowed losses exist

def reselection_origins(origins):
    """The first origin of each calendar quarter."""
    out, last = [], None
    for o in origins:
        q = (o.year, (o.month - 1) // 3)
        if q != last: out.append(o)
        last = q
    return out

def select(losses, origin, pool):
    """losses: {entry: {target_week: all-4 mean W2SQ}}. Trailing window = last WINDOW target weeks <= origin that every
    pool entry has (usable all-4 weeks). Lowest mean wins; within TIE_BAND of the lowest, the earliest entry in pool order."""
    weeks = sorted(set.intersection(*[{w for w in losses[e] if w <= origin} for e in pool]))[-WINDOW:]
    if len(weeks) < MIN_SEL_WEEKS: return None
    means = {e: sum(losses[e][w] for w in weeks) / len(weeks) for e in pool}
    best = min(means.values())
    pick = next(e for e in pool if means[e] <= best * (1 + TIE_BAND))
    return {'origin': str(origin.date()), 'selected': pick, 'window_first_week': str(weeks[0].date()),
            'window_last_week': str(weeks[-1].date()), 'n_weeks': len(weeks),
            'calendar_span_weeks': (weeks[-1] - weeks[0]).days // 7 + 1, 'mean_losses': means}

def build_schedules(losses, origins):
    """({origin: sel_entry}, {origin: bstar_entry}, records). A choice is held from its re-selection origin until the
    next one; origins before the first possible selection have none."""
    sel, bstar, records = {}, {}, {'SEL': [], 'B*': []}
    cur_sel = cur_b = None
    resel = set(reselection_origins(origins))
    for o in origins:
        if o in resel:
            s, b = select(losses, o, ENTRIES), select(losses, o, NON_OT)
            if s: cur_sel = s['selected']; records['SEL'].append(s)
            if b: cur_b = b['selected']; records['B*'].append(b)
        sel[o], bstar[o] = cur_sel, cur_b
    return sel, bstar, records

def write_schedules(records, out_dir):
    """Writes sel_schedule.json and bstar_schedule.json; returns their sha256s."""
    import hashlib
    out = {}
    for name, fn in (('SEL', 'sel_schedule.json'), ('B*', 'bstar_schedule.json')):
        path = Path(out_dir) / fn
        path.write_text(json.dumps(records[name], sort_keys=True, indent=1) + '\n')
        out[fn] = hashlib.sha256(path.read_bytes()).hexdigest()
    return out
