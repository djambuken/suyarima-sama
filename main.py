"""Suyarima-sama: a passcode-gated, generative falling-shapes visual."""

from __future__ import annotations

import math
import os
import random
import sys
from dataclasses import dataclass
from pathlib import Path

import pygame

try:
    import cv2
except ImportError:  # Video is optional; the generative scene still runs.
    cv2 = None


ROOT = Path(__file__).resolve().parent
VIDEO_PATH = ROOT / "assets" / "loop.mp4"
ACCESS_CODE = os.environ.get("SUYARIMA_CODE", "suyarima")
BACKGROUND = (23, 24, 28)
PURPLE = (153, 42, 174)
GREEN = (68, 196, 105)
RED = (255, 53, 74)


def rotate(point: tuple[float, float], angle: float) -> tuple[float, float]:
    x, y = point
    cosine, sine = math.cos(angle), math.sin(angle)
    return x * cosine - y * sine, x * sine + y * cosine


@dataclass
class Shape:
    x: float
    y: float
    radius: float
    sides: int
    color: tuple[int, int, int]
    speed: float
    rotation: float
    spin: float
    alpha: int = 150

    def points(self) -> list[tuple[int, int]]:
        vertices = []
        for index in range(self.sides):
            angle = math.tau * index / self.sides
            wobble = 0.78 + random.Random(index + self.sides).random() * 0.34
            px, py = rotate((math.cos(angle) * self.radius * wobble,
                             math.sin(angle) * self.radius * wobble), self.rotation)
            vertices.append((round(self.x + px), round(self.y + py)))
        return vertices

    def update(self, dt: float, width: int, height: int) -> None:
        self.y += self.speed * dt
        self.x += math.sin(self.y * 0.004 + self.rotation) * 8 * dt
        self.rotation += self.spin * dt
        if self.y - self.radius > height + 10:
            self.y = -self.radius - random.randrange(20, 180)
            self.x = random.randrange(max(width, 1))

    def draw(self, target: pygame.Surface) -> None:
        vertices = self.points()
        pygame.draw.polygon(target, (*self.color, 15), vertices, 0)
        pygame.draw.polygon(target, (*self.color, self.alpha), vertices, 1)
        # A second, offset outline gives the thin, fractured wireframe look.
        inner = [(int(self.x + (x - self.x) * 0.72 + 3),
                  int(self.y + (y - self.y) * 0.72 - 2)) for x, y in vertices]
        pygame.draw.polygon(target, (*self.color, max(35, self.alpha - 45)), inner, 1)


@dataclass
class NumberParticle:
    x: float
    y: float
    velocity_x: float
    velocity_y: float
    digit: str
    size: int
    age: float = 0
    lifetime: float = 8.0

    def update(self, dt: float, width: int, height: int) -> None:
        self.age += dt
        self.velocity_y = min(self.velocity_y + 250 * dt, 520)
        self.velocity_x += math.sin(self.age * 9 + self.x * 0.03) * 16 * dt
        self.x += self.velocity_x * dt
        self.y += self.velocity_y * dt
        if self.x < 0 or self.x > width:
            self.velocity_x *= -0.55
            self.x = min(max(self.x, 0), width)
        if self.y > height + 35:
            self.age = self.lifetime

    def draw(self, target: pygame.Surface, font: pygame.font.Font) -> None:
        fade = min(1.0, max(0.0, (self.lifetime - self.age) / 1.2))
        glyph = font.render(self.digit, True, RED)
        glyph.set_alpha(round(235 * fade))
        glow = font.render(self.digit, True, (135, 20, 36))
        glow.set_alpha(round(95 * fade))
        rect = glyph.get_rect(center=(round(self.x), round(self.y)))
        target.blit(glow, rect.move(1, 2))
        target.blit(glyph, rect)


class VideoLoop:
    def __init__(self, path: Path):
        self.capture = None
        self.frame = None
        if cv2 is not None and path.is_file():
            self.capture = cv2.VideoCapture(str(path))
            if not self.capture.isOpened():
                self.capture.release()
                self.capture = None

    def next_frame(self, size: tuple[int, int]) -> pygame.Surface | None:
        if self.capture is None:
            return None
        ok, frame = self.capture.read()
        if not ok:
            self.capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ok, frame = self.capture.read()
        if not ok:
            return None
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width = frame.shape[:2]
        target_w, target_h = size
        scale = max(target_w / width, target_h / height)
        frame = cv2.resize(frame, (round(width * scale), round(height * scale)))
        surface = pygame.surfarray.make_surface(frame.swapaxes(0, 1))
        crop = pygame.Rect(0, 0, target_w, target_h)
        crop.center = surface.get_rect().center
        return surface.subsurface(crop).copy()

    def close(self) -> None:
        if self.capture is not None:
            self.capture.release()


def make_shapes(width: int, height: int, amount: int = 54) -> list[Shape]:
    return [
        Shape(
            x=random.uniform(0, width),
            y=random.uniform(-height, height),
            radius=random.choices([random.uniform(5, 20), random.uniform(22, 66)], [0.72, 0.28])[0],
            sides=random.choice([3, 4, 5, 6, 7]),
            color=random.choice([PURPLE, GREEN, (105, 63, 143)]),
            speed=random.uniform(5, 29),
            rotation=random.random() * math.tau,
            spin=random.uniform(-0.12, 0.12),
            alpha=random.randint(70, 175),
        )
        for _ in range(amount)
    ]


def spawn_numbers(particles: list[NumberParticle], width: int, height: int, count: int = 12) -> None:
    origin_x = random.uniform(width * 0.18, width * 0.82)
    origin_y = random.uniform(-36, max(80, height * 0.16))
    for _ in range(count):
        particles.append(NumberParticle(
            x=origin_x + random.gauss(0, 15), y=origin_y + random.gauss(0, 7),
            velocity_x=random.uniform(-32, 32), velocity_y=random.uniform(25, 110),
            digit=str(random.randrange(10)), size=random.randint(17, 29),
        ))


def draw_gate(screen: pygame.Surface, font: pygame.font.Font, small: pygame.font.Font,
              code: str, message: str, error_time: float) -> None:
    width, height = screen.get_size()
    veil = pygame.Surface((width, height), pygame.SRCALPHA)
    veil.fill((12, 12, 17, 185))
    screen.blit(veil, (0, 0))
    panel = pygame.Rect(0, 0, min(440, width - 36), 286)
    panel.center = (width // 2, height // 2)
    pygame.draw.rect(screen, (27, 27, 34), panel, border_radius=16)
    pygame.draw.rect(screen, (110, 56, 133), panel, 1, border_radius=16)
    title = font.render("SUYARIMA", True, (235, 226, 241))
    screen.blit(title, title.get_rect(center=(panel.centerx, panel.y + 62)))
    prompt = small.render("ENTER ACCESS CODE", True, (158, 151, 169))
    screen.blit(prompt, prompt.get_rect(center=(panel.centerx, panel.y + 108)))
    box = pygame.Rect(panel.x + 42, panel.y + 132, panel.width - 84, 48)
    shake = round(math.sin(error_time * 48) * 5) if error_time > 0 else 0
    box.x += shake
    pygame.draw.rect(screen, (18, 19, 24), box, border_radius=8)
    pygame.draw.rect(screen, (104, 74, 119), box, 1, border_radius=8)
    typed = small.render("•" * len(code) + "▏", True, (224, 213, 234))
    screen.blit(typed, (box.x + 15, box.y + 14))
    hint = message if message else "Press Enter to unlock · Esc to quit"
    hint_color = RED if message else (130, 127, 143)
    footer = small.render(hint, True, hint_color)
    screen.blit(footer, footer.get_rect(center=(panel.centerx, panel.y + 220)))


def main() -> None:
    pygame.init()
    pygame.display.set_caption("Suyarima-sama — falling signal")
    screen = pygame.display.set_mode((1024, 768), pygame.RESIZABLE)
    clock = pygame.time.Clock()
    title_font = pygame.font.SysFont("menlo", 27, bold=True)
    small_font = pygame.font.SysFont("menlo", 13)
    shapes = make_shapes(*screen.get_size())
    shape_layer = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    font_cache: dict[int, pygame.font.Font] = {}
    particles: list[NumberParticle] = []
    video = VideoLoop(VIDEO_PATH)
    unlocked = False
    typed_code = ""
    message = ""
    error_time = 0.0
    space_held = False
    summon_timer = 0.0
    running = True

    while running:
        dt = min(clock.tick(60) / 1000.0, 0.05)
        width, height = screen.get_size()
        error_time = max(0.0, error_time - dt)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode(event.size, pygame.RESIZABLE)
                shapes = make_shapes(*screen.get_size())
                shape_layer = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
            elif event.type == pygame.KEYDOWN:
                if not unlocked:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_RETURN:
                        if typed_code == ACCESS_CODE:
                            unlocked = True
                            message = ""
                        else:
                            typed_code = ""
                            message = "Code not recognized"
                            error_time = 0.28
                    elif event.key == pygame.K_BACKSPACE:
                        typed_code = typed_code[:-1]
                        message = ""
                    elif event.unicode and event.unicode.isprintable() and len(typed_code) < 48:
                        typed_code += event.unicode
                        message = ""
                elif event.key == pygame.K_SPACE:
                    space_held = True
                    spawn_numbers(particles, width, height, 16)
            elif event.type == pygame.KEYUP and event.key == pygame.K_SPACE:
                space_held = False

        if unlocked:
            background = video.next_frame((width, height))
            if background is not None:
                screen.blit(background, (0, 0))
                shade = pygame.Surface((width, height), pygame.SRCALPHA)
                shade.fill((12, 12, 18, 95))
                screen.blit(shade, (0, 0))
            else:
                screen.fill(BACKGROUND)
                # Quiet ambient color bloom behind the wireframe field.
                bloom = pygame.Surface((width, height), pygame.SRCALPHA)
                pygame.draw.circle(bloom, (81, 27, 105, 24), (width // 3, height // 3), min(width, height) // 2)
                pygame.draw.circle(bloom, (28, 98, 58, 16), (width * 3 // 4, height * 3 // 4), min(width, height) // 2)
                screen.blit(bloom, (0, 0))

            shape_layer.fill((0, 0, 0, 0))
            for shape in shapes:
                shape.update(dt, width, height)
                shape.draw(shape_layer)
            screen.blit(shape_layer, (0, 0))

            summon_timer += dt
            while space_held and summon_timer >= 0.045:
                spawn_numbers(particles, width, height, 3)
                summon_timer -= 0.045
            if not space_held:
                summon_timer = 0

            for particle in particles:
                particle.update(dt, width, height)
            particles = [particle for particle in particles if particle.age < particle.lifetime]
            if len(particles) > 1600:
                particles = particles[-1600:]

            for particle in particles:
                font = font_cache.get(particle.size)
                if font is None:
                    font = pygame.font.SysFont("menlo", particle.size, bold=True)
                    font_cache[particle.size] = font
                particle.draw(screen, font)

            # Minimal control note; fades into the scene instead of competing with it.
            note = small_font.render("HOLD SPACE TO SUMMON", True, (153, 116, 160))
            note.set_alpha(155)
            screen.blit(note, (22, height - 33))
        else:
            screen.fill(BACKGROUND)
            shape_layer.fill((0, 0, 0, 0))
            for shape in shapes:
                shape.update(dt, width, height)
                shape.draw(shape_layer)
            screen.blit(shape_layer, (0, 0))
            draw_gate(screen, title_font, small_font, typed_code, message, error_time)

        pygame.display.flip()

    video.close()
    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
