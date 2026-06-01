# CV pipeline — setup on a new machine

1. **Clone**      `git clone https://github.com/chrismoffett/cv.git && cd cv`
2. **Virtualenv** `python3 -m venv .venv && source .venv/bin/activate`
3. **Install**    `pip install -r requirements.txt`
4. **Secrets**    Copy `.env` from Google Drive →
   `Second Brain/01 Areas/Academic/CV/.env` into this folder.
   (`.env` is gitignored and never committed.)
5. **Run**        `python3 cv_suggest.py`

## If Google auth fails (`invalid_grant` / token expired)
The OAuth **refresh token** has rotted. Regenerate it:

    python3 get_refresh_token.py     # mint a new GDRIVE_REFRESH_TOKEN, paste into .env

This uses the OAuth client in your Google Cloud Console project (the one whose
client id matches `GDRIVE_CLIENT_ID`). If that project's OAuth consent screen is
in **Testing** status, refresh tokens expire after ~7 days — set it to
**Published** to stop the rot. See the operator's note in Notion for details.

## What this does
Scans Gmail + Drive + Notion for activity since the last `cv_content.yaml`
commit (read from local git), runs `cv_filter` (an LLM precision pass that keeps
real CV lines and quarantines in-prep work and review invitations), and prepends
dated suggestions to `CV_Suggestions.md` in the Drive CV folder. The public CV is
built separately: `cv_build_html.py` → `index.html` → GitHub Pages.
