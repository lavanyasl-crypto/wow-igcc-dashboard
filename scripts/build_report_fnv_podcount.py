import json, datetime

FNV = json.load(open('scripts/report_fnv_only_stats.json', encoding='utf-8'))
d = json.load(open('pod_data.json', encoding='utf-8'))
audits = d['audits']; weekly_cat = d['weekly_cat']
WEEKS = FNV['weeks']

import pandas as pd
w = pd.read_csv('Audit response wide/Pod Audit Tool - Audit Responses (Wide) (1).csv')
w['Date'] = pd.to_datetime(w['Date'])
fnv = [c for c in w.columns if c.startswith('FNV') and c.endswith('(Score)') and 'Completed' not in c]
w['fnv_pct'] = w[fnv].sum(axis=1) / (w[fnv].notna() * 2).sum(axis=1) * 100
w = w.sort_values(['Store ID', 'Date'])
aud = w.groupby('Store ID').agg(fnv_a1=('fnv_pct', 'first')).reset_index()

bands = [('<50',0,50),('50-59',50,60),('60-69',60,70),('70-79',70,80),('80-89',80,90),('90+',90,101)]
out = []
for lbl, lo, hi in bands:
    ids = {int(r['Store ID']) for _, r in aud.iterrows() if pd.notna(r['fnv_a1']) and lo <= r['fnv_a1'] < hi}
    counts = []
    for ws in WEEKS:
        n = sum(1 for r in weekly_cat if r['ws'] == ws and r['store_id'] in ids and r.get('CATEGORY_FINAL') == 'FnV' and (r['ot'] or 0) > 0)
        counts.append(n)
    out.append({'band': lbl, 'total': len(ids), 'weekly': counts})
    print(lbl, 'total', len(ids), counts)

FNV['band_pod_counts'] = out
json.dump(FNV, open('scripts/report_fnv_only_stats.json', 'w'))
print('saved')
