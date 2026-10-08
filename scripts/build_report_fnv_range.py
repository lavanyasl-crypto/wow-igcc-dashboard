import json, datetime, math

CUTOFF = '2026-08-27'
d = json.load(open('pod_data.json', encoding='utf-8'))
audits = d['audits']; cats = d['cats']
dates = d['dates']
WEEKS = ['2026-08-24','2026-08-31','2026-09-07','2026-09-14','2026-09-21','2026-09-28','2026-10-05']
LATEST = WEEKS[-1]

def monday(ds):
    dt = datetime.date.fromisoformat(ds)
    return (dt - datetime.timedelta(days=dt.weekday())).isoformat()

# per-category weekly aggregation from daily matrices, restricted to audit era
agg = {}
for key, oi in d['igcc_cat_matrix'].items():
    pid, didx, ci = key.split('_')
    dt = dates[int(didx)]
    if dt < CUTOFF: continue
    k = (monday(dt), int(pid), int(ci))
    e = agg.setdefault(k, [0, 0]); e[1] += oi
for key, ot in d['ot_cat_matrix'].items():
    pid, didx, ci = key.split('_')
    dt = dates[int(didx)]
    if dt < CUTOFF: continue
    k = (monday(dt), int(pid), int(ci))
    e = agg.setdefault(k, [0, 0]); e[0] += ot

wcat = [{'ws': ws, 'store_id': pid, 'CATEGORY_FINAL': cats[ci], 'ot': ot, 'oi': oi}
        for (ws, pid, ci), (ot, oi) in agg.items()]

def qcat(pids, cat, ws):
    ot = oi = 0
    for r in wcat:
        if r['ws'] == ws and r['store_id'] in pids and r['CATEGORY_FINAL'] == cat:
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
out = {'cats': cats, 'weeks': WEEKS, 'cutoff': CUTOFF,
       'week_note': {'2026-08-24': '27-30 Aug (partial)'}}

out['bands_cat'] = {}
for cat in cats:
    rows = []
    for lbl, lo, hi in bands:
        ids = {a['store_id'] for a in audits if a['audit1'] is not None and lo <= a['audit1'] < hi}
        rows.append([lbl, len(ids), qcat(ids, cat, LATEST)])
    out['bands_cat'][cat] = rows

out['auditcount_cat'] = {}
for cat in cats:
    out['auditcount_cat'][cat] = {
        'w41': [qcat(ids, cat, LATEST) for ids in (ids0, ids1, ids2)],
        'weekly0': [qcat(ids0, cat, w) for w in WEEKS],
        'weekly1': [qcat(ids1, cat, w) for w in WEEKS],
        'weekly2': [qcat(ids2, cat, w) for w in WEEKS],
    }

cohorts = {
    'gain5+': {a['store_id'] for a in both if a['audit2']-a['audit1'] >= 5},
    'gain<5': {a['store_id'] for a in both if 0 < a['audit2']-a['audit1'] < 5},
    'flat': {a['store_id'] for a in both if a['audit2'] == a['audit1']},
    'declined': {a['store_id'] for a in both if a['audit2'] < a['audit1']},
}
out['a2_cohorts'] = {cat: {name: {'n': len(ids),
    'w38': qcat(ids, cat, '2026-09-14'), 'w41': qcat(ids, cat, LATEST)} for name, ids in cohorts.items()}
    for cat in cats}

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
        rows = [r for r in wcat if r['ws']==LATEST and r['store_id']==a['store_id'] and r['CATEGORY_FINAL']==cat]
        ot = sum(r['ot'] or 0 for r in rows); oi = sum(r['oi'] or 0 for r in rows)
        if ot >= 500: pairs.append((a['audit1'], oi/ot*100))
    out['corr'][cat] = {'r': corr(pairs), 'n': len(pairs)}

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

json.dump(out, open('scripts/report_fnv_stats.json', 'w'))
print('ok')
