
import pygame
import random
import math
from collections import deque

# ==========================================================
# PACMAN AI CHALLENGE - GAME ENGINE
# ==========================================================

TILE = 30

POWER_DURATION = 8000
GHOST_INTERVAL = 450
ANIMATION_DURATION = 150

# Ghost stays hidden for 2 seconds after capture.
GHOST_RESPAWN_DELAY = 2000

MOVE_COST = -1
FOOD_REWARD = 10
POWER_REWARD = 30
GHOST_REWARD = 100

LEVEL = [
    "111111111111111111111",
    "1P00000001000000000G1",
    "101110110010011011101",
    "1O00001000000010000O1",
    "101110010111010011101",
    "100000000010000000001",
    "101101110010111011101",
    "100001000000001000001",
    "111101011111010111101",
    "100000010000010000001",
    "101110010111010011101",
    "1G0000000000000000001",
    "111111111111111111111",
]

WALL = (12, 75, 190)
WALL_FILL = (5, 25, 65)
PELLET = (255, 205, 95)
POWER = (255, 245, 180)
YELLOW = (255, 215, 0)
WHITE = (245, 245, 255)
RED = (255, 65, 90)
PINK = (255, 115, 200)
FRIGHTENED = (70, 160, 255)

DIRECTIONS = [
    (1, 0),
    (-1, 0),
    (0, -1),
    (0, 1)
]

DIRECTION_ANGLES = {
    (1, 0): 0,
    (-1, 0): 180,
    (0, -1): 90,
    (0, 1): 270
}


# ==========================================================
# MAP VALIDATION
# ==========================================================

def validate_map():

    width = len(LEVEL[0])

    if not all(len(row) == width for row in LEVEL):
        raise ValueError(
            "Map rows have different lengths."
        )

    players = [
        (x, y)
        for y, row in enumerate(LEVEL)
        for x, cell in enumerate(row)
        if cell == "P"
    ]

    ghost_count = sum(
        row.count("G") for row in LEVEL
    )

    if len(players) != 1:
        raise ValueError(
            "Exactly one Pacman is required."
        )

    if ghost_count < 2:
        raise ValueError(
            "At least two ghosts are required."
        )

    start = players[0]
    visited = {start}
    queue = deque([start])

    while queue:

        x, y = queue.popleft()

        for dx, dy in DIRECTIONS:

            nx = x + dx
            ny = y + dy

            if not (
                0 <= nx < width
                and 0 <= ny < len(LEVEL)
            ):
                continue

            if LEVEL[ny][nx] == "1":
                continue

            if (nx, ny) not in visited:
                visited.add((nx, ny))
                queue.append((nx, ny))

    unreachable = []

    for y, row in enumerate(LEVEL):
        for x, cell in enumerate(row):

            if (
                cell in ("0", "O")
                and (x, y) not in visited
            ):
                unreachable.append((x, y))

    if unreachable:
        raise ValueError(
            f"Unreachable food positions: {unreachable}"
        )

    print("MAP VALIDATION PASSED")
    print("All food and power pellets are reachable.")


validate_map()


# ==========================================================
# GAME CLASS
# ==========================================================

class PacmanGame:

    def __init__(self):
        self.reset()

    def reset(self):

        self.walls = set()
        self.pellets = set()
        self.power_pellets = set()

        self.ghosts = []
        self.ghost_starts = []

        self.player = None
        self.direction = (1, 0)

        for y, row in enumerate(LEVEL):
            for x, cell in enumerate(row):

                pos = (x, y)

                if cell == "1":
                    self.walls.add(pos)

                elif cell == "0":
                    self.pellets.add(pos)

                elif cell == "O":
                    self.power_pellets.add(pos)

                elif cell == "P":
                    self.player = pos

                elif cell == "G":
                    self.ghosts.append(pos)
                    self.ghost_starts.append(pos)

        # Same seed at the start of each round.
        self.rng = random.Random(42)

        self.player_previous = self.player
        self.ghost_previous = self.ghosts.copy()

        # Zero = active ghost.
        # Positive value = hidden ghost awaiting respawn.
        self.ghost_respawn_timers = [
            0 for _ in self.ghosts
        ]

        self.score = 0
        self.moves = 0
        self.power_timer = 0

        self.status = "playing"
        self.paused = False

        self.elapsed_ms = 0
        self.ghost_elapsed = 0

        self.player_animation = ANIMATION_DURATION
        self.ghost_animation = ANIMATION_DURATION

        # Used for temporary capture feedback.
        self.capture_message_timer = 0
        self.capture_message = ""

    # ======================================================
    # MOVEMENT
    # ======================================================

    def can_move(self, pos):

        x, y = pos

        return (
            0 <= x < len(LEVEL[0])
            and 0 <= y < len(LEVEL)
            and pos not in self.walls
        )

    def valid_neighbors(self, pos):

        neighbors = []

        for dx, dy in DIRECTIONS:

            next_pos = (
                pos[0] + dx,
                pos[1] + dy
            )

            if self.can_move(next_pos):
                neighbors.append(next_pos)

        return neighbors

    def move_player(self, dx, dy):

        if self.status != "playing" or self.paused:
            return

        if (dx, dy) not in DIRECTIONS:
            return

        self.direction = (dx, dy)

        next_pos = (
            self.player[0] + dx,
            self.player[1] + dy
        )

        if not self.can_move(next_pos):
            return

        self.player_previous = self.player
        self.player = next_pos
        self.player_animation = 0

        self.moves += 1
        self.score += MOVE_COST

        if next_pos in self.pellets:

            self.pellets.remove(next_pos)
            self.score += FOOD_REWARD

        if next_pos in self.power_pellets:

            self.power_pellets.remove(next_pos)
            self.score += POWER_REWARD
            self.power_timer = POWER_DURATION

        self.check_collisions()

        if (
            not self.pellets
            and self.status == "playing"
        ):
            self.finish_game("completed")

    # ======================================================
    # GHOST MOVEMENT
    # ======================================================

    def choose_ghost_move(self, ghost):

        options = self.valid_neighbors(ghost)

        if not options:
            return ghost

        def distance(pos):
            return (
                abs(pos[0] - self.player[0])
                + abs(pos[1] - self.player[1])
            )

        if self.power_timer > 0:

            # Frightened ghosts usually run away.
            if self.rng.random() < 0.75:
                return max(
                    options,
                    key=distance
                )

        else:

            # Normal ghosts sometimes chase Pacman.
            if self.rng.random() < 0.60:
                return min(
                    options,
                    key=distance
                )

        return self.rng.choice(options)

    def move_ghosts(self):

        if self.status != "playing" or self.paused:
            return

        self.ghost_previous = self.ghosts.copy()

        new_positions = []

        for i, ghost in enumerate(self.ghosts):

            # Captured ghosts remain at their home
            # position internally but are inactive.
            if self.ghost_respawn_timers[i] > 0:
                new_positions.append(ghost)
                continue

            new_positions.append(
                self.choose_ghost_move(ghost)
            )

        self.ghosts = new_positions
        self.ghost_animation = 0

        self.check_collisions()

    # ======================================================
    # GHOST CAPTURE
    # ======================================================

    def capture_ghost(self, index):

        # Never capture an already inactive ghost.
        if self.ghost_respawn_timers[index] > 0:
            return

        self.score += GHOST_REWARD

        # Hide ghost temporarily.
        self.ghost_respawn_timers[index] = (
            GHOST_RESPAWN_DELAY
        )

        # Return it to the original spawn position.
        self.ghosts[index] = self.ghost_starts[index]
        self.ghost_previous[index] = (
            self.ghost_starts[index]
        )

        self.capture_message = (
            f"GHOST CAPTURED! +{GHOST_REWARD}"
        )

        self.capture_message_timer = 1000

    # ======================================================
    # COLLISION DETECTION
    # ======================================================

    def check_collisions(self):

        if self.status != "playing":
            return

        for i, ghost in enumerate(self.ghosts):

            # Ignore ghosts that are waiting to respawn.
            if self.ghost_respawn_timers[i] > 0:
                continue

            if ghost != self.player:
                continue

            if self.power_timer > 0:

                self.capture_ghost(i)

            else:

                self.finish_game("gameover")
                return

    # ======================================================
    # GAME STATUS
    # ======================================================

    def finish_game(self, result):

        if self.status == "playing":
            self.status = result

    def toggle_pause(self):

        if self.status == "playing":
            self.paused = not self.paused

    def elapsed_seconds(self):

        return self.elapsed_ms / 1000

    # ======================================================
    # UPDATE
    # dt is in milliseconds
    # ======================================================

    def update(self, dt):

        if self.status != "playing" or self.paused:
            return

        dt = max(0, min(dt, 100))

        self.elapsed_ms += dt

        self.player_animation = min(
            ANIMATION_DURATION,
            self.player_animation + dt
        )

        self.ghost_animation = min(
            ANIMATION_DURATION,
            self.ghost_animation + dt
        )

        if self.power_timer > 0:

            self.power_timer = max(
                0,
                self.power_timer - dt
            )

        if self.capture_message_timer > 0:

            self.capture_message_timer = max(
                0,
                self.capture_message_timer - dt
            )

        # Respawn captured ghosts after their delay.
        for i in range(len(self.ghosts)):

            if self.ghost_respawn_timers[i] <= 0:
                continue

            remaining = (
                self.ghost_respawn_timers[i] - dt
            )

            if remaining > 0:
                self.ghost_respawn_timers[i] = remaining
                continue

            # Avoid respawning directly on Pacman.
            if self.ghost_starts[i] == self.player:
                self.ghost_respawn_timers[i] = 100
                continue

            self.ghost_respawn_timers[i] = 0

        self.ghost_elapsed += dt

        if self.ghost_elapsed >= GHOST_INTERVAL:

            self.ghost_elapsed -= GHOST_INTERVAL
            self.move_ghosts()

    # ======================================================
    # SMOOTH VISUAL INTERPOLATION
    # ======================================================

    def interpolate(self, previous, current, progress):

        progress = min(1, max(0, progress))

        progress = (
            progress * progress * (3 - 2 * progress)
        )

        x = previous[0] + (
            current[0] - previous[0]
        ) * progress

        y = previous[1] + (
            current[1] - previous[1]
        ) * progress

        return x, y

    # ======================================================
    # DRAWING
    # ======================================================

    def draw(self, surface, offset_x, offset_y, t):

        # ---------------- WALLS ----------------

        for x, y in self.walls:

            rect = pygame.Rect(
                offset_x + x * TILE,
                offset_y + y * TILE,
                TILE,
                TILE
            )

            pygame.draw.rect(
                surface,
                WALL_FILL,
                rect,
                border_radius=5
            )

            pygame.draw.rect(
                surface,
                WALL,
                rect,
                2,
                border_radius=5
            )

        # ---------------- FOOD ----------------

        for x, y in self.pellets:

            center = (
                offset_x + x * TILE + TILE // 2,
                offset_y + y * TILE + TILE // 2
            )

            pygame.draw.circle(
                surface,
                PELLET,
                center,
                3
            )

        # ---------------- POWER PELLETS ----------------

        pulse = 6 + int(
            abs(math.sin(t * 4)) * 3
        )

        for x, y in self.power_pellets:

            center = (
                offset_x + x * TILE + TILE // 2,
                offset_y + y * TILE + TILE // 2
            )

            pygame.draw.circle(
                surface,
                POWER,
                center,
                pulse
            )

        # ---------------- PACMAN ----------------

        progress = (
            self.player_animation / ANIMATION_DURATION
        )

        x, y = self.interpolate(
            self.player_previous,
            self.player,
            progress
        )

        px = offset_x + x * TILE + TILE // 2
        py = offset_y + y * TILE + TILE // 2

        mouth = (
            5 + abs(math.sin(t * 9)) * 38
        )

        rotation = DIRECTION_ANGLES[
            self.direction
        ]

        points = [(px, py)]

        for i in range(61):

            angle = math.radians(
                rotation
                + mouth
                + (360 - 2 * mouth) * i / 60
            )

            points.append((
                px + math.cos(angle) * 12,
                py - math.sin(angle) * 12
            ))

        pygame.draw.polygon(
            surface,
            YELLOW,
            points
        )

        # ---------------- GHOSTS ----------------

        ghost_progress = (
            self.ghost_animation / ANIMATION_DURATION
        )

        for i, ghost in enumerate(self.ghosts):

            # Captured ghost is invisible.
            if self.ghost_respawn_timers[i] > 0:
                continue

            gx, gy = self.interpolate(
                self.ghost_previous[i],
                ghost,
                ghost_progress
            )

            cx = round(
                offset_x + gx * TILE + TILE // 2
            )

            cy = round(
                offset_y + gy * TILE + TILE // 2
            )

            if self.power_timer > 0:
                color = FRIGHTENED
            else:
                color = RED if i % 2 == 0 else PINK

            pygame.draw.circle(
                surface,
                color,
                (cx, cy - 3),
                11
            )

            pygame.draw.rect(
                surface,
                color,
                (cx - 11, cy - 3, 22, 14)
            )

            for wave_dx in (-7, 0, 7):

                pygame.draw.circle(
                    surface,
                    color,
                    (cx + wave_dx, cy + 10),
                    4
                )

            for eye_dx in (-5, 5):

                pygame.draw.circle(
                    surface,
                    WHITE,
                    (cx + eye_dx, cy - 4),
                    4
                )

                pygame.draw.circle(
                    surface,
                    (20, 35, 90),
                    (cx + eye_dx + 1, cy - 3),
                    2
                )

        # ---------------- CAPTURE MESSAGE ----------------

        if self.capture_message_timer > 0:

            font = pygame.font.SysFont(
                "arial",
                23,
                bold=True
            )

            message = font.render(
                self.capture_message,
                True,
                (65, 235, 165)
            )

            message_x = (
                offset_x
                + len(LEVEL[0]) * TILE // 2
            )

            message_y = offset_y - 18

            message_rect = message.get_rect(
                center=(message_x, message_y)
            )

            surface.blit(
                message,
                message_rect
            )
