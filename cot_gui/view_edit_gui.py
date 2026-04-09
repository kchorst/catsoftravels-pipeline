"""
cot_gui/view_edit_gui.py
View & Edit Live YouTube Metadata — GUI wrapper around youtube_meta.mode_review_live()
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
from cot_gui.cot_base_gui import CotBaseWindow
from tkinter import messagebox

try:
    import cot_config as cfg
    cfg.load(gui_mode=True)
    HAS_CONFIG = True
except ImportError:
    HAS_CONFIG = False


class ViewEditGui(CotBaseWindow):
    def __init__(self):
        super().__init__(
            title="View & Edit Live",
            subtitle="Search and edit published YouTube video metadata",
            width=680, height=580,
        )
        self._build_options()
        self._build_action_buttons()

    def _build_options(self):
        ctk.CTkLabel(
            self.options_frame, text="Live Metadata Editor",
            font=ctk.CTkFont(size=12, weight="bold"), anchor="w"
        ).grid(row=0, column=0, sticky="w", padx=12, pady=(10, 4))

        ctk.CTkLabel(
            self.options_frame,
            text="Fetches your live YouTube videos and lets you search, edit titles,\n"
                 "descriptions, tags, and privacy settings — then pushes changes to YouTube.\n"
                 "Bulk description: H=prepend heading, F=append footer. Delete: type DEL in the session menu (disabled when Dry Run is ON).",
            font=ctk.CTkFont(size=11), text_color="gray", anchor="w", justify="left"
        ).grid(row=1, column=0, sticky="w", padx=12, pady=(0, 10))

    def _build_action_buttons(self):
        self.launch_btn = ctk.CTkButton(
            self.buttons_frame, text="Open Review and Edit Session",
            command=self._run,
            font=ctk.CTkFont(size=13, weight="bold"), height=38,
        )
        self.launch_btn.grid(row=0, column=0, padx=(0, 6), pady=8, sticky="ew")

        ctk.CTkButton(
            self.buttons_frame, text="Clear Log",
            fg_color="transparent", border_width=1,
            command=self.clear_log,
        ).grid(row=0, column=2, padx=(6, 0), pady=8, sticky="ew")

    def _run(self):
        """Open the interactive Mode R session in a real terminal window."""
        meta_path = os.path.join(SCRIPTS_DIR, "youtube_meta.py")
        if not os.path.isfile(meta_path):
            messagebox.showerror(
                "Not found",
                f"youtube_meta.py not found in:\n{SCRIPTS_DIR}",
            )
            return

        runner = os.path.join(SCRIPTS_DIR, "_view_edit_runner.py")
        try:
            with open(runner, "w", encoding="utf-8") as f:
                f.write("import sys, os, traceback\n")
                f.write(f"sys.path.insert(0, r'{SCRIPTS_DIR}')\n")
                f.write(f"os.chdir(r'{SCRIPTS_DIR}')\n")
                f.write("os.environ.setdefault('COT_FORCE_IPV4', '1')\n")
                f.write("print('View & Edit Live runner starting...')\n")
                f.write("print('  python:', sys.executable)\n")
                f.write("print('  cwd   :', os.getcwd())\n")
                f.write("sys.stdout.flush()\n")
                f.write("try:\n")
                f.write("    print('Importing youtube_meta...')\n")
                f.write("    sys.stdout.flush()\n")
                f.write("    import youtube_meta\n")
                f.write("    print('Entering youtube_meta.mode_review_live()...')\n")
                f.write("    sys.stdout.flush()\n")
                f.write("    youtube_meta.mode_review_live()\n")
                f.write("except Exception:\n")
                f.write("    print('\\nERROR: View & Edit Live crashed.')\n")
                f.write("    traceback.print_exc()\n")
                f.write("finally:\n")
                f.write("    try:\n")
                f.write("        input('\\nDone. Press Enter to close...')\n")
                f.write("    except Exception:\n")
                f.write("        pass\n")
        except Exception as e:
            messagebox.showerror("Error", f"Could not write runner:\n{e}")
            return

        bat = os.path.join(SCRIPTS_DIR, "_view_edit_launcher.bat")
        py_exe = sys.executable.replace("pythonw.exe", "python.exe")
        try:
            with open(bat, "w", encoding="utf-8") as f:
                f.write("@echo off\r\n")
                f.write("title View & Edit Live\r\n")
                f.write(f'"{py_exe}" "{runner}"\r\n')
                f.write("pause\r\n")
        except Exception as e:
            messagebox.showerror("Error", f"Could not write bat file:\n{e}")
            return

        self.clear_log()
        self.set_status("Opened in terminal")
        self.log("Launching View & Edit Live in a terminal window...", "info")
        try:
            if sys.platform == "win32":
                subprocess.Popen(
                    [py_exe, "-u", runner],
                    creationflags=subprocess.CREATE_NEW_CONSOLE,
                    cwd=SCRIPTS_DIR,
                )
            else:
                os.startfile(bat)
        except Exception as e:
            messagebox.showerror("Launch Error", f"Failed to open terminal:\n{e}")
            return

    def _finish(self):
        self.hide_progress()
        self.launch_btn.configure(state="normal")
        self.set_status("Done")


if __name__ == "__main__":
    app = ViewEditGui()
    app.mainloop()
