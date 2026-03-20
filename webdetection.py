#!/usr/bin/env python3
# ===========================================================
#           KOOKIEEYY'S SPACE — GUI TERMINAL (Python)
# ===========================================================

import tkinter as tk
from tkinter import ttk, scrolledtext, simpledialog, messagebox
import subprocess
import threading

# ================== THEMES ==================
THEMES = {
    'Light': {
        'bg': '#f0f0f0',
        'text_bg': '#ffffff',
        'button_bg': '#1A7F3B',
        'accent': '#0D47A1',
        'text': '#333333',
        'sidebar_bg': '#e0e0e0',
        'frame_bg': '#ffffff',
        'button_hover': '#145C2B',
        'success_bg': '#c8e6c9',
        'success_fg': '#1b5e20',
        'error_bg': '#ffcdd2',
        'error_fg': '#b71c1c'
    },
    'Dark': {
        'bg': '#2d2d2d',
        'text_bg': '#1e1e1e',
        'button_bg': '#1E90FF',
        'accent': '#0A3D7A',
        'text': '#e0e0e0',
        'sidebar_bg': '#252526',
        'frame_bg': '#333333',
        'button_hover': '#1C86EE',
        'success_bg': '#4CAF50',
        'success_fg': '#ffffff',
        'error_bg': '#f44336',
        'error_fg': '#ffffff'
    },
    'Solarized': {
        'bg': '#fdf6e3',
        'text_bg': '#eee8d5',
        'button_bg': '#268bd2',
        'accent': '#b58900',
        'text': '#586e75',
        'sidebar_bg': '#eee8d5',
        'frame_bg': '#fdf6e3',
        'button_hover': '#2A8E43',
        'success_bg': '#859900',
        'success_fg': '#fdf6e3',
        'error_bg': '#dc322f',
        'error_fg': '#fdf6e3'
    },
    'Dracula': {
        'bg': '#282a36',
        'text_bg': '#44475a',
        'button_bg': '#3DC55D',
        'accent': '#bd93f9',
        'text': '#f8f8f2',
        'sidebar_bg': '#21222C',
        'frame_bg': '#343746',
        'button_hover': '#2A8E43',
        'success_bg': '#50fa7b',
        'success_fg': '#282a36',
        'error_bg': '#ff5555',
        'error_fg': '#282a36'
    }
}

current_theme = "Light"

# ================== STATUS BAR ==================
def update_status(message, msg_type="info"):
    t = THEMES[current_theme]
    status_var.set(message)
    if msg_type == "success":
        status_bar.config(bg=t.get("success_bg", t['accent']), fg=t.get("success_fg", "white"))
    elif msg_type == "error":
        status_bar.config(bg=t.get("error_bg", t['accent']), fg=t.get("error_fg", "white"))
    else:
        status_bar.config(bg=t['accent'], fg='white')

# ================== THEME APPLY ==================
def apply_theme(theme_name):
    global current_theme
    current_theme = theme_name
    t = THEMES[theme_name]
    root.configure(bg=t['bg'])
    sidebar.configure(style=f"{theme_name}.TFrame")
    main_frame.configure(style=f"{theme_name}.TFrame")
    status_bar.config(bg=t['accent'], fg='white')

    # Apply theme only to ttk buttons, not tk.Button
    for btn in tool_buttons + list(theme_buttons.values()):
        btn.configure(style=f"{theme_name}.TButton")


# ================== POPUP OUTPUT ==================
def show_output_popup(title, content):
    t = THEMES[current_theme]
    popup = tk.Toplevel(root)
    popup.title(title)
    popup.geometry("900x600")
    popup.configure(bg=t['frame_bg'])

    text_area = scrolledtext.ScrolledText(popup, font=("Consolas", 11),
                                          bg=t['text_bg'], fg=t['text'])
    text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    text_area.insert(tk.END, content)
    text_area.configure(state='disabled')

    # Close button
    close_btn = ttk.Button(popup, text="Close", command=popup.destroy,
                           style=f"{current_theme}.TButton")
    close_btn.pack(pady=5)

# ================== HELP/ABOUT POPUPS ==================
def show_help():
    help_text = (
        "KOOKIEEYY'S SPACE - Help\n\n"
        "1. Select a theme from the sidebar.\n"
        "2. Click a tool button to run it.\n"
        "3. Outputs appear in a popup window.\n"
        "4. Status bar shows execution info.\n"
        "5. Close popups when done.\n\n"
        "Tools include network scans, system info, and web reconnaissance."
    )
    show_output_popup("Help", help_text)

def show_about():
    about_text = (
        "KOOKIEEYY'S SPACE - About\n\n"
        "Version: 1.0\n"
        "Author: Bhavya Sehgal\n"
        "Purpose: GUI terminal for Kali Linux tools.\n"
        "Supports multiple themes including Light, Dark, Solarized, and Dracula.\n\n"
        "Operations and their descriptions:\n\n"
        "1. System Info - 'uname -a': Shows system information like OS, kernel version, hostname.\n"
        "2. Disk Usage Monitor - 'df -h': Displays free and used disk space in a human-readable format.\n"
        "3. IP Configuration - 'ip a': Shows all IP addresses, interfaces, and network configuration.\n"
        "4. ARP Scan - 'arp-scan --localnet': Scans local network to find all connected devices.\n"
        "5. Local Port Monitor - 'ss -tulnp': Displays active listening ports and the associated processes.\n"
        "6. MAC Address Viewer - 'ip link': Lists all network interfaces with their MAC addresses.\n"
        "7. Ping Host - 'ping -c 4 <target>': Sends ICMP packets to a host to check connectivity.\n"
        "   Example: ping -c 4 8.8.8.8\n"
        "8. Network Discovery - 'nmap -sn <subnet>': Scans subnet for live hosts without port scanning.\n"
        "9. Nmap Basic Scan - 'nmap <target>': Performs a simple port scan to find open ports.\n"
        "10. Nmap Intense Scan - 'nmap -A -T4 <target>': Performs aggressive scan with OS detection, scripts, and traceroute.\n"
        "11. Traceroute - 'traceroute <target>': Shows the path packets take to reach the target host.\n"
        "12. Whois Recon - 'whois <domain>': Retrieves domain registration info like owner, registrar, dates.\n"
        "13. DNS Enumeration - 'dig <domain> ANY': Fetches DNS records for a domain.\n"
        "14. Vulnerability Assessment - 'nmap --script vuln <target>': Runs vulnerability scripts on the target.\n"
        "15. Website Technology Scan - 'whatweb <website>': Detects CMS, server, plugins, and other tech of a website.\n"
        "16. SQL Injection Test - 'sqlmap -u <URL>': Checks a URL parameter for SQL injection vulnerability.\n"
        "\nAll tools run on Kali Linux and outputs are shown in a popup window for easy reading."
    )
    show_output_popup("About", about_text)


# ================== TOOL RUNNER ==================
def run_command(title, cmd_template, ask_input=False, input_label="Enter target:"):
    def execute():
        target = ""
        if ask_input:
            target = simpledialog.askstring(title, input_label)
            if not target:
                update_status("Cancelled", "error")
                return
            cmd = cmd_template.format(target=target)
        else:
            cmd = cmd_template

        update_status(f"Running {title}...", "info")

        def task():
            try:
                res = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, text=True)
                show_output_popup(title, res)
                update_status(f"{title} completed successfully", "success")
            except subprocess.CalledProcessError as e:
                show_output_popup(title, e.output)
                update_status(f"{title} failed", "error")

        threading.Thread(target=task, daemon=True).start()
    execute()

# ================== GUI SETUP ==================
root = tk.Tk()
root.title("KOOKIEEYY'S SPACE")
root.geometry("1100x700")

style = ttk.Style()
style.configure(".", font=("Segoe UI", 10))
for name, t in THEMES.items():
    style.configure(f"{name}.TFrame", background=t['bg'])
    style.configure(f"{name}.TButton", background=t['button_bg'], foreground="#000",
                    padding=8, font=("Segoe UI", 10, "bold"))
    style.map(f"{name}.TButton", background=[("active", t['button_hover'])])
    style.configure(f"{name}.TLabel", background=t['bg'], foreground=t['text'])

# ================== LAYOUT ==================
container = ttk.Frame(root)
container.pack(fill=tk.BOTH, expand=True)

sidebar = ttk.Frame(container, width=180)
sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

main_frame = ttk.Frame(container)
main_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

# ================== SIDEBAR ==================
ttk.Label(sidebar, text="Themes", font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=10, pady=(10,5))
theme_buttons = {}
for theme in THEMES:
    btn = ttk.Button(sidebar, text=theme, command=lambda t=theme: apply_theme(t))
    btn.pack(fill=tk.X, padx=10, pady=2)
    theme_buttons[theme] = btn

# Separator before Help/About
ttk.Separator(sidebar, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=5, pady=15)

# Help & About buttons at the bottom
help_btn = tk.Button(sidebar, text="Help", bg="#FFA500", fg="white", font=("Segoe UI", 10, "bold"), command=show_help)
help_btn.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(5,5))

about_btn = tk.Button(sidebar, text="About", bg="#FF4500", fg="white", font=("Segoe UI", 10, "bold"), command=show_about)
about_btn.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(5,5))



# ================== TOOL BUTTONS ==================
tools = [
    ("System Info", "uname -a", False),
    ("Disk Usage Monitor", "df -h", False),
    ("IP Configuration", "ip a", False),
    ("ARP Scan", "arp-scan --localnet", False),
    ("Local Port Monitor", "ss -tulnp", False),
    ("MAC Address Viewer", "ip link", False),
    ("Ping Host", "ping -c 4 {target}", True, "Enter IP/Domain:"),
    ("Network Discovery", "nmap -sn {target}", True, "Enter Subnet (192.168.1.0/24):"),
    ("Nmap Basic Scan", "nmap {target}", True, "Enter Target:"),
    ("Nmap Intense Scan", "nmap -A -T4 {target}", True, "Enter Target:"),
    ("Traceroute", "traceroute {target}", True, "Enter Target:"),
    ("Whois Recon", "whois {target}", True, "Enter Domain:"),
    ("DNS Enumeration", "dig {target} ANY", True, "Enter Domain:"),
    ("Vulnerability Assessment", "nmap --script vuln {target}", True, "Enter Target:"),
    ("Website Technology Scan", "whatweb http://{target}", True, "Enter Website URL:"),
    ("SQL Injection Test", "sqlmap -u {target} --batch --level=1 --risk=1", True, "Enter URL with parameter:")
]

tool_buttons = []

ttk.Label(main_frame, text="Kali Linux Tools", font=("Segoe UI", 16, "bold")).pack(pady=15)
grid = ttk.Frame(main_frame)
grid.pack()

r = c = 0
for name, cmd, ask_input, *extra in tools:
    label = extra[0] if extra else "Enter target:"
    btn = ttk.Button(grid, text=name, width=30,
                     command=lambda n=name, ccmd=cmd, ai=ask_input, l=label: run_command(n, ccmd, ai, l))
    btn.grid(row=r, column=c, padx=10, pady=10)
    tool_buttons.append(btn)
    c += 1
    if c == 2:
        c = 0
        r += 1

# ================== STATUS BAR ==================
status_var = tk.StringVar()
status_var.set("Ready")
status_bar = tk.Label(root, textvariable=status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W,
                      bg=THEMES[current_theme]['accent'], fg="white", font=("Segoe UI", 9))
status_bar.pack(side=tk.BOTTOM, fill=tk.X)

apply_theme(current_theme)
update_status("Ready. Click a tool to execute.", "info")
root.mainloop()
