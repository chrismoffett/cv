#!/usr/bin/env python3
"""
cv_suggest.py — Scan Gmail, Drive, Notion, and Obsidian for CV-worthy
activity since the last commit on `main` of chrismoffett/cv, and prepend
a dated block of paste-ready YAML suggestions to CV_Suggestions.md in
the Drive CV folder.

Usage:  python3 cv_suggest.py

Dependencies (install once):
    pip install python-dotenv google-auth google-api-python-client requests

Required env vars (in .env in the same directory as this script):
    GDRIVE_CLIENT_ID
    GDRIVE_CLIENT_SECRET
    GDRIVE_REFRESH_TOKEN     (must include `drive` AND `gmail.readonly` scopes)
    NOTION_API_KEY
    GITHUB_TOKEN             (listed per spec; this script uses `gh` CLI auth)

Optional:
    NOTION_PROJECTS_DB_ID    (override search for a database titled "Projects")
"""

import io
import os
import subprocess
import sys
from datetime import date, datetime, timezone
from pathlib import Path

try:
    from dotenv import load_dotenv
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
    import requests
except ImportError as e:
    sys.exit(
        f"Missing dependency: {e.name}.\n"
        "Install with: pip install python-dotenv google-auth "
        "google-api-python-client requests"
    )

# ── Config ──────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent.resolve()
load_dotenv(SCRIPT_DIR / ".env")

ACADEMIC_FOLDER_ID = "1dDLCTYK4n_KqxPKi80cNOa-OvKHSBkV3"
CV_FOLDER_ID = "1H2lg3z_HiPcSeS-gIlYV5GS24AedQ476"
OBSIDIAN_PATH = (
    "/Users/cm2189/My Drive (chris@chrismoffett.com)"
    "/Second Brain/04 Vault/Knowledge_Vault/writing/academic"
)
GH_REPO = "chrismoffett/cv"
GH_BRANCH = "main"
SUGGESTIONS_FILENAME = "CV_Suggestions.md"

GMAIL_SCOPE = "https://www.googleapis.com/auth/gmail.readonly"
DRIVE_SCOPE = "https://www.googleapis.com/auth/drive"

# ── Helpers ─────────────────────────────────────────────────────────────
def require_env(*names):
    missing = [n for n in names if not os.environ.get(n)]
    if missing:
        sys.exit(f"Missing required env var(s) in .env: {', '.join(missing)}")


def get_cutoff_date():
    """Date of the last commit on main, via `gh api`."""
    result = subprocess.run(
        ["gh", "api", f"repos/{GH_REPO}/commits/{GH_BRANCH}",
         "--jq", ".commit.committer.date"],
        capture_output=True, text=True, check=True,
    )
    iso = result.stdout.strip()
    return datetime.fromisoformat(iso.replace("Z", "+00:00"))


def make_google_creds():
    require_env("GDRIVE_CLIENT_ID", "GDRIVE_CLIENT_SECRET", "GDRIVE_REFRESH_TOKEN")
    return Credentials(
        token=None,
        refresh_token=os.environ["GDRIVE_REFRESH_TOKEN"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["GDRIVE_CLIENT_ID"],
        client_secret=os.environ["GDRIVE_CLIENT_SECRET"],
        scopes=[DRIVE_SCOPE, GMAIL_SCOPE],
    )


def yaml_escape(s):
    """Escape a string for safe inclusion inside YAML double quotes."""
    if s is None:
        return ""
    return (str(s)
            .replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("\n", " ")
            .strip())


def section_hint(text):
    """Best-guess mapping of an item to a cv_content.yaml section."""
    t = (text or "").lower()
    if any(k in t for k in ("publication", "published", "journal",
                            "doi", "isbn", "paper accepted", "book chapter")):
        return "publications.journal_articles"
    if any(k in t for k in ("book review",)):
        return "publications.book_reviews"
    if any(k in t for k in ("proceedings", "conference paper")):
        return "publications.conference_proceedings"
    if any(k in t for k in ("invited talk", "keynote", "invited to speak", "lecture")):
        return "invited_talks"
    if any(k in t for k in ("conference", "presented at", "panel", "presentation")):
        return "conference_presentations"
    if any(k in t for k in ("grant", "fellowship", "award", "prize", "funding")):
        return "fellowships"
    if any(k in t for k in ("course", "syllabus", "teaching", "lecturer", "instructor")):
        return "graduate_teaching OR undergraduate_teaching"
    if any(k in t for k in ("exhibit", "show", "workshop", "performance", "screening")):
        return "art_shows"
    if any(k in t for k in ("service", "committee", "review for", "editor", "reviewer")):
        return "service"
    if any(k in t for k in ("advisee", "dissertation", "thesis committee")):
        return "student_advising"
    return "(unclear — review and assign)"


# ── Gmail scanner ───────────────────────────────────────────────────────
def scan_gmail(creds, cutoff):
    service = build("gmail", "v1", credentials=creds, cache_discovery=False)
    after = cutoff.strftime("%Y/%m/%d")
    query = f"after:{after} (in:inbox OR label:CV)"
    resp = service.users().messages().list(
        userId="me", q=query, maxResults=100).execute()
    items = []
    for ref in resp.get("messages", []):
        msg = service.users().messages().get(
            userId="me", id=ref["id"], format="metadata",
            metadataHeaders=["From", "Subject", "Date"],
        ).execute()
        headers = {h["name"]: h["value"]
                   for h in msg.get("payload", {}).get("headers", [])}
        items.append({
            "from": headers.get("From", ""),
            "subject": headers.get("Subject", ""),
            "date": headers.get("Date", ""),
            "snippet": msg.get("snippet", ""),
        })
    return items


# ── Drive scanner ───────────────────────────────────────────────────────
def scan_drive_folder(creds, folder_id, cutoff):
    service = build("drive", "v3", credentials=creds, cache_discovery=False)
    cutoff_iso = cutoff.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    query = (f"'{folder_id}' in parents and "
             f"modifiedTime > '{cutoff_iso}' and trashed=false")
    items = []
    page_token = None
    while True:
        resp = service.files().list(
            q=query,
            fields=("nextPageToken,"
                    "files(id,name,modifiedTime,description,mimeType,webViewLink)"),
            pageSize=100,
            pageToken=page_token,
        ).execute()
        items.extend(resp.get("files", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return items


# ── Notion scanner ──────────────────────────────────────────────────────
NOTION_VERSION = "2022-06-28"


def notion_headers():
    require_env("NOTION_API_KEY")
    return {
        "Authorization": f"Bearer {os.environ['NOTION_API_KEY']}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def find_notion_projects_db():
    if db_id := os.environ.get("NOTION_PROJECTS_DB_ID"):
        return db_id
    r = requests.post(
        "https://api.notion.com/v1/search",
        headers=notion_headers(),
        json={
            "query": "Projects",
            "filter": {"value": "database", "property": "object"},
        },
        timeout=30,
    )
    r.raise_for_status()
    for db in r.json().get("results", []):
        title = "".join(t.get("plain_text", "") for t in db.get("title", []))
        if title.strip().lower() == "projects":
            return db["id"]
    raise RuntimeError(
        "No Notion database titled 'Projects' is shared with this integration. "
        "Either share one with the integration, or set NOTION_PROJECTS_DB_ID in .env."
    )


def _page_title(page):
    for prop in page.get("properties", {}).values():
        if prop.get("type") == "title":
            return "".join(t.get("plain_text", "") for t in prop.get("title", []))
    return "(untitled)"


def _page_status(page):
    for name, prop in page.get("properties", {}).items():
        if name.lower() in ("status", "state"):
            ptype = prop.get("type")
            if ptype == "status":
                return (prop.get("status") or {}).get("name", "")
            if ptype == "select":
                return (prop.get("select") or {}).get("name", "")
    return ""


def _page_has_academic(page):
    """Match 'Academic' in any select/multi-select/status property."""
    for prop in page.get("properties", {}).values():
        ptype = prop.get("type")
        if ptype == "multi_select":
            for opt in prop.get("multi_select", []):
                if opt.get("name", "").lower() == "academic":
                    return True
        elif ptype == "select":
            opt = prop.get("select") or {}
            if opt.get("name", "").lower() == "academic":
                return True
        elif ptype == "status":
            opt = prop.get("status") or {}
            if opt.get("name", "").lower() == "academic":
                return True
    return False


def scan_notion(cutoff):
    db_id = find_notion_projects_db()
    cutoff_iso = cutoff.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    items = []
    start_cursor = None
    while True:
        body = {
            "filter": {
                "timestamp": "last_edited_time",
                "last_edited_time": {"on_or_after": cutoff_iso},
            },
            "page_size": 100,
        }
        if start_cursor:
            body["start_cursor"] = start_cursor
        r = requests.post(
            f"https://api.notion.com/v1/databases/{db_id}/query",
            headers=notion_headers(),
            json=body,
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
        for p in data.get("results", []):
            if not _page_has_academic(p):
                continue
            items.append({
                "name": _page_title(p),
                "status": _page_status(p),
                "last_edited": p.get("last_edited_time", ""),
                "url": p.get("url", ""),
            })
        if not data.get("has_more"):
            break
        start_cursor = data.get("next_cursor")
    return items


# ── Obsidian scanner ────────────────────────────────────────────────────
def scan_obsidian(cutoff):
    root = Path(OBSIDIAN_PATH)
    if not root.exists():
        return []
    cutoff_ts = cutoff.timestamp()
    items = []
    for md in root.rglob("*.md"):
        try:
            mtime_ts = md.stat().st_mtime
        except OSError:
            continue
        if mtime_ts <= cutoff_ts:
            continue
        try:
            preview = md.read_text(encoding="utf-8", errors="replace")[:200]
        except OSError:
            preview = ""
        items.append({
            "filename": md.name,
            "path": str(md.relative_to(root)),
            "modified": datetime.fromtimestamp(mtime_ts, tz=timezone.utc).isoformat(),
            "preview": preview.replace("\n", " ").strip(),
        })
    return items


# ── Markdown formatters ─────────────────────────────────────────────────
def _fmt_yaml_stub(content):
    """Returns a YAML stub appropriate for most CV sections."""
    return (
        '- year: "' + str(date.today().year) + '"\n'
        f'  content: "{yaml_escape(content)}"'
    )


def fmt_gmail(items):
    if not items:
        return "_No new messages since cutoff._\n"
    parts = []
    for it in items:
        section = section_hint(f"{it['subject']} {it['snippet']}")
        parts.append(f"`# → {section}`\n")
        parts.append("```yaml\n" + _fmt_yaml_stub(it["subject"]) + "\n```")
        parts.append(
            f"<sub>**From:** {yaml_escape(it['from'])} · "
            f"**Date:** {yaml_escape(it['date'])}<br>"
            f"{yaml_escape(it['snippet'])[:200]}</sub>\n"
        )
    return "\n".join(parts)


def fmt_drive(items):
    if not items:
        return "_No files modified since cutoff._\n"
    parts = []
    for it in items:
        text = f"{it.get('name','')} {it.get('description') or ''}"
        section = section_hint(text)
        parts.append(f"`# → {section}`\n")
        parts.append("```yaml\n" + _fmt_yaml_stub(it.get("name", "")) + "\n```")
        link = it.get("webViewLink") or ""
        parts.append(
            f"<sub>modified {it.get('modifiedTime','')} · "
            f"{it.get('mimeType','')}"
            + (f" · [open]({link})" if link else "")
            + "</sub>\n"
        )
    return "\n".join(parts)


def fmt_notion(items):
    if not items:
        return "_No academic projects updated since cutoff._\n"
    parts = []
    for it in items:
        section = section_hint(it["name"])
        parts.append(f"`# → {section}`\n")
        parts.append("```yaml\n" + _fmt_yaml_stub(it["name"]) + "\n```")
        parts.append(
            f"<sub>status: {yaml_escape(it['status'])} · "
            f"last edited {it['last_edited']}"
            + (f" · [open]({it['url']})" if it.get("url") else "")
            + "</sub>\n"
        )
    return "\n".join(parts)


def fmt_obsidian(items):
    if not items:
        return "_No academic notes modified since cutoff._\n"
    parts = []
    for it in items:
        section = section_hint(it["filename"] + " " + it["preview"])
        title = it["filename"].removesuffix(".md")
        parts.append(f"`# → {section}`\n")
        parts.append("```yaml\n" + _fmt_yaml_stub(title) + "\n```")
        parts.append(
            f"<sub>{it['path']} · modified {it['modified']}<br>"
            f"{yaml_escape(it['preview'])[:200]}</sub>\n"
        )
    return "\n".join(parts)


# ── Drive read/write CV_Suggestions.md ──────────────────────────────────
def fetch_existing_suggestions(creds):
    service = build("drive", "v3", credentials=creds, cache_discovery=False)
    resp = service.files().list(
        q=(f"name='{SUGGESTIONS_FILENAME}' and "
           f"'{CV_FOLDER_ID}' in parents and trashed=false"),
        fields="files(id)",
    ).execute()
    files = resp.get("files", [])
    if not files:
        return None, ""
    file_id = files[0]["id"]
    request = service.files().get_media(fileId=file_id)
    buf = io.BytesIO()
    downloader = MediaIoBaseDownload(buf, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    return file_id, buf.getvalue().decode("utf-8", errors="replace")


def upload_suggestions(creds, existing_id, content):
    service = build("drive", "v3", credentials=creds, cache_discovery=False)
    tmp = SCRIPT_DIR / ".CV_Suggestions.tmp.md"
    tmp.write_text(content, encoding="utf-8")
    try:
        media = MediaFileUpload(str(tmp), mimetype="text/markdown")
        if existing_id:
            service.files().update(fileId=existing_id, media_body=media).execute()
        else:
            service.files().create(
                body={"name": SUGGESTIONS_FILENAME, "parents": [CV_FOLDER_ID]},
                media_body=media,
            ).execute()
    finally:
        tmp.unlink(missing_ok=True)


# ── Main ────────────────────────────────────────────────────────────────
def main():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] cv_suggest.py")

    try:
        cutoff = get_cutoff_date()
    except subprocess.CalledProcessError as e:
        sys.exit(f"`gh api` failed (is gh installed and authenticated?): {e.stderr}")
    except Exception as e:
        sys.exit(f"Failed to determine cutoff date: {e}")
    print(f"  Cutoff: {cutoff.isoformat()}  (last commit on {GH_REPO}/{GH_BRANCH})")

    creds = make_google_creds()

    gmail_items = drive_items = notion_items = obsidian_items = []

    print("  Scanning Gmail…")
    try:
        gmail_items = scan_gmail(creds, cutoff)
        print(f"    {len(gmail_items)} message(s)")
    except Exception as e:
        msg = str(e)
        print(f"    Gmail scan FAILED: {msg}", file=sys.stderr)
        if "insufficient" in msg.lower() or "scope" in msg.lower():
            print("    → Refresh token missing gmail.readonly scope. "
                  "Re-run OAuth with both drive AND gmail.readonly scopes.",
                  file=sys.stderr)

    print("  Scanning Drive (Academic + CV folders)…")
    try:
        drive_items = (scan_drive_folder(creds, ACADEMIC_FOLDER_ID, cutoff)
                       + scan_drive_folder(creds, CV_FOLDER_ID, cutoff))
        print(f"    {len(drive_items)} file(s)")
    except Exception as e:
        print(f"    Drive scan FAILED: {e}", file=sys.stderr)

    print("  Scanning Notion (Projects DB, label=Academic)…")
    try:
        notion_items = scan_notion(cutoff)
        print(f"    {len(notion_items)} project(s)")
    except Exception as e:
        print(f"    Notion scan FAILED: {e}", file=sys.stderr)

    print("  Scanning Obsidian (academic notes)…")
    try:
        obsidian_items = scan_obsidian(cutoff)
        print(f"    {len(obsidian_items)} note(s)")
    except Exception as e:
        print(f"    Obsidian scan FAILED: {e}", file=sys.stderr)

    today = date.today().isoformat()
    new_block = (
        f"---\n## Suggestions — {today}\n\n"
        f"### Gmail\n\n{fmt_gmail(gmail_items)}\n"
        f"### Drive\n\n{fmt_drive(drive_items)}\n"
        f"### Notion\n\n{fmt_notion(notion_items)}\n"
        f"### Obsidian\n\n{fmt_obsidian(obsidian_items)}\n"
    )

    print("  Fetching existing CV_Suggestions.md from Drive…")
    try:
        existing_id, existing_content = fetch_existing_suggestions(creds)
        if existing_id:
            print("    Found; will prepend.")
        else:
            print("    Not found; will create.")
    except Exception as e:
        print(f"    Fetch FAILED, will create new file: {e}", file=sys.stderr)
        existing_id, existing_content = None, ""

    combined = new_block + (("\n" + existing_content) if existing_content else "")

    print("  Uploading CV_Suggestions.md to Drive…")
    try:
        upload_suggestions(creds, existing_id, combined)
        print("    Done.")
    except Exception as e:
        sys.exit(f"Upload FAILED: {e}")


if __name__ == "__main__":
    main()
