import json
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

S = json.load(open('scripts/report_wow_stats.json', encoding='utf-8'))
WEEKS, WKL = S['weeks'], S['wk_labels']

def pct(v, nd=2): return f"{v:.{nd}f}" if v is not None else "—"
def delta(vals):
    if vals[0] is None or vals[-1] is None: return '—'
    d = vals[-1] - vals[0]
    return f"{d:+.2f}"

GOOD = RGBColor(0x1E, 0x7B, 0x34); BAD = RGBColor(0xC0, 0x39, 0x2B)

doc = Document()
style = doc.styles['Normal']; style.font.name = 'Calibri'; style.font.size = Pt(10.5)
for sec in doc.sections:
    sec.left_margin = Inches(0.7); sec.right_margin = Inches(0.7)
    sec.top_margin = Inches(0.7); sec.bottom_margin = Inches(0.7)

BLUE = RGBColor(0x1F, 0x4E, 0x79); GREY = RGBColor(0x60, 0x60, 0x60)
def h1(t):
    p = doc.add_heading(t, level=1)
    for r in p.runs: r.font.color.rgb = BLUE; r.font.size = Pt(15)
def h2(t):
    p = doc.add_heading(t, level=2)
    for r in p.runs: r.font.color.rgb = BLUE; r.font.size = Pt(12.5)
def para(t, bold=False, italic=False):
    p = doc.add_paragraph(); r = p.add_run(t); r.bold = bold; r.italic = italic

def delta_run(p, d):
    r = p.add_run(d)
    r.bold = True
    if d == '—': r.font.color.rgb = GREY
    elif d.startswith('+'): r.font.color.rgb = BAD   # IGCC up = bad
    else: r.font.color.rgb = GOOD                    # IGCC down = good

def wow_table(headers, rows, widths, delta_col_idx, shade_col_idx=None):
    """rows: list of lists; delta_col_idx = index of the delta column to colorize; shade_col_idx = index of row-label col to bold"""
    t = doc.add_table(rows=1+len(rows), cols=len(headers))
    t.style = 'Light Grid Accent 1'; t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for j, htxt in enumerate(headers):
        c = t.rows[0].cells[j]; c.text = htxt
        for p in c.paragraphs:
            for r in p.runs: r.bold = True; r.font.size = Pt(9.5)
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            c = t.rows[i+1].cells[j]
            p0 = c.paragraphs[0]
            r = p0.add_run(str(val)); r.font.size = Pt(9.5)
            if j == delta_col_idx: delta_run(p0, str(val)) if False else None
            if j == shade_col_idx and i == 0: r.bold = True
        if j == delta_col_idx: pass
    # colorize delta column (re-run since cell.text approach is messy)
    if delta_col_idx is not None:
        for i, row in enumerate(rows):
            cell = t.rows[i+1].cells[delta_col_idx]
            p0 = cell.paragraphs[0]
            txt = p0.text
            p0.clear()
            r = p0.add_run(txt); r.font.size = Pt(9.5); r.bold = True
            if txt == '—': r.font.color.rgb = GREY
            elif txt.startswith('+'): r.font.color.rgb = BAD
            else: r.font.color.rgb = GOOD
    if widths:
        for j, w in enumerate(widths):
            for row in t.rows: row.cells[j].width = Inches(w)
    doc.add_paragraph()

# ---------- Title ----------
tp = doc.add_paragraph(); tp.alignment = WD_ALIGN_PARAGRAPH.CENTER
tr = tp.add_run('Week-on-Week IGCC Comparison — W36 to W41'); tr.bold = True; tr.font.size = Pt(18); tr.font.color.rgb = BLUE
sp = doc.add_paragraph(); sp.alignment = WD_ALIGN_PARAGRAPH.CENTER
sr = sp.add_run('Full audit weeks only: 31 Aug – 08 Oct 2026 (W41 = w/c 05 Oct, partial 4 days) · Every table reads the same way: weeks across the top, last column = change W36 → W41. Green = IGCC improved, red = worsened.')
sr.italic = True; sr.font.size = Pt(10); sr.font.color.rgb = GREY
doc.add_paragraph()

# ---------- 1. Audits & overall IGCC ----------
h1('1. The Master Table — Audits Done vs Overall IGCC, Week by Week')
rows = []
for i, w in enumerate(WEEKS):
    aw = S['audits_week'][i]
    rows.append([WKL[i], w[5:], aw['a1'], aw['a2'], aw['total'], pct(S['overall'][i]), delta(S['overall'][:i+1]) if i else '—'])
wow_table(['Week', 'w/c', 'A1 audits', 'A2 audits', 'Total', 'IGCC %', 'vs W36 (pp)'],
          rows, widths=[0.7, 0.9, 0.9, 0.9, 0.8, 0.9, 1.1], delta_col_idx=6)
para('Read: the audit wave peaked in W38–W39 (578 audits), then tapered as the programme shifted to re-audits. '
     'IGCC peaked at 1.13% in W37 and has declined every week since — 1.13 → 1.12 → 1.11 → 1.10 → 1.06 — landing 0.07pp below the W36 start. '
     'The decline begins exactly when the audit volume hits scale.', italic=True)

# ---------- 2. Category ----------
h1('2. Category-wise IGCC, Week by Week')
rows = []
for c in S['cat_weekly']:
    vals = S['cat_weekly'][c]
    rows.append([c] + [pct(v) for v in vals] + [delta(vals)])
wow_table(['Category'] + WKL + ['Δ W36→41 (pp)'], rows,
          widths=[0.95] + [0.72]*len(WKL) + [1.15], delta_col_idx=len(WKL)+1)
para('FnV is the laggard: best week was W37 (1.20%), worst W40 (1.36%), and it ends only 0.02pp below where it started — audits have not yet bent the FnV curve. '
     'DBE is the quiet improver (-0.09pp). Ice Cream remains the highest-IGCC category throughout (1.63–1.84%) but eases 0.12pp by W41. '
     'Meat improves 0.13pp and finishes strong at 0.98% — the best week of the era.', italic=True)

# ---------- 3. Audit-count segments ----------
h1('3. IGCC by Audit Count — Never vs Once vs Twice Audited')
rows = []
for lbl, key, n in [('Never audited', 'noaudit', S['seg_counts']['n0']),
                    ('1 audit', 'a1', S['seg_counts']['n1']),
                    ('2 audits', 'a2', S['seg_counts']['n2'])]:
    vals = S['seg_weekly'][key]
    rows.append([f"{lbl} (n={n})"] + [pct(v) for v in vals] + [delta(vals)])
wow_table(['All-category segment'] + WKL + ['Δ W36→41 (pp)'], rows,
          widths=[1.35] + [0.68]*len(WKL) + [1.1], delta_col_idx=len(WKL)+1)
para('Twice-audited PODs end lowest (1.06% in W41) and improved most from their W37 base. '
     'Never-audited PODs sit between — they benefit from network-wide improvement but have had no direct intervention. '
     'Caution for the discussion: segment membership changes over time (PODs move from never→once→twice as audits happen), so read the direction, not the exact levels.', italic=True)

# ---------- 4. FnV segments ----------
doc.add_page_break()
h1('4. FnV IGCC by Audit Count — the Problem Category, Same Split')
rows = []
for lbl, key in [('Never audited', 'noaudit'), ('1 audit', 'a1'), ('2 audits', 'a2')]:
    vals = S['fnv_seg_weekly'][key]
    rows.append([lbl] + [pct(v) for v in vals] + [delta(vals)])
wow_table(['FnV segment'] + WKL + ['Δ W36→41 (pp)'], rows,
          widths=[1.35] + [0.68]*len(WKL) + [1.1], delta_col_idx=len(WKL)+1)
para('The FnV story is the same shape but flatter: twice-audited PODs run the lowest FnV IGCC in the latest weeks (1.21% in W41 vs 1.29–1.31% for the others), '
     'but the advantage only appears from W39 onward as re-audits scaled. FnV needs volume: the ~400 PODs still scoring below 60 on Audit 1 are the target for the next wave.', italic=True)

# ---------- 5. One-glance scorecard ----------
h1('5. One-Glance Scorecard — What Improved, What Did Not')
rows = [
    ['Overall IGCC', pct(S['overall'][0]), pct(S['overall'][-1]), delta(S['overall']), 'Improved 5 weeks straight since W37 peak'],
    ['FnV', pct(S['cat_weekly']['FnV'][0]), pct(S['cat_weekly']['FnV'][-1]), delta(S['cat_weekly']['FnV']), 'Flat — needs the next audit wave'],
    ['DBE', pct(S['cat_weekly']['DBE'][0]), pct(S['cat_weekly']['DBE'][-1]), delta(S['cat_weekly']['DBE']), 'Steady improver all era'],
    ['Ice Cream', pct(S['cat_weekly']['Ice Cream'][0]), pct(S['cat_weekly']['Ice Cream'][-1]), delta(S['cat_weekly']['Ice Cream']), 'Still highest; audit template needs cold-chain checks'],
    ['Meat', pct(S['cat_weekly']['Meat'][0]), pct(S['cat_weekly']['Meat'][-1]), delta(S['cat_weekly']['Meat']), 'Best W41 of the era — hold the gain'],
    ['2-audit PODs', '—', pct(S['seg_weekly']['a2'][-1]), '—', 'Lowest IGCC segment in W41'],
    ['Never-audited PODs', '—', pct(S['seg_weekly']['noaudit'][-1]), '—', 'Highest IGCC segment in W41'],
]
wow_table(['Metric', 'W36', 'W41', 'Δ (pp)', 'Read'], rows,
          widths=[1.3, 0.75, 0.75, 0.8, 2.7], delta_col_idx=3)
para('Bottom line: the audit programme is working where it reached (2-audit PODs, Meat, DBE, overall) and has not yet reached enough of FnV. '
     'Next wave: re-audit the ~400 sub-60 scorers, and add cold-chain checks to the Ice Cream template.', italic=True)

doc.add_paragraph()
fp = doc.add_paragraph()
fr = fp.add_run('Source: Pod Audit Tool responses + Instamart IGCC data (Snowflake). IGCC% = IGCC orders ÷ total orders. Full weeks W36 (w/c 31 Aug) through W41 (w/c 05 Oct, partial to 08 Oct). '
                'Green = IGCC improved (went down), red = worsened (went up). Segment n = PODs in each audit-count group as of 08 Oct.')
fr.italic = True; fr.font.size = Pt(8.5); fr.font.color.rgb = GREY

out = 'WOW_IGCC_Week_on_Week_W36_W41.docx'
doc.save(out)
print('saved', out)
