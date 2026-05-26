#!/usr/bin/env python3
"""
CV HTML Build Script — Chris Moffett
Produces a self-contained HTML file with all fonts embedded as base64.
Served via GitHub Pages at https://chrismoffett.github.io/cv/

Usage: python3 cv_build_html.py [--output path/to/output.html]
"""

import yaml, sys, os, base64

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
YAML_PATH  = os.path.join(SCRIPT_DIR, 'cv_content.yaml')
OUTPUT_PATH = os.path.join(SCRIPT_DIR, 'CV_Moffett.html')
FONTS_DIR  = os.path.join(SCRIPT_DIR, 'fonts_ttf')

if '--output' in sys.argv:
    idx = sys.argv.index('--output')
    OUTPUT_PATH = sys.argv[idx + 1]

with open(YAML_PATH, 'r', encoding='utf-8') as f:
    cv = yaml.safe_load(f)

# ── Embed fonts as base64 ───────────────────────────────────────────────
def b64font(path):
    with open(path, 'rb') as f:
        return base64.b64encode(f.read()).decode()

font_specs = [
    ('CG', '400', 'normal', 'CG-400-normal.ttf'),
    ('CG', '400', 'italic', 'CG-400-italic.ttf'),
    ('CG', '500', 'normal', 'CG-500-normal.ttf'),
    ('CG', '500', 'italic', 'CG-500-italic.ttf'),
    ('EB', '400', 'normal', 'EB-400-normal.ttf'),
    ('EB', '400', 'italic', 'EB-400-italic.ttf'),
    ('EB', '500', 'normal', 'EB-500-normal.ttf'),
    ('EB', '500', 'italic', 'EB-500-italic.ttf'),
    ('EB', '600', 'normal', 'EB-600-normal.ttf'),
    ('EB', '600', 'italic', 'EB-600-italic.ttf'),
]

font_faces = []
for family, weight, style, filename in font_specs:
    path = os.path.join(FONTS_DIR, filename)
    b64 = b64font(path)
    font_faces.append(
        f"@font-face {{ font-family: '{family}'; "
        f"src: url('data:font/truetype;base64,{b64}') format('truetype'); "
        f"font-weight: {weight}; font-style: {style}; }}"
    )

FONT_FACES = '\n'.join(font_faces)

# ── CSS ─────────────────────────────────────────────────────────────────
CSS = FONT_FACES + """
* { margin: 0; padding: 0; box-sizing: border-box; }
html { background: #e8e8e8; }
body {
    background: white;
    color: #1a1a1a;
    font-family: 'EB', 'Noto Serif SC', serif;
    font-size: 10.5pt;
    line-height: 1.42;
    font-feature-settings: "liga" 1;
    max-width: 680px;
    margin: 40px auto;
    padding: 72px 83px;
}
@media (max-width: 750px) {
    body { padding: 32px 24px; margin: 0; }
}
@media print {
    html { background: white; }
    body { margin: 0; padding: 0; max-width: none; }
}
.cjk { font-family: 'Noto Serif SC', serif; font-size: 0.81em; }
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
}
.cv-subsection-head {
    font-size: 10pt; font-style: italic; color: #1a1a1a; margin: 16pt 0 8pt;
}
.cv-advising-head {
    font-family: 'EB', serif; font-size: 10.5pt; font-weight: 600;
    color: #1a1a1a; margin: 16pt 0 6pt;
}
.cv-advising-subhead {
    font-family: 'EB', serif; font-size: 10pt; font-style: italic;
    font-weight: 400; color: #333; margin: 8pt 0 4pt 16pt;
}
.cv-entry { display: flex; gap: 14pt; margin-bottom: 8pt; line-height: 1.42; }
.cv-entry-year { min-width: 50pt; max-width: 50pt; flex-shrink: 0; font-size: 10pt; }
.cv-entry-content { flex: 1; }
.cv-entry-content em { font-style: italic; }
.cv-pub { padding-left: 18pt; text-indent: -18pt; margin-bottom: 7pt; line-height: 1.42; }
.cv-pub em { font-style: italic; }
.cv-pub-year { font-size: 9.5pt; }
.cv-item { padding-left: 18pt; text-indent: -18pt; margin-bottom: 7pt; line-height: 1.42; }
.cv-item em { font-style: italic; }
.cv-item-year { font-size: 9.5pt; }
.cv-list-item { margin-bottom: 6pt; line-height: 1.42; }
.cv-inst { margin-bottom: 14pt; }
.cv-inst-name { font-weight: 600; line-height: 1.42; margin-bottom: 5pt; }
.cv-dept { margin-left: 14pt; margin-top: 7pt; }
.cv-dept-name { font-weight: 500; line-height: 1.42; margin-bottom: 2pt; }
.cv-courses { margin-left: 14pt; }
.cv-course { line-height: 1.42; margin-bottom: 1pt; }
.cv-advisee { margin-left: 28pt; margin-bottom: 7pt; line-height: 1.42; }
.cv-advisee-name { font-weight: 400; display: block; }
.cv-advisee-title { font-style: italic; display: block; margin-left: 14pt; }
.cv-ref { margin-bottom: 12pt; line-height: 1.42; }
.cv-ref p { margin: 0; }
.cv-ref-name { font-weight: 600; }
.cv-distinction { font-style: italic; display: block; line-height: 1.42; }
.cv-pdf-button {
    display: block;
    margin: 0 0 28pt;
    text-align: right;
}
.cv-pdf-button a {
    display: inline-block;
    font-family: 'EB', serif;
    font-size: 8pt;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #888;
    border: 0.5pt solid #888;
    padding: 4pt 10pt;
    text-decoration: none;
}
.cv-pdf-button a:hover { color: #1a1a1a; border-color: #1a1a1a; }
@media print { .cv-pdf-button { display: none; } }
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

# ── Build HTML body ─────────────────────────────────────────────────────
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
        <p><a href="mailto:{p['email']}">{p['email']}</a></p>
        <p>{p['phone']}</p>
    </div>
</div>
<div class="cv-pdf-button"><a href="CV_Moffett.pdf" download>Download PDF</a></div>

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
<p class="cv-list-item">Available on request.</p>
"""

full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Chris Moffett — CV</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC&display=swap" rel="stylesheet">
<style>{CSS}</style>
</head>
<body>{body}</body>
</html>"""

with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
    f.write(full_html)
print(f"Built: {OUTPUT_PATH}")

# Also write as index.html so GitHub Pages serves it at the root URL
index_path = os.path.join(SCRIPT_DIR, 'index.html')
with open(index_path, 'w', encoding='utf-8') as f:
    f.write(full_html)
print(f"Built: {index_path}")
