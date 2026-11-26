"""Small, on-demand X11 Start panel, task picker and network panel."""
import calendar as dates
from datetime import date
from pathlib import Path
import os
import queue
import threading
import re
import subprocess
import sys
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
import unicodedata

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
                       "_NET_WM_NAME", "WM_NAME", "WM_CLASS", "_NET_WM_DESKTOP",
                       "_NET_WM_STATE", "_NET_WM_WINDOW_TYPE")
        if info.returncode or any(kind in info.stdout for kind in (
            "_NET_WM_STATE_SKIP_TASKBAR", "_NET_WM_WINDOW_TYPE_DESKTOP", "_NET_WM_WINDOW_TYPE_DOCK"
        )):
            continue
        desktop = re.search(r"^_NET_WM_DESKTOP = (\d+)", info.stdout, re.M)
        if desktop and current_desktop and desktop[1] not in (current_desktop, "4294967295"):
            continue
        title = re.search(r'^(_NET_WM_NAME|WM_NAME) = "(.*)"$', info.stdout, re.M)
        wm_class = re.search(r'^WM_CLASS = (.*)$', info.stdout, re.M)
        app = wm_class[1].lower() if wm_class else ""
        icon = next((icon for key, icon in (
            ("firefox", "internet"), ("pcmanfm", "files"), ("mousepad", "write"),
            ("education", "education"), ("network", "network"), ("sound", "sound"),
            ("help", "help")) if key in app), "windows")
        windows.append((window_id, title[2] if title else "Adsız pəncərə", icon))
    return windows


def panel(name, title):
    root = tk.Tk(className=name)
    root.withdraw()
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
    screen_height = root.winfo_screenheight()
    bar = command("xprop", "-root", "_NET_WORKAREA").stdout.partition("=")[2]
    bounds = re.findall(r"\d+", bar)
    bottom_edge = int(bounds[1]) + int(bounds[3]) if len(bounds) >= 4 else screen_height - 38
    y = bottom_edge - height if bottom else (screen_height - height) // 2
    root.geometry(f"+{max(x, 0)}+{max(y, 0)}")
    root.deiconify()


DARK = "#191919"
RAIL = "#141414"
CARD = "#222222"
EDGE = "#333333"
WHITE = "#f8f8f8"
SOFT = "#c9c9c9"
BLUE = "#0078d4"
ICONS = "/usr/share/icons/relife/"
APPS = (
    ("Açıq pəncərələr", "windows", ("relife-desktop", "switch")),
    ("Fayllarım", "files", ("pcmanfm",)),
    ("İnternet", "internet", ("relife-firefox",)),
    ("Kömək və bələdçi", "help", ("relife-help",)),
    ("Mətn yaz", "write", ("mousepad",)),
    ("Səs", "sound", ("relife-sound",)),
    ("Şəbəkə", "network", ("relife-desktop", "network")),
    ("Təhsil mərkəzi", "education", ("relife-education",)),
)


def dark_label(parent, text=None, *, variable=None, bg=DARK, fg=WHITE, size=10, bold=False, **kwargs):
    return tk.Label(parent, text=text, textvariable=variable, bg=bg, fg=fg, anchor="w",
                    font=(appearance.FONT, size, "bold" if bold else "normal"), **kwargs)


def dark_button(parent, label, callback, *, bg=CARD, icon=None, icon_size=32, **kwargs):
    suffix = "-24" if icon_size == 24 else ""
    image = None
    if icon:
        root = parent.winfo_toplevel()
        if not hasattr(root, "relife_images"):
            root.relife_images = {}
        key = icon + suffix
        if key not in root.relife_images:
            root.relife_images[key] = tk.PhotoImage(master=root, file=f"{ICONS}{key}.png")
        image = root.relife_images[key]
    button = tk.Button(parent, text=label, image=image, compound="left", command=callback,
                       bg=bg, fg=WHITE, activebackground="#2d2d2d", activeforeground=WHITE,
                       bd=0, relief="flat", highlightthickness=1, highlightbackground=bg,
                       highlightcolor="#1a86d9", font=(appearance.FONT, 10), cursor="hand2", **kwargs)
    button.relife_image = image
    button.bind("<Enter>", lambda event: button.configure(bg="#2d2d2d", highlightbackground="#606060"))
    button.bind("<Leave>", lambda event: button.configure(bg=bg, highlightbackground=bg))
    button.bind("<Return>", lambda event: button.invoke())
    return button


def search_key(value):
    normalized = unicodedata.normalize("NFKD", value.strip().casefold())
    return "".join(char for char in normalized if not unicodedata.combining(char)).translate(
        str.maketrans({"ə": "e", "ı": "i"}))


def start():
    root = panel("RelifeStart", "Başla")
    root.wm_attributes("-type", "dialog")
    root.attributes("-topmost", True)
    root.configure(bg=DARK, highlightbackground=EDGE, highlightthickness=1)
    shell = tk.Frame(root, bg=DARK)
    shell.pack(fill="both", expand=True)
    rail = tk.Frame(shell, bg=RAIL)
    rail.pack(side="left", fill="y")
    list_side = tk.Frame(shell, bg=DARK, padx=14, pady=13)
    list_side.pack(side="left", fill="both", expand=True)
    tiles = tk.Frame(shell, bg="#202020", padx=12, pady=13)
    tiles.pack(side="left", fill="both")
    dark_label(list_side, "Başla", size=18, bold=True).pack(fill="x", pady=(0, 9))

    def open_app(*args):
        root.destroy()
        launch(*args)

    expanded = False
    rail_actions = []

    def expand():
        nonlocal expanded
        expanded = not expanded
        for button, label in rail_actions:
            button.configure(text=label if expanded else "")

    dark_button(rail, "", expand, bg=RAIL, icon="start", padx=6).pack(fill="x", pady=(6, 0))
    for name, icon, args in (
        ("Güc", "power", ("relife-power-menu",)),
        ("Sistem məlumatı", "system", ("relife-desktop", "system")),
        ("Fayllarım", "files", ("pcmanfm",)),
        ("Kömək", "help", ("relife-help",)),
    ):
        button = dark_button(rail, "", lambda args=args: open_app(*args), bg=RAIL, icon=icon, padx=6)
        button.pack(side="bottom", fill="x", pady=2)
        rail_actions.append((button, name))

    query = tk.StringVar()
    search = tk.Entry(list_side, textvariable=query, bg="#252525", fg=WHITE, insertbackground=WHITE,
                      selectbackground=BLUE, bd=6, relief="flat", highlightthickness=1,
                      highlightbackground=EDGE, highlightcolor="#1a86d9", width=24)
    search.pack(fill="x")
    hint = dark_label(search, "Tətbiq axtar…", bg="#252525", fg=SOFT, cursor="xterm")
    hint.place(x=5, rely=.5, anchor="w")
    hint.bind("<Button-1>", lambda event: search.focus_set())
    listing = tk.Frame(list_side, bg=DARK)
    listing.pack(fill="both", expand=True, pady=(8, 0))
    buttons = [
        dark_button(listing, name, lambda args=args: open_app(*args), bg=DARK, icon=icon, icon_size=24, anchor="w")
        for name, icon, args in APPS
    ]
    empty = dark_label(listing, "Uyğun tətbiq tapılmadı.", fg=SOFT)
    visible = []

    def focus(offset):
        if visible:
            current = root.focus_get()
            index = visible.index(current) if current in visible else (-1 if offset > 0 else 0)
            visible[(index + offset) % len(visible)].focus_set()
        return "break"

    def filter_apps(*_):
        value = search_key(query.get())
        hint.place_forget()
        if not query.get():
            hint.place(x=5, rely=.5, anchor="w")
        empty.pack_forget()
        visible.clear()
        for (name, _, _), button in zip(APPS, buttons):
            button.pack_forget()
            if value in search_key(name):
                button.pack(fill="x")
                visible.append(button)
        if not visible:
            empty.pack(anchor="w", pady=8)

    def activate_first(event):
        if visible:
            visible[0].invoke()
        return "break"

    query.trace_add("write", filter_apps)
    root.bind("<Up>", lambda event: focus(-1))
    root.bind("<Down>", lambda event: focus(1))
    search.bind("<Return>", activate_first)
    root.bind("<Alt-p>", lambda event: open_app("relife-power-menu"))
    dark_label(tiles, "Tez aç", bg="#202020", fg=SOFT, bold=True).grid(
        row=0, columnspan=2, sticky="ew", pady=(4, 12))
    tile_apps = (7, 2, 1, 4, 6, 0, 3)
    cells = ((1, 0, 2), (2, 0, 1), (2, 1, 1), (3, 0, 1), (3, 1, 1), (4, 0, 1), (4, 1, 1))
    for index, (row, col, span) in zip(tile_apps, cells):
        name, icon, args = APPS[index]
        button = dark_button(tiles, name, lambda args=args: open_app(*args), icon=icon,
                             bg={7: "#0064b1", 2: "#005a9e"}.get(index, "#2b2b2b"),
                             width=116, height=58, wraplength=105, justify="left")
        button.grid(row=row, column=col, columnspan=span, sticky="ew", padx=2, pady=2)
    filter_apps()
    if root.winfo_screenwidth() < 620 or root.winfo_screenheight() < 450:
        tiles.pack_forget()
    place(root, x=0, bottom=True)
    search.focus_set()
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
    root.configure(bg=DARK)
    body = tk.Frame(root, bg=DARK, padx=18, pady=15)
    body.pack(fill="both", expand=True)
    dark_label(body, "Açıq pəncərələr", size=17, bold=True).pack(fill="x", pady=(0, 12))
    if not windows:
        dark_label(body, "Hazırda açıq tətbiq yoxdur.", fg=SOFT).pack(pady=10)
        dark_button(body, "Bağla", root.destroy, padx=12, pady=6).pack()
        place(root)
        root.mainloop()
        return

    area = tk.Frame(body, bg=DARK)
    area.pack(fill="both", expand=True)
    width = min(root.winfo_screenwidth() - 52, 475)
    canvas = tk.Canvas(area, bg=DARK, bd=0, highlightthickness=0, width=width,
                       height=min(len(windows), 5) * 48)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar = ttk.Scrollbar(area, orient="vertical", command=canvas.yview)
    if len(windows) > 5:
        scrollbar.pack(side="right", fill="y")
    canvas.configure(yscrollcommand=scrollbar.set)
    cards = tk.Frame(canvas, bg=DARK)
    canvas.create_window(0, 0, window=cards, anchor="nw", width=width)
    cards.bind("<Configure>", lambda event: canvas.configure(scrollregion=canvas.bbox("all")))
    controls = []
    selected = next((i for i, (wid, _, _) in enumerate(windows) if str(int(wid, 16)) == active), 0)
    offset = {"left": -1, "right": 1}.get(direction, 0)
    selected = (selected + offset) % len(windows)

    def activate(index):
        window_id = windows[index][0]
        root.destroy()
        command("xdotool", "windowactivate", window_id)

    def close(index):
        window_id = windows[index][0]
        root.destroy()
        command("xdotool", "windowactivate", "--sync", window_id)
        command("xdotool", "key", "alt+F4")
        launch("relife-desktop", "switch")

    def select(index):
        nonlocal selected
        controls[selected].configure(bg=CARD, highlightbackground=CARD)
        selected = index
        controls[selected].configure(bg="#005a9e", highlightbackground="#1a86d9")
        root.update_idletasks()
        if selected >= 4 or canvas.canvasy(0) > selected * 48:
            canvas.yview_moveto(max(0, selected - 3) / len(windows))
        return "break"

    for index, (_, title, icon) in enumerate(windows):
        row = tk.Frame(cards, bg=DARK, height=48)
        row.pack(fill="x")
        row.pack_propagate(False)
        label = title if len(title) <= 43 else title[:42] + "…"
        button = dark_button(row, label, lambda index=index: activate(index),
                             icon=icon, anchor="w", padx=5)
        button.pack(side="left", fill="both", expand=True, pady=(0, 4))
        controls.append(button)
        dark_button(row, "×", lambda index=index: close(index), padx=10).pack(
            side="right", fill="y", padx=(4, 0), pady=(0, 4))
    dark_label(body, "Oxlarla seç · Enter ilə aç · Esc ilə çıx", fg=SOFT).pack(anchor="w", pady=(10, 0))
    dark_button(body, "Seçilmiş pəncərəni aç", lambda: activate(selected), bg="#005a9e",
                padx=20, pady=6).pack(anchor="e", pady=(10, 0))
    for key, step in (("Left", -1), ("Up", -1), ("Right", 1), ("Down", 1)):
        root.bind(f"<{key}>", lambda event, step=step: select((selected + step) % len(windows)))
    root.bind("<Return>", lambda event: activate(selected))
    root.bind("<Button-4>", lambda event: canvas.yview_scroll(-1, "units"))
    root.bind("<Button-5>", lambda event: canvas.yview_scroll(1, "units"))
    place(root)
    select(selected)
    root.focus_set()
    root.mainloop()


def nm_fields(line):
    fields, field, escaped = [], [], False
    for char in line:
        if escaped:
            field.append(char)
            escaped = False
        elif char == "\\":
            escaped = True
        elif char == ":":
            fields.append("".join(field))
            field.clear()
        else:
            field.append(char)
    return fields + ["".join(field)]


def nmcli(*args, timeout=5):
    return subprocess.run(["nmcli", *args], capture_output=True, text=True, errors="replace",
                          env={**os.environ, "LC_ALL": "C"}, timeout=timeout, check=True).stdout.strip()


def network():
    root = panel("RelifeNetwork", "Şəbəkə")
    root.wm_attributes("-type", "dialog")
    root.attributes("-topmost", True)
    root.configure(bg="#1f1f1f", highlightbackground=EDGE, highlightthickness=1)
    body = tk.Frame(root, bg="#1f1f1f", padx=14, pady=13)
    body.pack(fill="both", expand=True)
    dark_label(body, "Şəbəkə", bg="#1f1f1f", size=17, bold=True).pack(fill="x")
    connected = tk.StringVar(value="Şəbəkə yoxlanılır…")
    dark_label(body, variable=connected, bg=CARD, padx=10, pady=8, height=3,
               wraplength=310).pack(fill="x", pady=8)
    entries = tk.Listbox(body, height=6, width=32, bg=CARD, fg=WHITE,
                         borderwidth=0, highlightthickness=1, highlightbackground=EDGE,
                         selectbackground="#005a9e", exportselection=False)
    entries.pack(fill="x", pady=(0, 8))
    status = tk.StringVar()
    dark_label(body, variable=status, bg="#1f1f1f", fg=SOFT, height=2, wraplength=310).pack(fill="x")
    rows = []
    wifi_devices = []
    results = queue.Queue()
    busy = False

    def snapshot():
        devices = [nm_fields(line) for line in nmcli(
            "-t", "-f", "DEVICE,TYPE,STATE,CONNECTION", "device", "status").splitlines()]
        adapters = [item for item in devices if len(item) == 4 and item[1] in ("wifi", "ethernet")]
        current = [item for item in adapters if item[2] == "connected"]
        summary = "Qoşulu şəbəkə yoxdur"
        if current:
            device, kind, _, name = current[0]
            details = nmcli("-g", "IP4.ADDRESS,IP4.GATEWAY", "device", "show", device).splitlines()
            summary = f"{name or device} · {'Wi-Fi' if kind == 'wifi' else 'Kabel'}"
            if details and details[0]:
                summary += f"\nIP  {details[0]}"
            if len(details) > 1 and details[1]:
                summary += f"\nKeçid  {details[1]}"
        visible = [(name or dev, dev, state, "ethernet") for dev, kind, state, name in adapters if kind == "ethernet"]
        if any(kind == "wifi" for _, kind, _, _ in adapters):
            scan = nmcli("-t", "-f", "SSID,SIGNAL,SECURITY,IN-USE", "device", "wifi", "list", "--rescan", "no")
            names = set()
            for line in scan.splitlines():
                item = nm_fields(line)
                if len(item) == 4 and item[0] and item[0] not in names:
                    name, level, security, used = item
                    names.add(name)
                    visible.append((f"{name}  {level}%", name, "connected" if used == "*" else security, "wifi"))
        return summary, visible, [device for device, kind, state, _ in current if kind == "wifi"]

    def work(args):
        try:
            if args:
                nmcli("--wait", "12", *args, timeout=14)
            results.put((snapshot(), ""))
        except (OSError, subprocess.SubprocessError):
            results.put((None, "Əməliyyat alınmadı. Şəbəkə seçimini açıb yenidən yoxla."))

    def collect():
        nonlocal busy
        try:
            result, message = results.get_nowait()
        except queue.Empty:
            root.after(100, collect)
            return
        busy = False
        status.set(message)
        if result:
            summary, visible, active_wifi = result
            wifi_devices[:] = active_wifi
            connected.set(summary)
            rows[:] = visible
            entries.delete(0, "end")
            for name, _, state, kind in rows:
                entries.insert("end", f"{'●' if state == 'connected' else '○'}  {name}")

    def refresh(*args):
        nonlocal busy
        if busy:
            return
        busy = True
        status.set("Yoxlanılır…")
        threading.Thread(target=work, args=(args,), daemon=True).start()
        root.after(100, collect)

    def advanced():
        launch("xterm", "-T", "Şəbəkəyə qoşul", "-e", "nmtui", "connect")

    def join():
        selection = entries.curselection()
        if not selection:
            advanced()
            return
        _, name, state, kind = rows[selection[0]]
        if kind == "ethernet":
            refresh("device", "disconnect" if state == "connected" else "connect", name)
        elif state == "connected":
            refresh("device", "disconnect", next(iter(wifi_devices), name))
        elif state in ("", "--"):
            refresh("device", "wifi", "connect", name)
        else:
            advanced()

    row = tk.Frame(body, bg="#1f1f1f")
    row.pack(fill="x", pady=(7, 5))
    dark_button(row, "Qoşul / Ayır", join, bg="#005a9e", padx=8, pady=5).pack(side="left")
    dark_button(row, "Wi-Fi aç", lambda: refresh("radio", "wifi", "on"), padx=6, pady=5).pack(side="left", padx=4)
    dark_button(row, "Yenilə", refresh, padx=6, pady=5).pack(side="left")
    dark_button(body, "Şəbəkə seçimi", advanced, anchor="w", pady=4).pack(fill="x")
    dark_button(body, "Giriş səhifəsini aç",
                lambda: launch("relife-firefox", "http://detectportal.firefox.com/canonical.html"),
                anchor="w", pady=4).pack(fill="x", pady=(4, 0))
    root.update_idletasks()
    place(root, x=root.winfo_screenwidth() - root.winfo_reqwidth(), bottom=True)
    refresh()
    root.mainloop()


def calendar():
    root = panel("RelifeCalendar", "Təqvim")
    root.wm_attributes("-type", "dialog")
    root.attributes("-topmost", True)
    body = tk.Frame(root, bg=DARK, padx=14, pady=12)
    body.pack(fill="both")
    today = date.today()
    months = ("Yanvar", "Fevral", "Mart", "Aprel", "May", "İyun",
              "İyul", "Avqust", "Sentyabr", "Oktyabr", "Noyabr", "Dekabr")
    dark_label(body, f"{months[today.month - 1]} {today.year}", size=15, bold=True).grid(
        row=0, column=0, columnspan=7, sticky="ew", pady=(0, 9))
    for col, name in enumerate(("Be", "Ça", "Çə", "Ca", "Cü", "Şə", "Ba")):
        dark_label(body, name, fg=SOFT, width=4).grid(row=1, column=col)
    for row, week in enumerate(dates.monthcalendar(today.year, today.month), start=2):
        for col, number in enumerate(week):
            dark_label(body, str(number) if number else "", width=4, pady=5,
                       bg="#005a9e" if number == today.day else DARK).grid(row=row, column=col)
    root.update_idletasks()
    place(root, x=root.winfo_screenwidth() - root.winfo_reqwidth(), bottom=True)
    root.mainloop()


def system_info():
    root = panel("RelifeSystem", "Sistem məlumatı")
    ttk.Label(root, text="ReLife RAM", style="Header.TLabel").pack(fill="x")
    version = os.uname()
    memory = command("free", "-m").stdout
    ttk.Label(root, text=f"{version.sysname} {version.release} · {version.machine}\n\n{memory}",
              padding=20, font=("DejaVu Sans Mono", 9)).pack(fill="x")
    place(root)
    root.mainloop()



def new_folder():
    root = panel("RelifeNewFolder", "Yeni qovluq")
    name = simpledialog.askstring("Yeni qovluq", "Qovluğun adı", parent=root)
    if name and name.strip():
        name = name.strip()
        if name in (".", "..") or "/" in name:
            messagebox.showerror("Yeni qovluq", "Düzgün qovluq adı daxil et.", parent=root)
        else:
            try:
                (Path.home() / "Desktop" / name).mkdir()
            except OSError:
                messagebox.showerror("Yeni qovluq", "Qovluğu yaratmaq mümkün olmadı.", parent=root)
    root.destroy()


def refresh_desktop():
    command("pcmanfm", "--profile", "ReLife", "--desktop-off")
    launch("pcmanfm", "--profile", "ReLife", "--desktop")


def main():
    action = sys.argv[1] if len(sys.argv) > 1 else "start"
    if action == "start":
        start()
    elif action == "switch":
        switch(sys.argv[2] if len(sys.argv) > 2 else None)
    elif action == "network":
        network()
    elif action == "calendar":
        calendar()
    elif action == "system":
        system_info()
    elif action == "new-folder":
        new_folder()
    elif action == "refresh-desktop":
        refresh_desktop()


if __name__ == "__main__":
    main()
