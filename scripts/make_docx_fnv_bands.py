import json
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

S = json.load(open('scripts/report_fnv_bands_stats.json', encoding='utf-8'))
WEEKS, WKL = S['weeks'], S['wk_labels']

GOOD = RGBColor(0x1E, 0x7B, 0x34); BAD = RGBColor(0xC0, 0x39, 0x2B)
BLUE = RGBColor(0x1F, 0x4E, 0x79); GREY = RGBColor(0x60, 0x60, 0x60)

def pct(v): return f"{v:.2f}" if v is not None else "—"
def dcol(v0, v1):
    if v0 is None or v1 is None: return '—'
    return f"{v1-v0:+.2f}"

doc = Document()
style = doc.styles['Normal']; style.font.name = 'Calibri'; style.font.size = Pt(10.5)
for sec in doc.sections:
    sec.left_margin = Inches(0.7); sec.right_margin = Inches(0.7)
    sec.top_margin = Inches(0.7); sec.bottom_margin = Inches(0.7)

def h1(t):
    p = doc.add_heading(t, level=1)
    for r in p.runs: r.font.color.rgb = BLUE; r.font.size = Pt(15)
def para(t, bold=False, italic=False):
    p = doc.add_paragraph(); r = p.add_run(t); r.bold = bold; r.italic = italic
def bullet(t, bold_prefix=None):
    p = doc.add_paragraph(style='List Bullet')
    if bold_prefix:
        r = p.add_run(bold_prefix); r.bold = True
    p.add_run(t)

# ---------- Title ----------
tp = doc.add_paragraph(); tp.alignment = WD_ALIGN_PARAGRAPH.CENTER
tr = tp.add_run('FnV Audit Score vs FnV IGCC — Week-on-Week by Score Band'); tr.bold = True; tr.font.size = Pt(18); tr.font.color.rgb = BLUE
sp = doc.add_paragraph(); sp.alignment = WD_ALIGN_PARAGRAPH.CENTER
sr = sp.add_run('The W41 band table from the POD-wise report, extended to every week W36–W41 (full weeks from 31 Aug) · Does the score-IGCC staircase hold week after week, or only in the latest week?')
sr.italic = True; sr.font.size = Pt(10); sr.font.color.rgb = GREY
doc.add_paragraph()

# ---------- Main table ----------
h1('FnV IGCC % by Audit-1 Score Band, Week by Week')
para('Each cell = FnV IGCC of all PODs in that score band during that week. Last column = change from W36 to W41 (green = improved, red = worsened).', italic=True)

t = doc.add_table(rows=1+len(S['bands']), cols=2+len(WKL)+1)
t.style = 'Light Grid Accent 1'; t.alignment = WD_TABLE_ALIGNMENT.CENTER
heads = ['Score band', 'PODs'] + WKL + ['Δ W36→41']
for j, htxt in enumerate(heads):
    c = t.rows[0].cells[j]; c.text = htxt
    for p in c.paragraphs:
        for r in p.runs: r.bold = True; r.font.size = Pt(9.5)
for i, b in enumerate(S['bands']):
    row = t.rows[i+1]
    vals = b['weekly']
    cells_txt = [b['band'], str(b['n'])] + [pct(v) for v in vals] + [dcol(vals[0], vals[-1])]
    for j, txt in enumerate(cells_txt):
        p0 = row.cells[j].paragraphs[0]
        r = p0.add_run(txt); r.font.size = Pt(9.5)
        if j == len(cells_txt)-1:
            r.bold = True
            if txt == '—': r.font.color.rgb = GREY
            elif txt.startswith('+'): r.font.color.rgb = BAD
            else: r.font.color.rgb = GOOD
for j, w in enumerate([1.0, 0.7, 0.72, 0.72, 0.72, 0.72, 0.72, 0.72, 1.0]):
    for row in t.rows: row.cells[j].width = Inches(w)
doc.add_paragraph()

para('What the week-on-week view adds that the single W41 snapshot could not show:', bold=True)
bullet('The staircase is real and persistent. In every single week, higher score bands run lower FnV IGCC — the 80–89 band is the lowest or tied-lowest in all six weeks (1.16 → 1.00). The W41 snapshot was not a lucky week.', bold_prefix='Staircase holds weekly: ')
bullet('But the IGCC rose mid-era for the two lowest bands before settling. <50 went 1.18% (W36) → 1.41% (W40) → 1.39% (W41) — net worsened +0.21pp over the era. 50–59 similarly ended +0.15pp up. The sub-60 population is not improving — it is where complaints are concentrating.', bold_prefix='Sub-60 bands worsening: ')
bullet('60–69 improved (-0.04pp), 80–89 improved strongly (-0.16pp, ending at the era low of 1.00%), and 90+ (only 18 PODs — noisy) ended -0.00pp. Improvement starts where scores are 60+.', bold_prefix='60+ bands improving: ')
bullet('Because FnV order volume is flat week to week, the divergence is not mix-driven: the same PODs in the same weeks, only their audit scores differ. The band gradient is a score effect, not a volume effect.', bold_prefix='Not a volume artefact: ')

h1('The One-Sentence Version')
para('The audit-score staircase in FnV IGCC holds in every week from 31 Aug to 08 Oct — but only PODs scoring 60+ improved over the era (80–89 scorers down 0.16pp to 1.00%, the network best), while the 400 PODs below 60 actually got worse (+0.15 to +0.21pp). '
     'The next audit wave should go there.', bold=True)

h1('Caveats to Mention if Asked')
bullet('W41 is a partial week (05–08 Oct). All bands are measured on the same 4 days, so comparisons across bands in the same week are valid; treat the absolute W41 levels as provisional.')
bullet('The 90+ band has only 18 PODs — small-sample noise. The gradient from <50 through 80–89 (159 → 58 PODs per band) is the signal.')
bullet('Band membership is fixed by Audit-1 score; PODs re-audited (A2) keep their original band. This is intentional: it tests whether A1 score predicts the FnV IGCC trajectory.')
bullet('Segment-level IGCC can wobble ±0.1pp week to week with city-level events (weather, stockouts); the persistent ordering across bands is the robust part, not any single week’s level.')

doc.add_paragraph()
fp = doc.add_paragraph()
fr = fp.add_run('Source: Pod Audit Tool responses + Instamart FnV-category IGCC data (Snowflake). FnV IGCC% = FnV IGCC orders ÷ FnV total orders. '
                'Full weeks W36 (w/c 31 Aug) through W41 (w/c 05 Oct, partial to 08 Oct). Bands fixed by Audit-1 score (27 Aug – 08 Oct).')
fr.italic = True; fr.font.size = Pt(8.5); fr.font.color.rgb = GREY

out = 'FnV_ScoreBand_Week_on_Week_W36_W41.docx'
doc.save(out)
print('saved', out)
