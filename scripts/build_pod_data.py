import platform
platform.libc_ver = lambda *a, **k: ('', '')

import pandas as pd, json, gzip

igcc = pd.read_csv('igcc_qnp_data.csv')
igcc['ORDERS_IGCC'] = igcc['ORDERS_IGCC'].fillna(0)
igcc['dt'] = pd.to_datetime(igcc['ORDER_DATE'])

w = pd.read_csv('Audit response wide/Pod Audit Tool - Audit Responses (Wide) deduped.csv')
w['Date'] = pd.to_datetime(w['Date'])
w = w.sort_values(['Store ID', 'Date'])
aud = w.groupby('Store ID').agg(
    audit1_date=('Date', 'first'), audit1=('Total Score', 'first'),
    audit2_date=('Date', lambda s: s.iloc[1] if len(s) > 1 else None),
    audit2=('Total Score', lambda s: s.iloc[1] if len(s) > 1 else None),
    audit3=('Total Score', lambda s: s.iloc[2] if len(s) > 2 else None),
    n_audits=('Total Score', 'size'), audit_city=('City', 'first'),
    store_name=('Store Name', 'first'),
).reset_index()
store_info = igcc.groupby('STORE_ID').agg(city=('CITY', 'first'), city2=('CITY_2', 'first'), tier=('TIER', 'first')).reset_index()
m = aud.merge(store_info, left_on='Store ID', right_on='STORE_ID', how='inner')
# include all IGCC stores so unaudited PODs appear too
all_stores = store_info.merge(aud, left_on='STORE_ID', right_on='Store ID', how='left')
all_stores['n_audits'] = all_stores['n_audits'].fillna(0).astype(int)
audited_ids = set(all_stores['STORE_ID'])
igcc_a = igcc[igcc['STORE_ID'].isin(audited_ids)]
igcc_a2 = igcc_a.copy()
igcc_a2['ws'] = (igcc_a2['dt'] - pd.to_timedelta(igcc_a2['dt'].dt.dayofweek, unit='D')).dt.strftime('%Y-%m-%d')

wk = igcc_a2.groupby(['STORE_ID', 'ws']).agg(ot=('ORDERS_TOTAL', 'sum'), oi=('ORDERS_IGCC', 'sum')).reset_index()
wk['qnp'] = (wk.oi / wk.ot * 100).round(3)

wk_cat = igcc_a2[igcc_a2['dt'] >= '2026-08-01'].groupby(['STORE_ID', 'ws', 'CATEGORY_FINAL']).agg(ot=('ORDERS_TOTAL', 'sum'), oi=('ORDERS_IGCC', 'sum')).reset_index()
wk_cat['qnp'] = (wk_cat.oi / wk_cat.ot * 100).round(3)

d = igcc_a[igcc_a['dt'] >= '2026-08-01']
dates = sorted(d['ORDER_DATE'].unique())
date_idx = {dd: i for i, dd in enumerate(dates)}
cats = ['FnV', 'DBE', 'Ice Cream', 'Meat']
cat_idx = {c: i for i, c in enumerate(cats)}

daily_pos = d[d['ORDERS_IGCC'] > 0]
dtot = d.groupby(['STORE_ID', 'ORDER_DATE']).agg(ot=('ORDERS_TOTAL', 'sum')).reset_index()

igcc_matrix = {}
igcc_cat_matrix = {}
ot_matrix = {}
ot_cat_matrix = {}
for _, r in daily_pos.iterrows():
    key = f"{int(r['STORE_ID'])}_{date_idx[r['ORDER_DATE']]}"
    igcc_matrix[key] = igcc_matrix.get(key, 0) + int(r['ORDERS_IGCC'])
    ckey = f"{int(r['STORE_ID'])}_{date_idx[r['ORDER_DATE']]}_{cat_idx[r['CATEGORY_FINAL']]}"
    igcc_cat_matrix[ckey] = int(r['ORDERS_IGCC'])
for _, r in dtot.iterrows():
    ot_matrix[f"{int(r['STORE_ID'])}_{date_idx[r['ORDER_DATE']]}"] = int(r['ot'])

# per-category daily orders total: sparse — only keep rows where the category had orders
dtot_cat = d.groupby(['STORE_ID', 'ORDER_DATE', 'CATEGORY_FINAL']).agg(ot=('ORDERS_TOTAL', 'sum')).reset_index()
for _, r in dtot_cat.iterrows():
    ot_cat_matrix[f"{int(r['STORE_ID'])}_{date_idx[r['ORDER_DATE']]}_{cat_idx[r['CATEGORY_FINAL']]}"] = int(r['ot'])

citywk = igcc.copy()
citywk['ws'] = (citywk['dt'] - pd.to_timedelta(citywk['dt'].dt.dayofweek, unit='D')).dt.strftime('%Y-%m-%d')
citywk = citywk.groupby(['CITY_2', 'TIER', 'ws']).agg(ot=('ORDERS_TOTAL', 'sum'), oi=('ORDERS_IGCC', 'sum')).reset_index()

aud_out = all_stores.rename(columns={'Store ID': 'store_id'})
aud_out['audit2_date'] = aud_out['audit2_date'].astype(str).replace('NaT', None)
aud_out['audit1_date'] = aud_out['audit1_date'].astype(str).replace('NaT', None)
aud_out['store_id'] = aud_out['store_id'].fillna(aud_out['STORE_ID']).astype(int)
aud_out = aud_out.drop(columns=['STORE_ID'], errors='ignore')
aud_out['store_name'] = aud_out['store_name'].fillna('')
aud_out['audit_city'] = aud_out['audit_city'].fillna('')
aud_out['audit1'] = aud_out['audit1'].where(aud_out['audit1'].notna(), None)

def _nan_to_none(o):
    import math
    if isinstance(o, dict): return {k: _nan_to_none(v) for k, v in o.items()}
    if isinstance(o, list): return [_nan_to_none(v) for v in o]
    if isinstance(o, float) and math.isnan(o): return None
    return o

data = {
    'dates': [str(x) for x in dates],
    'cats': cats,
    'audits': aud_out[['store_id', 'store_name', 'audit_city', 'city', 'city2', 'tier', 'n_audits', 'audit1', 'audit1_date', 'audit2', 'audit2_date', 'audit3']].to_dict('records'),
    'weekly': wk.rename(columns={'STORE_ID': 'store_id'}).to_dict('records'),
    'weekly_cat': wk_cat.rename(columns={'STORE_ID': 'store_id'}).to_dict('records'),
    'igcc_matrix': igcc_matrix,
    'igcc_cat_matrix': igcc_cat_matrix,
    'ot_matrix': ot_matrix,
    'ot_cat_matrix': ot_cat_matrix,
    'city_weekly': citywk.rename(columns={'CITY_2': 'city2', 'TIER': 'tier'}).to_dict('records'),
}
data = _nan_to_none(data)
s = json.dumps(data, separators=(',', ':'))
with gzip.open('pod_data.json.gz', 'wt') as f:
    f.write(s)
print('raw MB:', round(len(s) / 1e6, 1), '| gzipped MB:', round(len(gzip.compress(s.encode())) / 1e6, 1))
