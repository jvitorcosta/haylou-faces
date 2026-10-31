# How the Juma watch face was made

This is the path from "can we edit this watch?" to a custom face for the Haylou RT (LS05S). It has
no official SDK, so most of the work was finding out how the watch and its phone app behave. The
protocol and file format details are in the
[haylou-rt-tools](https://github.com/jvitorcosta/haylou-rt-tools) docs.

**Status:** the face is built but not yet confirmed on a real watch, so the drawing rules below come
from reading the app, not from the screen.

## The short version

1. Look at the watch over Bluetooth from the PC.
2. Decompile the Hello Haylou Android app to learn its protocol and face format.
3. Learn that a BLE uploader isn't needed: community `.tbwf` faces are a ZIP the app imports.
4. Prove that route with a community face, then generate our own `.tbwf` files in Python.
5. Design the face: jaguar, then pixel sprites, then the anime cub named Juma.
6. Fix the alignment by reimplementing the app's text drawing rules in a PC preview.
7. Rebuild the layout, font and palette, tested against that preview.
8. Copy the file to the phone, and import it in the app's Editor tab.

## 1. Talking to the watch

The toolkit's `haylou survey` connected from the PC and listed the watch's Bluetooth services. That
gave its command service, plus a `d0ff` service that looks like the firmware updater. We
never touched that one, because that's the way to break a watch.

## 2. Reading the app

The commands weren't documented, so we decompiled Hello Haylou 3.7.19 with jadx and read its LS05S
handler. The decompiled source stays out of this repo.

That gave the frame format (a 9-byte header, then a protobuf payload), the command ids and the
pairing steps. The toolkit's Bluetooth commands proved them on the real watch by reading firmware and
battery, pairing, and showing a text alert on the screen.

## 3. Finding the real route for faces

Sending a compiled face over Bluetooth looked possible but risky. Then we found a better way:
faces on amazfitwatchfaces.com are `.tbwf` files, which are editable projects, not compiled faces.
Hello Haylou imports them and does the compiling and uploading itself. A community face, "Keep
Improving", loaded this way and showed correctly on the watch.

So our job shrank to writing a valid `.tbwf`. It's a ZIP holding:

- `TiBoWaFe.json`: all 30 elements with position, font, colour and visibility. Positions are
  fractions of the screen.
- `/resourceImage/...`: the 454 × 454 background and image resources.
- `/font/*.ttf`: optional bundled fonts.

## 4. Generating faces

`build.py` builds the whole face from a sprite, using the toolkit to write the ZIP. Anything
fixed, like the cub, name and icons, is drawn into the background image. Anything live, like the time, steps and battery, stays as text
for the app to draw.

## 5. Designing the face

The art went through several rounds:

- A jaguar image, then jaguar sprites, then a cute anime cub.
- Pixel art generated with PixelLab, cropped so the cub peeks over a ledge.
- The name Juma, then a custom font.

Rejected along the way: a rosette rim and spotted heart and battery icons (muddy at this size), and
Pixelify Sans (8542 read as 8848).

## 6. Fixing the alignment

The old face looked misaligned because our preview guessed how text was drawn. The app's real rules
came from its code:

| What the app does | What it caused |
|---|---|
| Text size is screen width × `font.size` | Our preview drew text about 20% too big |
| Digits go in equal-width cells, centred | A thin `1` floats in a wide gap |
| Each element's top comes from its whole character set, including `/` | The colon rode high against the digits |
| The day name is drawn whole, and its top comes from the font's ascent | "Fri" sat lower than the date |
| `properties` sets the anchor, and also the day name's form and the `%` sign | Faces asked for "Friday" without us knowing |

The toolkit's renderer now follows these rules, so the PC preview should match the watch. The first
font we used, Mochiy, scored only 0.46 on digit evenness, which explained the gaps. The second review
caught the charset and day name rules, which the first version had missed.

## 7. Redesigning it

- **Font:** The toolkit's `haylou font-score` scored six fonts on narrowest digit ÷ widest digit. Nunito
  Black was the only one over the 0.7 target, at 0.89. Its subset keeps accented letters so `sáb.` renders.
- **Layout:** values are pinned to anchors, so a longer number grows away from what's next to it.
- **Palette:** four options passed contrast tests. Sky's red needed darkening to be visible.
- **Eyes:** the grey iris became a warm mid brown, `#8B6445`.
- **Review:** design and accessibility critiques, then an independent code review of everything.
  Automated tests cover extreme values such as `18888` steps and `sáb.`.

## 8. Getting it onto the watch

| Trap | What happened | What works |
|---|---|---|
| Wrong app tab | Custom files says "Invalid watch face file" for a `.tbwf` | Import from the **Editor** tab; Custom files only takes `.bin` |
| Phone not visible | After replugging, it can fall back to charging | Choose **File transfer** again and check it's under This PC |
| Copy stalls | `CopyHere` hung from PowerShell 7 | Run it in `powershell.exe -STA`, then compare hashes |

## Still unknown

- Whether the text lands on the watch exactly as the preview shows. A photo will settle this.
- The screen's exact resolution, believed to be 240 × 240.
- Whether the day name appears in English or Portuguese.
- Whether single-digit days get a leading zero.
