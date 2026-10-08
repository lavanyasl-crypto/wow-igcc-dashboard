import json, math
import pandas as pd

# ---- FnV-only subscore per audit ----
w = pd.read_csv('Audit response wide/Pod Audit Tool - Audit Responses (Wide) deduped.csv')
w['Date'] = pd.to_datetime(w['Date'])
fnv = [c for c in w.columns if c.startswith('FNV') and c.endswith('(Score)') and 'Completed' not in c]
w['fnv_pct'] = w[fnv].sum(axis=1) / (w[fnv].notna() * 2).sum(axis=1) * 100
w = w.sort_values(['Store ID', 'Date'])

aud = w.groupby('Store ID').agg(fnv_a1=('fnv_pct', 'first'), fnv_a2=('fnv_pct', lambda s: s.iloc[1] if len(s) > 1 else None),
                                n_audits=('fnv_pct', 'size')).reset_index()

d = json.load(open('pod_data.json', encoding='utf-8'))
weekly_cat = d['weekly_cat']
WEEKS = ['2026-08-31','2026-09-07','2026-09-14','2026-09-21','2026-09-28','2026-10-05']
LATEST = WEEKS[-1]

def qfnv(pids, ws):
    ot = oi = 0
    for r in weekly_cat:
        if r['ws'] == ws and r['store_id'] in pids and r.get('CATEGORY_FINAL') == 'FnV':
            ot += r['ot'] or 0; oi += r['oi'] or 0
    return round(oi/ot*100, 2) if ot else None

bands = [('<50',0,50),('50-59',50,60),('60-69',60,70),('70-79',70,80),('80-89',80,90),('90+',90,101)]
out = {'weeks': WEEKS, 'bands': [], 'corr': {}}

band_rows = []
for lbl, lo, hi in bands:
    ids = {int(r['Store ID']) for _, r in aud.iterrows() if pd.notna(r['fnv_a1']) and lo <= r['fnv_a1'] < hi}
    weekly = []
    for ws in WEEKS:
        weekly.append(qfnv(ids, ws))
    band_rows.append({'band': lbl, 'n': len(ids), 'weekly': weekly})

# POD-wise correlation: FnV-only A1 vs FnV IGCC (W41, >=500 FnV orders)
pairs = []
for _, r in aud.iterrows():
    if pd.isna(r['fnv_a1']): continue
    pid = int(r['Store ID'])
    ot = oi = 0
    for rr in weekly_cat:
        if rr['ws'] == LATEST and rr['store_id'] == pid and rr.get('CATEGORY_FINAL') == 'FnV':
            ot += rr['ot'] or 0; oi += rr['oi'] or 0
    if ot >= 500: pairs.append((r['fnv_a1'], oi/ot*100))

def corr(pairs):
    n = len(pairs)
    if n < 10: return None
    mx = sum(p[0] for p in pairs)/n; my = sum(p[1] for p in pairs)/n
    sx = math.sqrt(sum((p[0]-mx)**2 for p in pairs)); sy = math.sqrt(sum((p[1]-my)**2 for p in pairs))
    if not sx or not sy: return None
    return round(sum((p[0]-mx)*(p[1]-my) for p in pairs)/(sx*sy), 3)

out['bands'] = band_rows
out['corr'] = {'r': corr(pairs), 'n': len(pairs)}

# A2 vs A1 FnV-only cohorts
both = aud[aud['fnv_a2'].notna() & aud['fnv_a1'].notna()]
out['a2'] = {
    'both': int(len(both)),
    'imp': int((both['fnv_a2'] > both['fnv_a1']).sum()),
    'g2a1': round(float(both['fnv_a1'].mean()), 1),
    'g2a2': round(float(both['fnv_a2'].mean()), 1),
}
cohorts = {
    'gain5+': [int(r['Store ID']) for _, r in both.iterrows() if r['fnv_a2']-r['fnv_a1'] >= 5],
    'gain<5': [int(r['Store ID']) for _, r in both.iterrows() if 0 < r['fnv_a2']-r['fnv_a1'] < 5],
    'flat': [int(r['Store ID']) for _, r in both.iterrows() if r['fnv_a2'] == r['fnv_a1']],
    'declined': [int(r['Store ID']) for _, r in both.iterrows() if r['fnv_a2'] < r['fnv_a1']],
}
out['a2_cohorts'] = {name: {'n': len(ids), 'w38': qfnv(set(ids), '2026-09-14'), 'w41': qfnv(set(ids), LATEST)} for name, ids in cohorts.items()}

json.dump(out, open('scripts/report_fnv_only_stats.json', 'w'))
for b in out['bands']: print(b['band'], b['n'], b['weekly'])
print('corr:', out['corr'])
print('a2:', out['a2'])
print('cohorts:', {k: v for k, v in out['a2_cohorts'].items()})
