import json
from pathlib import Path
from .paths import SCORING_WALL, DATA_DIR

def diff_vintages(prev_long, cur_long):
    result = {'added_dates':{}, 'removed_dates':{}, 'valid_flag_changes':[], 'value_changes':[], 'post_wall_counts':{}}
    for series in sorted(set(prev_long.series) | set(cur_long.series)):
        a = prev_long[prev_long.series == series].set_index('date')
        b = cur_long[cur_long.series == series].set_index('date')
        result['added_dates'][series] = [str(d.date()) for d in b.index.difference(a.index) if str(d.date()) <= SCORING_WALL]
        result['removed_dates'][series] = [str(d.date()) for d in a.index.difference(b.index) if str(d.date()) <= SCORING_WALL]
        for date in a.index.intersection(b.index):
            if str(date.date()) <= SCORING_WALL and a.at[date,'valid'] != b.at[date,'valid']:
                result['valid_flag_changes'].append([series,str(date.date()),bool(a.at[date,'valid']),bool(b.at[date,'valid'])])
            if str(date.date()) <= SCORING_WALL:
                av,bv = a.at[date,'value'], b.at[date,'value']
                if av == av and bv == bv and av != bv:
                    result['value_changes'].append([series,str(date.date()),float(av),float(bv)])
        result['post_wall_counts'][series] = {name:{'obs':len(g[g.index > SCORING_WALL]),
            'valid':int(g.loc[g.index > SCORING_WALL,'valid'].sum())} for name,g in [('previous',a),('current',b)]}
    return result

def append_diff(diff, path=DATA_DIR/'vintage_diffs.jsonl'):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a') as f: f.write(json.dumps(diff,sort_keys=True)+'\n')
