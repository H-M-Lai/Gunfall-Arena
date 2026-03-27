import os

import pygame

import storyboard
from app_config import (
    ASSET_DIR,
    MAIN_MENU_BG_PATH,
    WIDTH,
    HEIGHT,
    WHITE,
    BLACK,
    CHARACTER_IMAGE_MAP,
    HANDGUN_OPTIONS,
    game_font,
)
from ui_helpers import (
    draw_text,
    draw_text_left,
    draw_wrapped_text_left,
    draw_input_text,
    draw_outlined_text,
    draw_outlined_text_center,
    draw_main_logo,
    draw_main_menu_item,
    draw_hover_info,
    draw_button,
    draw_toggle_button,
    draw_popup,
    draw_arrow_button,
    key_name,
)


gun_img_cache = {}
level_preview_cache = {}
main_menu_bg = None


def load_gun_image(path):
    if path in gun_img_cache:
        return gun_img_cache[path]

    if not os.path.exists(path):
        gun_img_cache[path] = None
        return None

    img = pygame.image.load(path).convert_alpha()
    gun_img_cache[path] = img
    return img


def load_level_preview(level_id, size):
    key = (level_id, int(size[0]), int(size[1]))
    if key in level_preview_cache:
        return level_preview_cache[key]

    if level_id == 1:
        bg_path = os.path.join(ASSET_DIR, "background", "level1.jpeg")
        plat_path = os.path.join(ASSET_DIR, "background", "platform.png")
    else:
        bg_path = os.path.join(ASSET_DIR, "background", "level2.jpeg")
        plat_path = os.path.join(ASSET_DIR, "background", "platform2.png")

    panel = pygame.Surface(size, pygame.SRCALPHA)
    panel.fill((95, 95, 95))

    if os.path.exists(bg_path):
        bg = pygame.image.load(bg_path).convert()
        panel.blit(pygame.transform.smoothscale(bg, size), (0, 0))

    if os.path.exists(plat_path):
        plat = pygame.image.load(plat_path).convert_alpha()
        pw = int(size[0] * 0.88)
        ph = int(size[1] * 0.74)
        plat_scaled = pygame.transform.smoothscale(plat, (pw, ph))
        panel.blit(plat_scaled, ((size[0] - pw) // 2, int(size[1] * 0.18)))

    level_preview_cache[key] = panel
    return panel


def load_main_menu_bg():
    global main_menu_bg
    if main_menu_bg is not None:
        return main_menu_bg
    if not os.path.exists(MAIN_MENU_BG_PATH):
        return None
    img = pygame.image.load(MAIN_MENU_BG_PATH).convert()
    main_menu_bg = pygame.transform.smoothscale(img, (WIDTH, HEIGHT))
    return main_menu_bg


def draw_snow_background(screen):
    screen.fill((58, 58, 58))
    storyboard._update_and_draw_snow(screen)


def draw_main_menu(screen, mouse_pos, hover_font):
    bg = load_main_menu_bg()
    if bg is not None:
        screen.blit(bg, (0, 0))

    storyboard._update_and_draw_snow(screen)
    draw_main_logo(screen, 20, 10)

    menu_right = WIDTH - 20
    menu_gap = 58
    menu_y = HEIGHT // 2 - 60

    start_btn, start_mid_y = draw_main_menu_item(screen, hover_font, "START GAME", menu_right, menu_y)
    control_btn, control_mid_y = draw_main_menu_item(
        screen, hover_font, "CONTROLS & SETTINGS", menu_right, menu_y + menu_gap
    )
    exit_btn, exit_mid_y = draw_main_menu_item(
        screen, hover_font, "QUIT", menu_right, menu_y + menu_gap * 2
    )

    start_hover_rect = pygame.Rect(0, start_mid_y - 20, WIDTH, 40)
    control_hover_rect = pygame.Rect(0, control_mid_y - 20, WIDTH, 40)
    exit_hover_rect = pygame.Rect(0, exit_mid_y - 20, WIDTH, 40)

    hover_text = None
    hover_y = 0
    if start_btn.collidepoint(mouse_pos) or start_hover_rect.collidepoint(mouse_pos):
        hover_text = "Start a new game and enter player names"
        hover_y = start_mid_y - 20
    elif control_btn.collidepoint(mouse_pos) or control_hover_rect.collidepoint(mouse_pos):
        hover_text = "Change movement and shoot key bindings"
        hover_y = control_mid_y - 20
    elif exit_btn.collidepoint(mouse_pos) or exit_hover_rect.collidepoint(mouse_pos):
        hover_text = "Close the game"
        hover_y = exit_mid_y - 20

    if hover_text:
        draw_hover_info(screen, hover_font, hover_text, hover_y)
        draw_main_menu_item(screen, hover_font, "START GAME", menu_right, menu_y)
        draw_main_menu_item(screen, hover_font, "CONTROLS & SETTINGS", menu_right, menu_y + menu_gap)
        draw_main_menu_item(screen, hover_font, "QUIT", menu_right, menu_y + menu_gap * 2)

    return {
        "start_btn": start_btn,
        "start_hover_rect": start_hover_rect,
        "control_btn": control_btn,
        "control_hover_rect": control_hover_rect,
        "exit_btn": exit_btn,
        "exit_hover_rect": exit_hover_rect,
        "hover_clickable": (
            start_btn.collidepoint(mouse_pos)
            or start_hover_rect.collidepoint(mouse_pos)
            or control_btn.collidepoint(mouse_pos)
            or control_hover_rect.collidepoint(mouse_pos)
            or exit_btn.collidepoint(mouse_pos)
            or exit_hover_rect.collidepoint(mouse_pos)
        ),
    }


def draw_level_select(screen, mouse_pos):
    draw_snow_background(screen)

    header = pygame.Rect(20, 10, WIDTH - 40, 60)
    pygame.draw.rect(screen, (120, 120, 120), header)
    pygame.draw.rect(screen, BLACK, header, 3)
    draw_outlined_text(screen, "LEVEL SELECT", game_font(44), WHITE, BLACK, 35, 12)

    card_y = 130
    card_w = 350
    card_h = 260

    lvl1_card = pygame.Rect(60, card_y, card_w, card_h)
    lvl2_card = pygame.Rect(WIDTH - 60 - card_w, card_y, card_w, card_h)

    for card, title, lvl in [
        (lvl1_card, "LEVEL 1", 1),
        (lvl2_card, "LEVEL 2", 2),
    ]:
        preview = load_level_preview(lvl, (card.w, card.h))
        screen.blit(preview, card.topleft)
        wash = pygame.Surface((card.w, card.h), pygame.SRCALPHA)
        wash.fill((255, 255, 255, 45))
        screen.blit(wash, card.topleft)
        pygame.draw.rect(screen, BLACK, card, 3)
        draw_outlined_text(screen, title, game_font(42), WHITE, BLACK, card.x + 20, card.y + 22)

    back_btn = draw_button(
        screen,
        "BACK",
        20,
        HEIGHT - 70,
        140,
        48,
        base_color=(200, 200, 200),
        hover_color=(140, 140, 140),
    )

    return {
        "lvl1_card": lvl1_card,
        "lvl2_card": lvl2_card,
        "back_btn": back_btn,
        "hover_clickable": (
            lvl1_card.collidepoint(mouse_pos)
            or lvl2_card.collidepoint(mouse_pos)
            or back_btn.collidepoint(mouse_pos)
        ),
    }


def draw_mode_select(screen, mouse_pos, name_input_font, state):
    draw_snow_background(screen)

    header = pygame.Rect(20, 10, WIDTH - 40, 60)
    pygame.draw.rect(screen, (120, 120, 120), header)
    pygame.draw.rect(screen, BLACK, header, 3)
    draw_outlined_text(screen, "PLAYER SETUP", game_font(44), WHITE, BLACK, 35, 12)

    left_panel = pygame.Rect(20, 95, 205, 420)
    mid_panel = pygame.Rect(245, 95, 205, 420)
    right_panel = pygame.Rect(470, 95, 410, 420)

    for panel in (left_panel, mid_panel, right_panel):
        pygame.draw.rect(screen, (205, 205, 205), panel)
        pygame.draw.rect(screen, BLACK, panel, 3)

    p1_avatar_rect = pygame.Rect(left_panel.centerx - 45, left_panel.y + 110, 90, 150)
    p1_char_img = load_gun_image(CHARACTER_IMAGE_MAP[state["player1_gender"]])
    if p1_char_img is not None:
        p1_preview = pygame.transform.smoothscale(p1_char_img, (p1_avatar_rect.w, p1_avatar_rect.h))
        screen.blit(p1_preview, (p1_avatar_rect.x, p1_avatar_rect.y))
    else:
        draw_text(screen, "P1", game_font(30), BLACK, p1_avatar_rect.centerx, p1_avatar_rect.centery)

    p1_left_arrow = draw_arrow_button(screen, p1_avatar_rect.x - 40, p1_avatar_rect.centery - 18, 36, "left")
    p1_right_arrow = draw_arrow_button(screen, p1_avatar_rect.right + 4, p1_avatar_rect.centery - 18, 36, "right")

    draw_text_left(screen, "NAME:", game_font(22), BLACK, left_panel.x + 26, left_panel.y + 278)
    p1_input_rect = pygame.Rect(left_panel.x + 26, left_panel.y + 304, left_panel.w - 52, 36)
    p1_active = state["name_edit_field"] == "P1"
    p1_cursor = p1_active and (pygame.time.get_ticks() // 500) % 2 == 0
    draw_input_text(screen, name_input_font, state["player1_name"], p1_input_rect, p1_active, p1_cursor)

    p1_handgun_btn = draw_button(
        screen,
        "HANDGUN",
        left_panel.x + 26,
        left_panel.y + 359,
        left_panel.w - 52,
        36,
        base_color=(190, 190, 190),
        hover_color=(150, 150, 150),
        font_size_override=22,
    )

    p2_input_rect = pygame.Rect(mid_panel.x + 26, mid_panel.y + 304, mid_panel.w - 52, 36)
    p2_handgun_btn = pygame.Rect(mid_panel.x + 26, mid_panel.y + 359, mid_panel.w - 52, 36)
    p2_left_arrow = pygame.Rect(0, 0, 0, 0)
    p2_right_arrow = pygame.Rect(0, 0, 0, 0)
    add_p2_btn = pygame.Rect(mid_panel.x + 26, mid_panel.y + 180, mid_panel.w - 52, 36)
    clear_slot_btn = pygame.Rect(mid_panel.x + 26, mid_panel.y + 16, mid_panel.w - 52, 36)
    handgun_option_btns = []
    handgun_back_btn = pygame.Rect(mid_panel.x + 26, mid_panel.y + 375, mid_panel.w - 52, 36)

    if state["selected_mode"] == 2:
        pygame.draw.rect(screen, (220, 180, 180), clear_slot_btn)
        pygame.draw.rect(screen, BLACK, clear_slot_btn, 2)
        draw_text(screen, "CLEAR SLOT", game_font(22), BLACK, clear_slot_btn.centerx, clear_slot_btn.centery)

        pygame.draw.line(
            screen,
            BLACK,
            (mid_panel.x, mid_panel.y + 62),
            (mid_panel.x + mid_panel.w, mid_panel.y + 62),
            3,
        )

        p2_avatar_rect = pygame.Rect(mid_panel.centerx - 45, mid_panel.y + 110, 90, 150)
        p2_char_img = load_gun_image(CHARACTER_IMAGE_MAP[state["player2_gender"]])
        if p2_char_img is not None:
            p2_preview = pygame.transform.smoothscale(p2_char_img, (p2_avatar_rect.w, p2_avatar_rect.h))
            screen.blit(p2_preview, (p2_avatar_rect.x, p2_avatar_rect.y))
        else:
            draw_text(screen, "P2", game_font(30), BLACK, p2_avatar_rect.centerx, p2_avatar_rect.centery)

        p2_left_arrow = draw_arrow_button(screen, p2_avatar_rect.x - 40, p2_avatar_rect.centery - 18, 36, "left")
        p2_right_arrow = draw_arrow_button(screen, p2_avatar_rect.right + 4, p2_avatar_rect.centery - 18, 36, "right")

        draw_text_left(screen, "NAME:", game_font(22), BLACK, mid_panel.x + 26, mid_panel.y + 278)
        p2_active = state["name_edit_field"] == "P2"
        p2_cursor = p2_active and (pygame.time.get_ticks() // 500) % 2 == 0
        draw_input_text(screen, name_input_font, state["player2_name"], p2_input_rect, p2_active, p2_cursor)

        p2_handgun_btn = draw_button(
            screen,
            "HANDGUN",
            mid_panel.x + 26,
            mid_panel.y + 359,
            mid_panel.w - 52,
            36,
            base_color=(190, 190, 190),
            hover_color=(150, 150, 150),
            font_size_override=22,
        )
    else:
        draw_outlined_text(screen, "SLOT EMPTY", game_font(24), (200, 30, 30), BLACK, mid_panel.x + 44, mid_panel.y + 22)
        coop_font = game_font(28)
        add_coop_w = coop_font.render("ADD COOP", True, WHITE).get_width()
        partner_w = coop_font.render("PARTNER", True, WHITE).get_width()
        draw_outlined_text(screen, "ADD COOP", coop_font, WHITE, BLACK, mid_panel.centerx - add_coop_w // 2, mid_panel.y + 112)
        draw_outlined_text(screen, "PARTNER", coop_font, WHITE, BLACK, mid_panel.centerx - partner_w // 2, mid_panel.y + 146)
        add_p2_btn = pygame.Rect(mid_panel.x + 26, mid_panel.y + 220, mid_panel.w - 52, 36)
        add_hover = add_p2_btn.collidepoint(mouse_pos)
        pygame.draw.rect(screen, (150, 150, 150) if add_hover else (190, 190, 190), add_p2_btn)
        pygame.draw.rect(screen, BLACK, add_p2_btn, 2)
        draw_text(screen, "ADD PLAYER 2", game_font(20), BLACK, add_p2_btn.centerx, add_p2_btn.centery)

    if state["handgun_select_target"] is not None:
        selector_panel = left_panel if state["handgun_select_target"] == "P1" else mid_panel
        pygame.draw.rect(screen, (205, 205, 205), selector_panel)
        pygame.draw.rect(screen, BLACK, selector_panel, 3)

        handgun_title_font = game_font(34)
        handgun_title_w = handgun_title_font.render("HANDGUN", True, WHITE).get_width()
        draw_outlined_text(
            screen,
            "HANDGUN",
            handgun_title_font,
            WHITE,
            BLACK,
            selector_panel.centerx - handgun_title_w // 2,
            selector_panel.y + 24,
        )
        grid_x = selector_panel.x + 24
        grid_y = selector_panel.y + 120
        cell_w = 72
        cell_h = 72
        gap_x = 14
        current_gun = state["selected_handgun_p1"] if state["handgun_select_target"] == "P1" else state["selected_handgun_p2"]

        for idx, option in enumerate(HANDGUN_OPTIONS):
            gun_name = option["label"]
            col = idx % 2
            rect = pygame.Rect(grid_x + col * (cell_w + gap_x), grid_y, cell_w, cell_h)
            hovered = rect.collidepoint(mouse_pos)
            selected = gun_name == current_gun
            fill = (
                (230, 205, 120)
                if selected
                else ((170, 170, 170) if hovered else (205, 205, 205))
            )
            pygame.draw.rect(screen, fill, rect)
            pygame.draw.rect(screen, BLACK, rect, 2)

            gun_img = load_gun_image(option["image"])
            if gun_img is not None:
                preview = pygame.transform.smoothscale(gun_img, (cell_w - 10, cell_h - 10))
                screen.blit(preview, (rect.x + 5, rect.y + 5))
            else:
                draw_text(screen, str(idx + 1), game_font(22), BLACK, rect.centerx, rect.centery)

            handgun_option_btns.append((rect, gun_name))

        draw_text(screen, current_gun, game_font(22), BLACK, selector_panel.centerx, selector_panel.y + 336)
        handgun_back_btn = draw_button(
            screen,
            "BACK",
            selector_panel.x + 26,
            selector_panel.y + 365,
            selector_panel.w - 52,
            36,
            base_color=(190, 190, 190),
            hover_color=(150, 150, 150),
            font_size_override=22,
        )

    preview_rect = pygame.Rect(right_panel.x + 20, right_panel.y + 24, right_panel.w - 40, 250)
    preview = load_level_preview(state["selected_level"], (preview_rect.w, preview_rect.h))
    screen.blit(preview, preview_rect.topleft)
    pygame.draw.rect(screen, BLACK, preview_rect, 3)

    level_title = "Level 1: Elimination" if state["selected_level"] == 1 else "Level 2: Flag Capture"
    map_title = "Map: Frozen Outskirts" if state["selected_level"] == 1 else "Map: Snowman Stronghold"
    level_desc = (
        "Knock the Snowman off the arena until their lives are depleted."
        if state["selected_level"] == 1
        else "Capture the flag objectives before the enemy team does."
    )
    draw_text_left(screen, level_title, game_font(28), BLACK, right_panel.x + 20, right_panel.y + 278)
    draw_text_left(screen, map_title, game_font(28), BLACK, right_panel.x + 20, right_panel.y + 308)
    pygame.draw.line(
        screen,
        BLACK,
        (right_panel.x + 20, right_panel.y + 348),
        (right_panel.x + right_panel.w - 20, right_panel.y + 348),
        3,
    )
    draw_wrapped_text_left(
        screen,
        level_desc,
        game_font(22),
        BLACK,
        right_panel.x + 20,
        right_panel.y + 356,
        right_panel.w - 48,
        0,
    )

    back_btn = draw_button(
        screen,
        "BACK",
        20,
        HEIGHT - 70,
        140,
        52,
        base_color=(230, 230, 230),
        hover_color=(190, 190, 190),
    )
    start_btn = pygame.Rect(WIDTH - 320, HEIGHT - 70, 300, 52)
    start_hover = start_btn.collidepoint(mouse_pos)
    start_color = (145, 10, 10) if start_hover else (185, 20, 20)
    pygame.draw.rect(screen, start_color, start_btn)
    pygame.draw.rect(screen, BLACK, start_btn, 3)
    draw_outlined_text_center(screen, "START LEVEL", game_font(30), WHITE, BLACK, start_btn.centerx, start_btn.centery)

    hover_clickable = (
        p1_input_rect.collidepoint(mouse_pos)
        or p1_handgun_btn.collidepoint(mouse_pos)
        or p1_left_arrow.collidepoint(mouse_pos)
        or p1_right_arrow.collidepoint(mouse_pos)
        or add_p2_btn.collidepoint(mouse_pos)
        or (
            state["selected_mode"] == 2
            and (
                clear_slot_btn.collidepoint(mouse_pos)
                or p2_input_rect.collidepoint(mouse_pos)
                or p2_handgun_btn.collidepoint(mouse_pos)
                or p2_left_arrow.collidepoint(mouse_pos)
                or p2_right_arrow.collidepoint(mouse_pos)
            )
        )
        or (
            state["handgun_select_target"] is not None
            and (
                any(rect.collidepoint(mouse_pos) for rect, _ in handgun_option_btns)
                or handgun_back_btn.collidepoint(mouse_pos)
            )
        )
        or back_btn.collidepoint(mouse_pos)
        or start_btn.collidepoint(mouse_pos)
    )

    return {
        "p1_left_arrow": p1_left_arrow,
        "p1_right_arrow": p1_right_arrow,
        "p1_input_rect": p1_input_rect,
        "p1_handgun_btn": p1_handgun_btn,
        "add_p2_btn": add_p2_btn,
        "clear_slot_btn": clear_slot_btn,
        "p2_input_rect": p2_input_rect,
        "p2_handgun_btn": p2_handgun_btn,
        "p2_left_arrow": p2_left_arrow,
        "p2_right_arrow": p2_right_arrow,
        "handgun_option_btns": handgun_option_btns,
        "handgun_back_btn": handgun_back_btn,
        "back_btn": back_btn,
        "start_btn": start_btn,
        "hover_clickable": hover_clickable,
    }


def draw_history_page(screen, mouse_pos, title_font, menu_font, small_font, records):
    screen.fill(WHITE)
    draw_text(screen, "Match History", title_font, BLACK, WIDTH // 2, 80)

    y = 150
    if not records:
        draw_text(screen, "No History", menu_font, BLACK, WIDTH // 2, 300)
    else:
        for record in records:
            d = record.split("|")
            txt = f"{d[0]} {d[1]}  {d[2]} vs {d[3]}  Winner:{d[5]}"
            draw_text(screen, txt, small_font, BLACK, WIDTH // 2, y)
            y += 40

    back_btn = draw_button(screen, "Back", 350, 500, 200, 60)
    return {
        "back_btn": back_btn,
        "hover_clickable": back_btn.collidepoint(mouse_pos),
    }


def draw_control_page(
    screen,
    mouse_pos,
    controls_p1,
    controls_p2,
    music_enabled,
    sound_enabled,
    show_popup,
    menu_font,
):
    draw_snow_background(screen)

    header = pygame.Rect(20, 10, WIDTH - 40, 60)
    pygame.draw.rect(screen, (120, 120, 120), header)
    pygame.draw.rect(screen, BLACK, header, 3)
    draw_outlined_text(screen, "Options", game_font(44), WHITE, BLACK, 35, 12)

    box = 56
    gap = 66
    key_spacing = 8
    card_w, card_h = 290, 310
    card_y = 120
    key_base = (200, 200, 200)
    key_hover = (140, 140, 140)

    p1_card = pygame.Rect(60, card_y, card_w, card_h)
    pygame.draw.rect(screen, (205, 205, 205), p1_card)
    pygame.draw.rect(screen, BLACK, p1_card, 3)
    draw_outlined_text(screen, "Player 1", game_font(38), WHITE, BLACK, p1_card.x + 82, p1_card.y + 2)

    p1_x = p1_card.centerx
    p1_y = p1_card.y + 125
    p1_jump = draw_button(screen, key_name(controls_p1["JUMP"]), p1_x - box // 2, p1_y - gap, box, box, base_color=key_base, hover_color=key_hover)
    p1_left = draw_button(screen, key_name(controls_p1["LEFT"]), p1_x - box - box // 2 - key_spacing, p1_y, box, box, base_color=key_base, hover_color=key_hover)
    p1_down = draw_button(screen, key_name(controls_p1["DOWN"]), p1_x - box // 2, p1_y, box, box, base_color=key_base, hover_color=key_hover)
    p1_right = draw_button(screen, key_name(controls_p1["RIGHT"]), p1_x + box // 2 + key_spacing, p1_y, box, box, base_color=key_base, hover_color=key_hover)
    draw_text(screen, "SHOOT", game_font(28), BLACK, p1_x, p1_y + 95)
    p1_shoot = draw_button(screen, key_name(controls_p1["SHOOT"]), p1_x - box // 2, p1_y + 120, box, box, base_color=key_base, hover_color=key_hover)

    p2_card = pygame.Rect(WIDTH - 60 - card_w, card_y, card_w, card_h)
    pygame.draw.rect(screen, (205, 205, 205), p2_card)
    pygame.draw.rect(screen, BLACK, p2_card, 3)
    draw_outlined_text(screen, "Player 2", game_font(38), WHITE, BLACK, p2_card.x + 82, p2_card.y + 2)

    p2_x = p2_card.centerx
    p2_y = p2_card.y + 125
    p2_jump = draw_button(screen, key_name(controls_p2["JUMP"]), p2_x - box // 2, p2_y - gap, box, box, base_color=key_base, hover_color=key_hover)
    p2_left = draw_button(screen, key_name(controls_p2["LEFT"]), p2_x - box - box // 2 - key_spacing, p2_y, box, box, base_color=key_base, hover_color=key_hover)
    p2_down = draw_button(screen, key_name(controls_p2["DOWN"]), p2_x - box // 2, p2_y, box, box, base_color=key_base, hover_color=key_hover)
    p2_right = draw_button(screen, key_name(controls_p2["RIGHT"]), p2_x + box // 2 + key_spacing, p2_y, box, box, base_color=key_base, hover_color=key_hover)
    draw_text(screen, "SHOOT", game_font(28), BLACK, p2_x, p2_y + 95)
    p2_shoot = draw_button(screen, key_name(controls_p2["SHOOT"]), p2_x - box // 2, p2_y + 120, box, box, base_color=key_base, hover_color=key_hover)

    options_box = pygame.Rect(40, 480, 560, 95)
    pygame.draw.rect(screen, (205, 205, 205), options_box)
    pygame.draw.rect(screen, BLACK, options_box, 3)

    draw_outlined_text(screen, "Game Options", game_font(34), WHITE, BLACK, 20, 434)
    draw_outlined_text(screen, "Controls", game_font(32), WHITE, BLACK, 20, 74)

    btn_w = 66
    btn_h = 40
    pair_w = btn_w * 2 + 14
    left_center_x = options_box.x + options_box.w // 4
    right_center_x = options_box.x + options_box.w * 3 // 4
    label_y = options_box.y + 6
    btn_y = options_box.y + 43

    option_label_font = game_font(30)
    music_w = option_label_font.render("Music", True, WHITE).get_width()
    draw_outlined_text(screen, "Music", option_label_font, WHITE, BLACK, left_center_x - music_w // 2, label_y)
    music_pair_x = left_center_x - pair_w // 2
    music_on_btn = draw_toggle_button(screen, "ON", music_pair_x, btn_y, btn_w, btn_h, music_enabled)
    music_off_btn = draw_toggle_button(screen, "OFF", music_pair_x + btn_w + 14, btn_y, btn_w, btn_h, not music_enabled)

    sfx_w = option_label_font.render("SFX", True, WHITE).get_width()
    draw_outlined_text(screen, "SFX", option_label_font, WHITE, BLACK, right_center_x - sfx_w // 2, label_y)
    sound_pair_x = right_center_x - pair_w // 2
    sound_on_btn = draw_toggle_button(screen, "ON", sound_pair_x, btn_y, btn_w, btn_h, sound_enabled)
    sound_off_btn = draw_toggle_button(screen, "OFF", sound_pair_x + btn_w + 14, btn_y, btn_w, btn_h, not sound_enabled)

    back_btn = pygame.Rect(660, 520, 210, 60)
    back_hover = back_btn.collidepoint(mouse_pos)
    back_color = (145, 10, 10) if back_hover else (185, 20, 20)
    pygame.draw.rect(screen, back_color, back_btn)
    pygame.draw.rect(screen, BLACK, back_btn, 3)
    draw_outlined_text(screen, "BACK TO MENU", game_font(30), WHITE, BLACK, back_btn.x + 23, back_btn.y + 12)

    if show_popup:
        draw_popup(screen, menu_font)

    hover_clickable = (
        p1_jump.collidepoint(mouse_pos)
        or p1_left.collidepoint(mouse_pos)
        or p1_right.collidepoint(mouse_pos)
        or p1_down.collidepoint(mouse_pos)
        or p1_shoot.collidepoint(mouse_pos)
        or p2_jump.collidepoint(mouse_pos)
        or p2_left.collidepoint(mouse_pos)
        or p2_right.collidepoint(mouse_pos)
        or p2_down.collidepoint(mouse_pos)
        or p2_shoot.collidepoint(mouse_pos)
        or music_on_btn.collidepoint(mouse_pos)
        or music_off_btn.collidepoint(mouse_pos)
        or sound_on_btn.collidepoint(mouse_pos)
        or sound_off_btn.collidepoint(mouse_pos)
        or back_btn.collidepoint(mouse_pos)
    )

    return {
        "p1_jump": p1_jump,
        "p1_left": p1_left,
        "p1_right": p1_right,
        "p1_down": p1_down,
        "p1_shoot": p1_shoot,
        "p2_jump": p2_jump,
        "p2_left": p2_left,
        "p2_right": p2_right,
        "p2_down": p2_down,
        "p2_shoot": p2_shoot,
        "music_on_btn": music_on_btn,
        "music_off_btn": music_off_btn,
        "sound_on_btn": sound_on_btn,
        "sound_off_btn": sound_off_btn,
        "back_btn": back_btn,
        "hover_clickable": hover_clickable,
    }
