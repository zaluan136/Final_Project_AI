"""Generate wall damage and six transparent destruction frames using Pygame.

Run this file to regenerate only these effects; no window or Pillow required.
"""

from pathlib import Path
import pygame

OUT = Path(__file__).resolve().parent


def damaged_wall(hp):
    image = pygame.Surface((32, 32), pygame.SRCALPHA)
    image.fill("#5f4938")
    for y, offset in ((1, 0), (11, 8), (21, 0)):
        pygame.draw.rect(image, "#a37852", (1, y, 30, 9))
        pygame.draw.line(image, "#c79965", (1, y), (30, y), 2)
        for x in range(offset, 32, 16):
            pygame.draw.rect(image, "#493b32", (x, y, 2, 9))
    pygame.draw.lines(
        image, "#2b241f", False, [(16, 0), (12, 8), (18, 13), (13, 21), (18, 31)], 2
    )
    if hp == 1:
        pygame.draw.lines(
            image,
            "#251f1c",
            False,
            [(0, 13), (11, 16), (18, 13), (25, 21), (31, 19)],
            2,
        )
        pygame.draw.polygon(
            image, (0, 0, 0, 0), [(13, 10), (20, 13), (16, 21), (10, 17)]
        )
        pygame.draw.lines(image, "#e2ae79", False, [(12, 9), (20, 12), (17, 19)], 1)
    return image


def breaking_wall(frame):
    image = pygame.Surface((64, 64), pygame.SRCALPHA)
    alpha = round(255 * (1 - frame / 6))
    # Six brick pieces spread outward, shrink and fade. No persistent rubble.
    for x, y, vx, vy in (
        (-11, -10, -2, -2),
        (0, -11, 0, -3),
        (10, -8, 2, -2),
        (-10, 5, -3, 1),
        (1, 2, 1, 2),
        (10, 9, 2, 3),
    ):
        px, py = 32 + x + vx * frame, 32 + y + vy * frame
        size = max(2, 10 - frame)
        rect = pygame.Rect(px - size // 2, py - size // 2, size, size - 2)
        pygame.draw.rect(image, (163, 120, 82, alpha), rect)
        pygame.draw.line(image, (221, 172, 116, alpha), rect.topleft, rect.topright, 1)
        pygame.draw.line(
            image, (74, 57, 41, alpha), rect.bottomleft, rect.bottomright, 1
        )
    return image


if __name__ == "__main__":
    for hp in (1, 2):
        pygame.image.save(damaged_wall(hp), str(OUT / f"wall_hp_{hp}.png"))
    for frame in range(6):
        pygame.image.save(breaking_wall(frame), str(OUT / f"wall_break_{frame}.png"))
