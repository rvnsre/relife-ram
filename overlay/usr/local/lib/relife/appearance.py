"""Shared colors and native widget styles for ReLife desktop applications."""
import tkinter.font as font
from tkinter import ttk

BACKGROUND = "#eaf1f5"
SURFACE = "#f8fbfd"
INK = "#172f42"
MUTED = "#43596b"
ACCENT = "#226e65"
BORDER = "#cbdbe4"


def configure(root):
    root.configure(background=BACKGROUND)
    for name in ("TkDefaultFont", "TkTextFont", "TkHeadingFont"):
        font.nametofont(name).configure(family="DejaVu Sans", size=10)
    style = ttk.Style()
    style.theme_use("clam")
    style.configure(".", background=SURFACE, foreground=INK, bordercolor=BORDER,
                    lightcolor=BORDER, darkcolor=BORDER, selectbackground=ACCENT,
                    selectforeground="#ffffff", fieldbackground="#ffffff")
    style.configure("TFrame", background=SURFACE)
    style.configure("TNotebook", background=BACKGROUND, tabmargins=(0, 0, 0, 0), borderwidth=1)
    style.configure("TNotebook.Tab", background=BACKGROUND, padding=(9, 8))
    style.map("TNotebook.Tab", background=[("selected", ACCENT), ("active", "#d8ebe9")],
              foreground=[("selected", "#ffffff")])
    style.configure("TButton", padding=(10, 6), background="#e3edf2")
    style.map("TButton", background=[("pressed", "#bfd8dd"), ("active", "#d4e9e8")])
    style.configure("Primary.TButton", background=ACCENT, foreground="#ffffff")
    style.map("Primary.TButton", background=[("pressed", "#154f49"), ("active", "#1a5f57")])
    style.configure("Caption.TLabel", background=BACKGROUND, foreground=MUTED)
    style.configure("Header.TLabel", background="#183246", foreground="#f1faff",
                    padding=(18, 9), font=("DejaVu Sans", 16, "bold"))
    style.configure("Practice.TFrame", background="#e7f1f2")
    style.configure("Practice.TLabel", background="#e7f1f2")
    style.configure("PracticeHeading.TLabel", background="#e7f1f2", font=("DejaVu Sans", 12, "bold"))
    style.configure("Section.TLabel", font=("DejaVu Sans", 12, "bold"), padding=(0, 0, 0, 6))
    style.configure("TEntry", padding=(7, 4), insertcolor=INK)
    style.configure("TCombobox", padding=(6, 3))
    style.map("TCombobox", fieldbackground=[("readonly", "#ffffff")],
              foreground=[("readonly", INK)])
