import json, datetime

d = json.load(open('pod_data.json', encoding='utf-8'))
audits = d['audits']; weekly_cat = d['weekly_cat']
WEEKS = ['2026-08-31','2026-09-07','2026-09-14','2026-09-21','2026-09-28','2026-10-05']
bands = [('<50',0,50),('50-59',50,60),('60-69',60,70),('70-79',70,80),('80-89',80,90),('90+',90,101)]

band_ids = []
for lbl, lo, hi in bands:
    ids = {a['store_id'] for a in audits if a['audit1'] is not None and lo <= a['audit1'] < hi}
    band_ids.append((lbl, ids))

out = {'weeks': WEEKS, 'wk_labels': ['W%d' % datetime.date.fromisoformat(w).isocalendar()[1] for w in WEEKS],
       'bands': []}
for lbl, ids in band_ids:
    row = {'band': lbl, 'n': len(ids), 'weekly': []}
    for w in WEEKS:
        ot = oi = 0
        for r in weekly_cat:
            if r['ws'] == w and r['store_id'] in ids and r.get('CATEGORY_FINAL') == 'FnV':
                ot += r['ot'] or 0; oi += r['oi'] or 0
        row['weekly'].append(round(oi/ot*100, 2) if ot else None)
    row['orders_wk'] = None
    out['bands'].append(row)

json.dump(out, open('scripts/report_fnv_bands_stats.json', 'w'))
for b in out['bands']:
    print(b['band'], b['n'], b['weekly'])
