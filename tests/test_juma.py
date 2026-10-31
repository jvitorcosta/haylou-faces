"""The Juma face's layout, palettes and built files."""

import json
import zipfile
from io import BytesIO

import pytest
from haylou_tools.color import contrast
from haylou_tools.render import CHARSETS, DAYS_EN, DAYS_PT, draw_value
from haylou_tools.tbwf import DIAL_NAME, SPEC_NAME
from haylou_tools.tbwf import DIAL_SIZE as SIZE
from PIL import Image, ImageChops

from faces.juma import build as build_face
from faces.juma.build import FONT, PALETTES, ROOT, SPRITE, juma_spec

JUMA = str(FONT)
DRIFT_PX = 2
BASE = {
    "hour": "20",
    "timeSeparator": ":",
    "minute": "48",
    "dayOfWeek": "Wed",
    "day": "30",
    "battery": "100",
    "step": "18888",
    "heartRate": "128",
}
EXTREME_VALUES = [
    dict(BASE, **change)
    for change in (
        {},
        {"hour": "11", "minute": "11"},
        {"dayOfWeek": "Sat"},
        {"dayOfWeek": "qua."},
        {"dayOfWeek": "s\u00e1b."},
        {"step": "0", "heartRate": "0"},
        {"battery": "0"},
        {"battery": "5"},
    )
]
CUB = (112, 0, 342, 232)
ICONS = (build_face.paw_box(), build_face.heart_box())


@pytest.fixture(scope="module")
def spec():
    return juma_spec(PALETTES["sky"])


def boxes(spec, values):
    out = {}
    for name, value in values.items():
        canvas = Image.new("RGB", (SIZE, SIZE))
        draw_value(canvas, spec["elements"][name], value, CHARSETS[name], JUMA, name == "dayOfWeek")
        out[name] = canvas.getbbox()
    e = spec["elements"]["batteryResource"]
    left, top = int(e["x"] * SIZE), int(e["y"] * SIZE)
    out["batteryResource"] = (left, top, left + build_face.BATTERY_PX, top + build_face.BATTERY_PX)
    return out


def centre_x(box):
    return (box[0] + box[2]) / 2


def centre_y(box):
    return (box[1] + box[3]) / 2


def test_colon_is_centred_on_digits(spec):
    found = boxes(spec, {"timeSeparator": ":", "hour": "00"})
    assert abs(centre_y(found["timeSeparator"]) - centre_y(found["hour"])) <= 2


def test_colon_is_centred_on_the_screen(spec):
    assert abs(centre_x(boxes(spec, {"timeSeparator": ":"})["timeSeparator"]) - SIZE / 2) <= 2


def test_time_gaps_match_either_side_of_the_colon(spec):
    found = boxes(spec, {"hour": "00", "timeSeparator": ":", "minute": "00"})
    left = found["timeSeparator"][0] - found["hour"][2]
    right = found["minute"][0] - found["timeSeparator"][2]
    assert abs(left - right) <= 3


def test_short_hour_hugs_the_colon(spec):
    assert abs(boxes(spec, {"hour": "9"})["hour"][2] - boxes(spec, {"hour": "19"})["hour"][2]) <= 3


@pytest.mark.parametrize("value", ("7", "72", "128", "8542", "18888"))
def test_stats_stay_centred_under_icons(spec, value):
    found = boxes(spec, {"step": value, "heartRate": value})
    assert abs(centre_x(found["step"]) - centre_x(ICONS[0])) <= 2
    assert abs(centre_x(found["heartRate"]) - centre_x(ICONS[1])) <= 2


@pytest.mark.parametrize("values", EXTREME_VALUES)
def test_nothing_is_clipped_by_the_round_edge(spec, values):
    margin = 6
    for box in list(boxes(spec, values).values()) + list(ICONS):
        for x in (box[0], box[2]):
            for y in (box[1], box[3]):
                assert ((x - 227) ** 2 + (y - 227) ** 2) ** 0.5 <= 227 - margin


@pytest.mark.parametrize("values", EXTREME_VALUES)
def test_nothing_overlaps(spec, values):
    items = list(boxes(spec, values).items()) + [("paw", ICONS[0]), ("heart", ICONS[1]), ("cub", CUB)]
    for i, (a, x) in enumerate(items):
        for b, y in items[i + 1 :]:
            assert x[2] <= y[0] or y[2] <= x[0] or x[3] <= y[1] or y[3] <= x[1], (a, b)


def test_day_gap_stays_tight_in_both_languages(spec):
    for days in ("Sun", "dom."):
        charset = DAYS_EN if days == "Sun" else DAYS_PT
        canvas = Image.new("RGB", (SIZE, SIZE))
        draw_value(canvas, spec["elements"]["dayOfWeek"], days, charset, JUMA, True)
        gap = boxes(spec, {"day": "30"})["day"][0] - canvas.getbbox()[2]
        assert 4 <= gap <= 22


def test_day_name_is_the_short_form(spec):
    assert spec["elements"]["dayOfWeek"]["properties"] & 7 == 1


def test_day_name_shares_the_dates_baseline(spec):
    found = boxes(spec, {"dayOfWeek": "Fri", "day": "30"})
    assert abs(found["dayOfWeek"][3] - found["day"][3]) <= 2


def test_battery_icon_is_centred_on_its_number(spec):
    found = boxes(spec, {"battery": "80"})
    assert abs(centre_y(found["batteryResource"]) - centre_y(found["battery"])) <= 2


def test_battery_has_no_percent_sign(spec):
    # Bit 4 makes the app add a shrunk % that the layout doesn't leave room for.
    assert spec["elements"]["battery"]["properties"] == 16


def read(path):
    with zipfile.ZipFile(path) as z:
        return {name: z.read(name) for name in z.namelist()}


def same_spec(built, committed):
    # Glyphs measure slightly differently per platform, so positions may drift a little.
    if isinstance(built, dict):
        return built.keys() == committed.keys() and all(same_spec(built[k], committed[k]) for k in built)
    if isinstance(built, list):
        return len(built) == len(committed) and all(map(same_spec, built, committed))
    if isinstance(built, float):
        return abs(built - committed) <= DRIFT_PX / SIZE
    return built == committed


@pytest.mark.parametrize("name", PALETTES)
def test_committed_faces_match_this_code(name, tmp_path):
    build_face.build(name, tmp_path, tmp_path)
    built = read(tmp_path / ("juma-%s.tbwf" % name))
    committed = read(ROOT / "tbwf" / ("juma-%s.tbwf" % name))
    assert built.keys() == committed.keys()
    assert same_spec(build_spec(built), build_spec(committed))
    pictures = [Image.open(BytesIO(faces[DIAL_NAME])).convert("L") for faces in (built, committed)]
    different = ImageChops.difference(*pictures).point(lambda value: 255 if value > 32 else 0)
    assert different.histogram()[255] <= SIZE * SIZE // 100


def build_spec(files):
    return json.loads(files[SPEC_NAME])


def test_face_bundles_the_font_it_names(tmp_path):
    build_face.build("sakura", tmp_path, tmp_path)
    files = read(tmp_path / "juma-sakura.tbwf")
    elements = build_spec(files)["elements"]
    assert len(elements) == 30 and elements["hour"]["font"]["family"] in files


def test_unknown_palette_is_refused():
    with pytest.raises(SystemExit):
        build_face.main(["nope"])


@pytest.mark.parametrize("p", PALETTES.values())
def test_ink_reads_on_sky_and_disc(p):
    assert contrast(p.ink, p.sky) >= 4.5 and contrast(p.ink, p.disc) >= 4.5


@pytest.mark.parametrize("p", PALETTES.values())
def test_text_and_accent_read_on_ground(p):
    assert contrast(p.text, p.ground) >= 7 and contrast(p.accent, p.ground) >= 4.5


@pytest.mark.parametrize("p", PALETTES.values())
def test_ears_stand_out_from_the_sky(p):
    assert contrast("#2A1A10", p.sky) >= 3


@pytest.mark.parametrize("p", PALETTES.values())
def test_low_battery_is_visible(p):
    assert contrast(p.alert, p.ground) >= 3


@pytest.mark.parametrize("p", PALETTES.values())
def test_heart_stands_out_from_the_sky(p):
    assert contrast(p.alert, p.sky) >= 3


def test_time_block_sits_low_enough_on_the_round_screen(spec):
    assert boxes(spec, {"day": "30"})["day"][1] >= 355


def eye_pixels(art):
    return [
        art.getpixel((x, y))[:3]
        for x0, x1 in build_face.EYE_X
        for x in range(x0, x1)
        for y in range(*build_face.EYE_Y)
    ]


def test_iris_turns_brown():
    art = build_face.brown_eyes(Image.open(SPRITE).convert("RGBA"))
    assert sum(1 for r, g, b in eye_pixels(art) if r > b + 25 and 60 < r < 200 and g < r) >= 60


def test_pupil_stays_black():
    before = Image.open(SPRITE).convert("RGBA")
    after = build_face.brown_eyes(before.copy())
    assert sum(1 for c in eye_pixels(before) if max(c) < 20) == sum(
        1 for c in eye_pixels(after) if max(c) < 20
    )


def test_spots_outside_the_eyes_stay_grey():
    before = Image.open(SPRITE).convert("RGBA")
    after = build_face.brown_eyes(before.copy())
    (left, _), (_, right) = build_face.EYE_X
    top, bottom = build_face.EYE_Y
    for x in range(96):
        for y in range(62):
            if not (top <= y < bottom and any(a <= x < b for a, b in build_face.EYE_X)):
                assert before.getpixel((x, y)) == after.getpixel((x, y))
