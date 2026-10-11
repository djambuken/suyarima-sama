"""Suyarima-sama: a looping-video digital rain of falling Python code."""

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
CODE_GREEN = (112, 255, 176)
CODE_GLOW = (24, 112, 76)
CODE_SNIPPETS = (
    "print(42)",
    "x = 0b1010",
    "range(0, 8)",
    "int(0x2A)",
    "n ** 2  # 16",
    "for i in range(9):",
    "value = 10101",
    "sum([2, 4, 8])",
    "if count == 7:",
)


@dataclass
class CodeParticle:
    x: float
    y: float
    velocity_x: float
    velocity_y: float
    code: str
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
        glyph = font.render(self.code, True, CODE_GREEN)
        glow = font.render(self.code, True, CODE_GLOW)
        size = (glyph.get_width() * 2, glyph.get_height() * 2)
        glyph = pygame.transform.scale(glyph, size)
        glow = pygame.transform.scale(glow, size)
        glyph.set_alpha(round(235 * fade))
        glow.set_alpha(round(110 * fade))
        rect = glyph.get_rect(topleft=(round(self.x), round(self.y)))
        target.blit(glow, rect.move(2, 2))
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


def spawn_code(particles: list[CodeParticle], width: int, count: int = 6) -> None:
    lane_count = max(1, min(count, width // 180 or 1))
    lane_width = width / lane_count
    lane_offset = random.randrange(lane_count)
    for index in range(count):
        lane = (index + lane_offset) % lane_count
        x = lane * lane_width + random.uniform(lane_width * 0.12, lane_width * 0.48)
        particles.append(CodeParticle(
            x=min(x, max(0, width - 220)),
            y=random.uniform(-110, -24),
            velocity_x=random.uniform(-12, 12),
            velocity_y=random.uniform(28, 58),
            code=random.choice(CODE_SNIPPETS),
            size=random.randint(8, 10),
        ))


def main() -> None:
    pygame.init()
    pygame.display.set_caption("suyarima-sama")
    screen = pygame.display.set_mode((1024, 768), pygame.RESIZABLE)
    clock = pygame.time.Clock()
    small_font = pygame.font.SysFont("menlo", 13)
    font_cache: dict[int, pygame.font.Font] = {}
    particles: list[CodeParticle] = []
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
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    space_held = True
                    spawn_code(particles, width, 4)
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
            # Subtle ambient color bloom behind the falling code.
            bloom = pygame.Surface((width, height), pygame.SRCALPHA)
            pygame.draw.circle(bloom, (81, 27, 105, 24), (width // 3, height // 3), min(width, height) // 2)
            pygame.draw.circle(bloom, (28, 98, 58, 16), (width * 3 // 4, height * 3 // 4), min(width, height) // 2)
            screen.blit(bloom, (0, 0))

        summon_timer += dt
        while space_held and summon_timer >= 0.28:
            spawn_code(particles, width, 1)
            summon_timer -= 0.28
        if not space_held:
            summon_timer = 0

        for particle in particles:
            particle.update(dt, width, height)
        particles = [particle for particle in particles if particle.age < particle.lifetime]
        if len(particles) > 180:
            particles = particles[-180:]

        for particle in particles:
            font = font_cache.get(particle.size)
            if font is None:
                font = pygame.font.SysFont("monospace", particle.size, bold=True)
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
