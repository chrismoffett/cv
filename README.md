# CV — Chris Moffett

Academic CV built from a YAML content file using Python + WeasyPrint.

**Live HTML version:** https://chrismoffett.github.io/cv/

---

## How it works

- `cv_content.yaml` — all CV content. Edit this file in Google Drive to update the CV.
- `cv_build.py` — renders YAML → PDF using WeasyPrint
- `cv_build_html.py` — renders YAML → self-contained HTML with embedded fonts
- `fonts_ttf/` — EB Garamond + Cormorant Garamond font files
- `.github/workflows/build-cv.yml` — GitHub Actions workflow

## Updating the CV

1. Edit `cv_content.yaml` in Google Drive (`Areas > Academic > CV`)
2. Trigger the build using the URL in the Drive README
3. GitHub Actions runs automatically (~60–90 seconds):
   - Resolves `cv_content.yaml` by name inside the Drive CV folder and downloads it
   - Builds `CV_Moffett.pdf` and `CV_Moffett.html`
   - Commits both to this repo
   - Uploads both back to Drive
4. GitHub Pages serves the updated HTML at the live URL above

## GitHub Secrets

The workflow authenticates to Google Drive via OAuth (not a service account) and needs four secrets in **Settings → Secrets and variables → Actions**:

| Secret | What it is |
|--------|------------|
| `GDRIVE_REFRESH_TOKEN` | OAuth refresh token for the Drive API |
| `GDRIVE_CLIENT_ID` | OAuth client ID (Google Cloud Console) |
| `GDRIVE_CLIENT_SECRET` | OAuth client secret |
| `GDRIVE_CV_FOLDER_ID` | `1H2lg3z_HiPcSeS-gIlYV5GS24AedQ476` — the CV folder in Drive. The build resolves `cv_content.yaml`, `CV_Moffett.pdf`, etc. by name inside this folder, so nothing is pinned to a specific file ID. |

If the refresh token expires (`invalid_grant`), see `SETUP.md` for regenerating it with `get_refresh_token.py`.

> **Note:** a `GDRIVE_YAML_FILE_ID` secret existed previously, pinning `cv_content.yaml` to one specific Drive file ID. That approach broke every time the file was recreated in Drive, so the workflow was changed (2026-08-17) to resolve the file by name instead. The old secret is no longer read by anything and can be deleted.

## Local build (optional)

```bash
# Install dependencies (macOS)
brew install weasyprint
pip install pyyaml
# For Chinese characters:
# brew install --cask font-noto-serif-cjk

python3 cv_build.py          # → CV_Moffett.pdf
python3 cv_build_html.py     # → CV_Moffett.html
```
