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
3. GitHub Actions runs automatically (~90 seconds):
   - Downloads the updated YAML from Drive
   - Builds `CV_Moffett.pdf` and `CV_Moffett.html`
   - Commits both to this repo
   - Uploads both back to Drive
4. GitHub Pages serves the updated HTML at the live URL above

## First-time setup (GitHub Secrets)

The workflow requires three secrets in **Settings → Secrets and variables → Actions**:

| Secret | Value |
|--------|-------|
| `GDRIVE_SERVICE_ACCOUNT_JSON` | Full JSON content of the Google service account key |
| `GDRIVE_YAML_FILE_ID` | `1CgSBI3au_Xvrw6EECfZLN8fvdwLJ2jVQ` |
| `GDRIVE_CV_FOLDER_ID` | `1H2lg3z_HiPcSeS-gIlYV5GS24AedQ476` |

### Creating the Google service account

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a new project (or use an existing one)
3. Enable the **Google Drive API** for that project
4. Go to **IAM & Admin → Service Accounts → Create Service Account**
5. Name it (e.g. `cv-builder`), click Create
6. Skip role assignment, click Done
7. Click the service account → **Keys → Add Key → Create new key → JSON**
8. Download the JSON file — this is `GDRIVE_SERVICE_ACCOUNT_JSON`
9. Copy the `client_email` from the JSON (looks like `cv-builder@...iam.gserviceaccount.com`)
10. In Google Drive, **share the CV folder** with that email address (Editor access)

Once secrets are set, trigger a build to verify everything works.

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
