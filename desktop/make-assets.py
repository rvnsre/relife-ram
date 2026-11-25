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
    if min(x - 2, 29 - x) + min(y - 2, 29 - y) < 4:
        return " "
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
    if kind in ("internet", "network"):
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
    width, height = 960, 600
    colors = ((12, 25, 43), (15, 37, 58), (22, 57, 77), (25, 76, 92), (34, 102, 111))
    rows = []
    for y in range(height):
        row = bytearray([0])
        for x in range(width):
            u, v = (x - 758) / 565, (y - 576) / 415
            field = math.hypot(u + .30 * v, v) + .17 * math.sin(u * 3.8 - v * 2.5)
            band = sum(field < bound for bound in (1.02, .81, .61, .41))
            light = round(5 * x / width + 3 * (1 - y / height))
            row.extend(channel + light for channel in colors[band])
        rows.append(row)

    png(path, width, height, 2, b"".join(rows))


def png(path, width, height, color_type, rows):
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"\x89PNG\r\n\x1a\n" +
                     chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, color_type, 0, 0, 0)) +
                     chunk(b"IDAT", zlib.compress(rows, 9)) + chunk(b"IEND", b""))


def theme_assets(theme):
    for suffix, background, glyph in (("A", "#183246", "#F1FAFF"), ("I", "#263746", "#CEDCE6"),
                                      ("O", "#34586D", "#FFFFFF")):
        for name in ("close", "maximize", "restore", "minimize"):
            hover = "#9E3049" if name == "close" and suffix == "O" else background

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
    for name, base, stripe in (("taskbarbg", "#101F2D", "#29475B"),
                               ("taskbuttonbg", "#182C3C", "#182C3C"),
                               ("taskbuttonactive", "#234B60", "#56D4C6"),
                               ("taskbuttonminimized", "#142434", "#142434"),
                               ("toolbuttonbg", "#101F2D", "#101F2D")):
        xpm(taskbar / f"{name}.xpm", 1, 32, {".": base, "-": stripe},
            lambda x, y: "-" if y == 31 and name == "taskbuttonactive" or y == 0 and name == "taskbarbg" else ".")
    xpm(taskbar / "icewm.xpm", 34, 30, {" ": "None", "a": "#66E0C8", "w": "#EAFBFF"},
        lambda x, y: "a" if 8 <= y <= 19 and (9 <= x <= 21 and abs(x - y - 2) <= 1) else
        "w" if 8 <= y <= 19 and (13 <= x <= 25 and abs(x + y - 31) <= 1) else " ")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("overlay", type=Path)
    dest = parser.parse_args().overlay / "usr/share"
    wallpaper(dest / "relife/desktop.png")
    theme_assets(dest / "icewm/themes/ReLife")
    colors = {"education": "#256D66", "files": "#A75B18", "write": "#3F5986",
              "help": "#555488", "internet": "#275E83", "network": "#275E83",
              "sound": "#3A5F76", "power": "#743E58"}
    for name, color in colors.items():
        xpm(dest / f"icons/relife/{name}.xpm", 32, 32, {" ": "None", ".": color, "w": "#FFFFFF"},
            lambda x, y: icon_pixel(name, x, y))
    glyphs = {" ": b"\0\0\0\0", "w": b"\xff" * 4, ".": bytes.fromhex("256d66ff")}
    rgba = b"".join(b"\0" + b"".join(glyphs[icon_pixel("education", x, y)] for x in range(32))
                    for y in range(32))
    png(dest / "icons/relife/education.png", 32, 32, 6, rgba)


if __name__ == "__main__":
    main()
