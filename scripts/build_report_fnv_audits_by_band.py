import json
import pandas as pd

d = json.load(open('pod_data.json', encoding='utf-8'))
WEEKS = ['2026-08-31','2026-09-07','2026-09-14','2026-09-21','2026-09-28','2026-10-05']

w = pd.read_csv('Audit response wide/Pod Audit Tool - Audit Responses (Wide) deduped.csv')
w['Date'] = pd.to_datetime(w['Date'])
fnv = [c for c in w.columns if c.startswith('FNV') and c.endswith('(Score)') and 'Completed' not in c]
w['fnv_pct'] = w[fnv].sum(axis=1) / (w[fnv].notna() * 2).sum(axis=1) * 100
w = w.sort_values(['Store ID', 'Date'])
w['audit_seq'] = w.groupby('Store ID').cumcount() + 1  # 1=A1, 2=A2, 3+=A3

bands = [('<50',0,50),('50-59',50,60),('60-69',60,70),('70-79',70,80),('80-89',80,90),('90+',90,101)]

def band_of(pct):
    for lbl, lo, hi in bands:
        if lo <= pct < hi: return lbl
    return None

w['band'] = w['fnv_pct'].apply(band_of)
w['ws'] = (w['Date'] - pd.to_timedelta(w['Date'].dt.dayofweek, unit='D')).dt.strftime('%Y-%m-%d')

out = {'weeks': WEEKS, 'wk_labels': ['W%d' % pd.Timestamp(ws).week for ws in WEEKS], 'bands': []}
for lbl, lo, hi in bands:
    sub = w[w['band'] == lbl]
    row = {'band': lbl}
    for seq, key in [(1, 'a1'), (2, 'a2')]:
        row[key] = [int((sub['ws'] == ws).sum() & (sub['audit_seq'] == seq).sum() if False else ((sub['ws'] == ws) & (sub['audit_seq'] == seq)).sum()) for ws in WEEKS]
    row['total'] = [int((sub['ws'] == ws).sum()) for ws in WEEKS]
    out['bands'].append(row)
    print(lbl, 'A1:', row['a1'], 'A2:', row['a2'], 'total:', row['total'])

json.dump(out, open('scripts/report_fnv_audits_by_band.json', 'w'))
print('saved')
