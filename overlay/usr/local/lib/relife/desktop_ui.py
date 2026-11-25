"""Small, on-demand X11 Start panel, task picker and network panel."""
import os
import re
import subprocess
import sys
import tkinter as tk
from tkinter import ttk

import appearance


def command(*args, timeout=4):
    return subprocess.run(args, capture_output=True, text=True, errors="replace", timeout=timeout)


def launch(*args):
    subprocess.Popen(args, start_new_session=True)


def window_list():
    listing = command("xprop", "-root", "_NET_CLIENT_LIST_STACKING", "_NET_CLIENT_LIST")
    lines = [line for line in listing.stdout.splitlines() if "window id #" in line]
    candidates = re.findall(r"0x[0-9a-f]+", lines[0]) if lines else []
    current_desktop = command("xdotool", "get_desktop").stdout.strip()
    windows = []
    for window_id in reversed(candidates):
        info = command("xprop", "-notype", "-id", window_id,
                       "_NET_WM_NAME", "WM_NAME", "_NET_WM_DESKTOP", "_NET_WM_STATE")
        if info.returncode or "_NET_WM_STATE_SKIP_TASKBAR" in info.stdout:
            continue
        desktop = re.search(r"^_NET_WM_DESKTOP = (\d+)", info.stdout, re.M)
        if desktop and current_desktop and desktop[1] not in (current_desktop, "4294967295"):
            continue
        title = re.search(r'^(_NET_WM_NAME|WM_NAME) = "(.*)"$', info.stdout, re.M)
        windows.append((window_id, title[2] if title else "Adsız pəncərə"))
    return windows


def panel(name, title):
    root = tk.Tk(className=name)
    root.title(title)
    appearance.configure(root)
    root.resizable(False, False)
    root.bind("<Escape>", lambda event: root.destroy())
    return root


def place(root, x=None, bottom=False):
    root.update_idletasks()
    width, height = root.winfo_reqwidth(), root.winfo_reqheight()
    if x is None:
        x = (root.winfo_screenwidth() - width) // 2
    y = root.winfo_screenheight() - height - 47 if bottom else (root.winfo_screenheight() - height) // 2
    root.geometry(f"+{max(x, 0)}+{max(y, 0)}")


def start():
    root = panel("RelifeStart", "Başla")
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    style = ttk.Style()
    style.configure("Tile.TButton", padding=(14, 14), anchor="w", background="#e0eef6")
    style.map("Tile.TButton", background=[("active", "#c7e3f2"), ("pressed", "#aad4ea")])
    ttk.Label(root, text="Başla", style="Header.TLabel").pack(fill="x")
    tiles = ttk.Frame(root, padding=12)
    tiles.pack(fill="both", expand=True)
    for col in range(2):
        tiles.columnconfigure(col, weight=1, uniform="apps")

    def open_app(*args):
        root.destroy()
        launch(*args)

    apps = [
        ("İnternet", "Dərs saytlarını aç", "internet", ("relife-firefox",)),
        ("Fayllarım", "Sənədləri və qovluqları aç", "files", ("pcmanfm",)),
        ("Təhsil mərkəzi", "İnternetsiz dərs və məşq", "education", ("relife-education",)),
        ("Mətn yaz", "Qeyd və tapşırıq yaz", "write", ("mousepad",)),
        ("Şəbəkə", "Wi-Fi və kabel bağlantısı", "network", ("relife-desktop", "network")),
        ("Açıq pəncərələr", "Başqa tətbiqə keç", "windows", ("relife-desktop", "switch")),
    ]
    images = []
    for i, (label, description, icon, argv) in enumerate(apps):
        image = tk.PhotoImage(file=f"/usr/share/icons/relife/{icon}.png")
        images.append(image)
        button = ttk.Button(tiles, text=f"{label}\n{description}", image=image, compound="left",
                            style="Tile.TButton", command=lambda argv=argv: open_app(*argv))
        button.grid(row=i // 2, column=i % 2, sticky="ew", padx=4, pady=4)

    footer = ttk.Frame(root, padding=(16, 0, 16, 12))
    footer.pack(fill="x")
    ttk.Button(footer, text="Kömək", command=lambda: open_app("relife-help")).pack(side="left")
    def power():
        open_app("relife-power-menu")
    ttk.Button(footer, text="Kompüteri söndür", command=power).pack(side="right")
    root.bind("<Alt-p>", lambda event: power())
    place(root, x=4, bottom=True)
    root.wait_visibility()
    root.focus_force()
    root.bind("<FocusOut>", lambda event: root.after_idle(
        lambda: root.destroy() if root.focus_displayof() is None else None))
    root.mainloop()


def switch(direction):
    existing = command("xdotool", "search", "--onlyvisible", "--class", "^RelifeSwitcher$")
    if existing.stdout.strip():
        window = existing.stdout.splitlines()[0]
        command("xdotool", "windowactivate", "--sync", window)
        if direction:
            command("xdotool", "key", "Right" if direction == "right" else "Left")
        return
    active = command("xdotool", "getactivewindow").stdout.strip()
    windows = window_list()
    root = panel("RelifeSwitcher", "Açıq pəncərələr")
    root.attributes("-topmost", True)
    root.wm_attributes("-type", "dialog")
    ttk.Label(root, text="Açıq pəncərələr", style="Header.TLabel").pack(fill="x")
    body = ttk.Frame(root, padding=14)
    body.pack(fill="both")
    if not windows:
        ttk.Label(body, text="Hazırda açıq tətbiq yoxdur.").pack(pady=12, padx=40)
        ttk.Button(body, text="Bağla", command=root.destroy).pack()
        place(root)
        root.mainloop()
        return
    entries = tk.Listbox(body, width=52, height=min(len(windows), 8), activestyle="none",
                         font="TkDefaultFont", highlightthickness=1, highlightcolor=appearance.ACCENT,
                         selectbackground=appearance.ACCENT, selectforeground="#ffffff", borderwidth=0)
    entries.grid(row=0, column=0, sticky="nsew")
    scroll = ttk.Scrollbar(body, orient="vertical", command=entries.yview)
    scroll.grid(row=0, column=1, sticky="ns")
    entries.configure(yscrollcommand=scroll.set)
    for _, title in windows:
        entries.insert("end", title)

    def select(index):
        entries.selection_clear(0, "end")
        entries.selection_set(index)
        entries.activate(index)
        entries.see(index)

    def move(step):
        current = entries.curselection()
        select(((current[0] if current else 0) + step) % len(windows))
        return "break"

    def activate(event=None):
        row = entries.curselection()
        if row:
            window_id = windows[row[0]][0]
            root.destroy()
            command("xdotool", "windowactivate", window_id)
        return "break"

    selected = next((i for i, (wid, _) in enumerate(windows) if str(int(wid, 16)) == active), 0)
    offset = {"left": -1, "right": 1}.get(direction, 0)
    select((selected + offset) % len(windows))
    entries.bind("<Left>", lambda event: move(-1))
    entries.bind("<Right>", lambda event: move(1))
    entries.bind("<Return>", activate)
    entries.bind("<Double-Button-1>", activate)
    root.bind("<Left>", lambda event: move(-1))
    root.bind("<Right>", lambda event: move(1))
    ttk.Button(body, text="Keç", command=activate, style="Primary.TButton").grid(row=1, column=0, sticky="e", pady=(10, 0))
    place(root)
    entries.focus_set()
    root.mainloop()


def network():
    root = panel("RelifeNetwork", "Şəbəkə")
    ttk.Label(root, text="Şəbəkə", style="Header.TLabel").pack(fill="x")
    body = ttk.Frame(root, padding=16)
    body.pack(fill="both")
    status = tk.StringVar()
    ttk.Label(body, textvariable=status, width=46, wraplength=360).pack(anchor="w", pady=(0, 12))
    box = ttk.Frame(body)
    box.pack(fill="x")

    def refresh():
        try:
            env = {**os.environ, "LC_ALL": "C"}
            result = subprocess.run(["nmcli", "-t", "-f", "TYPE,STATE", "device", "status"],
                                    capture_output=True, text=True, env=env, timeout=4)
        except (OSError, subprocess.TimeoutExpired):
            status.set("Şəbəkə xidməti cavab vermədi.")
            return
        devices = [line.split(":", 1) for line in result.stdout.splitlines() if ":" in line]
        adapters = [state for kind, state in devices if kind in ("wifi", "ethernet")]
        if result.returncode:
            text = "Şəbəkə xidmətinə qoşulmaq mümkün olmadı."
        elif any(state.startswith("connected") for state in adapters):
            text = "Şəbəkəyə qoşulub. İnternet açılmırsa, giriş səhifəsini yoxla."
        elif any(kind == "wifi" and state != "unavailable" for kind, state in devices):
            text = "Wi-Fi şəbəkəsi seç və tələb olunarsa parolu daxil et."
        else:
            text = "Aktiv Wi-Fi görünmür. Wi-Fi düyməsini və ya şəbəkə kabelini yoxla."
        status.set(text)

    ttk.Button(box, text="Şəbəkə seç", style="Primary.TButton",
               command=lambda: launch("xterm", "-T", "Wi-Fi və kabel", "-e", "nmtui", "connect")).pack(
                   side="left", padx=(0, 6))
    def enable_wifi():
        try:
            result = command("nmcli", "radio", "wifi", "on")
            if result.returncode == 0:
                refresh()
                return
        except (OSError, subprocess.TimeoutExpired):
            pass
        status.set("Wi-Fi açıla bilmədi. Kompüterdəki Wi-Fi düyməsini yoxla.")

    ttk.Button(box, text="Wi-Fi aç", command=enable_wifi).pack(side="left", padx=(0, 6))
    ttk.Button(box, text="Yenilə", command=refresh).pack(side="left")
    ttk.Button(body, text="Şəbəkənin giriş səhifəsini aç",
               command=lambda: launch("relife-firefox", "http://detectportal.firefox.com/canonical.html")).pack(
                   anchor="w", pady=(10, 0))
    refresh()
    root.update_idletasks()
    place(root, x=root.winfo_screenwidth() - root.winfo_reqwidth() - 12, bottom=True)
    root.mainloop()


def main():
    action = sys.argv[1] if len(sys.argv) > 1 else "start"
    if action == "start":
        start()
    elif action == "switch":
        switch(sys.argv[2] if len(sys.argv) > 2 else None)
    elif action == "network":
        network()


if __name__ == "__main__":
    main()
