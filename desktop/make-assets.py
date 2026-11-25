"""Rasterize the original ReLife desktop artwork using the Python standard library."""
import argparse
import math
from pathlib import Path
import struct
import zlib


def xpm(path, width, height, palette, pixel):
    path.parent.mkdir(parents=True, exist_ok=True)
    entries = [f"{width} {height} {len(palette)} 1"]
    entries.extend(f"{key} c {color}" for key, color in palette.items())
    entries.extend("".join(pixel(x, y) for x in range(width)) for y in range(height))
    path.write_text("/* XPM */\nstatic const char *image[] = {\n" +
                    ",\n".join(f'"{line}"' for line in entries) + "\n};\n")


def icon_pixel(kind, x, y):
    if not (2 <= x < 30 and 2 <= y < 30):
        return " "
    if math.hypot(max(8 - x, x - 23, 0), max(8 - y, y - 23, 0)) > 6:
        return " "
    if kind == "start":
        return "w" if (9 <= x <= 22 and y in (9, 10, 15, 16, 21, 22)) or (9 <= x <= 11 and 9 <= y <= 22) else "."
    if kind == "windows":
        return "w" if ((8 <= x <= 20 and 9 <= y <= 19 and (x in (8, 20) or y in (9, 19)))
                       or (12 <= x <= 24 and 13 <= y <= 23 and (x == 24 or y == 23))) else "."
    if kind == "network":
        radius = (x - 16)**2 + (y - 22)**2
        return "w" if ((y < 22 and (35 <= radius <= 63 or 102 <= radius <= 150))
                       or (14 <= x <= 17 and 21 <= y <= 24)) else "."
    if kind == "education":
        return "w" if (8 <= x <= 14 or 17 <= x <= 23) and (10 <= y <= 21 or (y == 22 and x in (14, 17))) else "."
    if kind == "files":
        return "w" if (7 <= x <= 24 and 13 <= y <= 22) or (8 <= x <= 14 and 10 <= y <= 12) else "."
    if kind == "write":
        if 11 <= x <= 20 and y in (13, 17, 21):
            return "."
        return "w" if 8 <= x <= 23 and 8 <= y <= 24 else "."
    if kind == "help":
        return "w" if (14 <= x <= 17 and y in range(15, 21)) or (14 <= x <= 17 and 9 <= y <= 11) else "."
    if kind == "internet":
        if 40 <= (x - 16)**2 + (y - 16)**2 <= 77:
            return "w"
        return "w" if (x in (15, 16, 17) and 8 <= y <= 24) or (y in (15, 16) and 8 <= x <= 24) else "."
    if kind == "sound":
        return "w" if (8 <= x <= 11 and 13 <= y <= 19) or (
            12 <= x <= 17 and abs(y - 16) <= x - 10
        ) or (19 <= x <= 24 and 26 <= (x - 17)**2 + (y - 16)**2 <= 48) else "."
    return "w" if (14 <= x <= 17 and 8 <= y <= 15) or (
        32 <= (x - 16)**2 + (y - 17)**2 <= 68 and (y >= 13 or abs(x - 16) >= 4)
    ) else "."


def wallpaper(path):
    width, height = 1152, 720
    rows = []
    for y in range(height):
        v = y / height
        row = bytearray()
        for x in range(width):
            u = x / width
            glow = math.exp(-7 * ((u - .76) ** 2 + (v - .25) ** 2))
            color = (int(47 + 34 * u + 74 * glow), int(39 + 69 * glow),
                     int(82 + 30 * u + 81 * glow))
            # Overlapping bands give the wallpaper depth without a large stored asset.
            ridge = .58 + .21 * math.sin((u - .21) * 4.5)
            for offset, thickness, light, dark in (
                (.14, .25, (106, 112, 205), (60, 53, 134)),
                (.03, .20, (162, 153, 243), (80, 68, 155)),
                (-.07, .14, (222, 193, 251), (117, 98, 192)),
            ):
                distance = (v - ridge - offset) / thickness
                if abs(distance) < 1:
                    gradient = (1 - distance) / 2
                    opacity = min(1, (1 - abs(distance)) * 55)
                    color = tuple(round(base + (lo + (hi - lo) * gradient - base) * opacity)
                                  for base, lo, hi in zip(color, dark, light))
            row.extend(color)
        # PNG's Sub filter keeps the smooth gradients compact.
        rows.append(bytes([1, *row[:3], *((row[i] - row[i - 3]) % 256 for i in range(3, len(row)))]))

    png(path, width, height, 2, b"".join(rows))


def png(path, width, height, color_type, rows):
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"\x89PNG\r\n\x1a\n" +
                     chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, color_type, 0, 0, 0)) +
                     chunk(b"IDAT", zlib.compress(rows, 9)) + chunk(b"IEND", b""))


def theme_assets(theme):
    for suffix, background, glyph in (("A", "#F6F3FE", "#29243F"), ("I", "#EFEDF6", "#655D7D"),
                                      ("O", "#E4DCF8", "#29243F")):
        for name in ("close", "maximize", "restore", "minimize"):
            hover = "#F5CCD8" if name == "close" and suffix == "O" else background

            def control(x, y):
                y %= 32
                x, y = x - 10, y - 11
                if name == "close":
                    visible = 0 <= x <= 9 and 0 <= y <= 9 and (abs(x - y) <= 1 or abs(x + y - 9) <= 1)
                elif name == "maximize":
                    visible = 0 <= x <= 9 and 0 <= y <= 9 and (x in (0, 9) or y in (0, 9))
                elif name == "restore":
                    visible = (0 <= x <= 7 and 2 <= y <= 9 and (x in (0, 7) or y in (2, 9))) or (
                        3 <= x <= 9 and 0 <= y <= 7 and (y == 0 or x == 9))
                else:
                    visible = 0 <= x <= 9 and y in (7, 8)
                return "w" if visible else "."

            xpm(theme / f"{name}{suffix}.xpm", 30, 64, {".": hover, "w": glyph}, control)
        if suffix != "O":
            for part in "TB":
                xpm(theme / f"title{suffix}{part}.xpm", 1, 32, {".": background}, lambda x, y: ".")

    taskbar = theme / "taskbar"
    for name, base, stripe in (("taskbarbg", "#F6F3FC", "#DFD9EF"),
                               ("taskbuttonbg", "#EEE9FA", "#EEE9FA"),
                               ("taskbuttonactive", "#E4DBFB", "#7055CD"),
                               ("taskbuttonminimized", "#F1EDF8", "#F1EDF8"),
                               ("toolbuttonbg", "#F6F3FC", "#F6F3FC")):
        xpm(taskbar / f"{name}.xpm", 1, 32, {".": base, "-": stripe},
            lambda x, y: "-" if y == 31 and name == "taskbuttonactive" or y == 0 and name == "taskbarbg" else ".")
    # The label is baked into the small IceWM start-button pixmap.
    label = (
        "███               █     ",
        "█  █              █     ",
        "███    ██   ███   █  ██ ",
        "█  █     █  █     █    █",
        "█  █   ███   ██   █  ███",
        "█  █  █  █     █  █ █  █",
        "███    ███  ███   █  ███",
        "              █         ",
    )

    def start(x, y):
        if 11 <= x <= 23 and 8 <= y <= 22:
            if abs(x - 16 - (6 - abs(y - 15))) <= 1:
                return "a"
        if 33 <= x < 81 and 7 <= y < 23 and label[(y - 7) // 2].ljust(24)[(x - 33) // 2] == "█":
            return "w"
        return " "

    xpm(taskbar / "icewm.xpm", 92, 30, {" ": "None", "a": "#6549C3", "w": "#302648"}, start)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("overlay", type=Path)
    dest = parser.parse_args().overlay / "usr/share"
    wallpaper(dest / "relife/desktop.png")
    theme_assets(dest / "icewm/themes/ReLife")
    colors = {"start":"#5A41BF", "windows":"#6954A4", "education": "#398074", "files": "#9D611C", "write": "#7152C2",
              "help": "#685596", "internet": "#3465AD", "network": "#3465AD",
              "sound": "#785798", "power": "#A34663"}
    for name, color in colors.items():
        xpm(dest / f"icons/relife/{name}.xpm", 32, 32, {" ": "None", ".": color, "w": "#FFFFFF"},
            lambda x, y: icon_pixel(name, x, y))
        glyphs = {" ": b"\0" * 4, "w": b"\xff" * 4, ".": bytes.fromhex(color[1:] + "ff")}
        rgba = b"".join(b"\0" + b"".join(glyphs[icon_pixel(name, x, y)] for x in range(32))
                        for y in range(32))
        png(dest / f"icons/relife/{name}.png", 32, 32, 6, rgba)


if __name__ == "__main__":
    main()
