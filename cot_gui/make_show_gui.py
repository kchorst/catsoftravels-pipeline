"""
cot_gui/make_show_gui.py
Make Show — GUI wrapper around make_show.py

Modes A, C, D are interactive (need terminal input) — launched in a
real console window via the launcher's CLI mechanism.
Mode B (Batch silent) needs no input and runs fully in the GUI thread.
"""

import os
import sys
import threading
import subprocess

SCRIPTS_DIR = os.environ.get(
    "COT_SCRIPTS_DIR",
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.insert(0, SCRIPTS_DIR)

import customtkinter as ctk
from tkinter import filedialog, messagebox
from cot_gui.cot_base_gui import CotBaseWindow

try:
    import cot_config as cfg
    cfg.load(gui_mode=True)
    HAS_CONFIG = True
except ImportError:
    HAS_CONFIG = False

# Windows process flags
CREATE_NEW_CONSOLE = 0x00000010
CREATE_NO_WINDOW   = 0x08000000


class MakeShowGui(CotBaseWindow):
    def __init__(self):
        super().__init__(
            title="Make Show",
            subtitle="Render beat-synced slideshow videos",
            width=700, height=580,
        )
        self._pause_event = threading.Event()
        self._stop_event = threading.Event()
        self._build_options()
        self._build_action_buttons()

    def _build_options(self):
        ctk.CTkLabel(
            self.options_frame, text="Video Settings",
            font=ctk.CTkFont(size=12, weight="bold"), anchor="w"
        ).grid(row=0, column=0, columnspan=4, sticky="w", padx=12, pady=(10, 6))

        # BPM
        ctk.CTkLabel(self.options_frame, text="BPM:", anchor="w"
                     ).grid(row=1, column=0, sticky="w", padx=12, pady=6)

        self._bpm_var = ctk.StringVar(value="120")
        ctk.CTkOptionMenu(
            self.options_frame,
            values=["60", "90", "120", "150", "180", "Custom"],
            variable=self._bpm_var,
            command=self._on_bpm_select,
            width=120,
        ).grid(row=1, column=1, sticky="w", padx=8, pady=6)

        self._custom_bpm = ctk.CTkEntry(self.options_frame, width=80,
                                         placeholder_text="e.g. 128")
        self._custom_bpm.grid(row=1, column=2, padx=8, pady=6)
        self._custom_bpm.grid_remove()

        ctk.CTkLabel(self.options_frame,
                     text="Multiples of 30 give perfect frame-exact sync.",
                     font=ctk.CTkFont(size=10), text_color="gray"
                     ).grid(row=1, column=3, sticky="w", padx=4, pady=6)

        # Pictures folder
        ctk.CTkLabel(self.options_frame, text="Pictures folder:", anchor="w"
                     ).grid(row=2, column=0, sticky="w", padx=12, pady=6)
        default_root = cfg.get("PICTURES_DIR", "") if HAS_CONFIG else ""
        self._root_var = ctk.StringVar(value=default_root)
        ctk.CTkEntry(self.options_frame, textvariable=self._root_var, width=280
                     ).grid(row=2, column=1, columnspan=2, sticky="w", padx=8, pady=6)
        ctk.CTkButton(self.options_frame, text="Browse", width=80,
                      command=self._browse_root
                      ).grid(row=2, column=3, padx=4, pady=6)

        # Mode
        ctk.CTkLabel(self.options_frame, text="Mode:", anchor="w"
                     ).grid(row=3, column=0, sticky="w", padx=12, pady=6)
        self._mode_var = ctk.StringVar(value="B — Batch silent (no audio, automatic)")
        ctk.CTkOptionMenu(
            self.options_frame,
            values=[
                "A — Normal (folder by folder, interactive)",
                "B — Batch silent (no audio, automatic)",
                "C — Batch audio (one audio track, interactive)",
                "D — Add audio to existing movies (interactive)",
            ],
            variable=self._mode_var,
            width=340,
        ).grid(row=3, column=1, columnspan=3, sticky="w", padx=8, pady=(6, 4))

        ctk.CTkLabel(
            self.options_frame,
            text="Modes A, C, D are interactive — they open in a terminal window.",
            font=ctk.CTkFont(size=10), text_color="gray", anchor="w"
        ).grid(row=4, column=0, columnspan=4, sticky="w", padx=12, pady=(0, 10))

    def _on_bpm_select(self, value):
        if value == "Custom":
            self._custom_bpm.grid()
        else:
            self._custom_bpm.grid_remove()

    def _browse_root(self):
        folder = filedialog.askdirectory(title="Select pictures root folder")
        if folder:
            self._root_var.set(folder)

    def _build_action_buttons(self):
        self.run_btn = ctk.CTkButton(
            self.buttons_frame, text="Run Make Show",
            command=self._run,
            font=ctk.CTkFont(size=13, weight="bold"), height=38,
        )
        self.run_btn.grid(row=0, column=0, padx=(0, 6), pady=8, sticky="ew")

        self.pause_btn = ctk.CTkButton(
            self.buttons_frame,
            text="Pause",
            command=self._toggle_pause,
            state="disabled",
        )
        self.pause_btn.grid(row=0, column=1, padx=6, pady=8, sticky="ew")

        self.stop_btn = ctk.CTkButton(
            self.buttons_frame,
            text="Stop",
            command=self._stop_run,
            fg_color="#F44336",
            hover_color="#D32F2F",
            text_color="black",
            state="disabled",
        )
        self.stop_btn.grid(row=0, column=2, padx=(6, 0), pady=8, sticky="ew")

    def _toggle_pause(self):
        if self._pause_event.is_set():
            self._pause_event.clear()
            self.pause_btn.configure(text="Pause")
            self.set_status("Running...")
            self.log("Resumed.", "info")
        else:
            self._pause_event.set()
            self.pause_btn.configure(text="Resume")
            self.set_status("Paused")
            self.log("Paused.", "info")

    def _stop_run(self):
        self._stop_event.set()
        self.set_status("Stopping...")
        self.log("Stop requested...", "info")

    def _get_bpm(self):
        val = self._bpm_var.get()
        if val == "Custom":
            try:
                return int(self._custom_bpm.get())
            except ValueError:
                return None
        return int(val)

    def _run(self):
        bpm = self._get_bpm()
        if bpm is None:
            messagebox.showerror("Invalid BPM", "Enter a valid custom BPM number.")
            return

        mode_letter = self._mode_var.get()[0]
        root = self._root_var.get().strip()

        if mode_letter != "D" and (not root or not os.path.isdir(root)):
            messagebox.showerror("No Folder", "Please select a valid pictures folder.")
            return

        # Modes A, C, D are interactive — launch in terminal
        if mode_letter in ("A", "C", "D"):
            self._launch_interactive(bpm, mode_letter, root)
            return

        # Mode B — batch silent, no input() calls, runs in GUI thread
        self.clear_log()
        self.show_progress()
        self.set_status("Running batch silent render...")
        self.run_btn.configure(state="disabled")
        self.pause_btn.configure(state="normal", text="Pause")
        self.stop_btn.configure(state="normal")
        self._stop_event.clear()
        self._pause_event.clear()
        self.log(f"Mode B — Batch Silent", "info")
        self.log(f"BPM: {bpm}  |  Root: {root}", "info")
        self.log("-" * 48, "info")
        threading.Thread(target=self._run_batch_silent,
                         args=(bpm, root), daemon=True).start()

    def _launch_interactive(self, bpm, mode_letter, root):
        """Launch interactive modes (A/C/D) in a real terminal window."""
        make_show_path = os.path.join(SCRIPTS_DIR, "make_show.py")
        if not os.path.isfile(make_show_path):
            messagebox.showerror("Not found",
                                 f"make_show.py not found in:\n{SCRIPTS_DIR}")
            return

        # Write a runner that pre-sets BPM and mode
        runner = os.path.join(SCRIPTS_DIR, "_make_show_runner.py")
        mode_name = {"A": "mode_normal", "C": "mode_batch_audio",
                     "D": "mode_add_audio_existing"}.get(mode_letter, "main")

        try:
            with open(runner, "w", encoding="utf-8") as f:
                f.write("import sys, os\n")
                f.write(f"sys.path.insert(0, r'{SCRIPTS_DIR}')\n")
                f.write(f"os.chdir(r'{SCRIPTS_DIR}')\n")
                f.write("import make_show\n")
                f.write("make_show.startup_cleanup()\n")
                f.write("make_show.rotate_log()\n")
                if mode_letter == "D":
                    f.write(f"make_show.mode_add_audio_existing(2.0)\n")
                else:
                    bpm_val = bpm
                    f.write(f"bpm = {bpm_val}\n")
                    f.write(f"fps = make_show.FPS\n")
                    f.write(f"import math\n")
                    f.write(f"frames_per_image = round((60.0/bpm)*fps)\n")
                    f.write(f"frames_hold = round(2.0*fps)\n")
                    f.write(f"frames_fade = round(2.0*fps)\n")
                    f.write(f"audio_fade_sec = 2.0\n")
                    f.write(f"root = r'{root}'\n")
                    f.write(f"subfolders = make_show.get_subfolders(root)\n")
                    if mode_letter == "A":
                        f.write("make_show.mode_normal(subfolders, frames_per_image, frames_hold, frames_fade, audio_fade_sec)\n")
                    elif mode_letter == "C":
                        f.write("make_show.mode_batch_audio(subfolders, frames_per_image, frames_hold, frames_fade, audio_fade_sec)\n")
                f.write("input('\\nDone. Press Enter to close...')\n")
        except Exception as e:
            messagebox.showerror("Error", f"Could not write runner:\n{e}")
            return

        bat = os.path.join(SCRIPTS_DIR, "_make_show_launcher.bat")
        py_exe = sys.executable.replace("pythonw.exe", "python.exe")
        try:
            with open(bat, "w", encoding="utf-8") as f:
                f.write("@echo off\r\n")
                f.write(f"title Make Show — Mode {mode_letter}\r\n")
                f.write(f'"{py_exe}" "{runner}"\r\n')
                f.write("pause\r\n")
        except Exception as e:
            messagebox.showerror("Error", f"Could not write bat file:\n{e}")
            return

        self.log(f"Launching Mode {mode_letter} in terminal window...", "info")
        self.log("Interact with the terminal to proceed.", "info")

        # Withdraw this window briefly so terminal gets focus
        try:
            os.startfile(bat)
        except Exception as e:
            messagebox.showerror("Launch Error", f"Failed to open terminal:\n{e}")


    def _run_batch_silent(self, bpm, root):
        """Mode B — fully automatic, no input() calls."""
        old_stdout = sys.stdout

        import io
        class Writer(io.TextIOBase):
            def __init__(self, log_fn):
                self._log_fn = log_fn
                self._buf = ""
            def write(self, s):
                self._buf += s
                while "\n" in self._buf:
                    line, self._buf = self._buf.split("\n", 1)
                    if line.strip():
                        self._log_fn(line, "normal")
                return len(s)
            def flush(self):
                if self._buf.strip():
                    self._log_fn(self._buf, "normal")
                    self._buf = ""

        sys.stdout = Writer(self.log)
        try:
            from cot_core.make_show_core import run_batch_silent
            run_batch_silent(
                root=root,
                bpm=bpm,
                skip_done=True,
                stop_event=self._stop_event,
                pause_event=self._pause_event,
                log_cb=lambda s: self.log(s, "info"),
            )
            if self._stop_event.is_set():
                self.log("Batch silent render stopped.", "info")
            else:
                self.log("Batch silent render complete.", "success")
        except Exception as e:
            import traceback
            self.log(f"Error: {e}", "error")
            self.log(traceback.format_exc(), "error")
        finally:
            sys.stdout = old_stdout
            self.after(0, self._finish)

    def _finish(self):
        self.hide_progress()
        self.run_btn.configure(state="normal")
        self.pause_btn.configure(state="disabled", text="Pause")
        self.stop_btn.configure(state="disabled")
        self.set_status("Done")


if __name__ == "__main__":
    app = MakeShowGui()
    app.mainloop()
