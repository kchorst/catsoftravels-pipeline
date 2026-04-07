# User Guide — COT YouTube Movie Creator Suite (Video and Audio Tools)

This guide is a feature-oriented overview of the suite and a practical walkthrough of the full workflow:

- Turn photo folders into beat-synced slideshow movies
- Prepare/clean music (optional)
- Add audio to your movies (optional)
- Generate YouTube metadata (manual or local LLM via LM Studio)
- Upload to YouTube
- Review analytics
- View and edit live YouTube metadata

---

## 1) What this tool is

This repo is a collection of Python tools plus a GUI launcher. You can:

- Use the **Master Launcher** to run everything from a single window
- Or run individual scripts from the command line

The suite is designed to be **channel-generic**:

- You authenticate with your own Google account
- You can select/store your preferred YouTube channel
- You can customize metadata style/voice via Settings (no code edits needed)

### Audio tools (optional)

The **Audio Prep Suite** tools (BPM analyzer, key detector, trimming, WAV→MP3, full audio pipeline) are **optional** and **not included in this repo**.

To enable audio tools inside the Master Launcher:

- Install/clone the Audio Prep Suite repo separately
- Settings → set the **Audio Prep Suite** folder path

---

## 1.1) GUI entrypoints and scripts (name + purpose)

If you only want a single tool, this section helps you pick the right file.

### GUI entrypoints

- **`launch.bat`**
  - Windows convenience launcher (starts the GUI without showing a console window).
  - Run:

```bash
launch.bat
```

- **`master_launcher.py`**
  - Main GUI dashboard.
  - Best first-run experience (Settings-based setup).
  - Launches all video and audio tools from one window.
  - Run:

```bash
python master_launcher.py
```

### Primary command-line scripts

- **`cot_pipeline.py`**
  - Text-menu pipeline that chains the suite into a single CLI workflow.
  - Run:

```bash
python cot_pipeline.py
```

- **`make_show.py`**
  - Slideshow creator. Turns photo folders into beat-synced MP4s.
  - Run:

```bash
python make_show.py
```

- **`youtube_meta.py`**
  - Metadata generator (manual or local LLM via LM Studio).
  - Also contains the “View & Edit Live (UC6)” functionality.
  - Run:

```bash
python youtube_meta.py
```

- **`youtube_upload.py`**
  - Upload tool (YouTube Data API).
  - Uses OAuth (`client_secrets.json` + auto-created `token.json`).
  - Run:

```bash
python youtube_upload.py
```

  - Notes:
    - `client_secrets.json` must be present (OAuth Desktop client credentials)
    - `token.json` is created on first successful authentication

- **`cot_analytics.py`**
  - Analytics tool (YouTube Analytics API) for channel/video performance reporting.
  - Run:

```bash
python cot_analytics.py
```

  - Notes:
    - Requires OAuth (same `client_secrets.json` / `token.json` as upload)

### GUI wrappers (optional)

The folder `cot_gui/` contains GUI wrappers (windows) for the tools above:

- `cot_gui/make_show_gui.py`
- `cot_gui/metadata_gui.py`
- `cot_gui/upload_gui.py`
- `cot_gui/analytics_gui.py`
- `cot_gui/view_edit_gui.py`

These are typically launched from `master_launcher.py`, but they can also be run directly:

```bash
python cot_gui/make_show_gui.py
python cot_gui/metadata_gui.py
python cot_gui/upload_gui.py
python cot_gui/analytics_gui.py
python cot_gui/view_edit_gui.py
```

---

## 2) Supported platforms

- **Windows**: primary supported platform (best tested)
- **macOS/Linux**: many pieces should work if Python + FFmpeg are set up, but some GUI/paths may require small adjustments

---

## 3) Install and prerequisites

### System requirements

- **Python**: 3.10–3.12 (3.12 recommended)
- **FFmpeg**: must be installed and available on PATH
- **LM Studio**: optional (only if you want local AI metadata generation)

### Python libraries (high-level)

- **GUI**
  - `customtkinter`
  - `tkinterdnd2`
- **General**
  - `requests`
- **YouTube API** (Upload / Analytics / View & Edit Live)
  - `google-api-python-client`
  - `google-auth`, `google-auth-oauthlib`, `google-auth-httplib2`

Install the commonly-needed set:

```bash
pip install customtkinter==5.2.2 tkinterdnd2==0.3.0 requests \
    google-auth google-auth-oauthlib google-auth-httplib2 \
    google-api-python-client pyreadline3
```

---

## 4) Setup: the two configuration entrypoints (Settings vs Admin)

There are two ways to configure the suite:

### Option A: Settings (recommended)

Open `master_launcher.py`, then click **Settings**.

Settings is the most robust path for new users and GitHub forkers:

- Configure folders
- Configure LM Studio (optional)
- Configure YouTube authentication paths
- Authenticate and select your YouTube channel
- Customize metadata voice/examples

### Option B: Admin Panel (power users)

Click **Admin** in the launcher.

Admin is useful if you want to:

- Run the interactive CLI setup wizard
- Run dependency checks
- Run auth checks
- View/dump current config

---

## 5) First run walkthrough (recommended)

1. Launch the suite:
   - Windows: double-click `launch.bat`, or
   - CLI: `python master_launcher.py`

2. Open **Settings**.

3. Configure:

### 5.1 FOLDERS

Set:

- Source pictures folder (your photo root)
- Output folder (where MP4 movies and CSV files are saved)
- Images folder (general images)
- Audio Prep Suite folder (optional)

### 5.2 LLM / AI (optional)

If you want AI-assisted metadata generation:

- Install and start **LM Studio**
- In Settings:
  - Set **LLM Mode** to “Use LM Studio (local AI)”
  - Click **Refresh** to list models
  - Pick a model

If you don’t want AI:

- Set **LLM Mode** to “Manual only”

### 5.3 YOUTUBE (authenticate + channel select)

In Settings → **YOUTUBE**:

- Set `client_secrets.json` path
  - Create it in Google Cloud Console (OAuth Desktop client)
  - Enable YouTube Data API v3
  - (Optional) Enable YouTube Analytics API

- `token.json`
  - It is auto-created the first time you authenticate successfully

- Click **Refresh** on the Channel row
  - This triggers Google OAuth in your browser if needed
  - The suite will load your channel list
  - If multiple channels exist, select the correct one

- Optional:
  - Fixed tags
  - LLM voice/style override (multiline)
  - LLM examples override (multiline)

4. Click **Save and Close**.

---

## 6) Big picture: the end-to-end workflow

A typical flow looks like:

1. **Make Show**: turn photo folders into silent MP4s
2. **Audio Prep (optional)**: prepare music
3. **Add Music**: attach music tracks to approved MP4s
4. **Metadata**: generate YouTube title/description/tags (manual or local LLM)
5. **Upload**: upload videos to YouTube
6. **Analytics**: review performance after publishing
7. **View & Edit Live**: refine metadata, adjust privacy, and manage your library

---

## 7) Make Show (slideshow creator)

### What it does

- Creates 1080p H.264 MP4s from photo folders
- Syncs image timing to a selected **BPM** (beat-per-minute)
- Supports final image “hold” and “fade” timing

### Typical usage

- Pick a photo folder
- Pick BPM
- Render

### Key concept: BPM-driven timing

Instead of “seconds per image”, each image lasts **exactly one beat**.

This makes slideshow pacing feel musical and consistent.

---

## 8) Audio tools (optional)

### Two ways to use audio

- **Full Pipeline**: do a full batch prep pass (trim/normalize/BPM/key/rename/export)
- **One tool at a time**: run trimmer, BPM analyzer, converter, or key detector separately

### Where audio fits in the video workflow

- You can render silent videos first
- Then attach audio later (“Add audio” mode)

This is often faster and more flexible than picking music upfront.

---

## 9) Metadata generation (manual or local LLM)

### What it does

Produces:

- Title
- Description
- Tags

Outputs are typically saved to CSV for upload.

### Manual mode

You write/edit the metadata yourself.

### Local LLM mode (LM Studio)

This suite can use a **local LLM** via **LM Studio**:

- Your prompts run locally on your machine
- No cloud LLM account is required

Where to configure:

- Settings → LLM / AI
  - LM Studio URL
  - Model selection

For a detailed, GUI-only walkthrough of how to tune voice/examples, see **`LLM_VOICE_GUI_GUIDE.md`**.

#### Recommended approach

- Keep your channel “voice” consistent by customizing:
  - **LLM voice/style override**
  - **LLM examples override**

These are stored in your config and used automatically.

### Starter templates (copy/paste)

If you want a fast, good default without writing your own prompt engineering, use these.
Paste *one* of the voice/style blocks below into **Settings → YOUTUBE → LLM voice/style override**.

#### Voice/style override option A (Mark Twain–style, channel-generic)

```text
You are writing YouTube metadata.

VOICE:
- Write in a dry, witty, observant travel-narrator voice (Mark Twain–style).
- Use clean, plain language. Avoid hype and marketing fluff.
- Prefer concrete details and specific images over generic adjectives.

RULES:
- Title: short, specific, curiosity-driven; no clickbait.
- Description: 2–5 short paragraphs; friendly and readable.
- Include a few natural keywords, but do not keyword-stuff.
- Avoid excessive emojis, excessive exclamation points, and repetitive phrasing.

CLOSER:
- End with a short, natural closer that fits the place.
- Use a generic closer like “Follow the channel for more.” if needed.
```

Note: if you leave the override blank, the suite already falls back to a built-in Mark Twain–style voice block.

#### Voice/style override option B (Generic travel journal vibe)

Paste this into **Settings → YOUTUBE → LLM voice/style override**:

```text
You are writing YouTube metadata.

VOICE:
- Write in a calm, modern travel-journal voice.
- Friendly, grounded, and descriptive — no hype.
- Short sentences are fine. Keep it easy to read.

RULES:
- Title: clear and specific; avoid clickbait.
- Description: 2–4 short paragraphs.
- Include practical details (what it felt like, what you saw, a small highlight), but keep it concise.
- Add a short “what to expect” line if it fits.

CLOSER:
- End with a simple closer (e.g., “Subscribe for more travel stories.”) or a natural sign-off.
```

#### Examples override (minimal)

Paste this into **Settings → YOUTUBE → LLM examples override**:

```text
=== REAL EXAMPLES — MATCH THIS OUTPUT FORMAT ===

Location: Kyoto, Japan
TITLE:
Kyoto After Dark: Lantern Streets and Quiet Temples
DESCRIPTION:
Kyoto doesn’t shout; it murmurs. Step off the bright avenues and the city turns to lantern light, narrow alleys, and temple gates that close like a book.

In this visit we wander the old lanes, pause for small meals, and let the night do most of the talking. If you’ve ever wanted Japan to slow down for a moment, Kyoto is willing.

TAGS:
Kyoto, Japan travel, lanterns, temples, night walk, Gion
```

---

## 10) Upload to YouTube

### What it does

- Uploads videos using the YouTube Data API
- Typically reads from the metadata CSV
- Shows quota status (YouTube API has daily quota limits)

### OAuth requirements

- `client_secrets.json` must exist
- First run will generate `token.json`

---

## 11) Analytics

### What it does

- Pulls view counts, watch time, and related stats
- Exports CSV so you can track performance over time

Note: Analytics metrics can take time to populate after publishing.

---

## 12) View & Edit Live (UC6)

### What it does

- Fetches your existing YouTube videos
- Allows searching/browsing
- Allows editing:
  - Title
  - Description
  - Tags
  - Privacy

This is the “library management” tool once videos are live.

---

## 13) Running only one script (standalone)

If you don’t want the full suite, you can run key tools directly:

```bash
python make_show.py
python youtube_meta.py
python youtube_upload.py
python cot_analytics.py
```

For YouTube scripts, you still need OAuth credentials (`client_secrets.json` + `token.json`).

---

## 14) Troubleshooting and reliability notes

### YouTube API timeouts

Some networks prefer IPv6 routes that can be unreliable for Google APIs.

This suite defaults to an IPv4-only workaround for YouTube calls when launched via the Master Launcher.

### Where config lives

Your local settings are stored in `cot_config.json` (and launcher-only settings in `master_config.json`).

Do not commit OAuth tokens or personal config to GitHub.
