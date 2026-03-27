import pygame
import sys 
import os
from datetime import datetime
import storyboard
import Level_1 as Level_1
import Level_2 as Level_2
from app_config import (
    WIDTH,
    HEIGHT,
    WHITE,
    BLACK,
    MAIN_MENU,
    STORYBOARD,
    LEVEL_SELECT,
    MODE_SELECT,
    HISTORY_PAGE,
    CONTROL_PAGE,
    LEVEL_1_PAGE,
    LEVEL_2_PAGE,
    HISTORY_FILE,
    game_font,
    create_screen,
)
from audio_manager import AudioManager
from menu_screens import (
    draw_main_menu,
    draw_level_select,
    draw_mode_select,
    draw_history_page,
    draw_control_page,
)
from ui_helpers import can_append_name_char

pygame.init()
screen = create_screen()
title_font = game_font(70)
menu_font = game_font(40)
input_font = game_font(35)
small_font = game_font(25)
hover_font = pygame.font.SysFont("Century Gothic", 16)
name_input_font = game_font(22)

clock = pygame.time.Clock()

game_state = MAIN_MENU

# ================== GAME DATA ==================
selected_mode = 1
selected_level = 1
player1_name = "Player 1"
player2_name = "Player 2"
input_stage = 1
active_name_field = "P1"
name_edit_field = None
handgun_select_target = None
selected_handgun_p1 = "GLOCK17"
selected_handgun_p2 = "SIG SAUER P226"
player1_gender = "male"
player2_gender = "female"

# ================== CONTROL SETTINGS ==================
controls_p1 = {
    "LEFT": pygame.K_LEFT,
    "RIGHT": pygame.K_RIGHT,
    "JUMP": pygame.K_UP,
    "DOWN": pygame.K_DOWN,
    "SHOOT": pygame.K_SPACE,
}

controls_p2 = {
    "LEFT": pygame.K_a,
    "RIGHT": pygame.K_d,
    "JUMP": pygame.K_w,
    "DOWN": pygame.K_s,
    "SHOOT": pygame.K_f,
}

waiting_for_key = None
show_popup = False
popup_action = ""
music_enabled = True
sound_enabled = True
controls_snow_ready = False
cursor_is_hand = False
audio_manager = AudioManager()
audio_manager.preload_ui_audio()


# ================== FUNCTIONS ==================
def set_game_state(new_state):
    global game_state
    # Stop lingering gameplay SFX when leaving a level page.
    if game_state in (LEVEL_1_PAGE, LEVEL_2_PAGE) and new_state != game_state:
        audio_manager.stop_active_level_audio()
    game_state = new_state
    audio_manager.sync_music_to_state(music_enabled, game_state)


def set_pointer_cursor(use_hand):
    global cursor_is_hand
    if use_hand == cursor_is_hand:
        return

    try:
        if use_hand:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
        else:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
        cursor_is_hand = use_hand
    except pygame.error:
        # Some platforms/cursor backends may not support system cursors.
        pass


# ================== HISTORY ==================
def save_match_record(
    player1, player2, mode, result, kills, falls, accuracy, flags, total_points
):

    now = datetime.now()

    record = (
        f"{now.strftime('%Y-%m-%d')}|"
        f"{now.strftime('%H:%M:%S')}|"
        f"{player1}|{player2}|{mode}|{result}|"
        f"{kills}|{falls}|{accuracy}|{flags}|{total_points}\n"
    )

    if not os.path.exists(HISTORY_FILE):
        open(HISTORY_FILE, "w").close()

    with open(HISTORY_FILE, "r") as f:
        lines = f.readlines()

    lines.append(record)
    lines = lines[-5:]

    with open(HISTORY_FILE, "w") as f:
        f.writelines(lines)


def load_history():

    if not os.path.exists(HISTORY_FILE):
        return []

    with open(HISTORY_FILE, "r") as f:
        return f.readlines()[::-1]


# ================== MAIN LOOP ==================
audio_manager.apply_sound_enabled(Level_1, Level_2, sound_enabled)
audio_manager.sync_music_to_state(music_enabled, game_state)

running = True

while running:

    screen.fill(WHITE)
    mouse_pos = pygame.mouse.get_pos()
    hover_clickable = False
    audio_manager.sync_music_to_state(music_enabled, game_state)

    # ================== MAIN MENU ==================
    if game_state == MAIN_MENU:
        if not controls_snow_ready:
            storyboard._init_snow()
            controls_snow_ready = True
        main_menu_ui = draw_main_menu(screen, mouse_pos, hover_font)
        start_btn = main_menu_ui["start_btn"]
        start_hover_rect = main_menu_ui["start_hover_rect"]
        control_btn = main_menu_ui["control_btn"]
        control_hover_rect = main_menu_ui["control_hover_rect"]
        exit_btn = main_menu_ui["exit_btn"]
        exit_hover_rect = main_menu_ui["exit_hover_rect"]
        hover_clickable = main_menu_ui["hover_clickable"]

    # ================== MODE ==================
    elif game_state == STORYBOARD:
        storyboard.draw(screen, title_font, menu_font, small_font)
        hover_clickable = storyboard.is_hovering_clickable(mouse_pos)
        if storyboard.is_finished():
            set_game_state(LEVEL_SELECT)

    # ================== LEVEL SELECT ==================
    elif game_state == LEVEL_SELECT:
        if not controls_snow_ready:
            storyboard._init_snow()
            controls_snow_ready = True
        level_select_ui = draw_level_select(screen, mouse_pos)
        lvl1_card = level_select_ui["lvl1_card"]
        lvl2_card = level_select_ui["lvl2_card"]
        back_btn = level_select_ui["back_btn"]
        hover_clickable = level_select_ui["hover_clickable"]

    # ================== PLAYER SETUP ==================
    elif game_state == MODE_SELECT:
        if not controls_snow_ready:
            storyboard._init_snow()
            controls_snow_ready = True
        # Keep the menu renderer stateless by passing the current setup data in one bundle.
        mode_select_ui = draw_mode_select(
            screen,
            mouse_pos,
            name_input_font,
            {
                "selected_mode": selected_mode,
                "selected_level": selected_level,
                "player1_name": player1_name,
                "player2_name": player2_name,
                "name_edit_field": name_edit_field,
                "handgun_select_target": handgun_select_target,
                "selected_handgun_p1": selected_handgun_p1,
                "selected_handgun_p2": selected_handgun_p2,
                "player1_gender": player1_gender,
                "player2_gender": player2_gender,
            },
        )
        p1_left_arrow = mode_select_ui["p1_left_arrow"]
        p1_right_arrow = mode_select_ui["p1_right_arrow"]
        p1_input_rect = mode_select_ui["p1_input_rect"]
        p1_handgun_btn = mode_select_ui["p1_handgun_btn"]
        add_p2_btn = mode_select_ui["add_p2_btn"]
        clear_slot_btn = mode_select_ui["clear_slot_btn"]
        p2_input_rect = mode_select_ui["p2_input_rect"]
        p2_handgun_btn = mode_select_ui["p2_handgun_btn"]
        p2_left_arrow = mode_select_ui["p2_left_arrow"]
        p2_right_arrow = mode_select_ui["p2_right_arrow"]
        handgun_option_btns = mode_select_ui["handgun_option_btns"]
        handgun_back_btn = mode_select_ui["handgun_back_btn"]
        back_btn = mode_select_ui["back_btn"]
        start_btn = mode_select_ui["start_btn"]
        hover_clickable = mode_select_ui["hover_clickable"]

    # ================== LEVEL PAGES ==================
    elif game_state == LEVEL_1_PAGE:
        Level_1.draw(screen, title_font, menu_font, small_font)
        hover_clickable = Level_1.is_hovering_clickable(mouse_pos)
        if Level_1.is_finished():
            if Level_1.consume_advance_to_next_level():
                selected_level = 2
                handgun_select_target = None
                name_edit_field = None
                set_game_state(MODE_SELECT)
            else:
                set_game_state(LEVEL_SELECT)

    elif game_state == LEVEL_2_PAGE:
        Level_2.draw(screen, title_font, menu_font, small_font)
        hover_clickable = Level_2.is_hovering_clickable(mouse_pos)
        if Level_2.is_finished():
            set_game_state(LEVEL_SELECT)

    # ================== HISTORY ==================
    elif game_state == HISTORY_PAGE:
        history_ui = draw_history_page(
            screen, mouse_pos, title_font, menu_font, small_font, load_history()
        )
        back_btn = history_ui["back_btn"]
        hover_clickable = history_ui["hover_clickable"]

    # ================== CONTROL PAGE ==================
    elif game_state == CONTROL_PAGE:
        if not controls_snow_ready:
            storyboard._init_snow()
            controls_snow_ready = True
        control_ui = draw_control_page(
            screen,
            mouse_pos,
            controls_p1,
            controls_p2,
            music_enabled,
            sound_enabled,
            show_popup,
            menu_font,
        )
        p1_jump = control_ui["p1_jump"]
        p1_left = control_ui["p1_left"]
        p1_right = control_ui["p1_right"]
        p1_down = control_ui["p1_down"]
        p1_shoot = control_ui["p1_shoot"]
        p2_jump = control_ui["p2_jump"]
        p2_left = control_ui["p2_left"]
        p2_right = control_ui["p2_right"]
        p2_down = control_ui["p2_down"]
        p2_shoot = control_ui["p2_shoot"]
        music_on_btn = control_ui["music_on_btn"]
        music_off_btn = control_ui["music_off_btn"]
        sound_on_btn = control_ui["sound_on_btn"]
        sound_off_btn = control_ui["sound_off_btn"]
        back_btn = control_ui["back_btn"]
        hover_clickable = control_ui["hover_clickable"]

    # ================== EVENTS ==================

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        # mouse
        if event.type == pygame.MOUSEBUTTONDOWN:
            if hover_clickable:
                audio_manager.play_click(sound_enabled)

            if game_state == MAIN_MENU:

                if start_btn.collidepoint(event.pos) or start_hover_rect.collidepoint(
                    event.pos
                ):
                    storyboard.reset()
                    set_game_state(STORYBOARD)

                elif control_btn.collidepoint(
                    event.pos
                ) or control_hover_rect.collidepoint(event.pos):
                    set_game_state(CONTROL_PAGE)

                elif exit_btn.collidepoint(event.pos) or exit_hover_rect.collidepoint(
                    event.pos
                ):
                    running = False

            elif game_state == STORYBOARD:
                storyboard.handle_click(event.pos)

            elif game_state == LEVEL_SELECT:
                if lvl1_card.collidepoint(event.pos):
                    selected_level = 1
                    set_game_state(MODE_SELECT)
                elif lvl2_card.collidepoint(event.pos):
                    selected_level = 2
                    set_game_state(MODE_SELECT)
                elif back_btn.collidepoint(event.pos):
                    set_game_state(MAIN_MENU)

            elif game_state == MODE_SELECT:
                name_edit_field = None
                handled_by_selector = False
                if handgun_select_target is not None:
                    for rect, gun_name in handgun_option_btns:
                        if rect.collidepoint(event.pos):
                            if handgun_select_target == "P1":
                                selected_handgun_p1 = gun_name
                            else:
                                selected_handgun_p2 = gun_name
                            handled_by_selector = True
                            break

                    if not handled_by_selector and handgun_back_btn.collidepoint(
                        event.pos
                    ):
                        handgun_select_target = None
                        handled_by_selector = True

                if not handled_by_selector and p1_left_arrow.collidepoint(event.pos):
                    player1_gender = "female" if player1_gender == "male" else "male"

                elif not handled_by_selector and p1_right_arrow.collidepoint(event.pos):
                    player1_gender = "female" if player1_gender == "male" else "male"

                elif (
                    not handled_by_selector
                    and selected_mode == 2
                    and p2_left_arrow.collidepoint(event.pos)
                ):
                    player2_gender = "female" if player2_gender == "male" else "male"

                elif (
                    not handled_by_selector
                    and selected_mode == 2
                    and p2_right_arrow.collidepoint(event.pos)
                ):
                    player2_gender = "female" if player2_gender == "male" else "male"

                elif not handled_by_selector and p1_input_rect.collidepoint(event.pos):
                    active_name_field = "P1"
                    name_edit_field = "P1"

                elif not handled_by_selector and p1_handgun_btn.collidepoint(event.pos):
                    active_name_field = "P1"
                    handgun_select_target = "P1"

                elif not handled_by_selector and add_p2_btn.collidepoint(event.pos):
                    selected_mode = 2
                    active_name_field = "P2"

                elif (
                    not handled_by_selector
                    and selected_mode == 2
                    and clear_slot_btn.collidepoint(event.pos)
                ):
                    selected_mode = 1
                    active_name_field = "P1"
                    player2_name = "Player 2"

                elif (
                    not handled_by_selector
                    and selected_mode == 2
                    and p2_input_rect.collidepoint(event.pos)
                ):
                    active_name_field = "P2"
                    name_edit_field = "P2"

                elif (
                    not handled_by_selector
                    and selected_mode == 2
                    and p2_handgun_btn.collidepoint(event.pos)
                ):
                    active_name_field = "P2"
                    handgun_select_target = "P2"

                elif not handled_by_selector and start_btn.collidepoint(event.pos):
                    if player1_name.strip() == "":
                        player1_name = "Player 1"
                    if selected_mode == 2 and player2_name.strip() == "":
                        player2_name = "Player 2"
                    if selected_level == 1:
                        Level_1.reset(
                            player1_name,
                            player2_name if selected_mode == 2 else "AI",
                            "2P" if selected_mode == 2 else "1P",
                            player1_gender,
                            player2_gender if selected_mode == 2 else "AI",
                            selected_handgun_p1,
                            selected_handgun_p2 if selected_mode == 2 else "N/A",
                            controls_p1,
                            controls_p2,
                        )
                        set_game_state(LEVEL_1_PAGE)
                    else:
                        Level_2.reset(
                            player1_name,
                            player2_name if selected_mode == 2 else "AI",
                            "2P" if selected_mode == 2 else "1P",
                            player1_gender,
                            player2_gender if selected_mode == 2 else "AI",
                            selected_handgun_p1,
                            selected_handgun_p2 if selected_mode == 2 else "N/A",
                            controls_p1,
                            controls_p2,
                        )
                        set_game_state(LEVEL_2_PAGE)

                elif not handled_by_selector and back_btn.collidepoint(event.pos):
                    set_game_state(LEVEL_SELECT)

            elif game_state == LEVEL_1_PAGE:
                Level_1.handle_click(event.pos)

            elif game_state == LEVEL_2_PAGE:
                Level_2.handle_click(event.pos)

            elif game_state == HISTORY_PAGE:

                if back_btn.collidepoint(event.pos):
                    set_game_state(MAIN_MENU)

            elif game_state == CONTROL_PAGE:

                # Player 1
                if p1_jump.collidepoint(event.pos):
                    waiting_for_key = ("P1", "JUMP")
                    show_popup = True

                elif p1_left.collidepoint(event.pos):
                    waiting_for_key = ("P1", "LEFT")
                    show_popup = True

                elif p1_right.collidepoint(event.pos):
                    waiting_for_key = ("P1", "RIGHT")
                    show_popup = True

                elif p1_down.collidepoint(event.pos):
                    waiting_for_key = ("P1", "DOWN")
                    show_popup = True

                elif p1_shoot.collidepoint(event.pos):
                    waiting_for_key = ("P1", "SHOOT")
                    show_popup = True

                # Player 2
                elif p2_jump.collidepoint(event.pos):
                    waiting_for_key = ("P2", "JUMP")
                    show_popup = True

                elif p2_left.collidepoint(event.pos):
                    waiting_for_key = ("P2", "LEFT")
                    show_popup = True

                elif p2_right.collidepoint(event.pos):
                    waiting_for_key = ("P2", "RIGHT")
                    show_popup = True

                elif p2_down.collidepoint(event.pos):
                    waiting_for_key = ("P2", "DOWN")
                    show_popup = True

                elif p2_shoot.collidepoint(event.pos):
                    waiting_for_key = ("P2", "SHOOT")
                    show_popup = True

                elif music_on_btn.collidepoint(event.pos):
                    music_enabled = True
                    audio_manager.sync_music_to_state(music_enabled, game_state)

                elif music_off_btn.collidepoint(event.pos):
                    music_enabled = False
                    audio_manager.sync_music_to_state(music_enabled, game_state)

                elif sound_on_btn.collidepoint(event.pos):
                    sound_enabled = True
                    audio_manager.apply_sound_enabled(Level_1, Level_2, sound_enabled)

                elif sound_off_btn.collidepoint(event.pos):
                    sound_enabled = False
                    audio_manager.apply_sound_enabled(Level_1, Level_2, sound_enabled)

                elif back_btn.collidepoint(event.pos):
                    set_game_state(MAIN_MENU)

        # keyboard
        if event.type == pygame.KEYDOWN:

            if game_state == STORYBOARD:
                storyboard.handle_key(event.key)

            elif game_state == LEVEL_1_PAGE:
                Level_1.handle_key(event.key)

            elif game_state == LEVEL_2_PAGE:
                Level_2.handle_key(event.key)

            elif game_state == MODE_SELECT:
                if (
                    event.key == pygame.K_TAB
                    and selected_mode == 2
                    and name_edit_field is not None
                ):
                    name_edit_field = "P2" if name_edit_field == "P1" else "P1"
                    active_name_field = name_edit_field
                elif event.key == pygame.K_BACKSPACE and name_edit_field is not None:
                    if name_edit_field == "P1":
                        player1_name = player1_name[:-1]
                    elif name_edit_field == "P2" and selected_mode == 2:
                        player2_name = player2_name[:-1]
                elif event.key == pygame.K_RETURN:
                    if player1_name.strip() == "":
                        player1_name = "Player 1"
                    if selected_mode == 2 and player2_name.strip() == "":
                        player2_name = "Player 2"

                    save_match_record(
                        player1_name,
                        player2_name if selected_mode == 2 else "AI",
                        "2P" if selected_mode == 2 else "1P",
                        player1_name,
                        5,
                        2,
                        "80%",
                        1,
                        150,
                    )
                    pygame.time.delay(300)
                    set_game_state(MAIN_MENU)
                else:
                    if event.unicode.isprintable() and name_edit_field is not None:
                        if name_edit_field == "P1" and can_append_name_char(
                            name_input_font, player1_name, event.unicode, 205 - 52
                        ):
                            player1_name += event.unicode
                        elif (
                            name_edit_field == "P2"
                            and selected_mode == 2
                            and can_append_name_char(
                                name_input_font, player2_name, event.unicode, 205 - 52
                            )
                        ):
                            player2_name += event.unicode

            elif game_state == CONTROL_PAGE and show_popup:

                player, action = waiting_for_key

                if player == "P1":
                    controls_p1[action] = event.key
                else:
                    controls_p2[action] = event.key

                show_popup = False
                waiting_for_key = None

    set_pointer_cursor(hover_clickable)
    pygame.display.update()
    clock.tick(60)


pygame.quit()
sys.exit()
