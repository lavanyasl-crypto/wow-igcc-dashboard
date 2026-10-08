import json, datetime
from collections import defaultdict

d = json.load(open('pod_data.json', encoding='utf-8'))
audits = d['audits']; wcat = d['weekly_cat']; cats = d['cats']
WEEKS = ['2026-08-24','2026-08-31','2026-09-07','2026-09-14','2026-09-21','2026-09-28','2026-10-05']
LATEST = WEEKS[-1]

def qcat(pids, cat, ws):
    ot = oi = 0
    for r in wcat:
        if r['ws'] == ws and r['store_id'] in pids and r.get('CATEGORY_FINAL') == cat:
            ot += r['ot'] or 0; oi += r['oi'] or 0
    return (oi / ot * 100) if ot else None

def qall(pids, ws):
    ot = oi = 0
    for r in d['weekly']:
        if r['ws'] == ws and r['store_id'] in pids:
            ot += r['ot'] or 0; oi += r['oi'] or 0
    return (oi / ot * 100) if ot else None

ids0 = {a['store_id'] for a in audits if a['n_audits'] == 0}
g1 = [a for a in audits if a['n_audits'] == 1]
g2 = [a for a in audits if a['n_audits'] == 2]
ids1 = {a['store_id'] for a in g1}; ids2 = {a['store_id'] for a in g2}
allids = {a['store_id'] for a in audits}
both = [a for a in audits if a['audit1'] is not None and a['audit2'] is not None]
avg = lambda xs: sum(xs)/len(xs) if xs else None

bands = [('<50',0,50),('50-59',50,60),('60-69',60,70),('70-79',70,80),('80-89',80,90),('90+',90,101)]
out = {'cats': cats, 'weeks': WEEKS}

# 1. band vs same-category IGCC (W41)
out['bands_cat'] = {}
for cat in cats:
    rows = []
    for lbl, lo, hi in bands:
        ids = {a['store_id'] for a in audits if a['audit1'] is not None and lo <= a['audit1'] < hi}
        rows.append([lbl, len(ids), qcat(ids, cat, LATEST)])
    out['bands_cat'][cat] = rows

# 2. audit-count split per category, W41 + weekly
out['auditcount_cat'] = {}
for cat in cats:
    out['auditcount_cat'][cat] = {
        'w41': [qcat(ids, cat, LATEST) for ids in (ids0, ids1, ids2)],
        'weekly0': [qcat(ids0, cat, w) for w in WEEKS],
        'weekly1': [qcat(ids1, cat, w) for w in WEEKS],
        'weekly2': [qcat(ids2, cat, w) for w in WEEKS],
    }

# 3. A2 vs A1 per category: does score improvement match category IGCC improvement
out['a2_cohorts'] = {}
for cat in cats:
    cohorts = {
        'gain5+': {a['store_id'] for a in both if a['audit2']-a['audit1'] >= 5},
        'gain<5': {a['store_id'] for a in both if 0 < a['audit2']-a['audit1'] < 5},
        'flat': {a['store_id'] for a in both if a['audit2'] == a['audit1']},
        'declined': {a['store_id'] for a in both if a['audit2'] < a['audit1']},
    }
    out['a2_cohorts'][cat] = {name: {'n': len(ids),
        'w38': qcat(ids, cat, '2026-09-14'), 'w41': qcat(ids, cat, LATEST)} for name, ids in cohorts.items()}

# 4. correlation A1 vs category IGCC podwise, min volume 500
import math
def corr(pairs):
    n = len(pairs)
    if n < 10: return None
    mx = sum(p[0] for p in pairs)/n; my = sum(p[1] for p in pairs)/n
    sx = math.sqrt(sum((p[0]-mx)**2 for p in pairs)); sy = math.sqrt(sum((p[1]-my)**2 for p in pairs))
    if not sx or not sy: return None
    return sum((p[0]-mx)*(p[1]-my) for p in pairs)/(sx*sy)
out['corr'] = {}
for cat in cats:
    pairs = []
    for a in audits:
        if a['audit1'] is None: continue
        rows = [r for r in wcat if r['ws']==LATEST and r['store_id']==a['store_id'] and r.get('CATEGORY_FINAL')==cat]
        ot = sum(r['ot'] or 0 for r in rows); oi = sum(r['oi'] or 0 for r in rows)
        if ot >= 500: pairs.append((a['audit1'], oi/ot*100))
    out['corr'][cat] = {'r': corr(pairs), 'n': len(pairs)}

# 5. overall weekly + per-cat weekly (mismatch explanation)
out['all_weekly'] = [qall(allids, w) for w in WEEKS]
out['cat_weekly_all'] = {cat: [qcat(allids, cat, w) for w in WEEKS] for cat in cats}

# 6. audit scores summary per category-relevant split
out['score_summary'] = {
    'a1': avg([a['audit1'] for a in audits if a['audit1'] is not None]),
    'a2': avg([a['audit2'] for a in audits if a['audit2'] is not None]),
    'g2a1': avg([a['audit1'] for a in g2 if a['audit1'] is not None]),
    'g2a2': avg([a['audit2'] for a in g2 if a['audit2'] is not None]),
    'n0': len(ids0), 'n1': len(g1), 'n2': len(g2),
    'imp': sum(1 for a in both if a['audit2'] > a['audit1']),
    'dec': sum(1 for a in both if a['audit2'] < a['audit1']),
    'same': sum(1 for a in both if a['audit2'] == a['audit1']),
    'both': len(both),
}

json.dump(out, open('scripts/report3_stats.json', 'w'))
print('ok')
