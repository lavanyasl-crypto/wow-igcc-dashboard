import json, datetime

d = json.load(open('pod_data.json', encoding='utf-8'))
audits = d['audits']
WEEKS = ['2026-08-31','2026-09-07','2026-09-14','2026-09-21','2026-09-28','2026-10-05']
cats = ['FnV', 'DBE', 'Ice Cream', 'Meat']

def wknum(ws): return datetime.date.fromisoformat(ws).isocalendar()[1]

ids0 = {a['store_id'] for a in audits if a['n_audits'] == 0}
ids1 = {a['store_id'] for a in audits if a['n_audits'] == 1}
ids2 = {a['store_id'] for a in audits if a['n_audits'] == 2}
allids = {a['store_id'] for a in audits}

def agg(rows, pids, ws, cat=None):
    ot = oi = 0
    for r in rows:
        if r['ws'] == ws and r['store_id'] in pids and (cat is None or r.get('CATEGORY_FINAL') == cat):
            ot += r['ot'] or 0; oi += r['oi'] or 0
    return (oi / ot * 100) if ot else None

weekly, weekly_cat = d['weekly'], d['weekly_cat']

out = {
    'weeks': WEEKS,
    'wk_labels': ['W%d' % wknum(w) for w in WEEKS],
    # 1. audits per week (A1 / A2)
    'audits_week': [],
    # 2. overall IGCC weekly
    'overall': [agg(weekly, allids, w) for w in WEEKS],
    # 3. category weekly
    'cat_weekly': {c: [agg(weekly_cat, allids, w, c) for w in WEEKS] for c in cats},
    # 4. audit-count segments weekly
    'seg_weekly': {
        'noaudit': [agg(weekly, ids0, w) for w in WEEKS],
        'a1': [agg(weekly, ids1, w) for w in WEEKS],
        'a2': [agg(weekly, ids2, w) for w in WEEKS],
    },
    # 5. FnV by audit count
    'fnv_seg_weekly': {
        'noaudit': [agg(weekly_cat, ids0, w, 'FnV') for w in WEEKS],
        'a1': [agg(weekly_cat, ids1, w, 'FnV') for w in WEEKS],
        'a2': [agg(weekly_cat, ids2, w, 'FnV') for w in WEEKS],
    },
    'seg_counts': {'n0': len(ids0), 'n1': len(ids1), 'n2': len(ids2)},
}

for w in WEEKS:
    s = new = datetime.date.fromisoformat(w)
    e = s + datetime.timedelta(days=6)
    a1 = sum(1 for a in audits if a['audit1_date'] and s.isoformat() <= a['audit1_date'] <= e.isoformat())
    a2 = sum(1 for a in audits if a['audit2_date'] and s.isoformat() <= a['audit2_date'] <= e.isoformat())
    out['audits_week'].append({'a1': a1, 'a2': a2, 'total': a1 + a2})

json.dump(out, open('scripts/report_wow_stats.json', 'w'))
print('ok', out['wk_labels'], 'overall:', [round(v, 2) if v else v for v in out['overall']])
