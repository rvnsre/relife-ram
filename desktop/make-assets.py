"""Rasterize the original ReLife desktop artwork using the Python standard library."""
import argparse
from pathlib import Path
import subprocess


def xpm(path, width, height, palette, pixel):
    path.parent.mkdir(parents=True, exist_ok=True)
    entries = [f"{width} {height} {len(palette)} 1"]
    entries.extend(f"{key} c {color}" for key, color in palette.items())
    entries.extend("".join(pixel(x, y) for x in range(width)) for y in range(height))
    path.write_text("/* XPM */\nstatic const char *image[] = {\n" +
                    ",\n".join(f'"{line}"' for line in entries) + "\n};\n")


def render(svg, output, width, height):
    output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["rsvg-convert", "-w", str(width), "-h", str(height),
                    "-o", str(output), str(svg)], check=True)


def theme_assets(theme):
    for suffix, background, glyph in (("A", "#FFFFFF", "#1A1A1A"), ("I", "#F3F3F3", "#5C5C5C"),
                                      ("O", "#E5E5E5", "#1A1A1A")):
        for name in ("close", "maximize", "restore", "minimize"):
            hover = "#E81123" if name == "close" and suffix == "O" else background

            def control(x, y):
                y %= 32
                x, y = x - 18, y - 11
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

            xpm(theme / f"{name}{suffix}.xpm", 46, 64, {".": hover, "w": "#FFFFFF" if name == "close" and suffix == "O" else glyph}, control)
        if suffix != "O":
            for part in "TB":
                xpm(theme / f"title{suffix}{part}.xpm", 1, 32, {".": background}, lambda x, y: ".")

    taskbar = theme / "taskbar"
    for name, base, stripe in (("taskbarbg", "#101010", "#2B2B2B"),
                               ("taskbuttonbg", "#222222", "#222222"),
                               ("taskbuttonactive", "#282828", "#0078D4"),
                               ("taskbuttonminimized", "#191919", "#191919"),
                               ("toolbuttonbg", "#101010", "#101010")):
        xpm(taskbar / f"{name}.xpm", 1, 40, {".": base, "-": stripe},
            lambda x, y: "-" if y >= 37 and name == "taskbuttonactive" or y == 0 and name == "taskbarbg" else ".")
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

    xpm(taskbar / "icewm.xpm", 92, 30, {" ": "None", "a": "#0078D4", "w": "#FFFFFF"}, start)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("overlay", type=Path)
    dest = parser.parse_args().overlay / "usr/share"
    artwork = Path(__file__).with_name("art")
    render(artwork / "desktop.svg", dest / "relife/desktop.png", 1920, 1080)
    theme_assets(dest / "icewm/themes/ReLife")
    from art.icons import PATHS
    for name, shape in PATHS.items():
        shade = "#ffffff" if name != "files" else "#eab94e"
        icon = dest / f"icons/relife/{name}.svg"
        icon.parent.mkdir(parents=True, exist_ok=True)
        icon.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'
                        f'<g fill="none" stroke="{shade}" stroke-width="1.7" stroke-linecap="round"'
                        f' stroke-linejoin="round">{shape}</g></svg>')
        render(icon, icon.with_suffix(".png"), 32, 32)
        render(icon, icon.with_name(f"{name}-24.png"), 24, 24)

    theme = dest / "icons/ReLife"
    (theme / "scalable/places").mkdir(parents=True, exist_ok=True)
    (theme / "index.theme").write_text(
        "[Icon Theme]\nName=ReLife\nInherits=Adwaita,hicolor\nDirectories=scalable/places\n"
        "[scalable/places]\nSize=48\nMinSize=16\nMaxSize=256\nType=Scalable\nContext=Places\n"
    )
    (theme / "scalable/places/folder.svg").write_text((dest / "icons/relife/files.svg").read_text())
    for name in ("folder-open", "folder-documents", "folder-download", "folder-desktop", "user-home"):
        alias = theme / f"scalable/places/{name}.svg"
        alias.unlink(missing_ok=True)
        alias.symlink_to("folder.svg")


if __name__ == "__main__":
    main()
