"""Offer normal systemd shutdown and restart from the desktop."""
import subprocess
import tkinter as tk
from tkinter import ttk

import appearance


def main():
    root = tk.Tk(className="RelifePower")
    root.title("Kompüteri söndür")
    root.resizable(False, False)
    appearance.configure(root)

    def select(action, verb):
        for button in buttons:
            button.state(["disabled"])
        status.set(f"Kompüter {verb}…")
        root.update_idletasks()
        try:
            response = subprocess.run(["/usr/local/bin/relife-power", action],
                                      capture_output=True, text=True, timeout=8)
            if response.returncode == 0:
                return
        except (OSError, subprocess.TimeoutExpired):
            pass
        status.set("Əmr qəbul edilmədi. Bir az gözlə və yenidən yoxla.")
        for button in buttons:
            button.state(["!disabled"])

    ttk.Label(root, text="Kompüteri söndür", style="Header.TLabel").pack(fill="x")
    pane = ttk.Frame(root, padding=18)
    pane.pack(fill="both")
    ttk.Label(pane, text="Vacib fayllarını xarici yaddaşa saxla.",
              wraplength=370).pack(anchor="w", pady=(0, 12))
    row = ttk.Frame(pane)
    row.pack(anchor="w")
    buttons = [
        ttk.Button(row, text="Söndür", style="Primary.TButton", command=lambda: select("poweroff", "sönür")),
        ttk.Button(row, text="Yenidən başlat", command=lambda: select("reboot", "yenidən başlayır")),
        ttk.Button(row, text="Ləğv et", command=root.destroy),
    ]
    for button in buttons:
        button.pack(side="left", padx=(0, 7))
    status = tk.StringVar()
    ttk.Label(pane, textvariable=status, wraplength=360).pack(anchor="w", pady=(12, 0))
    root.bind("<Escape>", lambda event: root.destroy())
    buttons[0].focus_set()
    root.update_idletasks()
    x = (root.winfo_screenwidth() - root.winfo_reqwidth()) // 2
    y = (root.winfo_screenheight() - root.winfo_reqheight()) // 2
    root.geometry(f"+{max(0, x)}+{max(0, y)}")
    root.mainloop()


if __name__ == "__main__":
    main()
