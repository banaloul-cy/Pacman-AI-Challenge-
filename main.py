
import pygame
import math
import sys

from game import PacmanGame, LEVEL, TILE
from utility_agent import UtilityBasedAgent

pygame.init()

# ==========================================================
# PACMAN AI CHALLENGE - HUMAN VS AI COMPETITION
# ==========================================================

WIDTH = 1280
HEIGHT = 800
FPS = 60

# Both competitors use the same movement interval.
MOVE_INTERVAL = 220

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("PACMAN AI | NEON ARCADE")
clock = pygame.time.Clock()

# ==========================================================
# COLORS
# ==========================================================

NAVY = (5, 9, 26)
WHITE = (245, 248, 255)
MUTED = (143, 159, 194)
GOLD = (255, 211, 35)
CYAN = (34, 190, 255)
PURPLE = (157, 88, 255)
RED = (255, 65, 90)
PINK = (255, 120, 210)
GREEN = (65, 235, 165)
PANEL_BG = (13, 27, 57)

# ==========================================================
# FONTS
# ==========================================================

title_font = pygame.font.SysFont(
    "arial", 82, bold=True
)
heading_font = pygame.font.SysFont(
    "arial", 48, bold=True
)
button_font = pygame.font.SysFont(
    "arial", 27, bold=True
)
body_font = pygame.font.SysFont(
    "arial", 21
)
small_font = pygame.font.SysFont(
    "arial", 16
)
number_font = pygame.font.SysFont(
    "arial", 36, bold=True
)

# ==========================================================
# BUTTONS
# ==========================================================

human_button = pygame.Rect(385, 480, 510, 76)
ai_button = pygame.Rect(385, 575, 510, 76)

continue_button = pygame.Rect(
    385, 590, 510, 72
)

restart_button = pygame.Rect(
    385, 650, 510, 68
)

# ==========================================================
# GAME STATE
# ==========================================================

# menu -> playing -> round_end -> playing
# -> round_end -> results

state = "menu"

game = PacmanGame()
ai_agent = UtilityBasedAgent()

round_order = []
round_index = 0
current_player = None

results = {}

move_timer = 0
animation_time = 0

human_direction = None

running = True

# ==========================================================
# TEXT FUNCTIONS
# ==========================================================

def draw_text(text, font, color, x, y):
    image = font.render(str(text), True, color)
    screen.blit(image, (x, y))


def centered_text(text, font, color, y):
    image = font.render(str(text), True, color)
    rect = image.get_rect(
        center=(WIDTH // 2, y)
    )
    screen.blit(image, rect)


# ==========================================================
# NEON GLOW
# ==========================================================

def glow_rect(surface, rect, color, radius=20):

    glow = pygame.Surface(
        (rect.width + 60, rect.height + 60),
        pygame.SRCALPHA
    )

    for spread in range(24, 0, -5):

        alpha = max(3, 32 - spread)

        r = pygame.Rect(
            30 - spread // 2,
            30 - spread // 2,
            rect.width + spread,
            rect.height + spread
        )

        pygame.draw.rect(
            glow,
            (*color, alpha),
            r,
            border_radius=radius + spread // 2
        )

    surface.blit(
        glow,
        (rect.x - 30, rect.y - 30)
    )


# ==========================================================
# BACKGROUND
# ==========================================================

def draw_background():

    for y in range(HEIGHT):

        factor = y / HEIGHT

        color = (
            int(5 + factor * 5),
            int(9 + factor * 3),
            int(26 + factor * 17)
        )

        pygame.draw.line(
            screen,
            color,
            (0, y),
            (WIDTH, y)
        )

    paths = [
        [(0, 80), (110, 80),
         (110, 145), (200, 145)],

        [(0, 250), (155, 250),
         (155, 320), (235, 320)],

        [(0, 450), (105, 450),
         (105, 540), (220, 540)],

        [(1280, 80), (1170, 80),
         (1170, 145), (1080, 145)],

        [(1280, 250), (1125, 250),
         (1125, 320), (1045, 320)],

        [(1280, 450), (1175, 450),
         (1175, 540), (1060, 540)]
    ]

    for path in paths:

        pygame.draw.lines(
            screen,
            (8, 39, 91),
            False,
            path,
            15
        )

        pygame.draw.lines(
            screen,
            (0, 125, 255),
            False,
            path,
            4
        )

    for side in (0, 1):

        for i in range(10):

            x = 45 + (i % 3) * 45

            if side:
                x = WIDTH - x

            y = 185 + i * 42

            pygame.draw.circle(
                screen,
                (230, 174, 42),
                (x, y),
                4
            )

    for x in range(0, WIDTH + 1, 80):

        pygame.draw.line(
            screen,
            (15, 29, 69),
            (x, 700),
            (x, HEIGHT),
            1
        )

    for y in range(700, HEIGHT, 25):

        pygame.draw.line(
            screen,
            (15, 29, 69),
            (0, y),
            (WIDTH, y),
            1
        )


# ==========================================================
# MENU PACMAN
# ==========================================================

def draw_pacman(x, y, radius, t):

    mouth = 16 + abs(math.sin(t * 5)) * 25

    start = math.radians(mouth)
    end = math.radians(360 - mouth)

    points = [(x, y)]

    for i in range(41):

        angle = (
            start + (end - start) * i / 40
        )

        points.append((
            x + math.cos(angle) * radius,
            y - math.sin(angle) * radius
        ))

    pygame.draw.polygon(
        screen,
        GOLD,
        points
    )

    pygame.draw.circle(
        screen,
        (12, 15, 25),
        (x + 5, y - radius // 2),
        4
    )


# ==========================================================
# MENU GHOST
# ==========================================================

def draw_ghost(x, y, color, t):

    y += int(math.sin(t * 3 + x) * 4)

    pygame.draw.circle(
        screen,
        color,
        (x, y - 12),
        24
    )

    pygame.draw.rect(
        screen,
        color,
        (x - 24, y - 12, 48, 30)
    )

    for dx in (-16, 0, 16):

        pygame.draw.circle(
            screen,
            color,
            (x + dx, y + 18),
            8
        )

    for dx in (-9, 10):

        pygame.draw.ellipse(
            screen,
            WHITE,
            (x + dx - 8, y - 17, 14, 19)
        )

        pygame.draw.circle(
            screen,
            (25, 48, 110),
            (x + dx - 1, y - 7),
            4
        )


# ==========================================================
# BUTTONS
# ==========================================================

def draw_button(rect, label, color, mouse):

    hovered = rect.collidepoint(mouse)

    glow_rect(
        screen,
        rect,
        color
    )

    base = tuple(
        min(
            255,
            int(c * (0.65 if hovered else 0.40))
        )
        for c in color
    )

    pygame.draw.rect(
        screen,
        base,
        rect,
        border_radius=19
    )

    pygame.draw.rect(
        screen,
        color,
        rect,
        3,
        border_radius=19
    )

    if hovered:

        overlay = pygame.Surface(
            rect.size,
            pygame.SRCALPHA
        )

        overlay.fill(
            (255, 255, 255, 18)
        )

        screen.blit(
            overlay,
            rect.topleft
        )

    image = button_font.render(
        label,
        True,
        WHITE
    )

    screen.blit(
        image,
        image.get_rect(center=rect.center)
    )


# ==========================================================
# MAIN MENU
# ==========================================================

def draw_menu(t):

    draw_background()

    centered_text(
        "PACMAN AI",
        title_font,
        GOLD,
        145
    )

    pygame.draw.line(
        screen,
        CYAN,
        (340, 214),
        (940, 214),
        3
    )

    centered_text(
        "UTILITY-BASED RATIONAL AGENT CHALLENGE",
        body_font,
        WHITE,
        249
    )

    draw_pacman(
        450, 365, 40, t
    )

    for i in range(4):

        pygame.draw.circle(
            screen,
            GOLD,
            (520 + i * 33, 365),
            5
        )

    colors = [
        RED,
        PINK,
        (40, 225, 245),
        (255, 160, 40)
    ]

    for i, color in enumerate(colors):

        draw_ghost(
            685 + i * 65,
            370,
            color,
            t
        )

    centered_text(
        "CHOOSE WHO PLAYS FIRST",
        body_font,
        MUTED,
        447
    )

    mouse = pygame.mouse.get_pos()

    draw_button(
        human_button,
        "HUMAN FIRST",
        CYAN,
        mouse
    )

    draw_button(
        ai_button,
        "AI FIRST",
        PURPLE,
        mouse
    )

    centered_text(
        "TWO ROUNDS  |  SAME MAP  |  ONE WINNER",
        body_font,
        MUTED,
        719
    )

    centered_text(
        "PYTHON + PYGAME  |  UTILITY-BASED AGENT",
        small_font,
        MUTED,
        759
    )


# ==========================================================
# COMPETITION MANAGEMENT
# ==========================================================

def start_competition(first):

    global round_order
    global round_index
    global results

    if first == "HUMAN":
        round_order = ["HUMAN", "AI"]
    else:
        round_order = ["AI", "HUMAN"]

    round_index = 0
    results = {}

    start_round()


def start_round():

    global state
    global current_player
    global move_timer
    global human_direction

    current_player = round_order[round_index]

    # Every round starts with identical initial game state.
    # game.reset() also resets the ghost random seed.
    game.reset()
    ai_agent.reset()

    move_timer = 0
    human_direction = None

    state = "playing"


def save_round_result():

    global state

    # Avoid recording a round more than once.
    if current_player in results:
        return

    results[current_player] = {
        "score": game.score,
        "time": game.elapsed_seconds(),
        "moves": game.moves,
        "completed": game.status == "completed",
        "food_left": len(game.pellets),
        "status": game.status
    }

    state = "round_end"


def continue_competition():

    global round_index
    global state

    if round_index == 0:
        round_index = 1
        start_round()
    else:
        state = "results"


# ==========================================================
# WINNER CALCULATION
# ==========================================================

def calculate_winner():

    human = results["HUMAN"]
    ai = results["AI"]

    # Rule 1: Completing the level has priority.
    if human["completed"] != ai["completed"]:
        return (
            "HUMAN" if human["completed"] else "AI"
        )

    # Rule 2: Higher score wins.
    if human["score"] != ai["score"]:
        return (
            "HUMAN"
            if human["score"] > ai["score"]
            else "AI"
        )

    # Rule 3: Shorter completion/game time wins.
    if abs(human["time"] - ai["time"]) > 0.001:
        return (
            "HUMAN"
            if human["time"] < ai["time"]
            else "AI"
        )

    return "TIE"


# ==========================================================
# HUD PANEL
# ==========================================================

def draw_hud_item(x, y, label, value):

    rect = pygame.Rect(x, y, 320, 75)

    pygame.draw.rect(
        screen,
        PANEL_BG,
        rect,
        border_radius=12
    )

    pygame.draw.rect(
        screen,
        CYAN,
        rect,
        1,
        border_radius=12
    )

    draw_text(
        label,
        small_font,
        MUTED,
        x + 18,
        y + 9
    )

    draw_text(
        value,
        button_font,
        WHITE,
        x + 18,
        y + 33
    )


# ==========================================================
# GAME SCREEN
# ==========================================================

def draw_game(t):

    draw_background()

    centered_text(
        f"ROUND {round_index + 1}/2  |  {current_player} MODE",
        button_font,
        GOLD,
        55
    )

    offset_x = 80
    offset_y = 145

    game.draw(
        screen,
        offset_x,
        offset_y,
        t
    )

    map_width = len(LEVEL[0]) * TILE
    panel_x = offset_x + map_width + 55

    labels = [
        ("SCORE", str(game.score)),
        ("TIME", f"{game.elapsed_seconds():.1f} s"),
        ("FOOD LEFT", str(len(game.pellets))),
        ("MOVES", str(game.moves)),
        ("POWER", f"{game.power_timer / 1000:.1f} s")
    ]

    for i, (label, value) in enumerate(labels):

        draw_hud_item(
            panel_x,
            165 + i * 95,
            label,
            value
        )

    # ======================================================
    # AI DECISION PANEL
    # ======================================================

    if current_player == "AI":

        info = ai_agent.get_decision_info()

        decision_rect = pygame.Rect(
            765, 645, 360, 115
        )

        pygame.draw.rect(
            screen,
            PANEL_BG,
            decision_rect,
            border_radius=12
        )

        pygame.draw.rect(
            screen,
            PURPLE,
            decision_rect,
            2,
            border_radius=12
        )

        draw_text(
            "AI DECISION ANALYSIS",
            small_font,
            PURPLE,
            782,
            655
        )

        draw_text(
            f"Direction: {info['direction']}",
            small_font,
            WHITE,
            782,
            681
        )

        draw_text(
            f"Utility: {info['utility']:.2f}",
            small_font,
            WHITE,
            782,
            704
        )

        draw_text(
            f"Target: {info['target']}",
            small_font,
            CYAN,
            782,
            727
        )

    # ======================================================
    # INSTRUCTIONS
    # ======================================================

    draw_text(
        "ARROW KEYS: MOVE",
        small_font,
        MUTED,
        90,
        725
    )

    draw_text(
        "P: PAUSE / RESUME",
        small_font,
        MUTED,
        300,
        725
    )

    draw_text(
        "ESC: MAIN MENU",
        small_font,
        MUTED,
        530,
        725
    )

    if game.paused:

        overlay = pygame.Surface(
            (WIDTH, HEIGHT),
            pygame.SRCALPHA
        )

        overlay.fill((0, 0, 0, 175))
        screen.blit(overlay, (0, 0))

        centered_text(
            "GAME PAUSED",
            heading_font,
            GOLD,
            320
        )

        centered_text(
            "PRESS P TO RESUME",
            button_font,
            WHITE,
            425
        )


# ==========================================================
# ROUND END SCREEN
# ==========================================================

def draw_round_end():

    draw_background()

    result = results[current_player]

    completed = result["completed"]

    if completed:
        headline = "LEVEL COMPLETED!"
        color = GREEN
    else:
        headline = "GAME OVER"
        color = RED

    centered_text(
        f"ROUND {round_index + 1} FINISHED",
        heading_font,
        GOLD,
        125
    )

    centered_text(
        f"{current_player} RESULT",
        button_font,
        WHITE,
        205
    )

    centered_text(
        headline,
        heading_font,
        color,
        285
    )

    centered_text(
        f"SCORE: {result['score']}",
        number_font,
        WHITE,
        365
    )

    centered_text(
        f"TIME: {result['time']:.1f} s",
        button_font,
        MUTED,
        420
    )

    centered_text(
        f"MOVES: {result['moves']}   |   FOOD LEFT: {result['food_left']}",
        body_font,
        MUTED,
        465
    )

    if round_index == 0:

        next_player = round_order[1]

        centered_text(
            f"NEXT PLAYER: {next_player}",
            body_font,
            CYAN,
            535
        )

        button_label = "START ROUND 2"

    else:

        centered_text(
            "BOTH ROUNDS ARE FINISHED",
            body_font,
            CYAN,
            535
        )

        button_label = "VIEW FINAL RESULTS"

    draw_button(
        continue_button,
        button_label,
        PURPLE,
        pygame.mouse.get_pos()
    )

    centered_text(
        "PRESS ENTER TO CONTINUE",
        small_font,
        MUTED,
        705
    )


# ==========================================================
# FINAL RESULTS - COMPARISON
# ==========================================================

def draw_result_card(x, y, player, result, color):

    rect = pygame.Rect(x, y, 490, 345)

    pygame.draw.rect(
        screen,
        PANEL_BG,
        rect,
        border_radius=20
    )

    pygame.draw.rect(
        screen,
        color,
        rect,
        3,
        border_radius=20
    )

    label = heading_font.render(
        player,
        True,
        color
    )

    screen.blit(
        label,
        label.get_rect(
            center=(x + 245, y + 48)
        )
    )

    status = (
        "COMPLETED"
        if result["completed"]
        else "GAME OVER"
    )

    status_color = (
        GREEN if result["completed"] else RED
    )

    rows = [
        ("STATUS", status, status_color),
        ("SCORE", str(result["score"]), WHITE),
        ("TIME", f"{result['time']:.1f} s", WHITE),
        ("MOVES", str(result["moves"]), WHITE),
        ("FOOD LEFT", str(result["food_left"]), WHITE)
    ]

    for i, (label_text, value, value_color) in enumerate(rows):

        row_y = y + 105 + i * 44

        draw_text(
            label_text,
            body_font,
            MUTED,
            x + 35,
            row_y
        )

        image = body_font.render(
            value,
            True,
            value_color
        )

        image_rect = image.get_rect(
            right=x + 455,
            top=row_y
        )

        screen.blit(image, image_rect)


def draw_final_results():

    draw_background()

    centered_text(
        "FINAL RESULTS",
        heading_font,
        GOLD,
        88
    )

    centered_text(
        "HUMAN VS AI - COMPETITION SUMMARY",
        body_font,
        MUTED,
        143
    )

    draw_result_card(
        105,
        195,
        "HUMAN",
        results["HUMAN"],
        CYAN
    )

    draw_result_card(
        685,
        195,
        "AI AGENT",
        results["AI"],
        PURPLE
    )

    winner = calculate_winner()

    if winner == "TIE":
        winner_text = "IT'S A TIE!"
        winner_color = WHITE

    elif winner == "HUMAN":
        winner_text = "HUMAN WINS!"
        winner_color = CYAN

    else:
        winner_text = "AI AGENT WINS!"
        winner_color = GREEN

    centered_text(
        winner_text,
        heading_font,
        winner_color,
        595
    )

    draw_button(
        restart_button,
        "BACK TO MAIN MENU",
        CYAN,
        pygame.mouse.get_pos()
    )

    centered_text(
        "COMPLETION  >  SCORE  >  TIME",
        small_font,
        MUTED,
        755
    )


# ==========================================================
# KEYBOARD DIRECTION
# ==========================================================

def direction_from_keys(keys):

    if keys[pygame.K_UP]:
        return (0, -1)

    if keys[pygame.K_DOWN]:
        return (0, 1)

    if keys[pygame.K_LEFT]:
        return (-1, 0)

    if keys[pygame.K_RIGHT]:
        return (1, 0)

    return None


# ==========================================================
# MAIN LOOP
# ==========================================================

while running:

    dt = clock.tick(FPS) / 1000.0
    animation_time += dt

    # ======================================================
    # EVENTS
    # ======================================================

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:

            if event.key == pygame.K_ESCAPE:
                state = "menu"
                results = {}
                round_order = []
                round_index = 0
                current_player = None
                human_direction = None

            elif state == "playing":

                if event.key == pygame.K_p:
                    game.toggle_pause()

                elif current_player == "HUMAN":

                    key_moves = {
                        pygame.K_UP: (0, -1),
                        pygame.K_DOWN: (0, 1),
                        pygame.K_LEFT: (-1, 0),
                        pygame.K_RIGHT: (1, 0)
                    }

                    if event.key in key_moves:
                        human_direction = key_moves[event.key]

            elif state == "round_end":

                if event.key in (
                    pygame.K_RETURN,
                    pygame.K_SPACE
                ):
                    continue_competition()

            elif state == "results":

                if event.key in (
                    pygame.K_RETURN,
                    pygame.K_SPACE
                ):
                    state = "menu"

        elif event.type == pygame.MOUSEBUTTONDOWN:

            if event.button == 1:

                if state == "menu":

                    if human_button.collidepoint(event.pos):
                        start_competition("HUMAN")

                    elif ai_button.collidepoint(event.pos):
                        start_competition("AI")

                elif state == "round_end":

                    if continue_button.collidepoint(event.pos):
                        continue_competition()

                elif state == "results":

                    if restart_button.collidepoint(event.pos):
                        state = "menu"

    # ======================================================
    # UPDATE
    # ======================================================

    if state == "playing":

        if not game.paused and game.status == "playing":

            game.update(dt * 1000)

            if game.status == "playing":

                move_timer += dt * 1000

                # Same movement rate for human and AI.
                if move_timer >= MOVE_INTERVAL:

                    move_timer -= MOVE_INTERVAL

                    action = None

                    if current_player == "AI":

                        action = ai_agent.choose_action(game)

                    elif current_player == "HUMAN":

                        keys = pygame.key.get_pressed()

                        pressed_direction = direction_from_keys(
                            keys
                        )

                        if pressed_direction is not None:
                            human_direction = pressed_direction

                        # One key press or held key can
                        # provide the next movement.
                        action = human_direction

                    if action is not None:

                        game.move_player(*action)

                        # Human must press again or hold
                        # a direction for continued movement.
                        if current_player == "HUMAN":

                            keys = pygame.key.get_pressed()

                            if direction_from_keys(keys) is None:
                                human_direction = None

        # End of current round.
        if game.status != "playing":
            save_round_result()

    # ======================================================
    # DRAW
    # ======================================================

    if state == "menu":
        draw_menu(animation_time)

    elif state == "playing":
        draw_game(animation_time)

    elif state == "round_end":
        draw_round_end()

    elif state == "results":
        draw_final_results()

    # Always update the display inside the main loop.
    pygame.display.flip()


pygame.quit()
sys.exit()
