# Haylou faces

Custom watch faces for the **Haylou RT (LS05S)**, built with
[haylou-rt-tools](https://github.com/jvitorcosta/haylou-rt-tools).

**Status:** early. No face here is confirmed on a real watch yet.

## Why I built it

I made these to use the tools from haylou-rt-tools on a real face, since the Haylou RT has no official way to make your own.

## Faces

| Face | Preview | About |
|---|---|---|
| [Juma](faces/juma) | ![Juma](faces/juma/previews/preview-pantanal.png) | A jaguar cub peeking over a ledge, in four palettes |

These are PC previews, and none of these faces is confirmed on a real watch yet, so what you see
there may differ slightly. A photo in an issue is very welcome.

## Install a face

1. Download a `.tbwf` from the face's `tbwf/` folder.
2. Copy it to your phone.
3. Pair [Hello Haylou](https://play.google.com/store/apps/details?id=hu.tiborsosdevs.haylou.hello) in
   Standalone mode.
4. Import the file from the **Editor** tab. The Custom files tab rejects `.tbwf`.

Tested only with Hello Haylou 3.7.19 on firmware `V21.01.004.2.1.1.3.51`.

## Build the faces

Needs Python 3.10 or newer.

```bash
pip install -r requirements.txt
```

Each face has its own build command, listed in its README. Run the tests with:

```bash
python -m pytest
```

## Add a face

Give it a folder under `faces/`, with a `build.py`, its art and fonts, and its built files in `tbwf/`
and `previews/`. Add a README, tests in `tests/`, a row in the table above, and any third-party
material in [THIRD_PARTY.md](THIRD_PARTY.md). Bundle only fonts whose licence allows it.

## Licence

Code is [MIT](LICENSE). Art and built faces are [CC BY 4.0](LICENSE-ART). Fonts keep their own
licences, listed in [THIRD_PARTY.md](THIRD_PARTY.md).

This is an unofficial fan project with no warranty. It isn't connected to Haylou or to Hello Haylou,
which is an independent app by a separate developer. Those names belong to their respective owners.
