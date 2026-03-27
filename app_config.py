import os
import pygame


BASE_DIR = os.path.dirname(__file__)
ASSET_DIR = os.path.join(BASE_DIR, "Assets")
SFX_DIR = os.path.join(ASSET_DIR, "sound effect")


def _prefer_ogg(name):
    ogg_path = os.path.join(SFX_DIR, f"{name}.ogg")
    if os.path.exists(ogg_path):
        return ogg_path
    return os.path.join(SFX_DIR, f"{name}.mp3")


CLICK_SOUND_PATH = os.path.join(SFX_DIR, "click.mp3")
MENU_BGM_PATH = _prefer_ogg("menu_music")
STORYBOARD_BGM_PATH = _prefer_ogg("storyboard_music")
LEVEL_1_BGM_PATH = os.path.join(SFX_DIR, "Level1BGM.mp3")
LEVEL_2_BGM_PATH = os.path.join(SFX_DIR, "Level2BGM.mp3")
MAIN_MENU_BG_PATH = os.path.join(ASSET_DIR, "background", "homepage.jpeg")

WIDTH, HEIGHT = 900, 600
WINDOW_TITLE = "Gunfall Arena"

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
YELLOW = (255, 200, 0)

FONT_FILE = os.path.join(ASSET_DIR, "fonts", "Avenir Next Condensed Bold.ttf")
HEADLINE_FONT_FILE = os.path.join(
    ASSET_DIR, "fonts", "futura-now-headline-condensed-blk.otf"
)

NAME_BOX_TEXT_PADDING_X = 8
NAME_BOX_TEXT_PADDING_Y = 1

MAIN_MENU = "main_menu"
STORYBOARD = "storyboard"
LEVEL_SELECT = "level_select"
MODE_SELECT = "mode_select"
NAME_INPUT = "name_input"
HISTORY_PAGE = "history_page"
CONTROL_PAGE = "control_page"
LEVEL_1_PAGE = "level_1_page"
LEVEL_2_PAGE = "level_2_page"

HISTORY_FILE = "history.txt"

HANDGUN_OPTIONS = [
    {
        "label": "GLOCK17",
        "image": os.path.join(ASSET_DIR, "gunImg", "glock17.png"),
    },
    {
        "label": "SIG SAUER P226",
        "image": os.path.join(ASSET_DIR, "gunImg", "SIGSauerP226.png"),
    },
]

CHARACTER_IMAGE_MAP = {
    "male": os.path.join(ASSET_DIR, "player image", "Male player character.png"),
    "female": os.path.join(ASSET_DIR, "player image", "Female player character.png"),
}


def game_font(size):
    if os.path.exists(FONT_FILE):
        return pygame.font.Font(FONT_FILE, size)
    return pygame.font.SysFont("arial", size)


def headline_font(size):
    if os.path.exists(HEADLINE_FONT_FILE):
        return pygame.font.Font(HEADLINE_FONT_FILE, size)
    return pygame.font.SysFont("arialblack", size)


def create_screen():
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption(WINDOW_TITLE)
    return screen
