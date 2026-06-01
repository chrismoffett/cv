"""
cv_filter.py — LLM precision layer for the CV suggestion scanner.

Architecture:
    keyword scan (cv_suggest.py)  ->  RAW CANDIDATES  ->  this module  ->  review file

The keyword scan is the recall layer: cast wide, accept noise.
This module is the precision layer: decide which candidates are real,
coherent scholarly accomplishments, report their TRUE stage (using the
source's own status, never an invented one), dedupe against cv_content.yaml,
and rank what survives. Nothing is written into the CV automatically.

Stage honesty: a Notion project status like "Working"/"Active" means the
work is in preparation, NOT under review. In-preparation items are flagged
for review, not asserted as finished CV lines. Likewise, an emailed request
or invitation to review, speak, or contribute is "invited", not completed
service: being asked to do something is not the same as having done it.
"""

import json
import os
import re
from datetime import date

import yaml
from anthropic import Anthropic

# Default model is a fixed, current snapshot. Model ids get retired over time;
# if a run fails with a 404 "model: ... not_found", the default has rotted —
# set CV_FILTER_MODEL in .env to a current id (see docs.claude.com models) or
# bump this default.
MODEL = os.environ.get("CV_FILTER_MODEL", "claude-sonnet-4-6")

KEEP_THRESHOLD = 0.60
REVIEW_THRESHOLD = 0.40
BATCH_SIZE = 12

# Sort order for the Suggested block: real CV lines first, prep last.
STATUS_ORDER = {"completed": 0, "forthcoming": 1, "in_review": 2, "in_preparation": 3, "invited": 4}

# Peer-review invitation phrasing. An item whose source text matches this is a
# solicitation to review, not a completed service line: being asked to review
# is not the same as having reviewed. partition() uses it as a deterministic
# rescue — run BEFORE the keep/drop filter — so a review invitation is always
# held in Quarantine for confirmation, whatever the model decided. Scoped
# tightly to review solicitations so it cannot rescue calendar/GitHub invites
# or downgrade a review that is genuinely complete.
REVIEW_INVITE_PATTERNS = re.compile(
    r"(are you (?:willing|available) to review"
    r"|would you be (?:willing|available|interested) (?:to|in) review"
    r"|invitation to review"
    r"|invited to review"
    r"|request to review"
    r"|reviewer invitation"
    r"|asked to review)",
    re.IGNORECASE,
)


def _looks_review_invite(src):
    blob = f"{src.get('title', '')} {src.get('text', '')}"
    return bool(REVIEW_INVITE_PATTERNS.search(blob))

SYSTEM_PROMPT = """\
You evaluate candidate items scraped from Chris Moffett's Gmail, Google \
Drive, Notion, and Obsidian. A keyword scan produced these, so the input is \
noisy: order receipts, calendar invites, mailing-list/newsletter blasts, \
account/forwarding confirmations, loan/marketing offers, automated GitHub \
build-failure notices, spam moderation requests. None of those belong on a \
CV. Reject them.

Your job: decide, per candidate, whether it is a REAL, COHERENT scholarly \
accomplishment attributable to Chris that belongs on an academic CV, and \
report its true stage accurately.

ACCURACY ABOUT STAGE IS CRITICAL. Some candidates include a `source_status` \
from their origin system — e.g. a Notion project status like "Working", \
"Active", "Waiting", "Done". Treat source_status as ground truth about the \
work's stage. NEVER assert a publication stage the source does not support. \
A project still being written or worked on is in preparation; it is NOT \
"under review" and NOT "forthcoming." A journal name in the title does not \
imply submission.

This rule applies to EVERY type, not only publications. NEVER infer that \
Chris accepted, agreed to, performed, scheduled, or completed anything the \
source does not explicitly state. An email that invites, asks, or solicits \
him to review a manuscript, speak, contribute, join, or apply is an \
INVITATION: being asked to do something is not the same as having done it. \
Such items are status "invited", never "completed", "forthcoming", or \
"in_review", no matter how confident the invitation sounds.

For each candidate, judge:

1. TYPE — publication, talk, grant, award, appointment, service, teaching, \
media, art_show, other. Use "other" sparingly.

2. STATUS — the true stage, mapped honestly:
   - completed      : published, delivered, awarded, appointed, concluded — source confirms it happened.
   - forthcoming    : accepted / in press / scheduled — ONLY if the source explicitly says so.
   - in_review      : submitted and under peer review — ONLY if the source explicitly says submitted / under review.
   - in_preparation : being drafted or worked on; a Notion status of Working / Active / In Progress maps here.
   - invited        : solicited or offered but NOT yet accepted or completed — e.g. an emailed request or invitation to review, speak, contribute, or apply.
   - speculative    : an idea or thing merely mentioned.
   If source_status is absent or ambiguous, do NOT assume submission — default
   a scholarly work to in_preparation unless there is explicit evidence it was
   submitted, accepted, or published. If a candidate is only a request or
   invitation, with no confirmation that Chris accepted and that the activity
   occurred or is scheduled, its status is "invited".

3. KEEP — true only for a genuine accomplishment of Chris's, not an \
announcement about someone else, automated mail, marketing, or spam. \
completed / forthcoming / in_review items are CV-worthy. in_preparation and \
invited items are kept too, but they are quarantined for your confirmation \
rather than asserted as finished lines. Drop speculative items and \
non-accomplishments. When unsure whether something is real, lean false; \
recall is handled upstream.

4. FORMATTING — peer review and editorial service: list as "Reviewer, \
<journal name>, <year>". NEVER include a manuscript number or submission \
control ID (e.g. "SPED-D-26-00171") — these are confidential and do not \
belong on a CV. If the journal name cannot be recovered from the source, \
write "Reviewer (journal unspecified), <year>" rather than falling back to \
any manuscript identifier.

Dedupe: if a candidate is already in EXISTING CV ENTRIES, set "duplicate_of" \
to the matching entry's text (fuzzy match is fine).

Return ONLY a JSON array, no prose, no markdown fences. One object per \
candidate, in the order received:

[
  {
    "id": "<passthrough id>",
    "keep": true,
    "type": "publication",
    "status": "in_preparation",
    "confidence": 0.0-1.0,
    "duplicate_of": null,
    "proposed_entry": "the citation line ONLY, with no trailing status word",
    "year": "publication year if completed; otherwise the exact stage word: \\"In review\\", \\"Forthcoming\\", \\"In preparation\\", or \\"Invited\\"",
    "rationale": "one sentence"
  }
]

confidence = how sure you are this is a real, non-duplicate CV item of the
stated type and stage. A confirmed completed publication is ~0.9; a clearly
submitted paper ~0.8; an order receipt or build-failure notice ~0.0.
"""


def _strip_html(s):
    return re.sub(r"<[^>]+>", " ", s)


def _clean(s):
    return re.sub(r"\s+", " ", _strip_html(str(s))).strip()


def _flatten_text(obj):
    out = []
    if isinstance(obj, str):
        out.append(obj)
    elif isinstance(obj, dict):
        for v in obj.values():
            out.extend(_flatten_text(v))
    elif isinstance(obj, list):
        for v in obj:
            out.extend(_flatten_text(v))
    return out


def load_existing_entries(cv_yaml_path, max_len=160):
    """Flatten cv_content.yaml into a compact dedupe list. Walks the whole
    tree so it catches flat {year, entry} sections, nested ones like
    publications.journal_articles, and the teaching trees. Skips 'personal'."""
    with open(cv_yaml_path) as f:
        cv = yaml.safe_load(f) or {}

    existing = []

    def walk(node, section):
        if isinstance(node, list):
            for item in node:
                text = _clean(" ".join(_flatten_text(item)))
                if not text:
                    continue
                year = item.get("year") if isinstance(item, dict) else None
                existing.append({"type": section, "year": year, "title": text[:max_len]})
        elif isinstance(node, dict):
            for k, v in node.items():
                walk(v, section or k)

    for section, value in cv.items():
        if section == "personal":
            continue
        walk(value, section)
    return existing


def normalize_candidate(raw, idx):
    """Map a scanner record onto the fields the classifier reads. Crucially,
    carry through the source's own status (Notion projects have one) so the
    model reports the true stage instead of guessing from the title."""
    def g(*keys):
        if not isinstance(raw, dict):
            return None
        return next((raw[k] for k in keys if raw.get(k)), None)

    title = g("title", "subject", "content", "name", "filename") or ""
    body = g("text", "snippet", "body", "summary", "preview", "description") or ""
    sender = g("from", "sender", "author") or ""
    return {
        "id": g("id", "message_id", "uid") or f"cand-{idx}",
        "source": g("source", "origin") or "unknown",
        "source_status": g("status", "state") or "",
        "title": title,
        "text": (f"From: {sender}\n{body}").strip() if sender else body,
        "url": g("url", "link", "permalink", "webViewLink"),
        "date": g("date", "received", "timestamp", "modifiedTime", "last_edited", "modified"),
    }


def _batch(seq, n):
    for i in range(0, len(seq), n):
        yield seq[i : i + n]


def classify_candidates(candidates, existing_entries, client=None):
    client = client or Anthropic()
    verdicts = []
    existing_blob = json.dumps(existing_entries, ensure_ascii=False)

    for batch in _batch(candidates, BATCH_SIZE):
        user_content = (
            f"TODAY: {date.today().isoformat()}\n\n"
            f"EXISTING CV ENTRIES (for dedupe):\n{existing_blob}\n\n"
            f"CANDIDATES TO EVALUATE:\n"
            f"{json.dumps(batch, ensure_ascii=False, default=str)}"
        )
        resp = client.messages.create(
            model=MODEL,
            max_tokens=2000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_content}],
        )
        text = "".join(b.text for b in resp.content if b.type == "text").strip()
        if text.startswith("```"):
            text = text.split("```", 2)[1].lstrip("json").strip()
        try:
            verdicts.extend(json.loads(text))
        except json.JSONDecodeError:
            for c in batch:
                verdicts.append({
                    "id": c.get("id"), "keep": False, "type": "other",
                    "status": "speculative", "confidence": 0.0, "duplicate_of": None,
                    "proposed_entry": "", "year": "",
                    "rationale": "parse error — review source candidate manually",
                })
    return verdicts


def partition(verdicts, candidates):
    """Suggested = real CV lines (completed/forthcoming/in_review) above the
    keep threshold. Quarantine = in-preparation and invited work plus
    borderline scores. Dropped = junk and duplicates. In-preparation and
    invited items never land in Suggested."""
    by_id = {c.get("id"): c for c in candidates}
    suggestions, quarantine = [], []

    for v in verdicts:
        src = by_id.get(v.get("id"), {})
        # Rescue (runs before the keep/drop filter): a peer-review invitation
        # is force-held in Quarantine for confirmation, regardless of whether
        # the model kept it as "completed" or dropped it as a non-accomplishment.
        # Skipped only if it duplicates something already on the CV.
        if _looks_review_invite(src) and not v.get("duplicate_of"):
            v["keep"] = True
            v["type"] = "service"
            v["status"] = "invited"
            v["year"] = "Invited"
            if not v.get("proposed_entry"):
                v["proposed_entry"] = "Reviewer (journal/year to confirm)"
            if not v.get("rationale"):
                v["rationale"] = ("Peer-review invitation; held for confirmation. "
                                  "Add as completed service only once the review is done.")

        if v.get("duplicate_of") or not v.get("keep"):
            continue
        conf = float(v.get("confidence", 0))
        status = v.get("status", "")
        v["_source"] = src.get("source")
        v["_url"] = src.get("url")
        if status in ("in_preparation", "invited"):
            quarantine.append(v)
        elif conf >= KEEP_THRESHOLD:
            suggestions.append(v)
        elif conf >= REVIEW_THRESHOLD:
            quarantine.append(v)

    keyfn = lambda v: (STATUS_ORDER.get(v.get("status"), 4), -float(v.get("confidence", 0)))
    suggestions.sort(key=keyfn)
    quarantine.sort(key=keyfn)
    return suggestions, quarantine


def write_review_file(suggestions, quarantine, out_path="cv_suggestions_review.md"):
    lines = []

    def block(title, rows):
        lines.append(f"### {title}")
        if not rows:
            lines.append("_none_\n")
            return
        for v in rows:
            status = v.get("status", "")
            conf = float(v.get("confidence", 0))
            year = v.get("year") or str(date.today().year)
            lines.append(f"`# → {v.get('type')}`")
            lines.append("```yaml")
            lines.append(f'- year: "{year}"')
            lines.append(f'  content: "{v.get("proposed_entry")}"')
            lines.append("```")
            meta = " · ".join(filter(None, [v.get("_source"), status, f"{conf:.2f}", v.get("_url")]))
            lines.append(f"<sub>{meta} — {v.get('rationale')}</sub>\n")
        lines.append("")

    block("Suggested (real CV lines, completed first)", suggestions)
    block("Quarantine (in preparation / borderline — confirm or discard)", quarantine)

    text = "\n".join(lines)
    with open(out_path, "w") as f:
        f.write(text)
    return out_path


def run(raw_candidates, cv_yaml_path, out_path="cv_suggestions_review.md"):
    candidates = [normalize_candidate(c, i) for i, c in enumerate(raw_candidates)]
    existing = load_existing_entries(cv_yaml_path)
    verdicts = classify_candidates(candidates, existing)
    suggestions, quarantine = partition(verdicts, candidates)
    path = write_review_file(suggestions, quarantine, out_path)

    by_id = {c.get("id"): c for c in candidates}
    dropped = [by_id.get(v.get("id"), {}).get("title", "(unknown)")
               for v in verdicts if v.get("duplicate_of") or not v.get("keep")]
    print(f"    {len(suggestions)} suggested, {len(quarantine)} quarantined, "
          f"{len(dropped)} dropped (from {len(candidates)} raw)")
    for t in dropped[:40]:
        print(f"      dropped: {t[:80]}")
    return path
