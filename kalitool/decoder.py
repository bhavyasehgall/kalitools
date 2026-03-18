#!/usr/bin/env python3
# ===========================================================
#           PRO AUTO DECODER GUI — FULL MIXED LAYER
#           Fixed & Improved Version
# ===========================================================

import time
import tkinter as tk
from tkinter import scrolledtext, ttk, messagebox
import base64, binascii, string, json, os
import urllib.parse
import html
from datetime import datetime

# History configuration
HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "decoder_history.json")
HISTORY_LIMIT = 100
history = []

# Theme definitions
THEMES = {
    'Light': {
        'bg': '#f0f0f0',
        'text_bg': '#ffffff',
        'button_bg': '#1A7F3B',
        'clear_button_bg': '#8B0000',
        'accent': '#0D47A1',
        'text': '#333333',
        'sidebar_bg': '#e0e0e0',
        'frame_bg': '#ffffff',
        'highlight': '#e3f2fd',
        'button_hover': '#145C2B',
        'clear_hover': '#6B0000',
        'label_fg': '#333333',
    },
    'Dark': {
        'bg': '#2d2d2d',
        'text_bg': '#1e1e1e',
        'button_bg': '#1E90FF',
        'clear_button_bg': '#E63E3E',
        'accent': '#0A3D7A',
        'text': '#e0e0e0',
        'disabled': '#757575',
        'sidebar_bg': '#252526',
        'frame_bg': '#333333',
        'highlight': '#44475a',
        'button_hover': '#1C86EE',
        'clear_hover': '#4B0000',
        'label_fg': '#e0e0e0',
    },
    'Solarized': {
        'bg': '#fdf6e3',
        'text_bg': '#eee8d5',
        'button_bg': '#4A4A8F',
        'clear_button_bg': '#A51C1C',
        'accent': '#268bd2',
        'text': '#586e75',
        'disabled': '#93a1a1',
        'sidebar_bg': '#eee8d5',
        'frame_bg': '#fdf6e3',
        'highlight': '#b58900',
        'button_hover': '#2A8E43',
        'clear_hover': '#B83030',
        'label_fg': '#586e75',
    },
    'Dracula': {
        'bg': '#282a36',
        'text_bg': '#44475a',
        'button_bg': '#3DC55D',
        'clear_button_bg': '#E63E3E',
        'accent': '#bd93f9',
        'text': '#f8f8f2',
        'disabled': '#6272a4',
        'sidebar_bg': '#21222C',
        'frame_bg': '#343746',
        'highlight': '#44475a',
        'button_hover': '#2A8E43',
        'clear_hover': '#B83030',
        'label_fg': '#f8f8f2',
    }
}

current_theme = 'Light'

# ===========================================================
# UTILITY
# ===========================================================

def is_good_text(s):
    """Check if a string is mostly printable ASCII."""
    try:
        printable = sum(c in string.printable for c in s)
        return printable / max(len(s), 1) > 0.85
    except:
        return False


def looks_like_plain_text(s):
    """Check if input already looks like readable English."""
    common_words = [
        "the", "and", "hello", "world", "this", "that",
        "flag", "ctf", "you", "have", "are", "is", "was",
        "for", "not", "with", "from", "they", "will"
    ]
    words = s.lower().split()
    matches = sum(1 for w in words if w in common_words)
    return matches >= 1


def is_likely_encoded(s):
    """Returns True if the string is plausibly encoded (not already readable plain text)."""
    if not s:
        return False
    if any(c in '+/=\\.%&;-_' for c in s):
        return True
    clean = s.replace(' ', '').replace('\n', '')
    if all(c in '0123456789abcdefABCDEF' for c in clean) and len(clean) >= 4 and len(clean) % 2 == 0:
        return True
    if is_good_text(s) and len(s) > 20 and looks_like_plain_text(s):
        return False
    return True

ENCODING_HINT_CHARS = set('+/=.%&;-_')


def has_encoding_hints(s):
    """Returns True if string still contains characters suggesting further encoding."""
    return any(c in ENCODING_HINT_CHARS for c in s)


def decode_hex(s):
    try:
        clean = s.replace(" ", "").replace("\n", "")
        if len(clean) < 4:
            return None
        if len(clean) % 2 != 0:
            return None
        # Must be ALL hex characters
        if not all(c in '0123456789abcdefABCDEF' for c in clean):
            return None
        result = binascii.unhexlify(clean).decode('latin-1')
        # Result can be another encoded string (multi-layer) or plain text
        printable = sum(c in string.printable for c in result)
        if printable / max(len(result), 1) < 0.85:
            return None
        return result
    except:
        return None
def decode_ascii_decimal(s):
    try:
        nums = s.strip().split()
        if not nums or len(nums) < 2:
            return None
        # All tokens must be digit strings
        if not all(n.isdigit() for n in nums):
            return None
        # Reject if ALL tokens are exactly 7 or 8 chars of only 0s/1s — that's binary
        if all(len(n) in (7, 8) and set(n) <= {'0', '1'} for n in nums):
            return None
        values = [int(n) for n in nums]
        # ASCII decimal values must be in printable range
        if not all(32 <= v <= 126 for v in values):
            return None
        result = "".join(chr(v) for v in values)
        if not is_good_text(result):
            return None
        return result
    except:
        return None


def decode_binary(s):
    try:
        bits = s.strip().split()
        if not bits or len(bits) < 2:
            return None
        if not all(set(b) <= {'0', '1'} for b in bits):
            return None
        if not all(len(b) in (7, 8) for b in bits):
            return None
        # Allow mixed 7-bit and 8-bit tokens
        result = "".join(chr(int(b, 2)) for b in bits)
        return result if is_good_text(result) else None
    except:
        return None

def decode_base64(s):
    try:
        s = s.strip()
        if len(s) < 4:
            return None
        allowed = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=\n\r")
        if not set(s) <= allowed:
            return None
        # If the string looks like a pure hex string (all hex chars, even length,
        # no +/= padding chars), let the Hex decoder handle it instead
        hex_only = set("0123456789abcdefABCDEF")
        if set(s) <= hex_only and len(s) % 2 == 0:
            return None
        padding = len(s) % 4
        if padding:
            s += "=" * (4 - padding)
        decoded = base64.b64decode(s).decode("utf-8", errors="ignore")
        if decoded.strip() == s.strip():
            return None
        if not is_good_text(decoded):
            return None
        return decoded
    except:
        return None


def decode_base32(s):
    try:
        s_upper = s.upper().strip()
        if len(s_upper) < 4:
            return None
        if not set(s_upper) <= set("ABCDEFGHIJKLMNOPQRSTUVWXYZ234567="):
            return None
        if not any(c in s_upper for c in "234567="):
            return None
        padded = s_upper + "=" * ((8 - (len(s_upper) % 8)) % 8)
        decoded = base64.b32decode(padded).decode('latin-1')
        printable = sum(c in string.printable for c in decoded)
        return decoded if printable / max(len(decoded), 1) >= 0.85 else None
    except:
        return None

def decode_base58(s):
    try:
        s = s.strip()
        if not s:
            return None
        if not all(c in BASE58_CHARS for c in s):
            return None
        num = 0
        for c in s:
            num = num * 58 + BASE58_CHARS.index(c)
        byte_length = (num.bit_length() + 7) // 8
        if byte_length == 0:
            return None
        decoded_bytes = num.to_bytes(byte_length, "big")
        decoded = decoded_bytes.decode("utf-8", errors="ignore")
        if not decoded or not is_good_text(decoded):
            return None
        # Stronger printable check for Base58
        printable_ratio = sum(c in string.printable and c not in '\x00\x01\x02\x03\x04\x05\x06\x07\x08\x0b\x0c\x0e\x0f' for c in decoded) / max(len(decoded), 1)
        if printable_ratio < 0.95:
            return None
        return decoded
    except:
        return None


def decode_base85(s):
    try:
        s = s.strip()
        allowed = set(
            "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
            "!#$%&()*+-;<=>?@^_`{|}~"
        )
        if not set(s) <= allowed:
            return None
        if len(s) < 5:
            return None
        decoded = base64.a85decode(s, adobe=False, ignorechars=b"")
        text = decoded.decode("utf-8", errors="ignore")
        if not text or not is_good_text(text):
            return None
        return text
    except:
        return None


def decode_url(s):
    try:
        decoded = urllib.parse.unquote(s)
        if decoded != s:
            return decoded
    except:
        pass
    return None


def decode_html_entities(s):
    try:
        decoded = html.unescape(s)
        if decoded != s:
            return decoded
    except:
        pass
    return None


def decode_rot13(s):
    # Don't decode already readable English
    if looks_like_plain_text(s):
        return None
    letters = sum(c.isalpha() for c in s)
    if len(s) == 0 or letters / len(s) < 0.6:
        return None
    rot = str.maketrans(
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
        "NOPQRSTUVWXYZABCDEFGHIJKLMnopqrstuvwxyzabcdefghijklm"
    )
    decoded = s.translate(rot)
    if decoded.lower() == s.lower():
        return None
    # Output must actually look like English words, not just printable chars.
    # is_good_text alone is too weak — every letter-only string passes it.
    if not looks_like_plain_text(decoded):
        return None
    return decoded


def decode_rot47(s):
    if looks_like_plain_text(s):
        return None
    printable = sum(33 <= ord(c) <= 126 for c in s)
    if len(s) == 0 or printable / len(s) < 0.9:
        return None
    result = ""
    for c in s:
        o = ord(c)
        if 33 <= o <= 126:
            result += chr(33 + ((o - 33 + 47) % 94))
        else:
            result += c
    if result == s:
        return None
    if not is_good_text(result):
        return None
    # Same guard as ROT13 — output must contain actual English words
    if not looks_like_plain_text(result):
        return None
    return result


MORSE = {
    '.-': 'A', '-...': 'B', '-.-.': 'C', '-..': 'D', '.': 'E',
    '..-.': 'F', '--.': 'G', '....': 'H', '..': 'I', '.---': 'J',
    '-.-': 'K', '.-..': 'L', '--': 'M', '-.': 'N', '---': 'O',
    '.--.': 'P', '--.-': 'Q', '.-.': 'R', '...': 'S', '-': 'T',
    '..-': 'U', '...-': 'V', '.--': 'W', '-..-': 'X', '-.--': 'Y',
    '--..': 'Z', '-----': '0', '.----': '1', '..---': '2',
    '...--': '3', '....-': '4', '.....': '5', '-....': '6',
    '--...': '7', '---..': '8', '----.': '9'
}

def decode_morse(s):
    s_clean = ' '.join(s.split())
    if not set(s_clean) <= {'.', '-', ' ', '/'}:
        return None
    try:
        words = s_clean.strip().split(' / ')
        out = " ".join("".join(MORSE.get(l, "?") for l in w.split()) for w in words)
        return out if len(out) > 1 and '?' not in out else None
    except:
        return None

def decode_caesar(s):
    """Brute-force Caesar cipher — tries all 25 shifts except 13 (that is ROT13)."""
    if not s:
        return None
    # Need at least 2 words to avoid false positives on single letters/short strings
    if len(s.split()) < 2:
        return None
    # Skip if already readable plain English
    if looks_like_plain_text(s):
        return None
    common_words = [
        "the", "and", "hello", "world", "flag", "ctf",
        "you", "are", "this", "that", "from", "have",
        "there", "is", "secret", "a", "was", "not", "with",
        "for", "they", "will", "been", "has", "had", "but",
    ]
    # Skip shift 13 — ROT13 handles that case
    for shift in [n for n in range(1, 26) if n != 13]:
        result = ""
        for c in s:
            if c.isalpha():
                base = ord('A') if c.isupper() else ord('a')
                result += chr((ord(c) - base + shift) % 26 + base)
            else:
                result += c
        if sum(1 for w in result.lower().split() if w in common_words) >= 1:
            return result
    return None


def decode_octal(s):
    """Decode space-separated octal values."""
    try:
        parts = s.strip().split()
        if not parts:
            return None
        if not all(all(c in '01234567' for c in p) for p in parts):
            return None
        chars = [chr(int(p, 8)) for p in parts]
        result = "".join(chars)
        if not is_good_text(result):
            return None
        return result
    except:
        return None


def decode_base64_url(s):
    """Decode URL-safe Base64 (uses - and _ instead of + and /)."""
    try:
        s = s.strip()
        if len(s) < 2:
            return None
        if '-' not in s and '_' not in s:
            return None
        allowed = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_=")
        if not set(s) <= allowed:
            return None
        converted = s.replace('-', '+').replace('_', '/')
        padding = len(converted) % 4
        if padding:
            converted += "=" * (4 - padding)
        decoded = base64.b64decode(converted).decode("utf-8", errors="ignore")
        if decoded.strip() == s.strip():
            return None
        return decoded if is_good_text(decoded) and len(decoded.strip()) >= 1 else None
    except:
        return None



# ===========================================================
# AUTO DETECTION
# ===========================================================

DECODERS = [
    ("Morse",         decode_morse),
    ("Binary",        decode_binary),
    ("ASCII Decimal", decode_ascii_decimal),
    ("Hex",           decode_hex),
    ("Base64",        decode_base64),
    ("Base64 URL",    decode_base64_url),
    ("Base32",        decode_base32),
    ("Base58",        decode_base58),
    ("URL",           decode_url),
    ("HTML",          decode_html_entities),
    ("Caesar",        decode_caesar),
    ("ROT13",         decode_rot13),
    ("ROT47",         decode_rot47),
]


def auto_decode(s):
    """Try each decoder and return the first successful (name, result) pair."""
    if not is_likely_encoded(s):
        return None

    for name, func in DECODERS:
        try:
            result = func(s)
            if result is None:
                continue
            if result.strip() == s.strip():
                continue
            return name, result
        except:
            continue

    return None


def auto_decode_multi_layer(s, max_layers=10):
    """Recursively decode until plain clean text or no decoder matches."""
    layers = []
    current = s.strip()
    seen = set()
    start_time = time.time()

    for _ in range(max_layers):
        if time.time() - start_time > 2.5:
            break
        if current in seen:
            break
        seen.add(current)

        decoded = auto_decode(current)
        if decoded is None:
            break

        enc_type, result = decoded
        if not result:
            break

        result = result.strip()
        if result in seen:
            break

        layers.append((enc_type, result))

        # Stop only when result is readable AND free of encoding hint characters
        if looks_like_plain_text(result) and is_good_text(result) and not has_encoding_hints(result):
            break

        current = result

    return layers


# ===========================================================
# HISTORY
# ===========================================================

def load_history():
    global history
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                history = json.load(f)
        except:
            history = []
    return history


def save_history():
    try:
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Warning: Could not save history: {e}")


def add_to_history(input_text, result, enc_type):
    global history
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = {
        'timestamp': timestamp,
        'input': input_text,
        'result': result,
        'type': enc_type
    }
    history.insert(0, entry)
    if len(history) > HISTORY_LIMIT:
        history = history[:HISTORY_LIMIT]
    save_history()


# ===========================================================
# THEME HELPERS
# ===========================================================

def apply_theme(theme_name):
    global current_theme
    current_theme = theme_name
    theme = THEMES[theme_name]

    root.config(bg=theme['bg'])
    menubar.config(bg=theme['bg'], fg=theme['text'])

    for frame in [main_frame, input_frame, result_frame, button_frame, sidebar_frame]:
        try:
            frame.config(style=f"{theme_name}.TFrame")
        except:
            pass

    text_input.config(
        bg=theme['text_bg'],
        fg=theme['text'],
        insertbackground=theme['text'],
        selectbackground=theme['accent']
    )
    result_display.config(
        bg=theme['text_bg'],
        fg=theme['text'],
        insertbackground=theme['text'],
        selectbackground=theme['accent']
    )

    decode_btn.config(style=f"{theme_name}.TButton")
    clear_btn.config(style=f"{theme_name}.Clear.TButton")
    copy_btn.config(style=f"{theme_name}.TButton")

    status_bar.config(
        bg=theme['accent'],
        fg='white'
    )

    # Update sidebar labels
    for lbl in sidebar_labels:
        lbl.config(bg=theme['bg'], fg=theme['label_fg'])

    # Update theme buttons
    for name, btn in theme_buttons.items():
        if name == theme_name:
            btn.config(style=f"{theme_name}.Active.TButton")
        else:
            btn.config(style=f"{theme_name}.TButton")

    # Update text tags
    text_input.tag_configure("highlight", background=theme['highlight'])
    result_display.tag_configure("header", font=('Arial', 10, 'bold'), foreground=theme['accent'])
    result_display.tag_configure("output", font=('Consolas', 10), foreground=theme['text'])
    result_display.tag_configure("error", font=('Arial', 10), foreground='#cc0000')

    update_status(f"Theme changed to {theme_name}", "info")


# ===========================================================
# GUI ACTIONS
# ===========================================================

def decode_input(event=None):
    user_text = text_input.get("1.0", tk.END).strip()
    if not user_text:
        update_status("No input provided.", "error")
        return

    update_status("Decoding...", "info")
    root.update()

    try:
        layers = auto_decode_multi_layer(user_text)

        result_display.config(state='normal')
        result_display.delete("1.0", tk.END)

        if layers:
            for i, (enc, res) in enumerate(layers, 1):
                result_display.insert(tk.END, f"Layer {i} ({enc}):\n", "header")
                result_display.insert(tk.END, f"{res}\n\n", "output")

            result = layers[-1][1]
            enc_type = " → ".join(e for e, _ in layers)
            update_status(f"Decoded {len(layers)} layer(s): {enc_type}", "success")
            add_to_history(user_text, result, enc_type)
        else:
            result_display.insert(tk.END, "[!] Unable to decode automatically.\n\n", "error")
            result_display.insert(
                tk.END,
                "Tried: " + ", ".join(n for n, _ in DECODERS) + "\n",
                "output"
            )
            update_status("Could not decode input.", "error")

    except Exception as e:
        update_status(f"Error: {str(e)}", "error")
        messagebox.showerror("Error", f"An error occurred: {str(e)}")
    finally:
        result_display.config(state='disabled')


def clear_text(event=None):
    text_input.delete("1.0", tk.END)
    result_display.config(state='normal')
    result_display.delete("1.0", tk.END)
    result_display.config(state='disabled')
    update_status("Cleared.", "info")
    text_input.focus_set()


def copy_to_clipboard(event=None):
    content = result_display.get("1.0", tk.END).strip()
    if content:
        root.clipboard_clear()
        root.clipboard_append(content)
        update_status("Copied to clipboard.", "success")
    else:
        update_status("Nothing to copy.", "error")


def update_status(message, msg_type="info"):
    if 'status_bar' not in globals():
        return
    try:
        if not status_bar.winfo_exists():
            return
    except:
        return

    status_var.set(message)
    theme = THEMES.get(current_theme, THEMES['Light'])

    colors = {
        "error":   ('#ffcdd2', '#b71c1c'),
        "success": ('#c8e6c9', '#1b5e20'),
        "info":    (theme.get('accent', '#2196F3'), 'white'),
    }
    bg, fg = colors.get(msg_type, colors["info"])
    status_bar.config(bg=bg, fg=fg)


# ===========================================================
# HISTORY WINDOW
# ===========================================================

def show_history():
    history_window = tk.Toplevel(root)
    history_window.title("Decoding History")
    history_window.geometry("820x600")
    history_window.config(bg=THEMES[current_theme]['bg'])

    container = ttk.Frame(history_window, style=f"{current_theme}.TFrame")
    container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    tk.Label(
        container,
        text="Decoding History",
        font=('Segoe UI', 14, 'bold'),
        bg=THEMES[current_theme]['bg'],
        fg=THEMES[current_theme]['label_fg']
    ).pack(pady=(0, 10))

    frame = ttk.Frame(container, style=f"{current_theme}.TFrame")
    frame.pack(fill=tk.BOTH, expand=True)

    scrollbar = ttk.Scrollbar(frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    history_list = tk.Listbox(
        frame,
        yscrollcommand=scrollbar.set,
        font=('Segoe UI', 10),
        bg=THEMES[current_theme]['text_bg'],
        fg=THEMES[current_theme]['text'],
        selectbackground=THEMES[current_theme]['accent'],
        selectforeground='white',
        borderwidth=0,
        highlightthickness=0
    )
    history_list.pack(fill=tk.BOTH, expand=True)
    scrollbar.config(command=history_list.yview)

    if not history:
        history_list.insert(tk.END, "  (No history yet)")
    else:
        for entry in history:
            preview = f"[{entry['timestamp']}]  {entry['type']}:  {entry['input'][:60]}..."
            history_list.insert(tk.END, preview)

    def view_selected():
        selection = history_list.curselection()
        if not selection:
            messagebox.showinfo("Select Entry", "Please select a history entry first.")
            return

        idx = selection[0]
        if idx >= len(history):
            return
        entry = history[idx]

        view_window = tk.Toplevel(history_window)
        view_window.title("History Entry")
        view_window.geometry("700x520")
        view_window.config(bg=THEMES[current_theme]['bg'])

        vc = ttk.Frame(view_window, style=f"{current_theme}.TFrame")
        vc.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        info_frame = ttk.Frame(vc, style=f"{current_theme}.TFrame")
        info_frame.pack(fill=tk.X, pady=(0, 8))

        for txt in [f"Timestamp: {entry['timestamp']}", f"Encoding: {entry['type']}"]:
            tk.Label(info_frame, text=txt, font=('Segoe UI', 9),
                     bg=THEMES[current_theme]['bg'],
                     fg=THEMES[current_theme]['label_fg']).pack(anchor='w')

        tk.Label(vc, text="Input:", font=('Segoe UI', 10, 'bold'),
                 bg=THEMES[current_theme]['bg'],
                 fg=THEMES[current_theme]['label_fg']).pack(anchor='w')

        input_box = scrolledtext.ScrolledText(
            vc, height=7, font=("Consolas", 10),
            bg=THEMES[current_theme]['text_bg'],
            fg=THEMES[current_theme]['text'], wrap=tk.WORD
        )
        input_box.insert('1.0', entry['input'])
        input_box.config(state='disabled')
        input_box.pack(fill=tk.X, pady=(0, 8))

        tk.Label(vc, text="Output:", font=('Segoe UI', 10, 'bold'),
                 bg=THEMES[current_theme]['bg'],
                 fg=THEMES[current_theme]['label_fg']).pack(anchor='w')

        output_box = scrolledtext.ScrolledText(
            vc, height=10, font=("Consolas", 10),
            bg=THEMES[current_theme]['text_bg'],
            fg=THEMES[current_theme]['text'], wrap=tk.WORD
        )
        output_box.insert('1.0', entry['result'])
        output_box.config(state='disabled')
        output_box.pack(fill=tk.BOTH, expand=True)

        btn_frame = ttk.Frame(vc, style=f"{current_theme}.TFrame")
        btn_frame.pack(fill=tk.X, pady=(10, 0))

        def load_entry():
            text_input.delete('1.0', tk.END)
            text_input.insert('1.0', entry['input'])
            result_display.config(state='normal')
            result_display.delete('1.0', tk.END)
            result_display.insert('1.0', entry['result'])
            result_display.config(state='disabled')
            view_window.destroy()
            history_window.destroy()
            text_input.focus_set()
            update_status(f"Loaded entry from {entry['timestamp']}", "success")

        ttk.Button(btn_frame, text="Load This Entry", command=load_entry,
                   style=f"{current_theme}.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Close", command=view_window.destroy,
                   style=f"{current_theme}.TButton").pack(side=tk.RIGHT, padx=5)

    def clear_all_history():
        if messagebox.askyesno("Clear History", "Clear all history? This cannot be undone."):
            global history
            history = []
            save_history()
            history_list.delete(0, tk.END)
            history_list.insert(tk.END, "  (History cleared)")
            update_status("History cleared.", "info")

    btn_frame = ttk.Frame(container, style=f"{current_theme}.TFrame")
    btn_frame.pack(fill=tk.X, pady=(10, 0))

    ttk.Button(btn_frame, text="View Selected", command=view_selected,
               style=f"{current_theme}.TButton").pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_frame, text="Clear History", command=clear_all_history,
               style=f"{current_theme}.Clear.TButton").pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_frame, text="Close", command=history_window.destroy,
               style=f"{current_theme}.TButton").pack(side=tk.RIGHT, padx=5)

    history_list.bind('<Double-1>', lambda e: view_selected())


def show_about():
    about_text = (
        "PRO AUTO DECODER GUI\n"
        "Fixed & Improved Version\n\n"
        "Supported encodings:\n"
        "  Base64, Base64-URL, Base32, Base58, Base85\n"
        "  Hex, Binary, Octal, ASCII Decimal\n"
        "  URL encoding, HTML entities\n"
        "  ROT13, ROT47, Caesar cipher\n"
        "  Morse code\n\n"
        "Multi-layer decoding supported.\n\n"
        "Author: Bhavya Sehgal\n"
        "Version: 2.0.0 (Fixed)"
    )
    messagebox.showinfo("About", about_text)


# ===========================================================
# GUI SETUP
# ===========================================================

def create_gui():
    global root, text_input, result_display, status_var, status_bar
    global main_frame, input_frame, result_frame, button_frame, sidebar_frame
    global decode_btn, clear_btn, copy_btn, theme_buttons, menubar, sidebar_labels

    root = tk.Tk()
    root.title("PRO AUTO DECODER")
    root.geometry("960x700")
    root.minsize(820, 600)
    root.config(bg=THEMES[current_theme]['bg'])

    try:
        root.iconbitmap("icon.ico")
    except:
        pass

    # ---- Styles ----
    style = ttk.Style()
    style.configure('.', font=('Segoe UI', 10))

    for theme_name, theme in THEMES.items():
        style.configure(f"{theme_name}.TFrame", background=theme['bg'])

        style.configure(
            f"{theme_name}.TButton",
            padding=8, relief="raised", borderwidth=2,
            background=theme['button_bg'], foreground='#ffffff',
            font=('Segoe UI', 10, 'bold'), width=15
        )
        style.map(
            f"{theme_name}.TButton",
            background=[('active', theme.get('button_hover', theme['button_bg'])),
                        ('!disabled', theme['button_bg'])],
            foreground=[('active', '#ffffff'), ('!disabled', '#ffffff')],
            relief=[('pressed', 'sunken'), ('!pressed', 'raised')]
        )

        style.configure(
            f"{theme_name}.Clear.TButton",
            padding=8, relief="raised", borderwidth=2,
            background=theme['clear_button_bg'], foreground='#ffffff',
            font=('Segoe UI', 10, 'bold'), width=15
        )
        style.map(
            f"{theme_name}.Clear.TButton",
            background=[('active', theme.get('clear_hover', theme['clear_button_bg'])),
                        ('!disabled', theme['clear_button_bg'])],
            foreground=[('active', '#ffffff'), ('!disabled', '#ffffff')],
            relief=[('pressed', 'sunken'), ('!pressed', 'raised')]
        )

        style.configure(
            f"{theme_name}.Active.TButton",
            padding=6, relief="sunken",
            background=theme['accent'], foreground='#ffffff',
            font=('Segoe UI', 9, 'bold')
        )
        style.map(
            f"{theme_name}.Active.TButton",
            background=[('active', theme['accent']), ('!disabled', theme['accent'])],
            foreground=[('active', '#ffffff'), ('!disabled', '#ffffff')]
        )

        style.configure(
            f"{theme_name}.TLabelframe",
            background=theme['bg'], foreground=theme['text']
        )
        style.configure(
            f"{theme_name}.TLabelframe.Label",
            background=theme['bg'], foreground=theme['accent'],
            font=('Segoe UI', 9, 'bold')
        )

    # ---- Menu Bar ----
    menubar = tk.Menu(root, bg=THEMES[current_theme]['bg'], fg=THEMES[current_theme]['text'])

    file_menu = tk.Menu(menubar, tearoff=0,
                        bg=THEMES[current_theme]['bg'], fg=THEMES[current_theme]['text'])
    file_menu.add_command(label="Clear All", command=clear_text, accelerator="Ctrl+L")
    file_menu.add_separator()
    file_menu.add_command(label="Exit", command=root.quit)
    menubar.add_cascade(label="File", menu=file_menu)

    edit_menu = tk.Menu(menubar, tearoff=0,
                        bg=THEMES[current_theme]['bg'], fg=THEMES[current_theme]['text'])
    edit_menu.add_command(label="Copy Result", command=copy_to_clipboard, accelerator="Ctrl+Shift+C")
    edit_menu.add_separator()
    edit_menu.add_command(label="History", command=show_history, accelerator="Ctrl+H")
    menubar.add_cascade(label="Edit", menu=edit_menu)

    view_menu = tk.Menu(menubar, tearoff=0,
                        bg=THEMES[current_theme]['bg'], fg=THEMES[current_theme]['text'])
    for theme in THEMES:
        view_menu.add_command(label=theme, command=lambda t=theme: apply_theme(t))
    menubar.add_cascade(label="Themes", menu=view_menu)

    help_menu = tk.Menu(menubar, tearoff=0,
                        bg=THEMES[current_theme]['bg'], fg=THEMES[current_theme]['text'])
    help_menu.add_command(label="About", command=show_about)
    menubar.add_cascade(label="Help", menu=help_menu)

    root.config(menu=menubar)

    # ---- Layout ----
    main_container = ttk.Frame(root)
    main_container.pack(fill=tk.BOTH, expand=True)

    # Sidebar
    sidebar_frame = ttk.Frame(main_container, width=160, style=f"{current_theme}.TFrame")
    sidebar_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
    sidebar_frame.pack_propagate(False)

    sidebar_labels = []

    def make_sidebar_label(parent, text, bold=False):
        font = ('Segoe UI', 10, 'bold') if bold else ('Segoe UI', 8)
        lbl = tk.Label(parent, text=text, font=font,
                       bg=THEMES[current_theme]['bg'],
                       fg=THEMES[current_theme]['label_fg'])
        lbl.pack(pady=(6, 2) if bold else (0, 0), anchor='w', padx=5)
        sidebar_labels.append(lbl)
        return lbl

    make_sidebar_label(sidebar_frame, "Themes", bold=True)

    theme_buttons = {}
    for theme in THEMES:
        btn = ttk.Button(
            sidebar_frame, text=theme,
            command=lambda t=theme: apply_theme(t),
            style=f"{current_theme}.TButton"
        )
        btn.pack(fill=tk.X, pady=2, padx=5)
        theme_buttons[theme] = btn

    ttk.Separator(sidebar_frame, orient='horizontal').pack(fill=tk.X, pady=8)
    make_sidebar_label(sidebar_frame, "Shortcuts", bold=True)

    for shortcut in ["Enter: Decode", "Esc: Clear", "Ctrl+L: Clear",
                     "Ctrl+Shift+C: Copy", "Ctrl+H: History"]:
        make_sidebar_label(sidebar_frame, shortcut)

    ttk.Separator(sidebar_frame, orient='horizontal').pack(fill=tk.X, pady=8)
    make_sidebar_label(sidebar_frame, "Encodings", bold=True)
    for enc in ["Base64 / URL / 32 / 58 / 85", "Hex, Binary, Octal",
                "ASCII Decimal", "URL, HTML", "ROT13, ROT47",
                "Morse, Caesar"]:
        make_sidebar_label(sidebar_frame, enc)

    history_btn = ttk.Button(
        sidebar_frame, text="History (Ctrl+H)",
        command=show_history, style=f"{current_theme}.TButton"
    )
    history_btn.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=(0, 8))

    # Main content
    main_frame = ttk.Frame(main_container, padding="10", style=f"{current_theme}.TFrame")
    main_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    # Input
    input_frame = ttk.LabelFrame(
        main_frame, text=" Input Text ",
        padding=10, style=f"{current_theme}.TLabelframe"
    )
    input_frame.pack(fill=tk.BOTH, expand=False, pady=(0, 8))

    text_input = scrolledtext.ScrolledText(
        input_frame, height=8, font=("Consolas", 11),
        bg=THEMES[current_theme]['text_bg'],
        fg=THEMES[current_theme]['text'],
        insertbackground=THEMES[current_theme]['text'],
        selectbackground=THEMES[current_theme]['accent'],
        padx=10, pady=10, wrap=tk.WORD
    )
    text_input.pack(fill=tk.BOTH, expand=True)

    # Buttons
    button_frame = ttk.Frame(main_frame, style=f"{current_theme}.TFrame")
    button_frame.pack(fill=tk.X, padx=5, pady=5)

    decode_btn = ttk.Button(
        button_frame, text="DECODE (Enter)",
        command=decode_input, style=f"{current_theme}.TButton"
    )
    decode_btn.pack(side=tk.LEFT, padx=5, ipadx=10, ipady=3)

    clear_btn = ttk.Button(
        button_frame, text="CLEAR (Esc)",
        command=clear_text, style=f"{current_theme}.Clear.TButton"
    )
    clear_btn.pack(side=tk.LEFT, padx=5, ipadx=10, ipady=3)

    copy_btn = ttk.Button(
        button_frame, text="Copy Result",
        command=copy_to_clipboard, style=f"{current_theme}.TButton"
    )
    copy_btn.pack(side=tk.LEFT, padx=5, ipadx=10, ipady=3)

    # Result
    result_frame = ttk.LabelFrame(
        main_frame, text=" Decoded Output ",
        padding=10, style=f"{current_theme}.TLabelframe"
    )
    result_frame.pack(fill=tk.BOTH, expand=True)

    result_display = scrolledtext.ScrolledText(
        result_frame, height=15, font=("Consolas", 11),
        bg=THEMES[current_theme]['text_bg'],
        fg=THEMES[current_theme]['text'],
        state='disabled',
        insertbackground=THEMES[current_theme]['text'],
        selectbackground=THEMES[current_theme]['accent'],
        padx=10, pady=10, wrap=tk.WORD
    )
    result_display.pack(fill=tk.BOTH, expand=True)

    # Status bar
    status_var = tk.StringVar(value="Ready")
    status_bar = tk.Label(
        root, textvariable=status_var,
        bd=1, relief=tk.SUNKEN, anchor=tk.W,
        bg=THEMES[current_theme]['accent'],
        fg="white", font=("Segoe UI", 9),
        padx=8
    )
    status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    # Tags
    text_input.tag_configure("highlight", background=THEMES[current_theme]['highlight'])
    result_display.tag_configure("header", font=('Arial', 10, 'bold'),
                                  foreground=THEMES[current_theme]['accent'])
    result_display.tag_configure("output", font=('Consolas', 10),
                                  foreground=THEMES[current_theme]['text'])
    result_display.tag_configure("error", font=('Arial', 10), foreground='#cc0000')

    # Keyboard bindings
    root.bind("<Return>", decode_input)
    root.bind("<Escape>", clear_text)
    root.bind("<Control-l>", lambda e: clear_text())
    root.bind("<Control-L>", lambda e: clear_text())
    root.bind("<Control-Shift-C>", lambda e: copy_to_clipboard())
    root.bind("<Control-h>", lambda e: show_history())
    root.bind("<Control-H>", lambda e: show_history())

    text_input.focus_set()

    apply_theme(current_theme)
    update_status("Ready. Paste encoded text and press Enter.", "info")
    load_history()


# ===========================================================
# ENTRY POINT
# ===========================================================

if __name__ == "__main__":
    create_gui()
    root.mainloop()
