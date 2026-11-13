"""Generate the 32 px pixel-art sprites used by the playground."""

from pathlib import Path
import sys
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent
S = 32


def sprite(name, paint):
    image = Image.new("RGBA", (S, S))
    draw = ImageDraw.Draw(image)
    paint(draw)
    image.save(OUT / f"{name}.png")


def ground(d):
    d.rectangle((0, 0, 31, 31), fill="#394936")
    d.rectangle((0, 0, 31, 1), fill="#526044")
    d.rectangle((3, 5, 7, 6), fill="#536449")
    d.rectangle((19, 3, 24, 4), fill="#536449")
    d.rectangle((10, 17, 15, 18), fill="#273a2e")
    d.rectangle((24, 24, 28, 25), fill="#273a2e")
    d.point([(4, 23), (26, 11), (17, 27)], fill="#718053")


def wall(d):
    d.rectangle((0, 0, 31, 31), fill="#5f4938")
    for y, offset in ((1, 0), (11, 8), (21, 0)):
        d.rectangle((1, y, 30, y + 8), fill="#a37852")
        d.line((1, y, 30, y), fill="#c79965", width=2)
        for x in range(offset, 32, 16):
            d.rectangle((x, y, x + 1, y + 8), fill="#493b32")
    d.line((0, 31, 31, 31), fill="#352f2b", width=2)


def tank(d, body, light, dark):
    d.rectangle((4, 7, 9, 27), fill="#1b2525")
    d.rectangle((22, 7, 27, 27), fill="#1b2525")
    for y in (9, 15, 21):
        d.line((5, y, 8, y), fill="#66716a", width=2)
        d.line((23, y, 26, y), fill="#66716a", width=2)
    d.rounded_rectangle((9, 8, 22, 27), radius=3, fill=body, outline=dark, width=2)
    d.rectangle((14, 1, 18, 14), fill=dark)
    d.rectangle((15, 1, 17, 11), fill=light)
    d.ellipse((10, 11, 21, 22), fill=light, outline=dark, width=2)
    d.rectangle((13, 15, 18, 18), fill=body)
    d.line((10, 25, 21, 25), fill=light, width=2)


def base(d, body, light, dark):
    d.rectangle((2, 2, 29, 29), fill="#1d2829")
    d.rectangle((4, 4, 27, 27), fill=dark)
    d.rectangle((6, 6, 25, 25), fill=body)
    d.rectangle((8, 8, 23, 23), outline=light, width=2)
    d.polygon([(16, 9), (22, 16), (16, 23), (10, 16)], fill=light)
    d.rectangle((14, 14, 17, 17), fill=dark)
    for x in (3, 27):
        for y in (3, 27):
            d.rectangle((x, y, x + 2, y + 2), fill=light)


def bullet(d):
    d.ellipse((11, 8, 20, 21), fill="#ffefaa")
    d.ellipse((13, 10, 18, 18), fill="#fff9df")
    d.polygon([(12, 21), (19, 21), (16, 28)], fill="#ff8c3c")


def flash(d, frame):
    lengths = (8, 13, 10, 5)
    tip = lengths[frame]
    d.polygon([(16, 14), (12, 7), (16, 8 - tip), (20, 7)], fill="#ff912e")
    d.polygon([(16, 12), (14, 6), (16, 8 - tip // 2), (18, 6)], fill="#fff2a0")
    d.point((16, max(0, 7 - tip)), fill="#ffffff")


def tracer(d, frame):
    """Up-facing dash/arrow stages on a transparent 32 px canvas."""
    length = (18, 11, 5)[frame]
    d.line((16, 9, 16, 9 + length), fill=(255, 180, 70, 190), width=3)
    d.line((16, 8, 16, 9 + length), fill=(255, 246, 190, 255), width=1)
    d.line((12, 12, 16, 6, 20, 12), fill=(255, 240, 160, 255), width=2)


for i in range(3):
    sprite(f"tracer_{i}", lambda d, i=i: tracer(d, i))

# Regenerate only the tracer assets without overwriting existing artwork.
if "--trails-only" in sys.argv:
    sys.exit(0)

sprite("ground", ground)
sprite("wall", wall)
sprite("tank_a", lambda d: tank(d, "#398fc0", "#75d3ed", "#20516d"))
sprite("tank_b", lambda d: tank(d, "#cb5c49", "#ffab77", "#773b38"))
sprite("tank_neutral", lambda d: tank(d, "#8a9491", "#c4d0bb", "#4e5d58"))
sprite("base_a", lambda d: base(d, "#398fc0", "#80d5ed", "#20516d"))
sprite("base_b", lambda d: base(d, "#cb5c49", "#ffc085", "#773b38"))
sprite("bullet", bullet)
for i in range(4):
    sprite(f"fire_{i}", lambda d, i=i: flash(d, i))
