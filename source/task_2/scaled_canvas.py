import pygame


class ScaledText:
    def __init__(self, surface, scale):
        self.surface = surface
        self.scale = scale

    def get_rect(self, **kwargs):
        width, height = self.surface.get_size()
        rect = pygame.Rect(0, 0, round(width / self.scale), round(height / self.scale))
        for name, value in kwargs.items():
            setattr(rect, name, value)
        return rect


class ScaledFont:
    def __init__(self, size, bold, scale):
        self.scale = scale
        self.font = pygame.font.SysFont(
            "segoeui", max(1, round(size * scale)), bold=bold
        )

    def render(self, text, antialias, color):
        return ScaledText(self.font.render(text, antialias, color), self.scale)

    def size(self, text):
        return tuple(round(value / self.scale) for value in self.font.size(text))


class ScaledCanvas:
    def __init__(self, size):
        self.surface = pygame.Surface(size)
        self.scale_x = size[0] / 1200
        self.scale_y = size[1] / 820

    def rect(self, rect):
        rect = pygame.Rect(rect)
        left = round(rect.left * self.scale_x)
        top = round(rect.top * self.scale_y)
        right = round(rect.right * self.scale_x)
        bottom = round(rect.bottom * self.scale_y)
        return pygame.Rect(left, top, max(1, right - left), max(1, bottom - top))

    def get_width(self):
        return 1200

    def get_height(self):
        return 820

    def fill(self, color):
        self.surface.fill(color)

    def blit(self, source, destination):
        if isinstance(destination, pygame.Rect):
            position = destination.topleft
        else:
            position = destination[:2]
        point = (round(position[0] * self.scale_x), round(position[1] * self.scale_y))
        if isinstance(source, ScaledText):
            self.surface.blit(source.surface, point)
        else:
            size = (
                max(1, round(source.get_width() * self.scale_x)),
                max(1, round(source.get_height() * self.scale_y)),
            )
            self.surface.blit(pygame.transform.scale(source, size), point)

    def get_clip(self):
        clip = self.surface.get_clip()
        return pygame.Rect(
            round(clip.x / self.scale_x),
            round(clip.y / self.scale_y),
            round(clip.width / self.scale_x),
            round(clip.height / self.scale_y),
        )

    def set_clip(self, rect):
        self.surface.set_clip(self.rect(rect))

    def draw_rect(self, color, rect, width=0, **kwargs):
        width = max(1, round(width * self.scale_x)) if width else 0
        if "border_radius" in kwargs:
            kwargs["border_radius"] = max(
                0, round(kwargs["border_radius"] * self.scale_x)
            )
        pygame.draw.rect(self.surface, color, self.rect(rect), width, **kwargs)

    def draw_circle(self, color, center, radius, width=0):
        point = (round(center[0] * self.scale_x), round(center[1] * self.scale_y))
        width = max(1, round(width * self.scale_x)) if width else 0
        pygame.draw.circle(
            self.surface, color, point, max(1, round(radius * self.scale_x)), width
        )
