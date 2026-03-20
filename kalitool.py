#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import os
import sys

# Paths to your scripts (update these paths as needed)
WEBDETECTION_SCRIPT = "webdetection.py"
DECODER_SCRIPT = "decoder.py"
STEGHIDE_SCRIPT = "steghide_gui.py"

def run_script(script_path):
    if not os.path.exists(script_path):
        messagebox.showerror("Error", f"Script not found:\n{script_path}")
        return
    # Run script in a new Python process
    try:
        subprocess.Popen([sys.executable, script_path])
    except Exception as e:
        messagebox.showerror("Error", f"Failed to run script:\n{e}")

# ----------------- GUI -----------------
root = tk.Tk()
root.title("Kali Tools Dashboard")
root.geometry("400x300")
root.resizable(False, False)

style = ttk.Style()
style.configure("TButton", font=("Segoe UI", 12), padding=10)

ttk.Label(root, text="Kali Linux Tools Dashboard", font=("Segoe UI", 16, "bold")).pack(pady=20)

# Buttons
btn_web = ttk.Button(root, text="Web Detection", width=25, command=lambda: run_script(WEBDETECTION_SCRIPT))
btn_web.pack(pady=10)

btn_decoder = ttk.Button(root, text="Decoder", width=25, command=lambda: run_script(DECODER_SCRIPT))
btn_decoder.pack(pady=10)

btn_steghide = ttk.Button(root, text="Steghide GUI", width=25, command=lambda: run_script(STEGHIDE_SCRIPT))
btn_steghide.pack(pady=10)

# Exit button
ttk.Button(root, text="Exit", width=25, command=root.destroy).pack(pady=20)

root.mainloop()
