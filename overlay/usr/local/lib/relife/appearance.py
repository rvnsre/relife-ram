"""ReLife's shared light palette, typography and native widget styles."""
import math
import tkinter as tk
import tkinter.font as font
from tkinter import ttk

BACKGROUND = "#f1f0f9"
SURFACE = "#fcfbff"
INK = "#211e36"
MUTED = "#5f5b75"
ACCENT = "#5240b6"
BORDER = "#ded9ed"
TINT = "#ebe6ff"
FONT = "DejaVu Sans"


def rounded_image(root, fill, edge, radius=7):
    size = 2 * radius + 3
    image = tk.PhotoImage(master=root, width=size, height=size)
    for y in range(size):
        for x in range(size):
            dx = max(radius - x, x - (size - 1 - radius), 0)
            dy = max(radius - y, y - (size - 1 - radius), 0)
            distance = math.hypot(dx, dy)
            if distance <= radius:
                image.put(edge if distance > radius - 1 or x in (0, size - 1) or y in (0, size - 1)
                          else fill, (x, y))
    return image


def configure(root):
    root.configure(background=BACKGROUND)
    for name in ("TkDefaultFont", "TkTextFont", "TkHeadingFont"):
        font.nametofont(name, root=root).configure(family=FONT, size=10)
    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure(".", background=SURFACE, foreground=INK, bordercolor=BORDER,
                    lightcolor=BORDER, darkcolor=BORDER, selectbackground=ACCENT,
                    selectforeground="#ffffff", fieldbackground="#ffffff", focuscolor=ACCENT)
    style.configure("TFrame", background=SURFACE)
    style.configure("Shell.TFrame", background=BACKGROUND)
    style.configure("TNotebook", background=BACKGROUND, tabmargins=(0, 0, 0, 0), borderwidth=1)
    style.configure("TNotebook.Tab", background=BACKGROUND, padding=(9, 9))
    style.map("TNotebook.Tab", background=[("selected", TINT), ("active", "#f7f3ff")],
              foreground=[("selected", "#3e2a9e")])
    for prefix, padding, normal, active, pressed in (
        ("", (14, 8), SURFACE, TINT, "#ded6ff"),
        ("Primary.", (16, 8), ACCENT, "#4834a7", "#382881"),
        ("Tile.", (12, 6), "#ffffff", "#f4efff", "#e5ddff"),
    ):
        variant = f"{prefix}TButton"
        element = f"{prefix}RelifeSurface"
        colors = [(normal, BORDER), (active, "#b3a6e7"), (pressed, ACCENT),
                  (normal, ACCENT), ("#efedf4", BORDER)]
        if prefix == "Primary.":
            colors = [(color, color) for color, _ in colors[:3]] + [(normal, INK), colors[-1]]
        images = [rounded_image(root, fill, edge) for fill, edge in colors]
        root._relife_style_images = getattr(root, "_relife_style_images", []) + images
        style.element_create(element, "image", images[0], ("disabled", images[4]),
                             ("pressed", images[2]), ("focus", images[3]), ("active", images[1]),
                             border=8, sticky="nsew")
        style.layout(variant, [(element, {"sticky": "nsew", "children":
                     [("Button.padding", {"sticky": "nsew", "children":
                      [("Button.label", {"sticky": "nsew"})]})]})])
        style.configure(variant, padding=padding, foreground="#ffffff" if prefix == "Primary." else INK)
        style.map(variant, foreground=[("disabled", MUTED)])
    style.configure("Caption.TLabel", background=BACKGROUND, foreground=MUTED)
    style.configure("Muted.TLabel", foreground=MUTED)
    style.configure("Header.TLabel", background=BACKGROUND, foreground=INK,
                    padding=(22, 15), font=(FONT, 18, "bold"))
    style.configure("Hero.TLabel", background=BACKGROUND, foreground=INK, font=(FONT, 23, "bold"))
    style.configure("Accent.TLabel", background=BACKGROUND, foreground=ACCENT, font=(FONT, 10, "bold"))
    style.configure("Practice.TFrame", background=TINT)
    style.configure("Practice.TLabel", background=TINT)
    style.configure("PracticeHeading.TLabel", background=TINT, font=(FONT, 12, "bold"))
    style.configure("Section.TLabel", font=(FONT, 12, "bold"), padding=(0, 0, 0, 6))
    entry_normal = rounded_image(root, "#ffffff", BORDER)
    entry_focus = rounded_image(root, "#ffffff", ACCENT)
    root._relife_style_images.extend((entry_normal, entry_focus))
    style.element_create("RelifeEntry", "image", entry_normal, ("focus", entry_focus),
                         border=8, sticky="nsew")
    style.layout("TEntry", [("RelifeEntry", {"sticky": "nsew", "children":
                 [("Entry.padding", {"sticky": "nsew", "children":
                  [("Entry.textarea", {"sticky": "nsew"})]})]})])
    style.configure("TEntry", padding=(6, 2), insertcolor=INK)
    style.configure("TCombobox", padding=(7, 4))
    style.map("TCombobox", fieldbackground=[("readonly", "#ffffff")],
              foreground=[("readonly", INK)])
    root.option_add("*Text.foreground", INK)
    root.option_add("*Text.background", "#ffffff")
    root.option_add("*Text.selectBackground", ACCENT)
    root.option_add("*Listbox.selectBackground", ACCENT)
