"""Small ALSA volume window for Extreme Lite."""
import re
import subprocess
import tkinter as tk
from tkinter import ttk

import appearance


def mixer(*args):
    return subprocess.run(["amixer", "sget" if not args else "sset", "Master", *args],
                          capture_output=True, text=True, check=True, timeout=3).stdout


def main():
    root = tk.Tk(className="RelifeSound")
    root.title("ReLife · Səs")
    root.resizable(False, False)
    appearance.configure(root)
    ttk.Label(root, text="Səs", style="Header.TLabel").pack(fill="x")
    pane = ttk.Frame(root, padding=16)
    pane.pack(fill="both")
    status = tk.StringVar()
    level = tk.DoubleVar()

    def refresh(*args):
        try:
            result = mixer(*args)
        except (OSError, subprocess.SubprocessError):
            status.set("Səs çıxışı tapılmadı.")
            apply_button.state(["disabled"])
            mute_button.state(["disabled"])
            return
        values = re.findall(r"\[(\d+)%\]", result)
        if values:
            level.set(int(values[0]))
        status.set("Səs söndürülüb" if "[off]" in result and "[on]" not in result else "Səs çıxışı")

    ttk.Label(pane, textvariable=status).pack(anchor="w")
    ttk.Scale(pane, from_=0, to=100, variable=level, length=235).pack(fill="x", pady=(8, 0))
    value = tk.StringVar()
    level.trace_add("write", lambda *_: value.set(f"{level.get():.0f}%"))
    ttk.Label(pane, textvariable=value).pack(anchor="e", pady=(0, 8))
    row = ttk.Frame(pane)
    row.pack(anchor="w")
    apply_button = ttk.Button(row, text="Tətbiq et", style="Primary.TButton",
                              command=lambda: refresh(f"{level.get():.0f}%"))
    apply_button.pack(side="left", padx=(0, 6))
    mute_button = ttk.Button(row, text="Səsi aç / söndür", command=lambda: refresh("toggle"))
    mute_button.pack(side="left")
    refresh()
    root.mainloop()


if __name__ == "__main__":
    main()
