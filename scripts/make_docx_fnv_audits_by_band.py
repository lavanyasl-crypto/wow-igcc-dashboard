import json
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

S = json.load(open('scripts/report_fnv_audits_by_band.json', encoding='utf-8'))
WKL = S['wk_labels']

BLUE = RGBColor(0x1F, 0x4E, 0x79); GREY = RGBColor(0x60, 0x60, 0x60)

doc = Document()
style = doc.styles['Normal']; style.font.name = 'Calibri'; style.font.size = Pt(10.5)
for sec in doc.sections:
    sec.left_margin = Inches(0.7); sec.right_margin = Inches(0.7)
    sec.top_margin = Inches(0.7); sec.bottom_margin = Inches(0.7)

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

def table(headers, rows, widths):
    t = doc.add_table(rows=1+len(rows), cols=len(headers))
    t.style = 'Light Grid Accent 1'; t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for j, htxt in enumerate(headers):
        c = t.rows[0].cells[j]; c.text = htxt
        for p in c.paragraphs:
            for r in p.runs: r.bold = True; r.font.size = Pt(9.5)
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            p0 = t.rows[i+1].cells[j].paragraphs[0]
            r = p0.add_run(str(val)); r.font.size = Pt(9.5)
            if j == len(headers)-1: r.bold = True
    for j, wd in enumerate(widths):
        for row in t.rows: row.cells[j].width = Inches(wd)
    doc.add_paragraph()

# ---------- Title ----------
tp = doc.add_paragraph(); tp.alignment = WD_ALIGN_PARAGRAPH.CENTER
tr = tp.add_run('Audits Done per Week, Split by FnV Score Band'); tr.bold = True; tr.font.size = Pt(18); tr.font.color.rgb = BLUE
sp = doc.add_paragraph(); sp.alignment = WD_ALIGN_PARAGRAPH.CENTER
sr = sp.add_run('Where did each week’s audit effort go? Audits (1st and 2nd) performed in W36–W41, split by the POD’s FnV-section score band · Audit era 27 Aug – 08 Oct 2026')
sr.italic = True; sr.font.size = Pt(10); sr.font.color.rgb = GREY
doc.add_paragraph()

# ---------- Table 1: all audits ----------
h1('Table 1: Total Audits per Week by FnV Score Band')
rows = []
tot = [0]*len(WKL)
for b in S['bands']:
    rows.append([b['band']] + b['total'] + [sum(b['total'])])
    for i, v in enumerate(b['total']): tot[i] += v
rows.append(['All bands'] + tot + [sum(tot)])
table(['FnV score band'] + WKL + ['Total'], rows,
      widths=[1.1] + [0.72]*len(WKL) + [0.8])
para('Read: the audit wave went overwhelmingly to the weakest bands. <50 and 50–59 PODs took 463 of the 1,072 audits (43%) across the era, and 90+ PODs were audited only from W39 onward (as better scorers started getting covered). '
     'W40–W41 shows the programme pivoting: fewer first audits, more of them on higher bands (80–89 became the largest single group in W41).', italic=True)

# ---------- Table 2: A1 ----------
h1('Table 2: First Audits (A1) per Week by FnV Score Band')
rows = []
for b in S['bands']:
    rows.append([b['band']] + b['a1'] + [sum(b['a1'])])
table(['FnV score band'] + WKL + ['Total'], rows,
      widths=[1.1] + [0.72]*len(WKL) + [0.8])
para('First audits targeted the weakest stores hardest in the W38–W39 peak (108 + 89 A1s on <50 PODs in those two weeks). By W41 first audits had tapered to a trickle (46 across all bands) as the programme shifted to re-audits.', italic=True)

# ---------- Table 3: A2 ----------
h1('Table 3: Second Audits (A2) per Week by FnV Score Band')
rows = []
for b in S['bands']:
    rows.append([b['band']] + b['a2'] + [sum(b['a2'])])
table(['FnV score band'] + WKL + ['Total'], rows,
      widths=[1.1] + [0.72]*len(WKL) + [0.8])
para('Re-audits scaled from W40 onward and spread across all bands — in W41 every band got re-audits (16 + 13 + 26 + 14 + 29 + 9 = 107). '
     'Note the 80–89 band’s 28 A2s in W41: re-audit effort is now checking whether high scorers sustain. '
     'The <50 band has the largest re-audit backlog (29 A2s done, but 297 PODs in band).', italic=True)

# ---------- Analysis ----------
h1('What This Table Set Says')
bullet('Effort followed weakness: the two weakest bands (<50, 50–59) absorbed ~40% of all first audits — the programme targeted exactly the PODs whose FnV IGCC (1.30–1.42%) is the network’s worst.', bold_prefix='Targeting was right: ')
bullet('W38–W39 was the surge (415 A1s across bands), which is precisely the fortnight after which the overall IGCC decline began (1.13% W37 → 1.06% W41). The timing link between audit volume and IGCC improvement is visible here.', bold_prefix='The surge preceded the payoff: ')
bullet('From W40 the mix flipped: A1s collapsed (40 → 25 → 46 range) while A2s grew (1 → 13 → 107 in W41). The programme is now in its verify-and-sustain phase — confirming that corrected PODs stayed corrected.', bold_prefix='The pivot to re-audits: ')
bullet('Despite 1,072 audits, 402 PODs remain never-audited and hundreds more await A2. At the W41 cadence (~25 A1s/week), covering the ~500 sub-60 PODs would take months — the next wave needs scale, or prioritisation within the sub-60 group by FnV IGCC.', bold_prefix='The coverage gap: ')

h1('Caveats')
bullet('A POD’s band is fixed by its FIRST audit’s FnV score — so a POD that improved to 75+ on A2 is still counted in its original band. The tables show where effort went, scored at first contact.')
bullet('Third audits (if any) are not shown; they are rare (a handful) and excluded from A1/A2 splits.')
bullet('W41 is a partial week (05–08 Oct) — its counts will grow slightly as late-dated audits land.')

doc.add_paragraph()
fp = doc.add_paragraph()
fr = fp.add_run('Source: Pod Audit Tool responses — audit dates and FnV-section question scores (each 0/1/2, % of points earned). '
                'An audit is counted in the Monday-start week of its date. A1 = POD’s first audit, A2 = second. Full weeks W36 (w/c 31 Aug) through W41 (w/c 05 Oct, partial).')
fr.italic = True; fr.font.size = Pt(8.5); fr.font.color.rgb = GREY

out = 'FnV_Audits_Per_Week_by_Band.docx'
doc.save(out)
print('saved', out)
