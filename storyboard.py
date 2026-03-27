import os
import random
import pygame


# Layout, pacing, and visual settings for the story sequence.
WIDTH, HEIGHT = 900, 600
BASE_DIR = os.path.dirname(__file__)
STORY_DIR = os.path.join(BASE_DIR, "assets", "story")

DIALOG_RECT = pygame.Rect(50, 370, WIDTH - 100, 160)

SKIP_RECT = pygame.Rect(WIDTH - 132, HEIGHT - 62, 120, 40)
SKIP_SYMBOL_W = 44
SKIP_GAP = 8

BAR_H = 20

TYPE_SPEED_MS = 28
FADE_STEP = 10
OVERLAY_ALPHA = 55
SNOW_COUNT = 90
SNOW_ALPHA = 180

PAGES = [
    {
        "title": "CHRISTMAS EVE",
        "bg": "assets/story/page1.png",
        "lines": [
            "Christmas Eve.",
            "Snow falls quietly over the peaceful mountain resort.",
            "But tonight... something is terribly wrong.",
            "A giant snowman has appeared, bringing chaos to the village."
        ]
    },
    {
        "title": "TWO HEROES",
        "bg": "assets/story/page2.png",
        "lines": [
            "As panic spreads across the village, two brave heroes step forward.",
            "They refuse to let the snowman destroy their home."
        ]
    },
    {
        "title": "THE PLAN",
        "bg": "assets/story/page3.png",
        "lines": [
            "The snowman has taken control of the surrounding area.",
            "To stop him, the heroes must complete two dangerous missions."
        ]
    },
    {
        "title": "MISSION A: ELIMINATION",
        "bg": "assets/story/page4.png",
        "lines": [
            "Defeat the snowman's minions guarding the battlefield.",
            "Each enemy has five lives.",
            "Knock them down and clear the area."
        ]
    },
    {
        "title": "MISSION B: CAPTURE THE FLAG",
        "bg": "assets/story/page5.png",
        "lines": [
            "Stand inside the capture zone to take control of the flag.",
            "Beware - enemies can steal it back.",
            "Save the village before it's too late."
        ]
    },
]


# Keep auto-loaded backgrounds in page order.
def _bg_sort_key(path: str):
    name = os.path.splitext(os.path.basename(path))[0].lower()
    digits = "".join(ch for ch in name if ch.isdigit())
    num = int(digits) if digits else 10**9
    return (num, name)


def _assign_story_backgrounds():
    if not os.path.isdir(STORY_DIR):
        return

    image_files = []
    for fname in os.listdir(STORY_DIR):
        lower = fname.lower()
        if lower.endswith((".png", ".jpg", ".jpeg", ".webp", ".bmp")):
            image_files.append(os.path.join(STORY_DIR, fname))

    image_files.sort(key=_bg_sort_key)
    for i, page in enumerate(PAGES):
        if i < len(image_files):
            page["bg"] = image_files[i]


_assign_story_backgrounds()


_idx = 0
_line_idx = 0
_char_idx = 0
_page_done = False
_finished = False

_last_tick = 0
_fade_alpha = 255

_bg_cache: dict[str, pygame.Surface | None] = {}
_snow = []


# Load and cache each background once at screen size.
def _load_bg(path: str) -> pygame.Surface | None:
    full_path = path
    if not os.path.isabs(full_path):
        full_path = os.path.join(BASE_DIR, full_path)
    full_path = os.path.normpath(full_path)

    if full_path in _bg_cache:
        return _bg_cache[full_path]

    if not os.path.exists(full_path):
        _bg_cache[full_path] = None
        return None

    img = pygame.image.load(full_path).convert()
    img = pygame.transform.smoothscale(img, (WIDTH, HEIGHT))
    _bg_cache[full_path] = img
    return img


def _draw_text_left(screen, text, font, color, x, y):
    surf = font.render(text, True, color)
    screen.blit(surf, (x, y))


def _draw_text_center(screen, text, font, color, x, y):
    surf = font.render(text, True, color)
    rect = surf.get_rect(center=(x, y))
    screen.blit(surf, rect)


def _draw_outlined_text_left(screen, text, font, text_color, outline_color, x, y):
    base = font.render(text, True, text_color)
    outline = font.render(text, True, outline_color)
    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, -1), (-1, 1), (1, 1)]:
        screen.blit(outline, (x + dx, y + dy))
    screen.blit(base, (x, y))


def _current_page():
    return PAGES[_idx]


# Show the full current page immediately.
def _force_complete_page():
    global _line_idx, _char_idx, _page_done
    _line_idx = len(_current_page()["lines"])
    _char_idx = 0
    _page_done = True


def _next_page():
    global _idx, _line_idx, _char_idx, _page_done, _finished, _fade_alpha
    _idx += 1
    _line_idx = 0
    _char_idx = 0
    _page_done = False
    _fade_alpha = 255

    if _idx >= len(PAGES):
        _finished = True


def _skip_logic():
    global _page_done
    if _finished:
        return
    if not _page_done:
        _force_complete_page()
    else:
        _next_page()


# Create a light snow layer for the storyboard.
def _init_snow():
    global _snow
    _snow = []
    for _ in range(SNOW_COUNT):
        x = random.randint(0, WIDTH)
        y = random.randint(0, HEIGHT)
        r = random.randint(1, 3)
        sp = random.randint(1, 3)
        _snow.append([x, y, sp, r])


def _update_and_draw_snow(screen):
    layer = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    for p in _snow:
        x, y, sp, r = p
        pygame.draw.circle(layer, (255, 255, 255, SNOW_ALPHA), (int(x), int(y)), r)
        p[1] += sp
        if p[1] > HEIGHT:
            p[0] = random.randint(0, WIDTH)
            p[1] = random.randint(-20, 0)
            p[2] = random.randint(1, 3)
            p[3] = random.randint(1, 3)
    screen.blit(layer, (0, 0))


# Draw the shared skip controls.
def _draw_skip_button(screen, small_font):
    mouse = pygame.mouse.get_pos()
    hover = SKIP_RECT.collidepoint(mouse)
    symbol_rect = _get_skip_symbol_rect()
    symbol_hover = symbol_rect.collidepoint(mouse)

    tick = pygame.time.get_ticks()
    arrow_offset = ((tick // 280) % 2) * 5

    sym_bg = (255, 200, 0) if symbol_hover else (230, 230, 230)
    pygame.draw.rect(screen, sym_bg, symbol_rect, border_radius=10)
    pygame.draw.rect(screen, (0, 0, 0), symbol_rect, 2, border_radius=10)
    sym_label = ">>|"
    sym_surf = small_font.render(sym_label, True, (0, 0, 0))
    sym_rect = sym_surf.get_rect(center=(symbol_rect.centerx + arrow_offset, symbol_rect.centery))
    screen.blit(sym_surf, sym_rect)

    bg_col = (255, 200, 0) if hover else (230, 230, 230)
    pygame.draw.rect(screen, bg_col, SKIP_RECT, border_radius=10)
    pygame.draw.rect(screen, (0, 0, 0), SKIP_RECT, 2, border_radius=10)

    label = "SKIP >>"
    surf = small_font.render(label, True, (0, 0, 0))
    rect = surf.get_rect(center=(SKIP_RECT.centerx + arrow_offset, SKIP_RECT.centery))
    screen.blit(surf, rect)


def _get_skip_symbol_rect():
    return pygame.Rect(
        SKIP_RECT.x - SKIP_GAP - SKIP_SYMBOL_W,
        SKIP_RECT.y,
        SKIP_SYMBOL_W,
        SKIP_RECT.height
    )


def _draw_cinematic_bars(screen):
    pygame.draw.rect(screen, (0, 0, 0), (0, 0, WIDTH, BAR_H))
    pygame.draw.rect(screen, (0, 0, 0), (0, HEIGHT - BAR_H, WIDTH, BAR_H))


# Fade each page in for a simple transition.
def _draw_fade(screen):
    global _fade_alpha
    if _fade_alpha <= 0:
        return
    fade = pygame.Surface((WIDTH, HEIGHT))
    fade.fill((0, 0, 0))
    fade.set_alpha(_fade_alpha)
    screen.blit(fade, (0, 0))
    _fade_alpha = max(0, _fade_alpha - FADE_STEP)


# Reset story progress when the storyboard opens.
def reset():
    global _idx, _line_idx, _char_idx, _page_done, _finished, _last_tick, _fade_alpha
    _idx = 0
    _line_idx = 0
    _char_idx = 0
    _page_done = False
    _finished = False
    _last_tick = pygame.time.get_ticks()
    _fade_alpha = 255
    _init_snow()


def is_finished() -> bool:
    return _finished


# Keyboard input advances or skips story pages.
def handle_key(key: int):
    if key in (pygame.K_SPACE, pygame.K_RETURN):
        _skip_logic()


# Mouse clicks can advance the story or exit it.
def handle_click(pos):
    global _finished
    symbol_rect = _get_skip_symbol_rect()
    if symbol_rect.collidepoint(pos):
        _finished = True
    elif SKIP_RECT.collidepoint(pos):
        _skip_logic()


def is_hovering_clickable(pos) -> bool:
    symbol_rect = _get_skip_symbol_rect()
    return SKIP_RECT.collidepoint(pos) or symbol_rect.collidepoint(pos)


# Draw the current storyboard page.
def draw(screen, title_font, menu_font, small_font):
    global _char_idx, _line_idx, _page_done, _last_tick

    if _finished:
        return

    page = _current_page()
    bg = _load_bg(page["bg"])
    if bg:
        screen.blit(bg, (0, 0))
    else:
        screen.fill((225, 235, 255))

    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, OVERLAY_ALPHA))
    screen.blit(overlay, (0, 0))

    _update_and_draw_snow(screen)
    _draw_cinematic_bars(screen)
    _draw_outlined_text_left(screen, page["title"], menu_font, (255, 255, 255), (0, 0, 0), 50, BAR_H + 10)

    dialogue_surface = pygame.Surface((DIALOG_RECT.width, DIALOG_RECT.height), pygame.SRCALPHA)
    pygame.draw.rect(
        dialogue_surface,
        (0, 0, 0, 140),
        pygame.Rect(0, 0, DIALOG_RECT.width, DIALOG_RECT.height),
        border_radius=14
    )
    screen.blit(dialogue_surface, (DIALOG_RECT.x, DIALOG_RECT.y))

    pygame.draw.rect(screen, (255,255,255), DIALOG_RECT, 2, border_radius=14)

    now = pygame.time.get_ticks()
    if not _page_done and (now - _last_tick) >= TYPE_SPEED_MS:
        _last_tick = now
        lines = page["lines"]

        if _line_idx < len(lines):
            _char_idx += 1
            if _char_idx > len(lines[_line_idx]):
                _line_idx += 1
                _char_idx = 0

        if _line_idx >= len(lines):
            _page_done = True

    x = DIALOG_RECT.x + 24
    y = DIALOG_RECT.y + 16
    lines = page["lines"]

    for i in range(len(lines)):
        if i < _line_idx:
            shown = lines[i]
        elif i == _line_idx and not _page_done:
            shown = lines[i][:_char_idx]
        elif i == _line_idx and _page_done:
            shown = lines[i]
        else:
            shown = ""

        if shown:
            _draw_text_left(screen, shown, small_font, (255, 255, 255), x, y)
        y += 34

    _draw_skip_button(screen, small_font)
    _draw_fade(screen)
