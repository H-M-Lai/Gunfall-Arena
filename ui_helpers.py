import pygame

from app_config import (
    WIDTH,
    HEIGHT,
    WHITE,
    BLACK,
    GRAY,
    YELLOW,
    NAME_BOX_TEXT_PADDING_X,
    NAME_BOX_TEXT_PADDING_Y,
    game_font,
    headline_font,
)


def draw_text(screen, text, font, color, x, y):
    render = font.render(text, True, color)
    rect = render.get_rect(center=(x, y))
    screen.blit(render, rect)


def draw_text_left(screen, text, font, color, x, y):
    render = font.render(text, True, color)
    screen.blit(render, (x, y))


def draw_wrapped_text_left(screen, text, font, color, x, y, max_width, line_gap=6):
    words = text.split()
    if not words:
        return

    lines = []
    current_line = words[0]
    for word in words[1:]:
        trial = f"{current_line} {word}"
        if font.size(trial)[0] <= max_width:
            current_line = trial
        else:
            lines.append(current_line)
            current_line = word
    lines.append(current_line)

    for idx, line in enumerate(lines):
        draw_text_left(screen, line, font, color, x, y + idx * (font.get_height() + line_gap))


def draw_input_text(screen, name_input_font, text, rect, active, show_cursor=False):
    pygame.draw.rect(screen, (140, 195, 230) if active else (230, 230, 230), rect)
    pygame.draw.rect(screen, BLACK, rect, 2)

    text_surf = name_input_font.render(text, True, BLACK)
    text_x = rect.x + NAME_BOX_TEXT_PADDING_X
    text_y = rect.bottom - text_surf.get_height() - NAME_BOX_TEXT_PADDING_Y

    clip_rect = pygame.Rect(
        rect.x + NAME_BOX_TEXT_PADDING_X,
        rect.y + 2,
        rect.width - (NAME_BOX_TEXT_PADDING_X * 2),
        rect.height - 4,
    )
    old_clip = screen.get_clip()
    screen.set_clip(clip_rect)
    screen.blit(text_surf, (text_x, text_y))
    if show_cursor:
        caret_x = text_x + min(text_surf.get_width(), max(0, clip_rect.width - 2))
        pygame.draw.line(
            screen,
            BLACK,
            (caret_x, rect.y + 7),
            (caret_x, rect.y + rect.height - 7),
            2,
        )
    screen.set_clip(old_clip)


def can_append_name_char(name_input_font, current_text, ch, input_box_width):
    max_width = input_box_width - (NAME_BOX_TEXT_PADDING_X * 2)
    return name_input_font.size(current_text + ch)[0] <= max_width


def draw_outlined_text(screen, text, font, text_color, outline_color, x, y):
    base = font.render(text, True, text_color)
    outline = font.render(text, True, outline_color)
    shadow = font.render(text, True, (0, 0, 0))
    shadow.set_alpha(90)

    screen.blit(shadow, (x + 2, y + 2))

    for dx, dy in [
        (-1, 0),
        (1, 0),
        (0, -1),
        (0, 1),
        (-1, -1),
        (1, -1),
        (-1, 1),
        (1, 1),
    ]:
        screen.blit(outline, (x + dx, y + dy))

    screen.blit(base, (x, y))


def draw_outlined_text_center(
    screen, text, font, text_color, outline_color, center_x, center_y
):
    surf = font.render(text, True, text_color)
    x = center_x - surf.get_width() // 2
    y = center_y - surf.get_height() // 2
    draw_outlined_text(screen, text, font, text_color, outline_color, x, y)


def draw_main_logo(screen, x, y):
    logo_font = headline_font(64)
    text = "GUNFALL ARENA"
    base = logo_font.render(text, True, (246, 236, 214))
    outline = logo_font.render(text, True, (38, 22, 14))
    glow = logo_font.render(text, True, (255, 203, 92))

    for dx, dy in [(-4, 0), (4, 0), (0, -4), (0, 4), (-3, -3), (3, -3), (-3, 3), (3, 3)]:
        glow_surf = glow.copy()
        glow_surf.set_alpha(68)
        screen.blit(glow_surf, (x + dx, y + dy))

    shadow = logo_font.render(text, True, (0, 0, 0))
    shadow.set_alpha(100)
    screen.blit(shadow, (x + 3, y + 4))

    for dx, dy in [
        (-2, 0),
        (2, 0),
        (0, -2),
        (0, 2),
        (-2, -2),
        (2, -2),
        (-2, 2),
        (2, 2),
        (-1, 0),
        (1, 0),
        (0, -1),
        (0, 1),
    ]:
        screen.blit(outline, (x + dx, y + dy))

    screen.blit(base, (x, y))

    underline_y = y + base.get_height() + 2
    underline_left = x + 14
    underline_right = x + base.get_width() - 14
    pygame.draw.line(screen, (116, 17, 20), (underline_left, underline_y), (underline_right, underline_y), 4)
    pygame.draw.line(screen, (191, 36, 36), (underline_left, underline_y - 1), (underline_right, underline_y - 1), 2)


def draw_main_menu_item(screen, hover_font, text, right_x, y):
    item_font = headline_font(32)
    text_surface = item_font.render(text, True, WHITE)
    text_rect = text_surface.get_rect(top=y, right=right_x)
    rect = pygame.Rect(
        text_rect.x - 12, text_rect.y - 6, text_rect.w + 24, text_rect.h + 12
    )

    draw_outlined_text(screen, text, item_font, WHITE, BLACK, text_rect.x, text_rect.y)
    return rect, text_rect.centery


def draw_hover_info(screen, hover_font, text, y):
    bar = pygame.Surface((WIDTH, 40), pygame.SRCALPHA)
    bar.fill((0, 0, 0, 180))
    bar_y = max(0, min(HEIGHT - 40, y))
    screen.blit(bar, (0, bar_y))
    text_y = bar_y + 40 - hover_font.get_height() - 4
    draw_text_left(screen, text, hover_font, WHITE, 20, text_y)


def draw_button(
    screen, text, x, y, w, h, base_color=GRAY, hover_color=YELLOW, font_size_override=None
):
    mouse = pygame.mouse.get_pos()
    rect = pygame.Rect(x, y, w, h)
    color = hover_color if rect.collidepoint(mouse) else base_color

    pygame.draw.rect(screen, color, rect)
    pygame.draw.rect(screen, BLACK, rect, 2)

    font_size = (
        font_size_override
        if font_size_override is not None
        else (10 if w <= 80 else 30)
    )
    btn_font = game_font(font_size)

    render = btn_font.render(text, True, BLACK)
    text_rect = render.get_rect(center=rect.center)
    screen.blit(render, text_rect)
    return rect


def draw_toggle_button(screen, text, x, y, w, h, selected):
    rect = pygame.Rect(x, y, w, h)
    hovered = rect.collidepoint(pygame.mouse.get_pos())
    if selected:
        fill = (255, 140, 0)
    else:
        fill = (120, 120, 120) if hovered else (150, 150, 150)
    pygame.draw.rect(screen, fill, rect, border_radius=6)
    pygame.draw.rect(screen, BLACK, rect, 2, border_radius=6)

    font = game_font(20)
    render = font.render(text, True, BLACK)
    text_rect = render.get_rect(center=rect.center)
    screen.blit(render, text_rect)
    return rect


def draw_popup(screen, menu_font):
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(180)
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (0, 0))

    box = pygame.Rect(WIDTH // 2 - 250, HEIGHT // 2 - 100, 500, 200)
    pygame.draw.rect(screen, WHITE, box)
    pygame.draw.rect(screen, BLACK, box, 3)
    draw_text(screen, "Press a Valid Key to Assign", menu_font, BLACK, WIDTH // 2, HEIGHT // 2)


def draw_arrow_button(screen, x, y, size, direction):
    rect = pygame.Rect(x, y, size, size)
    hovered = rect.collidepoint(pygame.mouse.get_pos())
    color = (70, 70, 70) if hovered else (120, 120, 120)

    if direction == "left":
        pts = [
            (rect.x + size * 0.70, rect.y + size * 0.20),
            (rect.x + size * 0.30, rect.y + size * 0.50),
            (rect.x + size * 0.70, rect.y + size * 0.80),
        ]
    else:
        pts = [
            (rect.x + size * 0.30, rect.y + size * 0.20),
            (rect.x + size * 0.70, rect.y + size * 0.50),
            (rect.x + size * 0.30, rect.y + size * 0.80),
        ]
    pygame.draw.polygon(screen, color, pts)
    return rect


def key_name(key):
    return pygame.key.name(key).upper()
