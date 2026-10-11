"""Suyarima-sama: a looping-video, generative falling-shapes visual."""

from __future__ import annotations

import math
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


def main() -> None:
    pygame.init()
    pygame.display.set_caption("suyarima-sama")
    screen = pygame.display.set_mode((1024, 768), pygame.RESIZABLE)
    clock = pygame.time.Clock()
    small_font = pygame.font.SysFont("menlo", 13)
    shapes = make_shapes(*screen.get_size())
    shape_layer = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    font_cache: dict[int, pygame.font.Font] = {}
    particles: list[NumberParticle] = []
    video = VideoLoop(VIDEO_PATH)
    space_held = False
    summon_timer = 0.0
    running = True

    while running:
        dt = min(clock.tick(60) / 1000.0, 0.05)
        width, height = screen.get_size()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode(event.size, pygame.RESIZABLE)
                shapes = make_shapes(*screen.get_size())
                shape_layer = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    space_held = True
                    spawn_numbers(particles, width, height, 16)
            elif event.type == pygame.KEYUP and event.key == pygame.K_SPACE:
                space_held = False

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

        # Keep the control hint plain text, framed as a compact HUD in the corner.
        command = small_font.render("SPACE BAR = NUMBERS", True, (190, 232, 207))
        padding_x, padding_y = 10, 7
        hud = pygame.Surface(
            (command.get_width() + padding_x * 2, command.get_height() + padding_y * 2),
            pygame.SRCALPHA,
        )
        pygame.draw.rect(hud, (10, 15, 20, 185), hud.get_rect(), border_radius=4)
        pygame.draw.rect(hud, (91, 185, 133, 190), hud.get_rect(), 1, border_radius=4)
        hud.blit(command, (padding_x, padding_y))
        screen.blit(hud, (18, 18))

        pygame.display.flip()

    video.close()
    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
