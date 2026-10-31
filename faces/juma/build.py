"""Build the Juma watch face for the Haylou RT (LS05S):

    python -m faces.juma.build [palette ...]

With no palette named, this builds all of them into tbwf/ and previews/. haylou-rt-tools does the
generic work. Anything fixed, like the cub and icons, is drawn into the dial. Anything live, like the
time and steps, stays as text for the app to draw.
"""

import argparse
import os
from collections import namedtuple
from pathlib import Path

from haylou_tools.color import to_argb as argb
from haylou_tools.color import to_rgba as rgba
from haylou_tools.render import (
    CENTRE,
    CHARSETS,
    DAYS_EN,
    DAYS_PT,
    LEFT,
    RIGHT,
    digit_centre,
    draw_face,
    glyph_cell,
    size_px,
    whole_top,
)
from haylou_tools.tbwf import DIAL_SIZE as SIZE
from haylou_tools.tbwf import default_spec, solid, text, write_face
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).parent
SPRITE = ROOT / "art" / "juma-sprite.png"
FONT = ROOT / "fonts" / "juma.ttf"
NAME = "Juma"
NAME_SIZE = 36
NAME_Y = 22

PIXEL = 3
BATTERY_PX = 39
PAW = (
    "...##.##...",
    "...##.##...",
    ".##.....##.",
    ".##.###.##.",
    "...#####...",
    "..#######..",
    "..#######..",
    "...##.##...",
)
HEART = (
    ".##...##.",
    "####.####",
    "#########",
    "#########",
    ".#######.",
    "..#####..",
    "...###...",
    "....#....",
)
MITT = ("..########..", ".#oooooooo#.", "#oooooooooo#", "#cc#ccc#ccc#", "#cc#ccc#ccc#", ".##########.")
MITT_PX = 36
MITT_COLOURS = {"#": (0x2A, 0x1A, 0x10, 255), "o": (0xF9, 0xB9, 0x48, 255), "c": (0xFF, 0xF3, 0xD9, 255)}
LEDGE_Y = 222
CHIN = 62
FACE_SCALE = 6  # In half pixels, so 3x.

Palette = namedtuple("Palette", "sky disc ground ink accent alert text")
PALETTES = {
    "sky": Palette("#6FD3E6", "#A6E6F0", "#000000", "#122B4A", "#FFC24D", "#C8102E", "#FFFFFF"),
    "pantanal": Palette("#FFD9A8", "#FFE9C9", "#1B1330", "#3A2018", "#FFB347", "#D93A1F", "#FFF4E3"),
    "sakura": Palette("#FFC7DA", "#FFE1EA", "#241433", "#4A1D3A", "#FFD166", "#D81B60", "#FFF1F6"),
    "jungle": Palette("#BFE8C8", "#DDF4DF", "#0B1F1C", "#123D32", "#FFC24D", "#D7263D", "#F6F1D3"),
}

TIME_SIZE = 0.22
TIME_Y = 0.555
TIME_GAP = 0.014
ROW_SIZE = 0.062
ROW_Y = 0.795
STAT_SIZE = 0.055
STAT_TEXT_Y = 0.385
ICON_Y = 146
PAW_X, HEART_X = 0.137, 0.863
DATE_END, BATTERY_START = 0.47, 0.53
DAY_GAP = 8
BATTERY_GAP = 6
SHORT_DAY = 1

IRIS = (0x8B, 0x64, 0x45)
IRIS_GREY = 0x55  # The sprite's main iris grey, which becomes IRIS exactly.
EYE_X = ((29, 43), (55, 70))
EYE_Y = (35, 50)

SAMPLE = {
    "hour": "10",
    "timeSeparator": ":",
    "minute": "48",
    "dayOfWeek": "Fri",
    "day": "30",
    "battery": "80",
    "step": "8542",
    "heartRate": "72",
}


def bitmap(rows, color, scale=PIXEL):
    img = Image.new("RGBA", (len(rows[0]), len(rows)))
    for y, row in enumerate(rows):
        for x, c in enumerate(row):
            if c == "#":
                img.putpixel((x, y), color)
    return img.resize((img.width * scale, img.height * scale), Image.NEAREST)


def battery_icon(level, full, low):
    # One image per 10%, centred on a square canvas because the app scales them square.
    color = low if level <= 20 else full
    bars = (level + 9) // 10 if level else 0
    rows = ["#" * 12 + ".", "#" + "." * 10 + "#."]
    rows += ["#" + "#" * bars + "." * (10 - bars) + "##"] * 3
    rows += [rows[1], rows[0]]
    icon = bitmap(rows, color)
    canvas = Image.new("RGBA", (BATTERY_PX, BATTERY_PX))
    canvas.paste(icon, ((BATTERY_PX - icon.width) // 2, (BATTERY_PX - icon.height) // 2), icon)
    return canvas


def mitt_icon():
    # Drawn fresh: the sprite's own paws carry leg spots that turn to mud when cropped.
    img = Image.new("RGBA", (len(MITT[0]), len(MITT)))
    for y, row in enumerate(MITT):
        for x, c in enumerate(row):
            if c in MITT_COLOURS:
                img.putpixel((x, y), MITT_COLOURS[c])
    return img.resize((img.width * 3, img.height * 3), Image.NEAREST)


def brown_eyes(art):
    # The iris is the neutral grey under the pupil. Skin is saturated and the sparkle too bright to match.
    for left, right in EYE_X:
        for x in range(left, right):
            for y in range(*EYE_Y):
                r, g, b, a = art.getpixel((x, y))
                if 0x22 <= max(r, g, b) <= 0xA0 and max(r, g, b) - min(r, g, b) <= 16:
                    art.putpixel((x, y), tuple(min(255, c * g // IRIS_GREY) for c in IRIS) + (a,))
    return art


def icon_left(rows, centre):
    return (centre * SIZE - len(rows[0]) * PIXEL / 2) / SIZE


def icon_box(rows, centre):
    left = int(icon_left(rows, centre) * SIZE)
    return left, ICON_Y, left + len(rows[0]) * PIXEL, ICON_Y + len(rows) * PIXEL


def paw_box():
    return icon_box(PAW, PAW_X)


def heart_box():
    return icon_box(HEART, HEART_X)


def dial(palette, sprite=SPRITE, font=FONT):
    # The face rests its chin on a ledge: it reads bigger, and black ears show against the sky.
    art = brown_eyes(Image.open(sprite).convert("RGBA"))
    image = Image.new("RGB", (SIZE, SIZE))
    d = ImageDraw.Draw(image)
    d.rectangle((0, 0, SIZE, LEDGE_Y), fill=rgba(palette.sky)[:3])
    d.ellipse((227 - 150, LEDGE_Y - 262, 227 + 150, LEDGE_Y + 38), fill=rgba(palette.disc)[:3])
    d.rectangle((0, LEDGE_Y, SIZE, SIZE), fill=rgba(palette.ground)[:3])
    face = art.crop((0, 0, 96, CHIN))
    side = (face.width * FACE_SCALE // 2, face.height * FACE_SCALE // 2)
    face = face.resize((side[0] * 2, side[1] * 2), Image.NEAREST).resize(side, Image.BOX)
    image.paste(face, ((SIZE - side[0]) // 2, LEDGE_Y - side[1] + 4), face)
    d.rectangle((0, LEDGE_Y, SIZE, LEDGE_Y + 7), fill=rgba(palette.accent)[:3])
    for x in (227 - 112, 227 + 112 - MITT_PX):
        mitt = mitt_icon()
        image.paste(mitt, (x, LEDGE_Y - mitt.height + 9), mitt)
    for rows, color, centre in ((PAW, palette.ink, PAW_X), (HEART, palette.alert, HEART_X)):
        icon = bitmap(rows, rgba(color))
        image.paste(icon, (int(icon_left(rows, centre) * SIZE), ICON_Y), icon)
    label = ImageFont.truetype(font, NAME_SIZE)
    d.text((SIZE // 2, NAME_Y), NAME, font=label, fill=rgba(palette.ink)[:3], anchor="mt")
    return image


def show_only_what_juma_uses(spec):
    e = spec["elements"]
    e["step"] = text(0, 0, STAT_SIZE, properties=16)
    e["heartRate"] = text(0, 0, STAT_SIZE, properties=16)
    e["battery"] = text(0, 0, ROW_SIZE, properties=LEFT)
    for name in ("stepResource", "heartRateResource", "month", "dateSeparator", "batteryPercentSign"):
        e[name]["visible"] = False
    e["batteryResource"]["visible"] = True
    e["batteryResource"]["resourceImage"]["size"] = BATTERY_PX / SIZE


def juma_layout(spec, font_path, palette):
    # Every value is pinned to an anchor, so a wider number grows away from what it sits beside.
    e = spec["elements"]
    family = "/font/" + os.path.basename(font_path)
    for item in e.values():
        if "font" in item:
            item["font"]["family"] = family
    colours = {
        "hour": palette.text,
        "timeSeparator": palette.accent,
        "minute": palette.text,
        "dayOfWeek": palette.accent,
        "day": palette.accent,
        "battery": palette.text,
        "step": palette.ink,
        "heartRate": palette.ink,
    }
    for name, color in colours.items():
        e[name]["color"] = solid(argb(color))

    def place(name, x, y, size, anchor):
        e[name].update(x=x, y=y, visible=True, properties=(e[name].get("properties", 0) & 7) | anchor)
        e[name]["font"]["size"] = size

    big = int(SIZE * TIME_SIZE)
    colon = glyph_cell(font_path, big, ":")
    spread = (colon.width / 2) / SIZE + TIME_GAP
    place("hour", 0.5 - spread, TIME_Y, TIME_SIZE, RIGHT)
    place("minute", 0.5 + spread, TIME_Y, TIME_SIZE, LEFT)
    # The colon's top sits at y like any element, so move it down onto the digits' middle.
    middle = digit_centre(font_path, big, CHARSETS["hour"])
    place("timeSeparator", 0.5, TIME_Y + (middle - colon.height / 2) / SIZE, TIME_SIZE, CENTRE)
    place("step", PAW_X, STAT_TEXT_Y, STAT_SIZE, CENTRE)
    place("heartRate", HEART_X, STAT_TEXT_Y, STAT_SIZE, CENTRE)
    place("day", DATE_END, ROW_Y, ROW_SIZE, RIGHT)
    small = size_px(e["day"])
    day_cell = glyph_cell(font_path, small, CHARSETS["day"])
    box = max(glyph_cell(font_path, small, DAYS_EN).width, glyph_cell(font_path, small, DAYS_PT).width)
    # Text and numbers measure their tops differently, so line them up by baseline.
    name_y = ROW_Y + (whole_top(font_path, small, DAYS_EN + DAYS_PT) - day_cell.top) / SIZE
    day_x = (DATE_END * SIZE - 2 * day_cell.width - DAY_GAP - box) / SIZE
    place("dayOfWeek", day_x, name_y, ROW_SIZE, RIGHT)
    e["dayOfWeek"]["properties"] = SHORT_DAY | RIGHT
    gauge_y = digit_centre(font_path, small, CHARSETS["battery"]) - BATTERY_PX / 2
    e["batteryResource"].update(x=BATTERY_START, y=ROW_Y + gauge_y / SIZE)
    place("battery", BATTERY_START + (BATTERY_PX + BATTERY_GAP) / SIZE, ROW_Y, ROW_SIZE, LEFT)
    e["battery"]["properties"] = LEFT  # Without bit 4 the app leaves off its % sign.


def juma_spec(palette, font=FONT):
    spec = default_spec()
    show_only_what_juma_uses(spec)
    juma_layout(spec, str(font), palette)
    return spec


def build(name, faces=ROOT / "tbwf", previews=ROOT / "previews"):
    palette = PALETTES[name]
    spec = juma_spec(palette)
    image = dial(palette)
    full, low = rgba(palette.accent), rgba(palette.alert)
    write_face(
        Path(faces) / ("juma-%s.tbwf" % name),
        spec,
        image,
        str(FONT),
        lambda level: battery_icon(level, full, low),
    )
    values = dict(SAMPLE, batteryResource=battery_icon(80, full, low))
    preview = draw_face(image, spec, values, str(FONT))
    preview.resize((240, 240), Image.LANCZOS).save(Path(previews) / ("preview-%s.png" % name))


def main(argv=None):
    parser = argparse.ArgumentParser(description="Build the Juma watch face.")
    parser.add_argument("palettes", nargs="*", help="any of %s; default: all" % ", ".join(PALETTES))
    names = parser.parse_args(argv).palettes or list(PALETTES)
    unknown = sorted(set(names) - set(PALETTES))
    if unknown:
        parser.error("unknown palette: %s" % ", ".join(unknown))
    for name in names:
        build(name)


if __name__ == "__main__":
    main()
