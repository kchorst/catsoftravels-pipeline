"""
master_launcher.py  v4.0
COT Master Launcher

Changes from v3.4:
- Console window fully suppressed for GUI tools (CREATE_NO_WINDOW)
- CLI tools (make_show, cot_pipeline) open a real console window (CREATE_NEW_CONSOLE)
- Clean error messages — no long path lists
- Settings now includes cot_config.json fields: PICTURES_DIR, OUTPUT_DIR,
  LLM_MODE (numbered radio), MODEL_NAME (dropdown from live LM Studio)
- LLM model dropdown fetches available models from LM Studio API
"""

import os
import sys
import json
import subprocess
import time
import traceback
import socket
import threading

LAUNCHER_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, LAUNCHER_DIR)
os.environ["COT_SCRIPTS_DIR"] = LAUNCHER_DIR
os.environ.setdefault("COT_FORCE_IPV4", "1")

import customtkinter as ctk
from tkinter import filedialog, messagebox

# ── Windows process flags ─────────────────────────────────────
CREATE_NO_WINDOW    = 0x08000000   # hide console — for GUI tools
CREATE_NEW_CONSOLE  = 0x00000010   # new visible terminal — for CLI tools

_SINGLE_INSTANCE_HOST = "127.0.0.1"
_SINGLE_INSTANCE_PORT = 51337


def _send_show_to_existing_instance() -> bool:
    """Return True if an existing launcher was found and notified."""
    try:
        with socket.create_connection((_SINGLE_INSTANCE_HOST, _SINGLE_INSTANCE_PORT), timeout=0.25) as s:
            s.sendall(b"SHOW\n")
        return True
    except OSError:
        return False


def _start_single_instance_server(app) -> None:
    """Start a background server to receive SHOW requests and focus the window."""

    def _handle_show():
        try:
            app.deiconify()
        except Exception:
            pass
        _focus_window(app)

    def _server():
        try:
            srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            srv.bind((_SINGLE_INSTANCE_HOST, _SINGLE_INSTANCE_PORT))
            srv.listen(5)
        except OSError:
            return

        while True:
            try:
                conn, _addr = srv.accept()
            except OSError:
                break
            try:
                data = conn.recv(64)
                if b"SHOW" in data:
                    app.after(0, _handle_show)
            except Exception:
                pass
            finally:
                try:
                    conn.close()
                except Exception:
                    pass

    threading.Thread(target=_server, daemon=True).start()

# ── Logging ───────────────────────────────────────────────────
def _log(msg):
    try:
        with open(os.path.join(LAUNCHER_DIR, "launcher_log.txt"), "a", encoding="utf-8") as f:
            f.write(f"[{time.asctime()}] {msg}\n")
    except Exception:
        pass


def _focus_window(win):
    """
    Reliably bring a window to the front on Windows.
    - topmost True forces it above everything including taskbar
    - lift + focus_force claim keyboard focus
    - Two-stage release: stay topmost for 600ms so Windows finishes
      compositing, then release so it behaves normally afterwards
    """
    def _do():
        try:
            win.attributes("-topmost", True)
            win.lift()
            win.focus_force()
            win.after(600, _release)
        except Exception:
            pass

    def _release():
        try:
            win.attributes("-topmost", False)
            win.lift()
        except Exception:
            pass

    win.after(80, _do)

# ── master_config.json ────────────────────────────────────────
MASTER_CONFIG_PATH = os.path.join(LAUNCHER_DIR, "master_config.json")
_MASTER_DEFAULTS = {
    "audio_suite_path": "",
    "images_path":      "",
    "theme":            "system",
    "accent":           "blue",
}

def _load_master():
    if os.path.isfile(MASTER_CONFIG_PATH):
        try:
            with open(MASTER_CONFIG_PATH, "r", encoding="utf-8") as f:
                return {**_MASTER_DEFAULTS, **json.load(f)}
        except Exception:
            pass
    return dict(_MASTER_DEFAULTS)

def _save_master(cfg):
    try:
        with open(MASTER_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    except Exception as e:
        _log(f"Failed to save master_config: {e}")

_mcfg = _load_master()

# ── cot_config.json ───────────────────────────────────────────
COT_CONFIG_PATH = os.path.join(LAUNCHER_DIR, "cot_config.json")
_COT_DEFAULTS = {
    "PICTURES_DIR":   "",
    "OUTPUT_DIR":     "",
    "LLM_MODE":       "manual_only",
    "LMSTUDIO_URL":   "http://127.0.0.1:1234/v1/chat/completions",
    "MODEL_NAME":     "",
    "CLIENT_SECRETS": os.path.join(LAUNCHER_DIR, "client_secrets.json"),
    "TOKEN_FILE":     os.path.join(LAUNCHER_DIR, "token.json"),
    "YT_CHANNEL_ID":  "",
    "CHANNEL_NAME":   "",
    "FIXED_TAGS":     [],
    "LLM_VOICE_STYLE":    "",
    "LLM_EXAMPLES_BLOCK": "",
    "MAKE_SHOW_FINAL_HOLD_SEC": 2.0,
    "MAKE_SHOW_FINAL_FADE_SEC": 2.0,
    "MAKE_SHOW_AUDIO_FADE_SEC": 2.0,
}

def _load_cot_config():
    if os.path.isfile(COT_CONFIG_PATH):
        try:
            with open(COT_CONFIG_PATH, "r", encoding="utf-8") as f:
                return {**_COT_DEFAULTS, **json.load(f)}
        except Exception:
            pass
    return dict(_COT_DEFAULTS)

def _save_cot_config(cfg):
    """Merge changes back into cot_config.json, preserving all other keys."""
    existing = {}
    if os.path.isfile(COT_CONFIG_PATH):
        try:
            with open(COT_CONFIG_PATH, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            pass
    existing.update(cfg)
    try:
        with open(COT_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2)
    except Exception as e:
        _log(f"Failed to save cot_config: {e}")
        raise

_ccfg = _load_cot_config()

# ── Theme ─────────────────────────────────────────────────────
ctk.set_appearance_mode(_mcfg.get("theme", "system"))
ctk.set_default_color_theme(_mcfg.get("accent", "blue"))

# ── Tool definitions ──────────────────────────────────────────
# CLI tools: open a real console window (user must interact with them)
# GUI tools: no console window needed

CLI_TOOLS = {
    "make_show_gui.py",    # make_show is interactive CLI
}

COT_TOOLS = [
    ("Make Show",          "make_show_gui.py",  "Render beat-synced slideshow videos",         "cli"),
    ("Metadata",           "metadata_gui.py",   "YouTube titles, tags & descriptions",          "gui"),
    ("Upload to YouTube",  "upload_gui.py",     "YouTube upload with quota tracker",            "gui"),
    ("Analytics",          "analytics_gui.py",  "YouTube channel & video performance",          "gui"),
    ("View and Edit Live", "view_edit_gui.py",  "Edit published metadata (DEL=delete; Dry Run blocks)",           "gui"),
]

AUDIO_TOOLS = [
    ("Full Pipeline",   os.path.join("pipeline",      "full_prep_gui.py"), "Trim, BPM, Key, Rename, MP3, CSV"),
    ("BPM Analyzer",    os.path.join("bpm_tool",      "bpm_gui.py"),       "Detect BPM, rename, export WAV to MP3"),
    ("WAV to MP3",      os.path.join("converters",    "wav_to_mp3.py"),    "Batch convert with optional trim + normalize"),
    ("Silence Trimmer", os.path.join("trimmers",      "trim_silence.py"),  "Trim leading/trailing silence"),
    ("Key Detector",    os.path.join("key_detection", "key_gui.py"),       "Musical key + Camelot wheel code"),
]


# ── LM Studio helper ──────────────────────────────────────────

def _fetch_lm_models(url: str) -> list[str]:
    """Query LM Studio /v1/models. Returns list of model IDs or empty list."""
    try:
        import urllib.request
        base = url.replace("/v1/chat/completions", "")
        req = urllib.request.urlopen(f"{base}/v1/models", timeout=4)
        data = json.loads(req.read())
        return [m["id"] for m in data.get("data", [])]
    except Exception:
        return []


# ── Folder row helper ─────────────────────────────────────────

def _folder_row(form, row_num, label_text, str_var, browse_title):
    ctk.CTkLabel(form, text=label_text, anchor="w", width=180).grid(
        row=row_num, column=0, sticky="w", padx=10, pady=5)
    fr = ctk.CTkFrame(form, fg_color="transparent")
    fr.grid(row=row_num, column=1, sticky="ew", padx=10, pady=5)
    fr.grid_columnconfigure(0, weight=1)
    ctk.CTkEntry(fr, textvariable=str_var).grid(
        row=0, column=0, sticky="ew", padx=(0, 6))
    def _browse(v=str_var, t=browse_title):
        folder = filedialog.askdirectory(title=t)
        if folder:
            v.set(folder)
    ctk.CTkButton(fr, text="Browse", width=70, command=_browse
                  ).grid(row=0, column=1)


def _file_row(form, row_num, label_text, str_var, browse_title, filetypes=("JSON files", "*.json")):
    ctk.CTkLabel(form, text=label_text, anchor="w", width=180).grid(
        row=row_num, column=0, sticky="w", padx=10, pady=5)
    fr = ctk.CTkFrame(form, fg_color="transparent")
    fr.grid(row=row_num, column=1, sticky="ew", padx=10, pady=5)
    fr.grid_columnconfigure(0, weight=1)
    ctk.CTkEntry(fr, textvariable=str_var).grid(
        row=0, column=0, sticky="ew", padx=(0, 6))

    def _browse(v=str_var, t=browse_title):
        path = filedialog.askopenfilename(title=t, filetypes=[filetypes, ("All files", "*")])
        if path:
            v.set(path)

    ctk.CTkButton(fr, text="Browse", width=70, command=_browse).grid(row=0, column=1)


# ── Card builder ──────────────────────────────────────────────

def _make_card(parent, title, desc, command):
    f = ctk.CTkFrame(parent)
    f.pack(fill="x", pady=4, padx=4)
    txt = ctk.CTkFrame(f, fg_color="transparent")
    txt.pack(side="left", padx=10, pady=8)
    ctk.CTkLabel(txt, text=title,
                 font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w")
    ctk.CTkLabel(txt, text=desc,
                 font=ctk.CTkFont(size=10), text_color="gray").pack(anchor="w")
    ctk.CTkButton(f, text="Launch", width=72,
                  command=command).pack(side="right", padx=10)


# ── Settings window ───────────────────────────────────────────

class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, parent, on_save=None):
        super().__init__(parent)
        self.title("Settings")
        self.geometry("620x580")
        self.resizable(False, False)
        self.grab_set()
        self.on_save = on_save
        _focus_window(self)

        # Scroll container so nothing is clipped
        scroll = ctk.CTkScrollableFrame(self)
        scroll.pack(fill="both", expand=True, padx=0, pady=0)
        scroll.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(scroll, text="Master Launcher Settings",
                     font=ctk.CTkFont(size=14, weight="bold")
                     ).grid(row=0, column=0, columnspan=2,
                             pady=(14, 4), padx=10, sticky="w")

        # ── Section: Folders ────────────────────────────────────
        ctk.CTkLabel(scroll, text="FOLDERS",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color="gray"
                     ).grid(row=1, column=0, columnspan=2,
                             sticky="w", padx=10, pady=(10, 2))

        self._audio_path   = ctk.StringVar(value=_mcfg.get("audio_suite_path", ""))
        self._images_path  = ctk.StringVar(value=_mcfg.get("images_path", ""))
        self._pics_path    = ctk.StringVar(value=_ccfg.get("PICTURES_DIR", ""))
        self._output_path  = ctk.StringVar(value=_ccfg.get("OUTPUT_DIR", ""))

        self._ms_hold_sec = ctk.StringVar(value=str(_ccfg.get("MAKE_SHOW_FINAL_HOLD_SEC", 2.0)))
        self._ms_fade_sec = ctk.StringVar(value=str(_ccfg.get("MAKE_SHOW_FINAL_FADE_SEC", 2.0)))
        self._ms_audio_fade_sec = ctk.StringVar(value=str(_ccfg.get("MAKE_SHOW_AUDIO_FADE_SEC", 2.0)))

        _folder_row(scroll, 2,  "Audio Prep Suite",     self._audio_path,  "Select Audio Prep Suite folder")
        _folder_row(scroll, 3,  "Images / Pictures",    self._images_path, "Select Images folder")
        _folder_row(scroll, 4,  "COT Pictures (source)",self._pics_path,   "Select COT source pictures folder")
        _folder_row(scroll, 5,  "COT Output (movies)",  self._output_path, "Select COT output / movies folder")

        ctk.CTkLabel(
            scroll,
            text="Audio Prep Suite is optional and installed separately.\nSet the folder path only if you want the audio tools.",
            font=ctk.CTkFont(size=10),
            text_color="gray",
            justify="left",
            anchor="w",
        ).grid(row=5, column=1, sticky="w", padx=10, pady=(0, 6))

        # ── Section: LLM ────────────────────────────────────────
        ctk.CTkLabel(scroll, text="LLM / AI",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color="gray"
                     ).grid(row=6, column=0, columnspan=2,
                             sticky="w", padx=10, pady=(14, 2))

        # LLM mode — numbered radio style
        ctk.CTkLabel(scroll, text="LLM Mode", anchor="w", width=180
                     ).grid(row=7, column=0, sticky="w", padx=10, pady=5)

        mode_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        mode_frame.grid(row=7, column=1, sticky="w", padx=10, pady=5)

        current_mode = _ccfg.get("LLM_MODE", "manual_only")
        self._llm_mode = ctk.StringVar(
            value="1" if current_mode == "lmstudio_local" else "2"
        )
        ctk.CTkRadioButton(mode_frame, text="1.  Use LM Studio (local AI)",
                           variable=self._llm_mode, value="1",
                           command=self._on_llm_mode_change
                           ).pack(anchor="w", pady=2)
        ctk.CTkRadioButton(mode_frame, text="2.  Manual only (no AI)",
                           variable=self._llm_mode, value="2",
                           command=self._on_llm_mode_change
                           ).pack(anchor="w", pady=2)

        # LM Studio URL
        ctk.CTkLabel(scroll, text="LM Studio URL", anchor="w", width=180
                     ).grid(row=8, column=0, sticky="w", padx=10, pady=5)
        self._lm_url = ctk.StringVar(value=_ccfg.get("LMSTUDIO_URL",
                                      "http://127.0.0.1:1234/v1/chat/completions"))
        self._url_entry = ctk.CTkEntry(scroll, textvariable=self._lm_url)
        self._url_entry.grid(row=8, column=1, sticky="ew", padx=10, pady=5)

        # Model selection
        ctk.CTkLabel(scroll, text="Model", anchor="w", width=180
                     ).grid(row=9, column=0, sticky="w", padx=10, pady=5)

        model_row = ctk.CTkFrame(scroll, fg_color="transparent")
        model_row.grid(row=9, column=1, sticky="ew", padx=10, pady=5)
        model_row.grid_columnconfigure(0, weight=1)

        self._model_var = ctk.StringVar(value=_ccfg.get("MODEL_NAME", ""))
        self._model_menu = ctk.CTkOptionMenu(
            model_row, variable=self._model_var, values=["(click Refresh to load)"],
            width=300)
        self._model_menu.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ctk.CTkButton(model_row, text="Refresh", width=80,
                      command=self._refresh_models
                      ).grid(row=0, column=1)

        self._model_status = ctk.CTkLabel(scroll, text="",
                                          font=ctk.CTkFont(size=10),
                                          text_color="gray", anchor="w")
        self._model_status.grid(row=10, column=1, sticky="w", padx=10)

        # ── Section: YouTube ───────────────────────────────────
        ctk.CTkLabel(scroll, text="YOUTUBE",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color="gray"
                     ).grid(row=11, column=0, columnspan=2,
                             sticky="w", padx=10, pady=(14, 2))

        self._client_secrets = ctk.StringVar(value=_ccfg.get("CLIENT_SECRETS", os.path.join(LAUNCHER_DIR, "client_secrets.json")))
        self._token_file = ctk.StringVar(value=_ccfg.get("TOKEN_FILE", os.path.join(LAUNCHER_DIR, "token.json")))
        self._yt_channel_id = ctk.StringVar(value=_ccfg.get("YT_CHANNEL_ID", ""))
        self._channel_name = ctk.StringVar(value=_ccfg.get("CHANNEL_NAME", ""))
        tags_val = _ccfg.get("FIXED_TAGS", [])
        if isinstance(tags_val, list):
            tags_val = ", ".join(tags_val)
        self._fixed_tags = ctk.StringVar(value=str(tags_val or ""))

        self._voice_style = _ccfg.get("LLM_VOICE_STYLE", "") or ""
        self._examples_block = _ccfg.get("LLM_EXAMPLES_BLOCK", "") or ""

        _file_row(scroll, 12, "client_secrets.json", self._client_secrets, "Select client_secrets.json")
        _file_row(scroll, 13, "token.json", self._token_file, "Select token.json")

        # Channel selection row
        ctk.CTkLabel(scroll, text="Channel", anchor="w", width=180
                     ).grid(row=14, column=0, sticky="w", padx=10, pady=5)
        ch_row = ctk.CTkFrame(scroll, fg_color="transparent")
        ch_row.grid(row=14, column=1, sticky="ew", padx=10, pady=5)
        ch_row.grid_columnconfigure(0, weight=1)

        self._channels_menu_var = ctk.StringVar(value="(click Refresh)")
        self._channels_menu = ctk.CTkOptionMenu(ch_row, variable=self._channels_menu_var, values=["(click Refresh)"])
        self._channels_menu.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ctk.CTkButton(ch_row, text="Refresh", width=80,
                      command=self._refresh_channels
                      ).grid(row=0, column=1)

        self._yt_status = ctk.CTkLabel(scroll, text="",
                                       font=ctk.CTkFont(size=10),
                                       text_color="gray", anchor="w")
        self._yt_status.grid(row=15, column=1, sticky="w", padx=10)

        # Channel name/id fields
        ctk.CTkLabel(scroll, text="Channel name", anchor="w", width=180
                     ).grid(row=16, column=0, sticky="w", padx=10, pady=5)
        ctk.CTkEntry(scroll, textvariable=self._channel_name).grid(row=16, column=1, sticky="ew", padx=10, pady=5)

        ctk.CTkLabel(scroll, text="Channel ID", anchor="w", width=180
                     ).grid(row=17, column=0, sticky="w", padx=10, pady=5)
        ctk.CTkEntry(scroll, textvariable=self._yt_channel_id).grid(row=17, column=1, sticky="ew", padx=10, pady=5)

        ctk.CTkLabel(scroll, text="Fixed tags (comma-separated)", anchor="w", width=180
                     ).grid(row=18, column=0, sticky="w", padx=10, pady=5)
        ctk.CTkEntry(scroll, textvariable=self._fixed_tags).grid(row=18, column=1, sticky="ew", padx=10, pady=5)

        # LLM prompt template overrides
        ctk.CTkLabel(scroll, text="LLM voice/style override", anchor="w", width=180
                     ).grid(row=19, column=0, sticky="nw", padx=10, pady=5)
        self._voice_box = ctk.CTkTextbox(scroll, height=90)
        self._voice_box.grid(row=19, column=1, sticky="ew", padx=10, pady=5)
        self._voice_box.insert("1.0", self._voice_style)

        ctk.CTkLabel(scroll, text="LLM examples override", anchor="w", width=180
                     ).grid(row=20, column=0, sticky="nw", padx=10, pady=5)
        self._examples_box = ctk.CTkTextbox(scroll, height=120)
        self._examples_box.grid(row=20, column=1, sticky="ew", padx=10, pady=5)
        self._examples_box.insert("1.0", self._examples_block)

        # ── Section: Appearance ──────────────────────────────────
        ctk.CTkLabel(scroll, text="APPEARANCE",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color="gray"
                     ).grid(row=21, column=0, columnspan=2,
                             sticky="w", padx=10, pady=(14, 2))

        ctk.CTkLabel(scroll, text="Theme", anchor="w", width=180
                     ).grid(row=22, column=0, sticky="w", padx=10, pady=5)
        self._theme = ctk.CTkOptionMenu(
            scroll, values=["system", "dark", "light"],
            command=lambda v: ctk.set_appearance_mode(v))
        self._theme.set(_mcfg.get("theme", "system"))
        self._theme.grid(row=22, column=1, sticky="w", padx=10, pady=5)

        # ── Section: Make Show ──────────────────────────────────
        ctk.CTkLabel(scroll, text="MAKE SHOW",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color="gray"
                     ).grid(row=23, column=0, columnspan=2,
                             sticky="w", padx=10, pady=(14, 2))

        ctk.CTkLabel(scroll, text="Final hold (sec)", anchor="w", width=180
                     ).grid(row=24, column=0, sticky="w", padx=10, pady=5)
        ctk.CTkEntry(scroll, textvariable=self._ms_hold_sec, width=120
                     ).grid(row=24, column=1, sticky="w", padx=10, pady=5)

        ctk.CTkLabel(scroll, text="Final fade (sec)", anchor="w", width=180
                     ).grid(row=25, column=0, sticky="w", padx=10, pady=5)
        ctk.CTkEntry(scroll, textvariable=self._ms_fade_sec, width=120
                     ).grid(row=25, column=1, sticky="w", padx=10, pady=5)

        ctk.CTkLabel(scroll, text="Audio fade (sec)", anchor="w", width=180
                     ).grid(row=26, column=0, sticky="w", padx=10, pady=5)
        ctk.CTkEntry(scroll, textvariable=self._ms_audio_fade_sec, width=120
                     ).grid(row=26, column=1, sticky="w", padx=10, pady=5)

        # ── Save button ──────────────────────────────────────────
        ctk.CTkButton(self, text="Save and Close", height=36,
                      command=self._save).pack(pady=12, padx=20, fill="x")

        # Update UI state for current mode
        self._on_llm_mode_change()

        # Auto-refresh models if LM Studio mode is active
        if _ccfg.get("LLM_MODE") == "lmstudio_local":
            self.after(300, self._refresh_models)

    def _on_llm_mode_change(self):
        is_lm = self._llm_mode.get() == "1"
        state = "normal" if is_lm else "disabled"
        self._url_entry.configure(state=state)
        self._model_menu.configure(state=state)

    def _refresh_models(self):
        url = self._lm_url.get().strip()
        self._model_status.configure(text="Connecting to LM Studio...")
        self.update()
        models = _fetch_lm_models(url)
        if models:
            current = self._model_var.get()
            self._model_menu.configure(values=models)
            if current in models:
                self._model_var.set(current)
            else:
                self._model_var.set(models[0])
            self._model_status.configure(
                text=f"{len(models)} model(s) loaded", text_color="green")
        else:
            self._model_menu.configure(values=["(LM Studio not reachable)"])
            self._model_status.configure(
                text="Could not reach LM Studio. Is the server running?",
                text_color="orange")

    def _refresh_channels(self):
        self._yt_status.configure(text="Connecting to YouTube...", text_color="gray")
        self.update()

        def _worker():
            try:
                try:
                    import cot_config as _cfg
                    _cfg.load(gui_mode=True)
                    _cfg.set("CLIENT_SECRETS", self._client_secrets.get().strip(), save_now=False)
                    _cfg.set("TOKEN_FILE", self._token_file.get().strip(), save_now=False)
                except Exception:
                    pass
                import youtube_upload as yt_upload
                youtube = yt_upload.authenticate()
                resp = youtube.channels().list(part="id,snippet", mine=True).execute()
                chans = []
                for it in resp.get("items", []):
                    cid = it.get("id", "")
                    title = (it.get("snippet") or {}).get("title", "")
                    if cid:
                        label = f"{title}  [{cid}]" if title else f"(no title)  [{cid}]"
                        chans.append((label, cid, title))
                return (chans, None)
            except Exception as e:
                return ([], e)

        def _done(result):
            chans, err = result
            if err:
                self._channels_menu.configure(values=["(refresh failed)"])
                self._yt_status.configure(text=f"YouTube error: {err}", text_color="orange")
                return
            if not chans:
                self._channels_menu.configure(values=["(no channels found)"])
                self._yt_status.configure(text="No channels found for this account.", text_color="orange")
                return

            self._channel_choices = {label: (cid, title) for (label, cid, title) in chans}
            labels = [label for (label, _cid, _title) in chans]
            self._channels_menu.configure(values=labels)

            preferred = (self._yt_channel_id.get() or "").strip()
            chosen_label = None
            if preferred:
                for label, cid, _title in chans:
                    if cid == preferred:
                        chosen_label = label
                        break
            if not chosen_label:
                chosen_label = labels[0]

            self._channels_menu_var.set(chosen_label)
            cid, title = self._channel_choices.get(chosen_label, ("", ""))
            if cid:
                self._yt_channel_id.set(cid)
            if title and not self._channel_name.get().strip():
                self._channel_name.set(title)

            self._yt_status.configure(text=f"{len(chans)} channel(s) found", text_color="green")

        def _bg():
            result = _worker()
            self.after(0, _done, result)

        threading.Thread(target=_bg, daemon=True).start()

    def _save(self):
        # Validate folder paths
        for key, var, label in [
            ("audio_suite_path", self._audio_path,  "Audio Prep Suite"),
            ("images_path",      self._images_path, "Images"),
        ]:
            path = var.get().strip()
            if path and not os.path.isdir(path):
                messagebox.showerror("Not found", f"{label} folder not found:\n{path}")
                return
            _mcfg[key] = path

        for key, var, label in [
            ("PICTURES_DIR", self._pics_path,   "COT Pictures"),
            ("OUTPUT_DIR",   self._output_path, "COT Output"),
        ]:
            path = var.get().strip()
            if path and not os.path.isdir(path):
                messagebox.showerror("Not found", f"{label} folder not found:\n{path}")
                return
            _ccfg[key] = path

        # LLM settings
        _ccfg["LLM_MODE"]     = "lmstudio_local" if self._llm_mode.get() == "1" else "manual_only"
        _ccfg["LMSTUDIO_URL"] = self._lm_url.get().strip()
        model = self._model_var.get()
        if model and "(LM Studio" not in model and "(click" not in model:
            _ccfg["MODEL_NAME"] = model

        # Make Show timing (seconds)
        try:
            _ccfg["MAKE_SHOW_FINAL_HOLD_SEC"] = float(self._ms_hold_sec.get().strip() or "2.0")
            _ccfg["MAKE_SHOW_FINAL_FADE_SEC"] = float(self._ms_fade_sec.get().strip() or "2.0")
            _ccfg["MAKE_SHOW_AUDIO_FADE_SEC"] = float(self._ms_audio_fade_sec.get().strip() or "2.0")
        except Exception:
            messagebox.showerror("Invalid value", "Make Show timing fields must be numbers (seconds).")
            return

        # Appearance
        _mcfg["theme"] = self._theme.get()

        # YouTube / channel settings
        _ccfg["CLIENT_SECRETS"] = self._client_secrets.get().strip()
        _ccfg["TOKEN_FILE"] = self._token_file.get().strip()
        _ccfg["YT_CHANNEL_ID"] = self._yt_channel_id.get().strip()
        _ccfg["CHANNEL_NAME"] = self._channel_name.get().strip()
        tags_str = self._fixed_tags.get().strip()
        _ccfg["FIXED_TAGS"] = [t.strip() for t in tags_str.split(",") if t.strip()] if tags_str else []

        try:
            _ccfg["LLM_VOICE_STYLE"] = self._voice_box.get("1.0", "end").strip()
            _ccfg["LLM_EXAMPLES_BLOCK"] = self._examples_box.get("1.0", "end").strip()
        except Exception:
            pass

        try:
            _save_master(_mcfg)
            _save_cot_config({
                "PICTURES_DIR": _ccfg["PICTURES_DIR"],
                "OUTPUT_DIR":   _ccfg["OUTPUT_DIR"],
                "LLM_MODE":     _ccfg["LLM_MODE"],
                "LMSTUDIO_URL": _ccfg["LMSTUDIO_URL"],
                "MODEL_NAME":   _ccfg["MODEL_NAME"],
                "CLIENT_SECRETS": _ccfg.get("CLIENT_SECRETS", ""),
                "TOKEN_FILE":     _ccfg.get("TOKEN_FILE", ""),
                "YT_CHANNEL_ID":  _ccfg.get("YT_CHANNEL_ID", ""),
                "CHANNEL_NAME":   _ccfg.get("CHANNEL_NAME", ""),
                "FIXED_TAGS":     _ccfg.get("FIXED_TAGS", []),
                "LLM_VOICE_STYLE":    _ccfg.get("LLM_VOICE_STYLE", ""),
                "LLM_EXAMPLES_BLOCK": _ccfg.get("LLM_EXAMPLES_BLOCK", ""),
                "MAKE_SHOW_FINAL_HOLD_SEC":  _ccfg["MAKE_SHOW_FINAL_HOLD_SEC"],
                "MAKE_SHOW_FINAL_FADE_SEC":  _ccfg["MAKE_SHOW_FINAL_FADE_SEC"],
                "MAKE_SHOW_AUDIO_FADE_SEC":  _ccfg["MAKE_SHOW_AUDIO_FADE_SEC"],
            })
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save settings:\n{e}")
            return

        self.destroy()
        if self.on_save:
            self.on_save()



# ── Admin window ──────────────────────────────────────────────

class AdminWindow(ctk.CTkToplevel):
    """
    Admin panel with two modes:
      - Run Setup Wizard / Edit Config  → opens cot_config.py in a real console
      - Read-only checks (deps, auth, LM Studio, show config) → output shown inline
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Admin — COT Configuration")
        self.geometry("700x580")
        self.minsize(600, 480)
        # No grab_set() — must allow subprocess windows to get focus
        self._build_ui()
        _focus_window(self)

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # ── Header ──────────────────────────────────────────────
        ctk.CTkLabel(self, text="COT Admin Panel",
                     font=ctk.CTkFont(size=15, weight="bold"),
                     anchor="w"
                     ).grid(row=0, column=0, sticky="w", padx=16, pady=(14, 4))
        ctk.CTkLabel(self,
                     text="Run checks and edit configuration for the CatsofTravels pipeline.",
                     font=ctk.CTkFont(size=11), text_color="gray", anchor="w"
                     ).grid(row=1, column=0, sticky="w", padx=16, pady=(0, 8))

        # ── Button row ───────────────────────────────────────────
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=2, column=0, sticky="ew", padx=14, pady=(0, 6))

        # Left: interactive / wizard buttons (open console window)
        interactive = ctk.CTkFrame(btn_frame, corner_radius=8)
        interactive.pack(side="left", fill="y", padx=(0, 8))

        ctk.CTkLabel(interactive, text="Interactive (opens terminal)",
                     font=ctk.CTkFont(size=11, weight="bold"), text_color="gray"
                     ).pack(anchor="w", padx=10, pady=(8, 4))

        ctk.CTkButton(interactive, text="Run Setup Wizard",
                      width=200, height=34,
                      command=lambda: self._run_cli("wizard")
                      ).pack(padx=10, pady=3, fill="x")
        ctk.CTkButton(interactive, text="Full Admin Menu",
                      width=200, height=34,
                      fg_color="transparent", border_width=1,
                      command=lambda: self._run_cli("admin")
                      ).pack(padx=10, pady=(3, 10), fill="x")

        # Right: read-only checks (output shown in log panel below)
        checks = ctk.CTkFrame(btn_frame, corner_radius=8)
        checks.pack(side="left", fill="both", expand=True)

        ctk.CTkLabel(checks, text="Live checks (output below)",
                     font=ctk.CTkFont(size=11, weight="bold"), text_color="gray"
                     ).pack(anchor="w", padx=10, pady=(8, 4))

        btn_row1 = ctk.CTkFrame(checks, fg_color="transparent")
        btn_row1.pack(fill="x", padx=6, pady=2)
        btn_row2 = ctk.CTkFrame(checks, fg_color="transparent")
        btn_row2.pack(fill="x", padx=6, pady=(0, 8))

        for text, fn, row in [
            ("Check Dependencies",    "deps",   btn_row1),
            ("Check Google Auth",     "auth",   btn_row1),
            ("Check LM Studio",       "llm",    btn_row2),
            ("Show Current Config",   "config", btn_row2),
        ]:
            ctk.CTkButton(row, text=text, height=32,
                          command=lambda f=fn: self._run_check(f)
                          ).pack(side="left", padx=4, pady=2, expand=True, fill="x")

        # ── Log output ───────────────────────────────────────────
        log_frame = ctk.CTkFrame(self)
        log_frame.grid(row=3, column=0, sticky="nsew", padx=14, pady=(4, 4))
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        self._log_box = ctk.CTkTextbox(
            log_frame,
            font=ctk.CTkFont(family="Courier New", size=11),
            wrap="word", state="disabled"
        )
        self._log_box.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)

        # ── Footer ───────────────────────────────────────────────
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=4, column=0, sticky="ew", padx=14, pady=(0, 10))
        footer.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(footer,
                     text=f"Config file: {COT_CONFIG_PATH}",
                     font=ctk.CTkFont(size=10), text_color="gray", anchor="w"
                     ).grid(row=0, column=0, sticky="w")
        ctk.CTkButton(footer, text="Clear Log", width=80, height=26,
                      fg_color="transparent", border_width=1,
                      command=self._clear_log
                      ).grid(row=0, column=1, sticky="e")

        # Auto-run show config on open
        self.after(200, lambda: self._run_check("config"))

    # ── Interactive: run cot_config.py in a real console ─────────

    def _run_cli(self, mode: str):
        """
        Open wizard/admin in a real visible terminal.
        Writes a .bat file and uses os.startfile() — the only reliable
        way to get a visible cmd window from a pythonw parent process.
        """
        cot_config_path = os.path.join(LAUNCHER_DIR, "cot_config.py")
        if not os.path.isfile(cot_config_path):
            messagebox.showerror("Not found",
                                 f"cot_config.py not found in:\n{LAUNCHER_DIR}")
            return

        label = "Setup Wizard" if mode == "wizard" else "Admin Menu"
        fn    = "cfg.run_wizard()" if mode == "wizard" else "cfg.run_admin()"
        runner = os.path.join(LAUNCHER_DIR, "_admin_runner.py")
        bat    = os.path.join(LAUNCHER_DIR, "_admin_launcher.bat")

        # ── Write the Python runner — use explicit open/write, no escaping ──
        try:
            with open(runner, "w", encoding="utf-8") as rf:
                rf.write("# -*- coding: utf-8 -*-\n")
                rf.write("import sys, os\n")
                rf.write("sys.stdout.reconfigure(encoding='utf-8', errors='replace')\n")
                rf.write(f"sys.path.insert(0, r'{LAUNCHER_DIR}')\n")
                rf.write(f"os.chdir(r'{LAUNCHER_DIR}')\n")
                rf.write("import cot_config as cfg\n")
                rf.write("cfg.load()\n")
                rf.write(f"{fn}\n")
                rf.write("input('\\nDone. Press Enter to close...')\n")
        except Exception as e:
            messagebox.showerror("Error", f"Could not write runner:\n{e}")
            return

        if sys.platform == "win32":
            # Use python.exe (not pythonw) so the child has stdout
            py_exe = sys.executable.replace("pythonw.exe", "python.exe")
            if not os.path.isfile(py_exe):
                py_exe = sys.executable

            # ── Write the .bat launcher ──────────────────────────
            try:
                with open(bat, "w", encoding="utf-8") as bf:
                    bf.write("@echo off\r\n")
                    bf.write(f"title COT {label}\r\n")
                    bf.write(f'"{py_exe}" "{runner}"\r\n')
                    bf.write("pause\r\n")
            except Exception as e:
                messagebox.showerror("Error", f"Could not write bat file:\n{e}")
                return

            try:
                # Withdraw Admin window briefly so it cannot steal focus
                # back from the terminal as it opens. Restore after 1.5s.
                self.withdraw()
                os.startfile(bat)
                self._append_log(
                    f"{label} opened in a new terminal window.\n"
                    f"Changes to cot_config.json take effect on next launch.\n",
                    "info"
                )
                self.after(1500, self._restore)
            except Exception as e:
                self.deiconify()
                _log(f"os.startfile failed: {e}")
                messagebox.showerror("Launch Error",
                                     f"Failed to open terminal:\n{e}\n\n"
                                     f"Try running manually:\n{bat}")
        else:
            for term in ["x-terminal-emulator", "gnome-terminal", "xterm"]:
                try:
                    self.withdraw()
                    subprocess.Popen([term, "--", sys.executable, runner],
                                     cwd=LAUNCHER_DIR)
                    self._append_log(f"{label} opened in terminal.\n", "info")
                    self.after(1500, self._restore)
                    break
                except FileNotFoundError:
                    continue
            else:
                messagebox.showerror("No terminal",
                                     f"Run manually:\n  python {runner}")

    def _restore(self):
        """Restore Admin window after terminal has had time to take focus."""
        try:
            self.deiconify()
            self.lift()
        except Exception:
            pass
    # ── Read-only checks: capture output and show in log ─────────

    def _run_check(self, check: str):
        """Run a cot_config check function and capture its output into the log."""
        import io
        from contextlib import redirect_stdout

        self._append_log(f"--- {check.upper()} ---\n", "header")

        # Build a tiny script that runs the check and prints results
        check_calls = {
            "deps":   "cfg.check_dependencies()",
            "auth":   "cfg.check_auth()",
            "llm":    "cfg.check_lmstudio()",
            "config": "cfg.show_config()",
        }
        fn_call = check_calls.get(check, "")
        if not fn_call:
            return

        runner = os.path.join(LAUNCHER_DIR, "_check_runner.py")
        script = (
            f"import sys, io, json\n"
            # Force UTF-8 stdout so Unicode chars (checkmark, cross etc) don't crash on cp1252
            f"sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')\n"
            f"sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')\n"
            f"sys.path.insert(0, r'{LAUNCHER_DIR}')\n"
            f"import cot_config as cfg\n"
            f"cfg.load()\n"
            f"import contextlib\n"
            f"buf = io.StringIO()\n"
            f"with contextlib.redirect_stdout(buf):\n"
            f"    {fn_call}\n"
            f"sys.stdout.buffer.write(buf.getvalue().encode('utf-8', errors='replace'))\n"
            f"sys.stdout.buffer.flush()\n"
        )

        try:
            with open(runner, "w", encoding="utf-8") as f:
                f.write(script)
        except Exception as e:
            self._append_log(f"Could not write check script: {e}\n", "error")
            return

        check_env = os.environ.copy()
        check_env["PYTHONUTF8"] = "1"        # force UTF-8 mode on Windows
        check_env["PYTHONIOENCODING"] = "utf-8"

        try:
            result = subprocess.run(
                [sys.executable, runner],
                cwd=LAUNCHER_DIR,
                capture_output=True,
                env=check_env,
                timeout=15,
                creationflags=CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )
            output = result.stdout.decode("utf-8", errors="replace") if result.stdout else ""
            errors = result.stderr.decode("utf-8", errors="replace") if result.stderr else ""
            if output.strip():
                self._append_log(output, "normal")
            if errors.strip():
                self._append_log(errors, "error")
            if not output.strip() and not errors.strip():
                self._append_log("(no output)\n", "info")
        except subprocess.TimeoutExpired:
            self._append_log("Check timed out (15s).\n", "error")
        except Exception as e:
            self._append_log(f"Check failed: {e}\n", "error")

    # ── Log helpers ───────────────────────────────────────────────

    def _append_log(self, msg: str, kind: str = "normal"):
        colors = {
            "error":  "#F44336",
            "info":   "#9E9E9E",
            "header": "#4FC3F7",
            "normal": "",
        }
        self._log_box.configure(state="normal")
        color = colors.get(kind, "")
        if color:
            tag = f"tag_{kind}"
            self._log_box.tag_config(tag, foreground=color)
            self._log_box.insert("end", msg, tag)
        else:
            self._log_box.insert("end", msg)
        self._log_box.configure(state="disabled")
        self._log_box.see("end")

    def _clear_log(self):
        self._log_box.configure(state="normal")
        self._log_box.delete("1.0", "end")
        self._log_box.configure(state="disabled")


# ── Main launcher ─────────────────────────────────────────────

class MasterLauncher(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("COT YouTube Movie Creator Suite (Video and Audio Tools)")
        self.geometry("900x560")
        self.minsize(700, 440)
        self._build_ui()
        _focus_window(self)
        _start_single_instance_server(self)

        # Open settings on first run if paths not configured
        if not _mcfg.get("audio_suite_path") or not _mcfg.get("images_path"):
            self.after(500, lambda: SettingsWindow(self, on_save=self._refresh_cards))

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header
        hdr = ctk.CTkFrame(self, height=54, corner_radius=0)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(hdr, text="COT YouTube Movie Creator Suite",
                     font=ctk.CTkFont(size=18, weight="bold")
                     ).grid(row=0, column=0, sticky="w", padx=20, pady=14)
        ctk.CTkLabel(hdr, text="Video and Audio Tools",
                     font=ctk.CTkFont(size=11), text_color="gray"
                     ).grid(row=0, column=1, sticky="w", padx=6, pady=14)
        ctk.CTkButton(hdr, text="Admin", width=75, height=30,
                      fg_color="transparent", border_width=1,
                      command=self._open_admin
                      ).grid(row=0, column=2, padx=(0, 6), pady=12, sticky="e")
        ctk.CTkButton(hdr, text="Settings", width=85, height=30,
                      command=self._open_settings
                      ).grid(row=0, column=3, padx=(0, 12), pady=12, sticky="e")

        # Two-column body
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew", padx=12, pady=10)
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(body, text="VIDEO TOOLS",
                     font=ctk.CTkFont(size=11, weight="bold"), anchor="w"
                     ).grid(row=0, column=0, sticky="w", padx=4, pady=(0, 4))
        ctk.CTkLabel(body, text="AUDIO PREP SUITE",
                     font=ctk.CTkFont(size=11, weight="bold"), anchor="w"
                     ).grid(row=0, column=1, sticky="w", padx=4, pady=(0, 4))

        self.v_frame = ctk.CTkScrollableFrame(body, fg_color="transparent")
        self.v_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 6))

        self.a_frame = ctk.CTkScrollableFrame(body, fg_color="transparent")
        self.a_frame.grid(row=1, column=1, sticky="nsew", padx=(6, 0))

        # Footer
        ctk.CTkLabel(self, text="github.com/kchorst/youtube-movie-creator-toolkit",
                     font=ctk.CTkFont(size=10), text_color="gray"
                     ).grid(row=2, column=0, pady=(0, 8))

        self._refresh_cards()

    def _refresh_cards(self):
        for w in self.v_frame.winfo_children():
            w.destroy()
        for w in self.a_frame.winfo_children():
            w.destroy()

        for label, fname, desc, mode in COT_TOOLS:
            _make_card(self.v_frame, label, desc,
                       lambda f=fname, m=mode: self._launch_cot(f, m))

        audio_root = _mcfg.get("audio_suite_path", "")
        if audio_root and os.path.isdir(audio_root):
            for label, rel_path, desc in AUDIO_TOOLS:
                _make_card(self.a_frame, label, desc,
                           lambda p=rel_path: self._launch_audio(p))
        else:
            ctk.CTkLabel(self.a_frame,
                         text=(
                             "Audio Prep Suite is optional and not included in this repo.\n\n"
                             "To enable audio tools:\n"
                             "1) Install/clone the Audio Prep Suite repo\n"
                             "2) Settings → set 'Audio Prep Suite' folder path\n"
                         ),
                         text_color="gray", justify="left"
                         ).pack(pady=30, padx=12)

    # ── Launch handlers ──────────────────────────────────────────

    def _launch_cot(self, filename: str, mode: str):
        """
        Launch a COT tool.
        mode='cli'  -> CREATE_NEW_CONSOLE (user needs to interact in terminal)
        mode='gui'  -> CREATE_NO_WINDOW   (suppress console, GUI only)
        """
        # Look in cot_gui/ first, then directly in LAUNCHER_DIR
        candidates = [
            os.path.join(LAUNCHER_DIR, "cot_gui", filename),
            os.path.join(LAUNCHER_DIR, filename),
        ]
        target = next((p for p in candidates if os.path.isfile(p)), None)

        if not target:
            expected = os.path.join(LAUNCHER_DIR, "cot_gui", filename)
            messagebox.showerror(
                "Script not found",
                f"Could not find:  {filename}\n\n"
                f"Expected location:\n{expected}\n\n"
                f"Make sure the cot_gui folder is in:\n{LAUNCHER_DIR}"
            )
            _log(f"Launch failed: {filename} not found in {LAUNCHER_DIR}")
            return

        env = os.environ.copy()
        env["COT_SCRIPTS_DIR"] = LAUNCHER_DIR
        env["PYTHONPATH"] = LAUNCHER_DIR
        env["PYTHONUTF8"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"

        flags = CREATE_NEW_CONSOLE if mode == "cli" else CREATE_NO_WINDOW

        # For GUI tools, capture stderr to a log file so we can diagnose crashes
        stderr_log = os.path.join(LAUNCHER_DIR, "child_stderr.log")

        try:
            if mode == "cli":
                # CLI tool — open in a new console window and keep it open
                if sys.platform == "win32":
                    # Use cmd.exe /K to keep the window open after script finishes
                    command = ["cmd.exe", "/K", sys.executable, target]
                    proc = subprocess.Popen(command, cwd=LAUNCHER_DIR, env=env)
                else:
                    # For non-Windows, use previous behavior (or improve if needed for specific terminals)
                    proc = subprocess.Popen(
                        [sys.executable, target],
                        cwd=LAUNCHER_DIR,
                        env=env,
                        **({"start_new_session": True} if sys.platform != "win32" else {}),
                    )
            else:
                # GUI tool — capture stderr so crashes are visible in log
                stderr_f = open(stderr_log, "w", encoding="utf-8")
                proc = subprocess.Popen(
                    [sys.executable, target],
                    cwd=LAUNCHER_DIR,
                    env=env,
                    stderr=stderr_f,
                    creationflags=CREATE_NO_WINDOW if sys.platform == "win32" else 0,
                    **({"start_new_session": True} if sys.platform != "win32" else {}),
                )
                stderr_f.close()

            _log(f"Launched {mode.upper()} tool: {target} (pid {proc.pid})")

            # Minimize the launcher so the new tool can get focus
            self.iconify()

            if mode == "gui":
                # Check for quick exit (crash) and show error if so
                self.after(2000, lambda p=proc, t=target: self._check_exit(p, t))

        except Exception as e:
            _log(f"Popen failed: {target}: {e}")
            messagebox.showerror("Launch Error", f"Failed to start:\n{filename}\n\n{e}")

    def _check_exit(self, proc, target):
        """If a GUI tool exited within 2s, read stderr and show the error."""
        ret = proc.poll()
        if ret is not None and ret != 0:
            stderr_log = os.path.join(LAUNCHER_DIR, "child_stderr.log")
            err = ""
            try:
                err = open(stderr_log, encoding="utf-8", errors="replace").read().strip()
            except Exception:
                pass
            _log(f"Tool crashed (exit {ret}): {target}\n{err}")
            if err:
                # Show last 20 lines — most relevant part
                lines = err.strip().splitlines()
                snippet = "\n".join(lines[-20:])
                messagebox.showerror(
                    "Tool crashed",
                    f"{os.path.basename(target)} exited with error:\n\n{snippet}"
                )

    def _launch_audio(self, rel_path: str):
        audio_root = _mcfg.get("audio_suite_path", "")
        if not audio_root:
            messagebox.showerror(
                "Audio tools not configured",
                "Audio Prep Suite is optional and installed separately.\n\n"
                "To enable audio tools:\n"
                "1) Install/clone the Audio Prep Suite repo\n"
                "2) Settings → set the Audio Prep Suite folder path\n",
            )
            return
        target = os.path.join(audio_root, rel_path)
        if not os.path.isfile(target):
            messagebox.showerror("Not found", f"Script not found:\n{target}")
            return

        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        try:
            subprocess.Popen(
                [sys.executable, target],
                cwd=audio_root,
                env=env,
                creationflags=CREATE_NO_WINDOW if sys.platform == "win32" else 0,
                **({"start_new_session": True} if sys.platform != "win32" else {}),
            )
            _log(f"Launched audio tool: {target}")
        except Exception as e:
            _log(f"Audio Popen failed: {target}: {e}")
            messagebox.showerror("Launch Error", f"Failed to start:\n{rel_path}\n\n{e}")

    # ── Admin ────────────────────────────────────────────────────

    def _open_admin(self):
        win = AdminWindow(self)
        _focus_window(win)

    # ── Settings ─────────────────────────────────────────────────

    def _open_settings(self):
        win = SettingsWindow(self, on_save=self._refresh_cards)
        _focus_window(win)


if __name__ == "__main__":
    try:
        if _send_show_to_existing_instance():
            raise SystemExit(0)

        ctk.set_appearance_mode(_mcfg.get("theme", "system"))
        ctk.set_default_color_theme(_mcfg.get("accent", "blue"))
        app = MasterLauncher()
        app.mainloop()
    except Exception as e:
        _log(f"FATAL: {e}\n{traceback.format_exc()}")
        try:
            messagebox.showerror("Fatal Error", f"{e}\n\nSee launcher_log.txt")
        except Exception:
            print("Fatal:", e)
