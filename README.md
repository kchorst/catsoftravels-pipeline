# COT YouTube Movie Creator Suite (Video and Audio Tools)

A unified GUI launcher for a complete YouTube movie creation workflow, with an integrated Audio Prep Suite.

Covers every stage from raw photos to published YouTube video: slideshow rendering, metadata generation, uploading, analytics, and audio preparation.

## Docs (start here)

- **User Guide (full workflow):** `USER_GUIDE.md`
- **LLM Voice Guide (GUI-only):** `LLM_VOICE_GUI_GUIDE.md`

## Audio Prep Suite (separate optional repo)

The Audio Prep Suite tools are **optional** and **not included in this repo**.

- Repo: https://github.com/kchorst/audio-prep-suite
- Audio user guide (in that repo): `AUDIO_USER_GUIDE.md`

To enable audio tools in the launcher:

- Install/clone Audio Prep Suite
- Settings → set the **Audio Prep Suite** folder path

---

## What's in This Repo

```
COTCode/
├── master_launcher.py          # Main GUI launcher (entry point)
├── launch.bat                  # Double-click to start (no console window)
│
├── cot_pipeline.py             # CLI pipeline orchestrator
├── make_show.py                # Beat-synced slideshow video renderer
├── youtube_meta.py             # YouTube metadata generator (LLM-assisted)
├── youtube_upload.py           # YouTube uploader with quota tracking
├── cot_analytics.py            # YouTube Analytics puller
├── cot_config.py               # Shared config manager + admin wizard
├── cot_config.json             # Your personal settings (gitignored)
├── client_secrets.json         # Google OAuth credentials (gitignored)
│
└── cot_gui/                    # GUI wrappers for each tool
    ├── cot_base_gui.py         # Shared base window class
    ├── make_show_gui.py        # Make Show GUI
    ├── metadata_gui.py         # Metadata GUI
    ├── upload_gui.py           # Upload GUI
    ├── analytics_gui.py        # Analytics GUI
    └── view_edit_gui.py        # View & Edit Live GUI
```

---

## Tools

### Video Suite (left column)

| Tool | Description |
|---|---|
| **Make Show** | Renders beat-synced slideshow MP4s from photo folders. BPM-driven — each image displays for exactly one beat. Supports normal, batch silent, batch audio, and add-audio modes. |
| **Metadata** | Generates YouTube titles, descriptions, and tags using a local LLM (LM Studio) or manual entry. Supports one-by-one, selective, and batch modes. Saves to CSV for upload. |
| **Upload to YouTube** | Uploads videos from the metadata CSV to YouTube via the Data API. Shows quota status (free tier: ~6 videos/day). Dry run mode available. |
| **Analytics** | Pulls view counts, watch time, top countries, and traffic sources for all channel videos. Exports to CSV with a leaderboard view. |
| **View and Edit Live** | Fetches live YouTube metadata and lets you search, edit titles/descriptions/tags/privacy, and push changes back to YouTube. |

### Audio Prep Suite (right column)

| Tool | Description |
|---|---|
| **Full Pipeline** | Trim → Normalize → BPM → Key → Rename → Export MP3 → CSV in one pass |
| **BPM Analyzer** | Batch BPM detection with rename and WAV→MP3 export |
| **WAV to MP3** | Batch converter with optional normalize and trim |
| **Silence Trimmer** | Trim leading/trailing silence with adjustable threshold |
| **Key Detector** | Musical key + Camelot wheel code detection and file renaming |

---

## Requirements

### System

| Requirement | Notes |
|---|---|
| **Python 3.10–3.12** | 3.12 recommended |
| **FFmpeg** | Must be on system PATH |
| **LM Studio** | Optional — required only for AI-assisted metadata generation |

### Audio Prep Suite (optional)

The Audio Prep Suite tools are **optional** and **not included in this repo**.

- To use the audio tools in the launcher’s right column, install/clone the Audio Prep Suite repo separately.
- Then open **Settings** and set the **Audio Prep Suite** folder path.

### Python Packages

```
customtkinter==5.2.2
tkinterdnd2==0.3.0
requests
```

For YouTube API tools (upload, analytics, live edit):

```
google-auth
google-auth-oauthlib
google-auth-httplib2
google-api-python-client
```

Install everything:

```bash
pip install customtkinter==5.2.2 tkinterdnd2==0.3.0 requests \
    google-auth google-auth-oauthlib google-auth-httplib2 \
    google-api-python-client pyreadline3
```

---

## Installation

### 1. Clone this repo

```bash
git clone https://github.com/kchorst/catsoftravels-suite.git
cd catsoftravels-suite
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Install FFmpeg

**Windows:**
1. Download from https://www.gyan.dev/ffmpeg/builds/ (get `ffmpeg-release-full.7z`)
2. Extract to e.g. `C:\ffmpeg\`
3. Add `C:\ffmpeg\bin\` to your system PATH
4. Verify: `ffmpeg -version`

**macOS:** `brew install ffmpeg`

**Linux:** `sudo apt install ffmpeg`

### 4. Set up Google API credentials (for YouTube tools)

1. Go to https://console.cloud.google.com
2. Create a project → Enable **YouTube Data API v3** and **YouTube Analytics API**
3. Create an OAuth 2.0 credential (Desktop type)
4. Download and rename to `client_secrets.json`
5. Place in the `COTCode` folder
6. On first YouTube tool use, a browser login flow will create `token.json` automatically

### 5. Set up LM Studio (optional — for AI metadata)

1. Download LM Studio from https://lmstudio.ai
2. Download a model — recommended: `Meta-Llama-3.1-8B-Instruct-GGUF`
3. Open the Local Server tab (the `<->` icon) and start the server
4. In the launcher Settings, set LLM Mode to **Use LM Studio** and click Refresh to select the model

### 6. Configure paths

Launch the app and open **Settings**:

- **COT Pictures folder** — your source photos root (e.g. `C:\Users\You\Pictures`)
- **COT Output folder** — where rendered MP4s are saved (e.g. `...\Pictures\COTMovies`)
- **Audio Prep Suite folder** — path to your Audio Prep Suite installation
- **Images folder** — general images folder

Or run the interactive setup wizard: **Admin → Run Setup Wizard**

---

## Launch

**Double-click `launch.bat`** — opens the launcher with no console window.

Or from terminal:

```bash
python master_launcher.py
```

---

## First Run Walkthrough (Fork-Friendly Setup)

This walkthrough is the recommended first-time setup for anyone who forks this repo and wants to use it for their own YouTube channel.

### 1) Install Python + dependencies

- **Python**: 3.10–3.12 (3.12 recommended)
- Install required packages (minimum set for most users):

```bash
pip install customtkinter==5.2.2 tkinterdnd2==0.3.0 requests \
    google-auth google-auth-oauthlib google-auth-httplib2 \
    google-api-python-client pyreadline3
```

### 2) Launch the Master Launcher

- Double-click `launch.bat` (Windows)
- Or run:

```bash
python master_launcher.py
```

### 3) Open Settings and configure the basics

Click **Settings** in the launcher.

#### FOLDERS

- Set your **Pictures/source** folder and **Output/movies** folder.
- Set **Images / Pictures** and (optional) **Audio Prep Suite** paths.

#### LLM / AI (optional)

- If using LM Studio:
  - Set **LLM Mode** = *Use LM Studio*
  - Click **Refresh** to load models and select one
- Otherwise:
  - Set **LLM Mode** = *Manual only*

For GUI-only help tuning metadata voice and examples, see **`LLM_VOICE_GUI_GUIDE.md`**.

#### YOUTUBE (authenticate + verify/select channel)

1. Set **client_secrets.json** path.
   - If you do not have it yet:
     - Google Cloud Console → create OAuth Client ID (Desktop)
     - Enable **YouTube Data API v3** (and **YouTube Analytics API** if you want analytics)
     - Download the JSON and save it locally

2. `token.json` is created automatically the first time you authenticate.

3. Click **Refresh** on the **Channel** row.
   - This triggers Google login/consent in the browser if needed.
   - After authentication, your channel(s) are loaded.
   - If more than one channel is available, select the one you want.

4. Optional:
   - Set **Fixed tags** (comma-separated)
   - Customize **LLM voice/style** and **LLM examples** (multiline overrides)

### 4) Save

Click **Save and Close**.

This updates your local `cot_config.json` (gitignored) so your fork is fully configured without editing scripts.

### 5) Run tools

Back in the launcher, use:

- **Make Show**: render videos
- **Metadata**: generate titles/descriptions/tags
- **Upload to YouTube**: upload from CSV
- **Analytics**: pull performance stats
- **View and Edit Live**: browse/search/edit live metadata (and delete with safeguards)

### Note on network timeouts

Some networks have unreliable IPv6 routes to Google APIs. The launcher defaults to an IPv4-only workaround for YouTube API calls.

---

## Run Individual Scripts (Standalone / Command Line)

Some users may only want one tool from this repo. The primary scripts can be run directly from a terminal.

### Master Launcher (GUI)

```bash
python master_launcher.py
```

### Pipeline Menu (CLI)

Runs a unified text menu that chains the tools together:

```bash
python cot_pipeline.py
```

### Make Show (CLI)

Renders beat-synced slideshow videos.

```bash
python make_show.py
```

### Metadata Generator (CLI)

Generates titles/descriptions/tags and can also run **UC6 View & Edit Live**.

```bash
python youtube_meta.py
```

### Upload to YouTube (CLI)

Uploads videos using the YouTube Data API.

Required local files:
- `client_secrets.json` (OAuth client credentials)
- `token.json` (auto-created on first successful login)

```bash
python youtube_upload.py
```

### Analytics (CLI)

Pulls YouTube Analytics + exports CSV.

```bash
python cot_analytics.py
```

---

## Settings

Click **Settings** in the launcher header to configure:

- Folder paths (COT scripts, pictures, output, audio suite)
- LLM mode (LM Studio or manual)
- LM Studio URL and model (with live Refresh from running server)
- Theme (system / dark / light)

## Admin Panel

Click **Admin** in the launcher header to:

- **Run Setup Wizard** — interactive terminal wizard to set all config values
- **Full Admin Menu** — full admin: deps check, auth check, LM Studio check, config edit
- **Check Dependencies** — verify all required packages are installed
- **Check Google Auth** — verify `client_secrets.json` and `token.json`
- **Check LM Studio** — ping server, list loaded models
- **Show Current Config** — dump all `cot_config.json` values inline

---

## Folder Structure (on disk)

```
C:\Users\you\Desktop\COTCode\       <- this repo
    master_launcher.py
    launch.bat
    cot_pipeline.py
    make_show.py
    youtube_meta.py
    youtube_upload.py
    cot_analytics.py
    cot_config.py
    cot_config.json                 <- gitignored
    client_secrets.json             <- gitignored
    token.json                      <- gitignored (auto-created)
    cot_gui\
        ...

C:\Users\you\Pictures\              <- source photos (PICTURES_DIR)
    2024 Tokyo\
        photo1.jpg
        ...
    2025 Paris\
        ...

C:\Users\you\Pictures\COTMovies\    <- rendered output (OUTPUT_DIR)
    2024 Tokyo.mp4
    2024 Tokyo_music.mp4
    youtube_uploads.csv
    upload_log.json

D:\Audio Prep Suite\                <- Audio Suite (separate repo)
    main.py
    ...
```

---

## How the Pipeline Works

```
PHOTOS FOLDER
    |
    v
[Make Show]  ──────────────────────────  renders silent MP4s
    |
    v
[Make Show Mode D]  ────────────────────  adds music to approved videos
    |
    v
[Metadata]  ────────────────────────────  generates title + description + tags via LLM
    |
    v                                      saves to youtube_uploads.csv
[Upload]  ──────────────────────────────  uploads to YouTube (~6/day free quota)
    |
    v
[Analytics]  ───────────────────────────  pulls stats after 2-3 day delay
    |
    v
[View & Edit Live]  ────────────────────  edit published metadata if needed
```

---

## Audio Suite Integration

The Audio Prep Suite runs alongside the Video Suite in the right column of the launcher. Configure its folder in Settings. Each audio tool opens in its own window with a **Back to Launcher** button.

Audio tools are documented separately at: https://github.com/kchorst/audio-prep-suite

---

## Gitignore

The following are excluded from version control — never commit these:

```
cot_config.json        # contains your personal folder paths
client_secrets.json    # Google OAuth client credentials
token.json             # Google OAuth access token
launcher_log.txt       # runtime log
_admin_runner.py       # temp file generated at runtime
_admin_launcher.bat    # temp file generated at runtime
_check_runner.py       # temp file generated at runtime
__pycache__/
*.pyc
```

---

## License

MIT
