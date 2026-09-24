"""Recolor gh-space-shooter's GIF palettes without changing its animation."""

import os
import sys
from pathlib import Path


COLORS = {
    (0, 109, 50): (117, 80, 9),     # dark contribution square
    (38, 166, 65): (166, 106, 31),
    (57, 211, 83): (217, 155, 61),
    (87, 242, 135): (245, 199, 107),
    (41, 82, 136): (153, 99, 28),  # spaceship shadow
    (68, 147, 248): (255, 211, 112),
    (255, 223, 0): (245, 199, 107),  # projectiles
}


def skip_subblocks(data: bytearray, position: int) -> int:
    while True:
        size = data[position]
        position += 1
        if size == 0:
            return position
        position += size


def recolor_palette(data: bytearray, start: int, entries: int) -> int:
    changed = 0
    for index in range(entries):
        offset = start + 3 * index
        old = tuple(data[offset : offset + 3])
        if old in COLORS:
            data[offset : offset + 3] = bytes(COLORS[old])
            changed += 1
    return changed


def recolor_gif(path: Path) -> int:
    data = bytearray(path.read_bytes())
    if data[:6] not in (b"GIF87a", b"GIF89a"):
        raise ValueError(f"Not a GIF: {path}")

    position = 13
    changed = 0
    global_flags = data[10]
    if global_flags & 0x80:
        entries = 1 << ((global_flags & 0x07) + 1)
        changed += recolor_palette(data, position, entries)
        position += 3 * entries

    while position < len(data):
        marker = data[position]
        position += 1
        if marker == 0x3B:  # GIF trailer
            break
        if marker == 0x21:  # extension
            position += 1  # extension label
            position = skip_subblocks(data, position)
        elif marker == 0x2C:  # image frame
            flags = data[position + 8]
            position += 9  # image descriptor
            if flags & 0x80:
                entries = 1 << ((flags & 0x07) + 1)
                changed += recolor_palette(data, position, entries)
                position += 3 * entries
            position += 1  # LZW minimum code size
            position = skip_subblocks(data, position)
        else:
            raise ValueError(f"Unexpected GIF block 0x{marker:02x} at {position - 1}")

    if changed == 0:
        raise ValueError("No matching colors found; the generator palette may have changed")

    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(data)
    os.replace(temporary, path)
    return changed


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: recolor_space_shooter.py PATH_TO_GIF")
    count = recolor_gif(Path(sys.argv[1]))
    print(f"Recolored {count} GIF palette entries")
