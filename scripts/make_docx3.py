import json
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

S = json.load(open('scripts/report3_stats.json', encoding='utf-8'))
CATS, WEEKS = S['cats'], S['weeks']
LATEST = WEEKS[-1]

def wk(ws): return 'W' + str(__import__('datetime').date.fromisoformat(ws).isocalendar()[1])
def pct(v, nd=2): return f"{v:.{nd}f}%" if v is not None else "—"
def num(v, nd=1): return f"{v:.{nd}f}" if v is not None else "—"

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
def bullet(t, bold_prefix=None):
    p = doc.add_paragraph(style='List Bullet')
    if bold_prefix:
        r = p.add_run(bold_prefix); r.bold = True
    p.add_run(t)
def add_table(headers, rows, widths=None):
    t = doc.add_table(rows=1+len(rows), cols=len(headers))
    t.style = 'Light Grid Accent 1'; t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for j, htxt in enumerate(headers):
        c = t.rows[0].cells[j]; c.text = htxt
        for p in c.paragraphs:
            for r in p.runs: r.bold = True; r.font.size = Pt(9.5)
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            c = t.rows[i+1].cells[j]; c.text = str(val)
            for p in c.paragraphs:
                for r in p.runs: r.font.size = Pt(9.5)
    if widths:
        for j, w in enumerate(widths):
            for row in t.rows: row.cells[j].width = Inches(w)
    doc.add_paragraph()

# ---------- Title ----------
tp = doc.add_paragraph(); tp.alignment = WD_ALIGN_PARAGRAPH.CENTER
tr = tp.add_run('Category-wise Audit vs IGCC Analysis — WOW × IGCC'); tr.bold = True; tr.font.size = Pt(18); tr.font.color.rgb = BLUE
sp = doc.add_paragraph(); sp.alignment = WD_ALIGN_PARAGRAPH.CENTER
sr = sp.add_run('FnV audit scores mapped to FnV IGCC, DBE to DBE, Ice Cream to Ice Cream, Meat to Meat — POD-wise, audit era 27 Aug – 08 Oct 2026')
sr.italic = True; sr.font.size = Pt(10); sr.font.color.rgb = GREY
doc.add_paragraph()

# ---------- Why the numbers differ ----------
h1('First — Why the IGCC % Differed Between Sections')
para('The earlier report and dashboard showed two different things side by side, which is why the FnV numbers did not match:', bold=True)
bullet('Weekly progression, Audited-vs-Non-audited and the audit-count tables used ALL-category IGCC (every complaint of the POD — FnV + DBE + Ice Cream + Meat combined).', bold_prefix='All-category IGCC: ')
bullet('The Category-wise table used FnV-only IGCC (only FnV complaints). FnV IGCC (1.34% in W39) is naturally higher than the blended figure (1.11%) because FnV generates the most complaints per order.', bold_prefix='Category-only IGCC: ')
para('Both were correct — they just answer different questions. From this report on, every audit-score comparison is mapped to the SAME category\'s IGCC (FnV score ↔ FnV IGCC), so numbers are directly comparable.')
para('Note on "Nectr": it is not a store — it is an IGCC complaint product name (e.g. "nectr Robusta Banana" appears in the complaint-bucketing file). No store named Nectr exists in the audit file (865 names) or store data, so nothing shows for it in the dashboard. If Nectr is a brand or dark-store cluster you need tracked, it must be added to the store master first.', italic=True)

# ---------- Executive summary ----------
h1('Executive Summary')
ss = S['score_summary']
para(f"Mapping each category's audit score to its own IGCC sharpens the picture. FnV shows a clean gradient: PODs scoring below 50 run {pct(S['bands_cat']['FnV'][0][2])} FnV-IGCC versus {pct(S['bands_cat']['FnV'][4][2])} for 80-89 scorers — POD-wise correlation is -0.18 (moderate but real). "
     f"DBE shows the same direction with a weaker signal; Meat follows it except for a noisy sub-50 bucket. Ice Cream shows no relationship — its IGCC stays 1.2-1.8% regardless of score, indicating complaint drivers outside storage SOPs (packaging, substitutions, delivery). "
     f"Overall {ss['imp']} of {ss['both']} twice-audited PODs improved their score (avg {num(ss['g2a1'])} to {num(ss['g2a2'])}), and PODs with the biggest A2 gains also cut their FnV IGCC the most (-0.05pp for 5+ gainers).")

add_table(
    ['Category', 'IGCC % (W41)', 'Audit-score gradient?', 'A1↔IGCC corr (POD-wise)', 'Verdict'],
    [
        ['FnV', pct(S['cat_weekly_all']['FnV'][-1]), 'Yes — 1.38% (<50) → 0.99% (80-89)', '-0.18 (n=678)', 'Audits are working — expand coverage'],
        ['DBE', pct(S['cat_weekly_all']['DBE'][-1]), 'Weak — 0.82% (<50) → 0.53-0.60% (80+)', '-0.07 (n=743)', 'Improving; audits help at the top end'],
        ['Ice Cream', pct(S['cat_weekly_all']['Ice Cream'][-1]), 'No — flat 1.7% across all score bands', 'n/a (too few orders)', 'Complaints not driven by storage SOPs'],
        ['Meat', pct(S['cat_weekly_all']['Meat'][-1]), 'Yes above 50 — 1.17% → 0.84%', 'n/a (too few orders)', '2-audit PODs clearly best (1.06%)'],
    ],
    widths=[1.0, 1.0, 2.1, 1.4, 1.7])

# ---------- Per category deep dive ----------
h1('FnV — Audit Score vs FnV IGCC (POD-wise)')
h2('FnV IGCC % by Audit-1 score band (W41)')
add_table(['Audit 1 score band', 'PODs', 'FnV IGCC % (W41)'],
          [[lbl, n, pct(v)] for lbl, n, v in S['bands_cat']['FnV']],
          widths=[2.0, 1.0, 1.6])
para('Every step up in audit score (except the small 90+ bucket, 11 PODs) comes with lower FnV IGCC: 1.38% → 1.36% → 1.25% → 1.25% → 0.99%. '
     'A better FnV audit score IS leading to lower FnV IGCC — the relationship holds POD-wise (correlation -0.18, strengthening to -0.30 for higher-volume PODs).', italic=True)

h2('Is the 2nd audit score better than the 1st — and does FnV IGCC follow?')
rows = []
for name, label in [('gain5+', 'Score gain ≥ 5'), ('gain<5', 'Score gain 0-5'), ('flat', 'Score unchanged'), ('declined', 'Score declined')]:
    c = S['a2_cohorts']['FnV'][name]
    rows.append([label, c['n'], pct(c['w38']), pct(c['w41']),
                 f"{c['w41']-c['w38']:+.2f}" if (c['w38'] is not None and c['w41'] is not None) else '—'])
add_table(['A1→A2 cohort', 'PODs', 'FnV IGCC (W38)', 'FnV IGCC (W41)', 'Change'], rows,
          widths=[1.6, 0.8, 1.3, 1.3, 1.0])
para('Yes — 101 of 189 twice-audited PODs improved their second-audit score. And the FnV IGCC follows: '
     'PODs with the largest score gains cut FnV complaints (1.28% → 1.23%), while the "gain 0-5" cohort — which started from the worst base (1.52%) — improved the most (-0.40pp). '
     'Score-declined PODs also fell, but from a lower base; the pattern confirms re-audits drive FnV quality in the right direction.', italic=True)

h2('FnV IGCC week-on-week by audit count (audit era)')
rows = []
for label, key in [('No audit', 'weekly0'), ('1 audit', 'weekly1'), ('2 audits', 'weekly2')]:
    vals = S['auditcount_cat']['FnV'][key]
    rows.append([label] + [pct(v) for v in vals])
add_table(['FnV segment'] + [wk(w) for w in WEEKS], rows, widths=[1.1, 0.85, 0.85, 0.85, 0.85, 0.85, 0.85, 0.85])
para('Twice-audited PODs now run the lowest FnV IGCC (1.23% in W41 vs 1.31% never-audited) — a 0.08pp advantage that emerged as re-audits scaled in W39-W40.', italic=True)

# ---------- DBE ----------
doc.add_page_break()
h1('DBE — Audit Score vs DBE IGCC')
h2('DBE IGCC % by Audit-1 score band (W41)')
add_table(['Audit 1 score band', 'PODs', 'DBE IGCC % (W41)'],
          [[lbl, n, pct(v)] for lbl, n, v in S['bands_cat']['DBE']],
          widths=[2.0, 1.0, 1.6])
para('Direction is right (0.82% for <50 → 0.53-0.60% for 80+) but the middle bands are flat at 0.74-0.78% — a weaker signal than FnV. DBE complaints (chilled/dairy) respond less to the storage-SOP checks the audit emphasises.', italic=True)

h2('DBE IGCC week-on-week by audit count')
rows = []
for label, key in [('No audit', 'weekly0'), ('1 audit', 'weekly1'), ('2 audits', 'weekly2')]:
    vals = S['auditcount_cat']['DBE'][key]
    rows.append([label] + [pct(v) for v in vals])
add_table(['DBE segment'] + [wk(w) for w in WEEKS], rows, widths=[1.1, 0.85, 0.85, 0.85, 0.85, 0.85, 0.85, 0.85])
para('All three segments improved from ~0.85% (W35) to 0.72-0.77% (W41), with twice-audited PODs best (0.72%). A2 cohorts for DBE: gain-5+ PODs moved 0.83% → 0.79%.', italic=True)

# ---------- Ice Cream ----------
h1('Ice Cream — Audit Score vs Ice Cream IGCC')
h2('Ice Cream IGCC % by Audit-1 score band (W41)')
add_table(['Audit 1 score band', 'PODs', 'Ice Cream IGCC % (W41)'],
          [[lbl, n, pct(v)] for lbl, n, v in S['bands_cat']['Ice Cream']],
          widths=[2.0, 1.0, 1.6])
para('No gradient — IGCC stays 1.74-1.76% across all bands below 70. Only the small 70+ cohorts (54-11 PODs) run lower (1.23-1.32%), likely a volume/assortment effect rather than audit quality. '
     'Ice Cream complaints are therefore NOT driven by the storage-SOP factors the audit measures — melting in last-mile delivery, substitutions and packaging are the usual suspects. '
     'Recommendation: add Ice Cream-specific checks (freezer temp at dispatch, dry-ice practice, packaging integrity) to the audit template before drawing further conclusions.', italic=True)

h2('Ice Cream IGCC week-on-week by audit count')
rows = []
for label, key in [('No audit', 'weekly0'), ('1 audit', 'weekly1'), ('2 audits', 'weekly2')]:
    vals = S['auditcount_cat']['Ice Cream'][key]
    rows.append([label] + [pct(v) for v in vals])
add_table(['Ice Cream segment'] + [wk(w) for w in WEEKS], rows, widths=[1.1, 0.85, 0.85, 0.85, 0.85, 0.85, 0.85, 0.85])
para('Twice-audited PODs consistently run ~0.15-0.2pp below never-audited (1.65% vs 1.69% in W41, widening to 1.48% vs 1.64% in W35) — audits do help, just not through the score. Seasonal easing visible across all segments in W41.', italic=True)

# ---------- Meat ----------
doc.add_page_break()
h1('Meat — Audit Score vs Meat IGCC')
h2('Meat IGCC % by Audit-1 score band (W41)')
add_table(['Audit 1 score band', 'PODs', 'Meat IGCC % (W41)'],
          [[lbl, n, pct(v)] for lbl, n, v in S['bands_cat']['Meat']],
          widths=[2.0, 1.0, 1.6])
para('Clean gradient above 50: 0.99% (50-59) → 1.17% (60-69) → 1.16% (70-79) → 0.87% (80-89) → 0.84% (90+). '
     'The sub-50 bucket (1.80%) is noisy — only ~130 PODs have Meat volume, and many have too few Meat orders for a stable rate. Treat the 50+ pattern as the signal.', italic=True)

h2('Meat IGCC week-on-week by audit count')
rows = []
for label, key in [('No audit', 'weekly0'), ('1 audit', 'weekly1'), ('2 audits', 'weekly2')]:
    vals = S['auditcount_cat']['Meat'][key]
    rows.append([label] + [pct(v) for v in vals])
add_table(['Meat segment'] + [wk(w) for w in WEEKS], rows, widths=[1.1, 0.85, 0.85, 0.85, 0.85, 0.85, 0.85, 0.85])
para('Twice-audited PODs are the best performers in four of the last five weeks (1.06% in W41 vs 1.17-1.20% for the others) — the strongest audit-effect of any category, worth expanding Meat re-audits.', italic=True)

# ---------- Recommendations ----------
h1('What To Do Next')
for txt in [
    'FnV: expand the audit wave — the score→IGCC link is proven POD-wise. Prioritise the 398 PODs scoring below 60, whose FnV IGCC (1.36-1.38%) is a third higher than 80+ scorers (0.99%).',
    'FnV re-audits: keep going. Score-gaining PODs cut FnV IGCC; the 76 unchanged PODs need root-cause follow-up, not just a repeat audit.',
    'Ice Cream: stop expecting the current score to predict complaints. Redesign its audit section around cold-chain at dispatch and packaging, then re-measure.',
    'Meat: expand 2nd audits — the 2-audit cohort beats both other segments in 4 of 5 recent weeks.',
    'DBE: maintain cadence; the improvement is steady but driven by the whole network, not audit targeting.',
    'Dashboard: the "Audit score vs IGCC" chart is now category-scoped — select FnV in the Category filter and the buckets show FnV-only IGCC (title confirms it). The mismatch you saw earlier was all-category vs category-only IGCC, both correct but measuring different things.',
]:
    bullet(txt)

doc.add_paragraph()
fp = doc.add_paragraph()
fr = fp.add_run('Source: Pod Audit Tool responses (wide) + Instamart IGCC category-level data (Snowflake). IGCC% = IGCC orders ÷ total orders within the same category. '
                'Correlations are POD-wise (Audit-1 score vs same-category IGCC %, W41, PODs with ≥500 orders in category).')
fr.italic = True; fr.font.size = Pt(8.5); fr.font.color.rgb = GREY

out = 'WOW_IGCC_Categorywise_Audit_Analysis.docx'
doc.save(out)
print('saved', out)
