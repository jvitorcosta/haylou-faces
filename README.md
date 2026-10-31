# Juma

A cute jaguar cub watch face for the **Haylou RT (LS05S)**, peeking over a ledge above the time.

| Pantanal | Sakura | Jungle | Sky |
|---|---|---|---|
| ![Pantanal](previews/preview-pantanal.png) | ![Sakura](previews/preview-sakura.png) | ![Jungle](previews/preview-jungle.png) | ![Sky](previews/preview-sky.png) |

These are PC previews. The face isn't yet confirmed on a real watch, so what you see there may differ
slightly. A photo in an issue is very welcome.

## Install it

1. Download a face from [faces/](faces).
2. Copy it to your phone.
3. Pair [Hello Haylou](https://play.google.com/store/apps/details?id=hu.tiborsosdevs.haylou.hello) in
   Standalone mode.
4. Import the file from the **Editor** tab. The Custom files tab rejects `.tbwf`.

Tested only with Hello Haylou 3.7.19 on firmware `V21.01.004.2.1.1.3.51`.

## Build it

Needs Python 3.10 or newer.

```bash
pip install -r requirements.txt
```

```bash
python build_face.py
```

That rebuilds every face into `faces/` and `previews/`. Name a palette to build one:

```bash
python build_face.py pantanal
```

Add a palette to `PALETTES` in [build_face.py](build_face.py). The tests check its contrast and that
nothing overlaps or gets clipped by the round screen:

```bash
python -m pytest
```

The generic code lives in [haylou-rt-tools](https://github.com/jvitorcosta/haylou-rt-tools). This
repository only holds what's specific to Juma: the art, layout and palettes.
[How it was made](docs/how-it-was-made.md) tells the whole story.

## Licence

Code is [MIT](LICENSE). The art and built faces are [CC BY 4.0](LICENSE-ART). The font is SIL OFL 1.1.
See [THIRD_PARTY.md](THIRD_PARTY.md).

This is an unofficial fan project with no warranty. It isn't connected to Haylou or to Hello Haylou,
which is an independent app by a separate developer. Those names belong to their respective owners.
