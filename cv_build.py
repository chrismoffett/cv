#!/usr/bin/env python3
"""
CV Build Script — Chris Moffett
Usage: python3 cv_build.py [--full] [--output path/to/output.pdf]

Reads cv_content.yaml and renders to PDF using WeasyPrint.
Fonts are loaded from fonts_ttf/ directory (EB Garamond, Cormorant Garamond).
Noto Serif CJK SC is loaded from system for Chinese characters.

Flags:
  --full     Render references in full. Default output: CV_Moffett.pdf
  (default)  Replace references with "Available on request."
             Default output: CV_Moffett_public.pdf
  --output   Override the output path.

To update the CV:
  1. Edit cv_content.yaml
  2. Run: python3 cv_build.py            # builds public PDF (no refs)
     or:  python3 cv_build.py --full     # builds full PDF (with refs)
"""

import yaml
import sys
import os
from weasyprint import HTML

# ── Paths ──────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
YAML_PATH  = os.path.join(SCRIPT_DIR, 'cv_content.yaml')
FULL = '--full' in sys.argv
OUTPUT_PATH = os.path.join(
    SCRIPT_DIR,
    'CV_Moffett.pdf' if FULL else 'CV_Moffett_public.pdf',
)
FONTS_DIR  = f'file://{SCRIPT_DIR}/fonts_ttf'
# CJK font — try common locations across Linux and macOS
def _find_cjk_font():
    candidates = [
        '/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc',      # Linux apt
        '/usr/share/fonts/noto-cjk/NotoSerifCJK-Regular.ttc',           # Linux alt
        '/opt/homebrew/share/fonts/noto/NotoSerifCJK-Regular.ttc',      # macOS Homebrew
        '/Library/Fonts/NotoSerifCJK-Regular.ttc',                       # macOS system
        os.path.expanduser('~/Library/Fonts/NotoSerifCJK-Regular.ttc'), # macOS user
    ]
    for path in candidates:
        if os.path.exists(path):
            return f'file://{path}'
    return None  # Chinese characters will fall back to system font

CJK_FONT = _find_cjk_font()

if '--output' in sys.argv:
    idx = sys.argv.index('--output')
    OUTPUT_PATH = sys.argv[idx + 1]

# ── Load content ────────────────────────────────────────────────────────
with open(YAML_PATH, 'r', encoding='utf-8') as f:
    cv = yaml.safe_load(f)

# ── References block: full vs. public ───────────────────────────────────
if FULL:
    references_html = ''.join(
        f'<div class="cv-ref">'
        f'<p class="cv-ref-name">{r["name"]}</p>'
        f'<p>{r["title"]}</p>'
        f'<p>{r["contact"]}</p>'
        f'</div>'
        for r in cv['references']
    )
else:
    references_html = '<p class="cv-list-item">Available on request.</p>'

# ── CSS ─────────────────────────────────────────────────────────────────
F = FONTS_DIR
FONT_FACES = f"""
@font-face {{ font-family: 'CG'; src: url('{F}/CG-400-normal.ttf') format('truetype'); font-weight: 400; font-style: normal; }}
@font-face {{ font-family: 'CG'; src: url('{F}/CG-400-italic.ttf') format('truetype'); font-weight: 400; font-style: italic; }}
@font-face {{ font-family: 'CG'; src: url('{F}/CG-500-normal.ttf') format('truetype'); font-weight: 500; font-style: normal; }}
@font-face {{ font-family: 'CG'; src: url('{F}/CG-500-italic.ttf') format('truetype'); font-weight: 500; font-style: italic; }}
@font-face {{ font-family: 'EB'; src: url('{F}/EB-400-normal.ttf') format('truetype'); font-weight: 400; font-style: normal; }}
@font-face {{ font-family: 'EB'; src: url('{F}/EB-400-italic.ttf') format('truetype'); font-weight: 400; font-style: italic; }}
@font-face {{ font-family: 'EB'; src: url('{F}/EB-500-normal.ttf') format('truetype'); font-weight: 500; font-style: normal; }}
@font-face {{ font-family: 'EB'; src: url('{F}/EB-500-italic.ttf') format('truetype'); font-weight: 500; font-style: italic; }}
@font-face {{ font-family: 'EB'; src: url('{F}/EB-600-normal.ttf') format('truetype'); font-weight: 600; font-style: normal; }}
@font-face {{ font-family: 'EB'; src: url('{F}/EB-600-italic.ttf') format('truetype'); font-weight: 600; font-style: italic; }}
{"@font-face { font-family: 'NotoSC'; src: url('" + CJK_FONT + "') format('truetype'); font-weight: 400; font-style: normal; }" if CJK_FONT else ""}
"""

CSS = FONT_FACES + """
@page {
    size: letter;
    margin: 0.95in 1.15in;
    @bottom-center {
        content: "Moffett  |  " counter(page) " of " counter(pages);
        font-family: 'EB', serif;
        font-size: 8pt;
        color: #888;
        letter-spacing: 0.18em;
        text-transform: uppercase;
    }
}
@page :first { @bottom-center { content: none; } }
* { margin: 0; padding: 0; }
body {
    background: white; color: #1a1a1a;
    font-family: 'EB', serif; font-size: 10.5pt;
    line-height: 1.42; font-feature-settings: "liga" 1;
}
.cjk { font-family: 'NotoSC', serif; font-size: 0.81em; line-height: 1.42; }
.cv-name {
    font-family: 'CG', serif; font-size: 28pt; font-weight: 400;
    text-align: center; line-height: 1.05; margin: 0 0 5pt;
    font-feature-settings: "liga" 1, "dlig" 1;
}
.cv-subtitle {
    font-family: 'CG', serif; font-size: 8pt; text-align: center;
    letter-spacing: 0.18em; text-transform: uppercase; color: #888; margin: 0 0 18pt;
}
.cv-contact {
    display: flex; justify-content: space-between;
    font-size: 9.5pt; line-height: 1.55; margin-bottom: 26pt;
}
.cv-contact p { margin: 0; }
.cv-contact-right { text-align: right; }
.cv-section-head {
    font-family: 'EB', serif; font-size: 8pt; font-weight: 400;
    text-transform: uppercase; letter-spacing: 0.18em; color: #888;
    margin: 28pt 0 12pt; padding-bottom: 3pt; border-bottom: 0.5pt solid #888;
    page-break-after: avoid;
}
.cv-subsection-head {
    font-size: 10pt; font-style: italic; color: #1a1a1a;
    margin: 16pt 0 8pt; page-break-after: avoid;
}
.cv-advising-head {
    font-family: 'EB', serif; font-size: 10.5pt; font-weight: 600;
    color: #1a1a1a; margin: 16pt 0 6pt; page-break-after: avoid;
}
.cv-advising-subhead {
    font-family: 'EB', serif; font-size: 10pt; font-style: italic;
    font-weight: 400; color: #333; margin: 8pt 0 4pt; margin-left: 16pt;
    page-break-after: avoid;
}
.cv-entry {
    display: flex; gap: 14pt; margin-bottom: 8pt; line-height: 1.42;
    page-break-inside: avoid;
}
.cv-entry-year { min-width: 50pt; max-width: 50pt; flex-shrink: 0; font-size: 10pt; color: #1a1a1a; }
.cv-entry-content { flex: 1; }
.cv-entry-content em { font-style: italic; }
.cv-pub {
    padding-left: 18pt; text-indent: -18pt;
    margin-bottom: 7pt; line-height: 1.42; page-break-inside: avoid;
}
.cv-pub em { font-style: italic; }
.cv-pub-year { font-size: 9.5pt; }
.cv-item {
    padding-left: 18pt; text-indent: -18pt;
    margin-bottom: 7pt; line-height: 1.42; page-break-inside: avoid;
}
.cv-item em { font-style: italic; }
.cv-item-year { font-size: 9.5pt; }
.cv-list-item { margin-bottom: 6pt; line-height: 1.42; }
.cv-inst { margin-bottom: 14pt; }
.cv-inst-name { font-weight: 600; line-height: 1.42; margin-bottom: 5pt; page-break-after: avoid; }
.cv-dept { margin-left: 14pt; margin-top: 7pt; margin-bottom: 0; page-break-inside: avoid; }
.cv-dept-name { font-weight: 500; line-height: 1.42; margin-bottom: 2pt; page-break-after: avoid; }
.cv-courses { margin-left: 14pt; }
.cv-course { line-height: 1.42; margin-bottom: 1pt; }
.cv-advisee { margin-left: 28pt; margin-bottom: 7pt; line-height: 1.42; page-break-inside: avoid; }
.cv-advisee-name { font-weight: 400; display: block; }
.cv-advisee-title { font-style: italic; display: block; margin-left: 14pt; line-height: 1.42; }
.cv-ref { margin-bottom: 12pt; line-height: 1.42; page-break-inside: avoid; }
.cv-ref p { margin: 0; }
.cv-ref-name { font-weight: 600; }
.cv-distinction { font-style: italic; display: block; line-height: 1.42; }
"""

# ── HTML helpers ────────────────────────────────────────────────────────
def entry(year, content):
    return f'<div class="cv-entry"><span class="cv-entry-year">{year}</span><span class="cv-entry-content">{content}</span></div>\n'

def pub(content, year):
    return f'<p class="cv-pub">{content} <span class="cv-pub-year">{year}.</span></p>\n'

def item(content, year):
    return f'<p class="cv-item">{content} <span class="cv-item-year">{year}.</span></p>\n'

def advisee(name, title=None):
    t = f'<span class="cv-advisee-title">{title}</span>' if title else ''
    return f'<div class="cv-advisee"><span class="cv-advisee-name">{name}</span>{t}</div>\n'

def teaching_section(institutions):
    html = ''
    for inst in institutions:
        html += '<div class="cv-inst">\n'
        html += f'<p class="cv-inst-name">{inst["institution"]}</p>\n'
        for dept in inst.get('departments', []):
            html += '<div class="cv-dept">'
            html += f'<p class="cv-dept-name">{dept["name"]}</p>'
            html += '<div class="cv-courses">'
            for course in dept.get('courses', []):
                html += f'<p class="cv-course">{course}</p>'
            html += '</div></div>\n'
        html += '</div>\n'
    return html

# ── Build HTML ──────────────────────────────────────────────────────────
p = cv['personal']
body = f"""
<p class="cv-name">{p['name']}</p>
<p class="cv-subtitle">{p['title']}</p>
<div class="cv-contact">
    <div>
        <p>{p['institution']}</p>
        <p>{p['department']}</p>
        <p>{p['address']}</p>
        <p>{p['city']}</p>
    </div>
    <div class="cv-contact-right">
        <p>{p['email']}</p>
        <p>{p['phone']}</p>
    </div>
</div>

<p class="cv-section-head">Education</p>
{''.join(entry(e['year'], e['entry']) for e in cv['education'])}

<p class="cv-section-head">Positions</p>
{''.join(entry(e['year'], e['entry']) for e in cv['positions'])}

<p class="cv-section-head">Graduate Teaching Experience</p>
{teaching_section(cv['graduate_teaching'])}

<p class="cv-section-head">Undergraduate Teaching Experience</p>
{teaching_section(cv['undergraduate_teaching'])}

<p class="cv-section-head">Publications</p>
<p class="cv-subsection-head">Journal Articles and Book Chapters</p>
{''.join(pub(e['content'], e['year']) for e in cv['publications']['journal_articles'])}
<p class="cv-subsection-head">Conference Proceedings</p>
{''.join(pub(e['content'], e['year']) for e in cv['publications']['conference_proceedings'])}
<p class="cv-subsection-head">Book Reviews</p>
{''.join(pub(e['content'], e['year']) for e in cv['publications']['book_reviews'])}

<p class="cv-section-head">Fellowships, Grants &amp; Awards</p>
{''.join(entry(e['year'], e['entry']) for e in cv['fellowships'])}

<p class="cv-section-head">Invited Talks</p>
{''.join(item(e['content'], e['year']) for e in cv['invited_talks'])}

<p class="cv-section-head">Conference Presentations</p>
{''.join(item(e['content'], e['year']) for e in cv['conference_presentations'])}

<p class="cv-section-head">Art Shows, Workshops &amp; Performances</p>
{''.join(item(e['content'], e['year']) for e in cv['art_shows'])}

<p class="cv-section-head">Relevant Professional Experience</p>
{''.join(entry(e['year'], e['entry']) for e in cv['professional_experience'])}

<p class="cv-section-head">Service</p>
{''.join(entry(e['year'], e['entry']) for e in cv['service'])}

<p class="cv-section-head">Student Advising</p>
<p class="cv-advising-head">Doctoral Committees</p>
<p class="cv-advising-subhead">Art Education</p>
{''.join(advisee(s['name'], s.get('title')) for s in cv['student_advising']['doctoral']['art_education'])}
<p class="cv-advising-subhead">Technology, Media &amp; Learning</p>
{''.join(advisee(s['name'], s.get('title')) for s in cv['student_advising']['doctoral']['technology_media_learning'])}
<p class="cv-advising-head">Thesis Committees</p>
{''.join(advisee(s['name'], s.get('title')) for s in cv['student_advising']['thesis'])}

<p class="cv-section-head">Languages</p>
{''.join(f'<p class="cv-list-item">{lang}</p>' for lang in cv['languages'])}

<p class="cv-section-head">Memberships</p>
{''.join(f'<p class="cv-list-item">{m}</p>' for m in cv['memberships'])}

<p class="cv-section-head">References</p>
{references_html}
"""

full_html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>{CSS}</style></head>
<body>{body}</body></html>"""

HTML(string=full_html).write_pdf(OUTPUT_PATH)
print(f"Built: {OUTPUT_PATH}")
