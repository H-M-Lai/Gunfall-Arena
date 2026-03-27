import os
import re
import random
import pygame
from drops import DropManager, load_drop_assets
import sfx_manager as sfx

WIDTH, HEIGHT = 900, 600
NAME_FONT = None
ASSET_DIR = os.path.join(os.path.dirname(__file__), "Assets")
HEADLINE_FONT_FILE = os.path.join(
    ASSET_DIR, "fonts", "futura-now-headline-condensed-blk.otf"
)

BG_IMAGE = None
PLATFORM_IMAGE = None
FLAG_IMAGE = None
FLAG_DRAW_IMAGE = None
FLAG_Y_OFFSET = -28

# Level 2 platform collision map (latest tuned coordinates).
PLATFORM_RECTS = [
    pygame.Rect(92, 299, 200, 10),   # X:92-292, Y:299
    pygame.Rect(342, 299, 225, 10),  # X:342-567, Y:299
    pygame.Rect(612, 309, 195, 10),  # X:612-807, Y:309
    pygame.Rect(312, 364, 275, 10),  # X:312-587, Y:364
    pygame.Rect(77, 414, 255, 10),   # X:77-332, Y:414
    pygame.Rect(542, 414, 285, 10),  # X:542-827, Y:414
    pygame.Rect(272, 469, 315, 10),  # X:272-587, Y:469
]

_finished = False
_state = {}
drop_manager = None
SOUND_ENABLED = True
_last_capture_tick = 0
ROUND_COUNTDOWN_MS = 3500
_round_start_tick = 0
_paused = False
_resume_rect = pygame.Rect(0, 0, 0, 0)
_exit_rect = pygame.Rect(0, 0, 0, 0)
# Adjust in-level snowfall density/brightness here.
SNOW_COUNT = 36
SNOW_ALPHA = 115
_snow = []
FLAG_TARGET_1P = 3
FLAG_TARGET_2P = 5
BULLET_SPEED = 12
BULLET_LENGTH = 26
BULLET_THICKNESS = 2
BULLET_GLOW_THICKNESS = 5
BULLET_COLOR = (255, 245, 150)
BULLET_GLOW_COLOR = (255, 255, 210)
BULLET_LIFETIME_MS = 1200
AI_MIN_RANGE = 130
AI_MAX_RANGE = 280
AI_SHOOT_RANGE = 460
AI_SHOOT_VERTICAL_TOL = 70
AI_DODGE_RADIUS = 150
AI_LOOT_SEEK_RANGE_X = 260
AI_LOOT_SEEK_RANGE_Y = 170
AI_LOOT_DROP_ALIGN_X = 95
AI_LOOT_DROP_MIN_DY = 28
AI_RECOVER_MIN_BELOW = 12
AI_RECOVER_MAX_BELOW = 150
AI_RECOVER_MAX_X = 260
AI_SHOOT_FORWARD_COMP = 1.10
AI_TURN_SHOOT_DELAY_MS = 90

# GM2-style physics constants
GROUND_FRICTION = 0.62
AIR_FRICTION    = 0.88
FREEPASS_MS     = 380
SPAWN_SHIELD_MS = 1600
SPAWN_EDGE_MARGIN = 28
SPAWN_MIN_GAP = 120
WIND_SPAWN_MS = 60


# Adjust hit particle count, spread, and fade here.
class HitEffect:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.alpha = 255
        self.particles = []
        count = random.randint(10, 16)
        for _ in range(count):
            vx = random.uniform(-2.4, 2.4)
            vy = random.uniform(-2.0, 1.2)
            r = random.randint(1, 3)
            life = random.randint(16, 26)
            self.particles.append([self.x, self.y, vx, vy, r, life])

    def update(self):
        self.alpha -= 12
        for p in self.particles:
            p[0] += p[2]
            p[1] += p[3]
            p[3] += 0.18
            p[5] -= 1

    def draw(self, screen):
        if self.alpha <= 0:
            return
        a = max(0, min(255, int(self.alpha)))
        for p in self.particles:
            if p[5] <= 0:
                continue
            fade = a * (p[5] / 26.0)
            color = (170, 25, 25, int(fade))
            pygame.draw.circle(screen, color, (int(p[0]), int(p[1])), p[4])

    def finished(self):
        return self.alpha <= 0 or all(p[5] <= 0 for p in self.particles)


_HIT_FONT_CACHE = {}


def _hit_font(size):
    font = _HIT_FONT_CACHE.get(size)
    if font is not None:
        return font
    if os.path.exists(HEADLINE_FONT_FILE):
        font = pygame.font.Font(HEADLINE_FONT_FILE, size)
    else:
        font = pygame.font.SysFont("arialblack", size)
    _HIT_FONT_CACHE[size] = font
    return font


class HitTextEffect:
    def __init__(self, x, y, direction=1, text="HIT", size=32):
        self.x = float(x)
        self.y = float(y)
        self.vx = random.uniform(-0.3, 0.3) + (0.3 * direction)
        self.vy = random.uniform(-0.9, -0.4)
        self.alpha = 255
        self.scale = 1.0
        self.text = text
        self.size = size

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.alpha -= 16
        self.scale += 0.01

    def draw(self, screen):
        if self.alpha <= 0:
            return
        font = _hit_font(self.size)
        base = font.render(self.text, True, (255, 214, 54))
        outline = font.render(self.text, True, (30, 18, 0))

        pad = 3
        w = base.get_width() + pad * 2
        h = base.get_height() + pad * 2
        surf = pygame.Surface((w, h), pygame.SRCALPHA)

        for ox, oy in (
            (-2, 0), (2, 0), (0, -2), (0, 2),
            (-2, -2), (-2, 2), (2, -2), (2, 2),
        ):
            surf.blit(outline, (pad + ox, pad + oy))
        surf.blit(base, (pad, pad))

        line_y = h // 2 + 3
        pygame.draw.line(surf, (255, 230, 120, 160), (2, line_y), (w - 2, line_y), 2)

        surf.set_alpha(max(0, min(255, int(self.alpha))))
        if self.scale != 1.0:
            nw = max(1, int(w * self.scale))
            nh = max(1, int(h * self.scale))
            surf = pygame.transform.smoothscale(surf, (nw, nh))

        screen.blit(surf, surf.get_rect(center=(int(self.x), int(self.y))))

    def finished(self):
        return self.alpha <= 0


# Adjust landing / movement dust here.
class DustEffect:
    def __init__(self, x, y, direction=0):
        self.x = float(x)
        self.y = float(y)
        self.alpha = 220
        self.particles = []
        count = random.randint(8, 12)
        for _ in range(count):
            vx = random.uniform(-1.6, 1.6) + (0.6 * direction)
            vy = random.uniform(-3.6, -1.9)
            r = random.randint(1, 3)
            life = random.randint(14, 22)
            self.particles.append([self.x, self.y, vx, vy, r, life])

    def update(self):
        self.alpha -= 14
        for p in self.particles:
            p[0] += p[2]
            p[1] += p[3]
            p[3] += 0.21
            p[5] -= 1

    def draw(self, screen):
        if self.alpha <= 0:
            return
        a = max(0, min(255, int(self.alpha)))
        for p in self.particles:
            if p[5] <= 0:
                continue
            fade = a * (p[5] / 22.0)
            color = (190, 170, 130, int(fade))
            pygame.draw.circle(screen, color, (int(p[0]), int(p[1])), p[4])

    def finished(self):
        return self.alpha <= 0 or all(p[5] <= 0 for p in self.particles)


# Adjust recoil / speed streak size and fade here.
class WindEffect:
    def __init__(self, x, y, direction=1, size=24):
        self.alpha = 200
        self.direction = 1 if direction >= 0 else -1
        size = max(18, int(size))
        self.streaks = []
        count = random.randint(4, 6)
        for _ in range(count):
            sx = float(x) + random.uniform(-4, 4)
            sy = float(y) + random.uniform(-size * 0.50, size * 0.50)
            vx = random.uniform(0.6, 1.4) * self.direction
            vy = random.uniform(-0.2, 0.2)
            length = random.randint(int(size * 0.20), int(size * 0.35))
            life = random.randint(10, 16)
            self.streaks.append([sx, sy, vx, vy, length, life])

    def update(self):
        self.alpha -= 18
        for s in self.streaks:
            s[0] += s[2]
            s[1] += s[3]
            s[5] -= 1

    def draw(self, screen):
        if self.alpha <= 0:
            return
        a = max(0, min(255, int(self.alpha)))
        for s in self.streaks:
            if s[5] <= 0:
                continue
            fade = a * (s[5] / 16.0)
            color = (220, 240, 255, int(fade))
            x1 = int(s[0])
            y1 = int(s[1])
            x2 = int(s[0] - s[4] * self.direction)
            y2 = int(s[1])
            pygame.draw.line(screen, color, (x1, y1), (x2, y2), 2)

    def finished(self):
        return self.alpha <= 0 or all(s[5] <= 0 for s in self.streaks)

FIRE_RATE_TO_COOLDOWN_MS = {
    "high": 130,
    "med-high": 170,
    "medium": 220,
    "low": 320,
}
RELOAD_TIME_TO_MS = {
    "short": 700,
    "medium": 1000,
    "slow": 1400,
}
RECOIL_TO_SPREAD_PX = {
    "low": 1,
    "med-low": 2,
    "medium": 3,
    "high": 5,
    "very high": 7,
}
WEAPON_PROFILES = {
    "glock17":      {"blowback": 12, "pushback": 2.0, "recoil": "low",      "weight": 0.05, "fire_rate": "high",     "reload": "short",  "mag": 14, "pellets": 1},
    "SIGSauerP226": {"blowback": 14, "pushback": 2.5, "recoil": "med-low",  "weight": 0.06, "fire_rate": "medium",   "reload": "medium", "mag": 12, "pellets": 1},
    "deserteagle":  {"blowback": 22, "pushback": 4.5, "recoil": "high",     "weight": 0.10, "fire_rate": "low",      "reload": "slow",   "mag": 7,  "pellets": 1},
    "MP5":          {"blowback": 16, "pushback": 2.5, "recoil": "med-low",  "weight": 0.12, "fire_rate": "high",     "reload": "medium", "mag": 24, "pellets": 1},
    "ump45":        {"blowback": 18, "pushback": 3.0, "recoil": "medium",   "weight": 0.15, "fire_rate": "medium",   "reload": "medium", "mag": 20, "pellets": 1},
    "M870":         {"blowback": 36, "pushback": 6.0, "recoil": "very high","weight": 0.28, "fire_rate": "low",      "reload": "slow",   "mag": 5,  "pellets": 5},
    "M4A1":         {"blowback": 20, "pushback": 3.0, "recoil": "medium",   "weight": 0.18, "fire_rate": "med-high", "reload": "medium", "mag": 24, "pellets": 1},
    "scar-h":       {"blowback": 30, "pushback": 5.0, "recoil": "high",     "weight": 0.25, "fire_rate": "low",      "reload": "slow",   "mag": 16, "pellets": 1},
}
HANDGUN_WEAPONS = {"glock17", "SIGSauerP226"}


def _weapon_profile(weapon_name):
    return WEAPON_PROFILES.get(weapon_name, WEAPON_PROFILES["glock17"])


def set_sound_enabled(enabled):
    global SOUND_ENABLED
    SOUND_ENABLED = bool(enabled)
    sfx.set_enabled(enabled)


def _load_sfx():
    sfx.ensure_ready()


def _play_reload_sfx():
    if not SOUND_ENABLED:
        return
    sfx.play("reload")


def _play_jump_sfx():
    if not SOUND_ENABLED:
        return
    sfx.play("jump")


def _play_hit_sfx():
    if not SOUND_ENABLED:
        return
    sfx.play("hit")


def _play_capture_sfx():
    if not SOUND_ENABLED:
        return
    sfx.play("capture")


def _play_shot_sfx(weapon_name):
    if not SOUND_ENABLED:
        return
    if weapon_name in HANDGUN_WEAPONS:
        sfx.play("shot_handgun")
    else:
        sfx.play("shot_rifle")


def _play_walk_sfx():
    if not SOUND_ENABLED:
        _stop_walk_sfx()
        return
    sfx.start_loop("walk")


def _stop_walk_sfx():
    sfx.stop_loop("walk")


def _play_landing_sfx():
    if not SOUND_ENABLED:
        return
    sfx.play("landing")


def _play_respawn_sfx():
    if not SOUND_ENABLED:
        return
    sfx.play("respawn")


def _weight_speed_mult(weight):
    return max(0.65, 1.0 - (weight * 0.9))


def _random_spawn_point(avoid_x=None, min_gap=SPAWN_MIN_GAP):
    avoid_x = avoid_x or []
    for _ in range(36):
        plat = random.choice(PLATFORM_RECTS)
        left = plat.left + SPAWN_EDGE_MARGIN
        right = plat.right - SPAWN_EDGE_MARGIN
        if right <= left:
            x = plat.centerx
        else:
            x = random.randint(left, right)
        if all(abs(x - ax) >= min_gap for ax in avoid_x):
            return x, plat.top
    plat = random.choice(PLATFORM_RECTS)
    return plat.centerx, plat.top


def _load_level_assets():
    global BG_IMAGE, PLATFORM_IMAGE, FLAG_IMAGE, FLAG_DRAW_IMAGE
    if BG_IMAGE is None:
        BG_IMAGE = pygame.image.load(
            os.path.join(ASSET_DIR, "background", "level2.jpeg")
        ).convert()
    if PLATFORM_IMAGE is None:
        PLATFORM_IMAGE = pygame.transform.smoothscale(
            pygame.image.load(
                os.path.join(ASSET_DIR, "background", "platform2.png")
            ).convert_alpha(),
            (780, 420),
        )
    if FLAG_IMAGE is None:
        FLAG_IMAGE = pygame.transform.smoothscale(
            pygame.image.load(
                os.path.join(ASSET_DIR, "ability", "flag.png")
            ).convert_alpha(),
            (62, 62),
        )
        vis = FLAG_IMAGE.get_bounding_rect()
        if vis.width > 0 and vis.height > 0:
            FLAG_DRAW_IMAGE = pygame.Surface((vis.width, vis.height), pygame.SRCALPHA)
            FLAG_DRAW_IMAGE.blit(FLAG_IMAGE, (-vis.x, -vis.y))
        else:
            FLAG_DRAW_IMAGE = FLAG_IMAGE


def _init_snow():
    global _snow
    _snow = []
    for _ in range(SNOW_COUNT):
        _snow.append(
            [
                random.randint(0, WIDTH),
                random.randint(0, HEIGHT),
                random.uniform(0.35, 0.85),
                random.randint(1, 3),
            ]
        )


def _update_and_draw_snow(screen):
    if not _snow:
        _init_snow()

    layer = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    for flake in _snow:
        flake[1] += flake[2]
        if flake[1] > HEIGHT + 6:
            flake[0] = random.randint(0, WIDTH)
            flake[1] = random.randint(-40, -8)
            flake[2] = random.uniform(0.35, 0.85)
            flake[3] = random.randint(1, 3)
        pygame.draw.circle(
            layer,
            (255, 255, 255, SNOW_ALPHA),
            (int(flake[0]), int(flake[1])),
            flake[3],
        )
    screen.blit(layer, (0, 0))


def _normalize_gun(gun_name):
    name = (gun_name or "").lower().strip()
    if "sig" in name:
        return "SIGSauerP226"
    if "scar" in name:
        return "scar-h"
    if "ump" in name:
        return "ump45"
    if "m4" in name:
        return "M4A1"
    if "m870" in name:
        return "M870"
    if "mp5" in name:
        return "MP5"
    return "glock17"


def _folder_for(gender, gun_name):
    gun_key = _normalize_gun(gun_name)
    if str(gender).lower() == "snowman":
        root = os.path.join(os.path.dirname(__file__), "Assets", "character", "snowman")
        return os.path.join(root, f"snowman ({gun_key})")
    gender_key = "female" if str(gender).lower() == "female" else "male"
    root = os.path.join(os.path.dirname(__file__), "Assets", "character")
    return os.path.join(root, gender_key, f"{gender_key} character ({gun_key})")


def _stand_path_for(gender, gun_name):
    gun_key = _normalize_gun(gun_name)
    gender_key = "female" if str(gender).lower() == "female" else "male"
    root = os.path.join(os.path.dirname(__file__), "Assets", "character")
    return os.path.join(
        root, gender_key, f"{gender_key} character ({gun_key})", "stand.png"
    )


def _frame_sort_key(path):
    name = os.path.basename(path)
    nums = re.findall(r"\d+", name)
    return int(nums[0]) if nums else 0


def _load_frames(gender, gun_name):
    folder = _folder_for(gender, gun_name)
    if not os.path.isdir(folder):
        return []

    files = [
        os.path.join(folder, f)
        for f in os.listdir(folder)
        if f.lower().endswith(".png")
    ]
    files.sort(key=_frame_sort_key)

    frames = []
    for path in files:
        try:
            img = pygame.image.load(path).convert_alpha()
            frames.append(img)
        except pygame.error:
            continue
    return frames


def _load_stand_frame(gender, gun_name):
    path = _stand_path_for(gender, gun_name)
    if not os.path.exists(path):
        return None
    try:
        img = pygame.image.load(path).convert_alpha()
    except pygame.error:
        return None
    bounds = img.get_bounding_rect()
    if bounds.width <= 0 or bounds.height <= 0:
        return img
    frame = pygame.Surface((bounds.width, bounds.height), pygame.SRCALPHA)
    frame.blit(img, (-bounds.x, -bounds.y))
    return frame


class _Player:
    def __init__(self, pid, x, label, controls, frames, gender="female", team="ally", is_ai=False):
        self.pid = pid
        self.label = label
        self.controls = controls
        self.gender = gender
        self.muzzle_height_ratio = 0.44 if str(gender).lower() == "snowman" else 0.38
        self.team = team
        self.is_ai = is_ai
        self.walk_right = []
        self.walk_left = []
        self.stand_right = None
        self.stand_left = None
        self.size_scale = 1.0
        self.base_walk_right = []
        self._set_weapon_frames(frames[:] if frames else [self._fallback((230, 140, 120))])
        self.image = self.stand_right
        self.spawn_x = x
        self.spawn_y = PLATFORM_RECTS[1].top
        self.rect = self.image.get_rect(midbottom=(self.spawn_x, self.spawn_y))
        self.facing_right = True
        self.frame_idx = 0.0
        self.vx = 0
        self.vy = 0
        self.on_ground = True
        self.prev_on_ground = True
        self.speed = 3
        self.jump_power = 13
        self.gravity = 0.8
        self.max_jumps = 2
        self.base_speed_nominal = 3
        self.base_speed = 3
        self.base_jump = 13
        self.base_jumps = 2
        self.jumps_remaining = 2
        self.prev_jump_down = False
        self.prev_down_down = False
        self.current_platform_idx = None
        self.drop_ignore_platform_idx = None
        self.drop_ignore_until = 0
        self.drop_request_until = 0
        self.drop_hold_lock = False
        self.lives = 5
        self.weapon = "glock17"
        self.handgun_weapon = "glock17"
        self.ability = "None"
        self.ability_end = 0
        self.last_shot_time = 0
        self.prev_shoot_down = False
        self.shot_cooldown_ms = FIRE_RATE_TO_COOLDOWN_MS["medium"]
        self.reload_time_ms = RELOAD_TIME_TO_MS["medium"]
        self.recoil_spread_px = RECOIL_TO_SPREAD_PX["low"]
        self.magazine_size = 12
        self.current_ammo = 12
        self.pellet_count = 1
        self.reloading_until = 0
        self.auto_reload = True
        self.freepass_until = 0   # invincibility timer after being hit (GM2's freepass)
        self.spawn_shield_until = 0
        self.next_wind_time = 0
        self.pending_ability_text = None

        # --- GM2-style AI state ---
        self.ai_next_jump_time = 0
        self.ai_range_until = 0
        self.ai_min_range = AI_MIN_RANGE
        self.ai_max_range = AI_MAX_RANGE
        # target commitment (targettime)
        self.ai_target = None
        self.ai_target_until = 0
        # optimalx - preferred fighting X position
        self.ai_optimal_x = x
        self.ai_optimal_until = 0
        # stuck detection (idletime2 + prevx)
        self.ai_prev_x = x
        self.ai_idle_ticks = 0
        # resting state
        self.ai_resting = False
        self.ai_rest_until = 0
        # simulated keypresses (GM2 style)
        self.ai_key_left = False
        self.ai_key_right = False
        self.ai_key_jump = False
        self.ai_key_down = False
        self.ai_turn_shoot_until = 0

        self.apply_weapon_profile(self.weapon)
        self.kills = 0
        self.falls = 0
        self.pickups = 0
        self.flags_captured = 0
        self.shots_hit = 0
        self.shots_fired = 0
        self.last_hit_by = None

    def activate_spawn_shield(self, now=None):
        if now is None:
            now = pygame.time.get_ticks()
        self.spawn_shield_until = now + SPAWN_SHIELD_MS
        self.freepass_until = max(self.freepass_until, self.spawn_shield_until)

    def has_spawn_shield(self, now=None):
        if now is None:
            now = pygame.time.get_ticks()
        return now < self.spawn_shield_until

    def _fallback(self, color):
        s = pygame.Surface((42, 62), pygame.SRCALPHA)
        s.fill(color)
        pygame.draw.rect(s, (20, 20, 20), s.get_rect(), 2)
        return s

    def _set_weapon_frames(self, frames):
        self.base_walk_right = [f.copy() for f in frames]
        self._rebuild_scaled_frames()

    def _rebuild_scaled_frames(self):
        if not self.base_walk_right:
            self.base_walk_right = [self._fallback((230, 140, 120))]

        if self.size_scale == 1.0:
            self.walk_right = [f.copy() for f in self.base_walk_right]
        else:
            self.walk_right = []
            for f in self.base_walk_right:
                w = max(1, int(f.get_width() * self.size_scale))
                h = max(1, int(f.get_height() * self.size_scale))
                self.walk_right.append(pygame.transform.scale(f, (w, h)))

        self.walk_left = [pygame.transform.flip(f, True, False) for f in self.walk_right]
        self.stand_right = self.walk_right[0]
        self.stand_left = pygame.transform.flip(self.stand_right, True, False)

    def apply_size_scale(self, scale):
        self.size_scale = max(0.3, min(2.0, float(scale)))
        bottom = self.rect.bottom if hasattr(self, "rect") else None
        centerx = self.rect.centerx if hasattr(self, "rect") else None
        self._rebuild_scaled_frames()
        self.image = self.stand_right if self.facing_right else self.stand_left
        if bottom is not None and centerx is not None:
            self.rect = self.image.get_rect(midbottom=(centerx, bottom))

    def apply_weapon_profile(self, weapon_name):
        self.weapon = weapon_name
        profile = _weapon_profile(weapon_name)
        self.auto_reload = weapon_name in HANDGUN_WEAPONS
        self.shot_cooldown_ms = FIRE_RATE_TO_COOLDOWN_MS[profile["fire_rate"]]
        self.reload_time_ms = RELOAD_TIME_TO_MS[profile["reload"]]
        self.recoil_spread_px = RECOIL_TO_SPREAD_PX[profile["recoil"]]
        self.pellet_count = profile.get("pellets", 1)
        self.magazine_size = profile.get("mag", 12)
        self.current_ammo = self.magazine_size
        self.reloading_until = 0
        self.blowback_force = profile.get("blowback", 6)    # overwrites target vx on hit
        self.pushback_force = profile.get("pushback", 2.0)  # backward recoil on shooter
        self.base_speed = max(2, int(round(self.base_speed_nominal * _weight_speed_mult(profile["weight"]))))
        if self.ability == "speedUp":
            self.speed = self.base_speed * 1.6
        elif self.ability == "slowDown":
            self.speed = self.base_speed * 0.5
        else:
            self.speed = self.base_speed

    def update(self, keys, players=None, bullets=None):
        now = pygame.time.get_ticks()
        if self.pending_ability_text:
            _state["effects"].append(
                HitTextEffect(self.rect.centerx, self.rect.top - 10, 1, self.pending_ability_text, 24)
            )
            self.pending_ability_text = None
        if self.auto_reload and self.reloading_until and now >= self.reloading_until:
            self.reloading_until = 0
            self.current_ammo = self.magazine_size
        moving = False

        # Apply friction each frame - decays knockback naturally (GM2's friction/airfriction)
        if self.on_ground:
            self.vx *= GROUND_FRICTION
        else:
            self.vx *= AIR_FRICTION
        if abs(self.vx) < 0.3:
            self.vx = 0.0

        # ability timer reset
        if self.ability != "None" and now > self.ability_end:
            self.ability = "None"
            self.speed = self.base_speed
            self.jump_power = self.base_jump
            self.max_jumps = self.base_jumps
            self.apply_size_scale(1.0)

        if self.is_ai:
            self._run_ai_brain(now, players or [], bullets or [])
            # Apply simulated keypresses with acceleration so knockback is not canceled instantly.
            left_pressed = bool(self.ai_key_left)
            right_pressed = bool(self.ai_key_right)
            desired_vx = 0.0
            if left_pressed and not right_pressed:
                desired_vx = -self.speed
                self.facing_right = False
                moving = True
            elif right_pressed and not left_pressed:
                desired_vx = self.speed
                self.facing_right = True
                moving = True
            if desired_vx != 0.0:
                move_accel = self.speed * (0.55 if self.on_ground else 0.30)
                if self.vx < desired_vx:
                    self.vx = min(desired_vx, self.vx + move_accel)
                elif self.vx > desired_vx:
                    self.vx = max(desired_vx, self.vx - move_accel)
            if self.ai_key_jump and not self.prev_jump_down and self.jumps_remaining > 0:
                self.vy = -self.jump_power
                self.on_ground = False
                self.jumps_remaining -= 1
                self.ai_next_jump_time = now + 350
                _play_jump_sfx()
                _state["effects"].append(
                    # Use DustEffect here when the player jumps.
                    DustEffect(self.rect.centerx, self.rect.bottom - 4, -1 if not self.facing_right else 1)
                )
            if self.ai_key_down and self.on_ground:
                # AI drop-through: ignore current platform briefly to descend a level.
                self.drop_ignore_platform_idx = self.current_platform_idx
                self.drop_ignore_until = now + 250
                self.on_ground = False
                self.rect.y += 6
                self.vy = max(self.vy, 2)
            self.prev_jump_down = self.ai_key_jump
            self.prev_down_down = False
        else:
            left_pressed = keys[self.controls["LEFT"]]
            right_pressed = keys[self.controls["RIGHT"]]
            desired_vx = 0.0
            if left_pressed and not right_pressed:
                desired_vx = -self.speed
                self.facing_right = False
                moving = True
            elif right_pressed and not left_pressed:
                desired_vx = self.speed
                self.facing_right = True
                moving = True
            if desired_vx != 0.0:
                move_accel = self.speed * (0.55 if self.on_ground else 0.30)
                if self.vx < desired_vx:
                    self.vx = min(desired_vx, self.vx + move_accel)
                elif self.vx > desired_vx:
                    self.vx = max(desired_vx, self.vx - move_accel)
            jump_down = keys[self.controls["JUMP"]]
            if jump_down and not self.prev_jump_down and self.jumps_remaining > 0:
                self.vy = -self.jump_power
                self.on_ground = False
                self.jumps_remaining -= 1
                _play_jump_sfx()
                _state["effects"].append(
                    # Use DustEffect here when the player jumps.
                    DustEffect(self.rect.centerx, self.rect.bottom - 4, -1 if not self.facing_right else 1)
                )
            self.prev_jump_down = jump_down

            down_down = keys[self.controls["DOWN"]]
            if not down_down:
                self.drop_hold_lock = False
            if down_down and not self.drop_hold_lock:
                # Buffer drop input so hold-to-drop still works while being juggled by hits.
                self.drop_request_until = now + 220
            if self.on_ground and now <= self.drop_request_until and not self.drop_hold_lock:
                # Ignore only the platform currently stood on.
                self.drop_ignore_platform_idx = self.current_platform_idx
                self.drop_ignore_until = now + 250
                self.drop_request_until = 0
                self.drop_hold_lock = True
                self.on_ground = False
                self.rect.y += 6
                self.vy = max(self.vy, 2)
            self.prev_down_down = down_down

        self.rect.x += self.vx

        self.vy += self.gravity
        self.rect.y += int(self.vy)
        self.on_ground = False

        landed_idx = None
        for idx, platform in enumerate(PLATFORM_RECTS):
            if (
                self.drop_ignore_platform_idx == idx
                and now < self.drop_ignore_until
            ):
                continue

            if (
                self.vy >= 0
                and self.rect.bottom >= platform.top
                and self.rect.bottom - self.vy <= platform.top
                and self.rect.centerx > platform.left
                and self.rect.centerx < platform.right
            ):
                self.rect.bottom = platform.top
                self.vy = 0
                self.on_ground = True
                self.jumps_remaining = self.max_jumps
                landed_idx = idx
                if not self.prev_on_ground:
                    _state["effects"].append(
                        # Use DustEffect here when the player lands.
                        DustEffect(self.rect.centerx, self.rect.bottom - 3)
                    )
                    _play_landing_sfx()
                break

        self.current_platform_idx = landed_idx
        if now >= self.drop_ignore_until:
            self.drop_ignore_platform_idx = None
        self.prev_on_ground = self.on_ground

        if self.rect.top > HEIGHT:
            if self.last_hit_by is not None:
                self.last_hit_by.kills += 1

            self.falls += 1
            self.last_hit_by = None
            self.lives -= 1
            others_x = [p.rect.centerx for p in _state.get("players", []) if p is not self]
            self.spawn_x, self.spawn_y = _random_spawn_point(others_x)
            self.rect.midbottom = (self.spawn_x, self.spawn_y)
            self.vx = 0
            self.vy = 0
            self.on_ground = False
            self.jumps_remaining = self.base_jumps
            self.current_platform_idx = None
            self.drop_ignore_platform_idx = None
            self.drop_ignore_until = 0
            self.drop_request_until = 0
            self.drop_hold_lock = False
            self.reloading_until = 0
            self.ability = "None"
            self.ability_end = 0
            self.speed = self.base_speed
            self.jump_power = self.base_jump
            self.max_jumps = self.base_jumps
            self.apply_size_scale(1.0)

            frames = _load_frames(self.gender, self.handgun_weapon)
            if frames:
                self._set_weapon_frames(frames)
                self.frame_idx = 0
                self.image = self.stand_right if self.facing_right else self.stand_left
            self.apply_weapon_profile(self.handgun_weapon)
            self.activate_spawn_shield(now)
            _play_respawn_sfx()

        bottom = self.rect.bottom
        centerx = self.rect.centerx
        frames = self.walk_right if self.facing_right else self.walk_left
        if not self.on_ground:
            self.image = frames[min(1, len(frames) - 1)]
        elif moving:
            self.frame_idx = (self.frame_idx + 0.22) % len(frames)
            self.image = frames[int(self.frame_idx)]
        else:
            self.frame_idx = 0
            self.image = self.stand_right if self.facing_right else self.stand_left

        # Keep collision anchor stable for all animation frames.
        self.rect = self.image.get_rect(midbottom=(centerx, bottom))

        if self.ability == "speedUp" and now >= self.next_wind_time and abs(self.vx) > 0.6:
            vis = self.image.get_bounding_rect()
            body_left = self.rect.x + vis.x
            body_right = self.rect.x + vis.x + vis.width
            back_x = body_left - 4 if self.facing_right else body_right + 4
            back_y = self.rect.y + vis.y + int(vis.height * 0.50)
            direction = -1 if self.facing_right else 1
            size = max(18, int(vis.height))
            # Use WindEffect here to visualize the speed boost.
            _state["effects"].append(WindEffect(back_x, back_y, direction, size))
            self.next_wind_time = now + WIND_SPAWN_MS

    def draw(self, screen):
        global NAME_FONT
        if NAME_FONT is None:
            NAME_FONT = pygame.font.SysFont("arial", 18, bold=True)

        now = pygame.time.get_ticks()
        if self.has_spawn_shield(now):
            # Short spawn-protection bubble.
            radius = max(1, min(self.rect.width, self.rect.height) // 2 - 16)
            cx, cy = self.rect.centerx, self.rect.centery
            bubble = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(bubble, (140, 215, 255, 40), (radius + 2, radius + 2), radius)
            pygame.draw.circle(bubble, (210, 245, 255, 170), (radius + 2, radius + 2), radius, 1)
            screen.blit(bubble, (cx - radius - 2, cy - radius - 2))

        screen.blit(self.image, self.rect)
        visible = self.image.get_bounding_rect()
        visual_top = (
            self.rect.y + visible.top
            if visible.width and visible.height
            else self.rect.top
        )
        name = NAME_FONT.render(self.label, True, (245, 245, 245))
        r = name.get_rect(center=(self.rect.centerx, visual_top - 14))
        shadow = NAME_FONT.render(self.label, True, (0, 0, 0))
        sr = shadow.get_rect(center=(r.centerx + 2, r.centery + 2))
        screen.blit(shadow, sr)
        screen.blit(name, r)
        # Adjust reload ring size, color, and thickness here.
        if self.reloading_until > now and self.reload_time_ms > 0:
            progress = 1.0 - ((self.reloading_until - now) / self.reload_time_ms)
            progress = max(0.0, min(1.0, progress))
            ring_center = (r.right + 14, r.centery)
            ring_radius = 7
            pygame.draw.circle(screen, (70, 70, 85), ring_center, ring_radius, 2)
            arc_rect = pygame.Rect(0, 0, ring_radius * 2, ring_radius * 2)
            arc_rect.center = ring_center
            pygame.draw.arc(
                screen,
                (255, 210, 90),
                arc_rect,
                -1.5708,
                -1.5708 + (6.2832 * progress),
                3,
            )

    def _choose_ai_target(self, players):
        enemies = [p for p in players if p is not self and p.team != self.team]
        if not enemies:
            return None
        return min(enemies, key=lambda p: abs(p.rect.centerx - self.rect.centerx))

    def _choose_ai_loot_target(self):
        global drop_manager
        if drop_manager is None:
            return None
        drops = getattr(drop_manager, "drops", None) or []
        best_drop = None
        best_score = -10**9
        for drop in drops:
            dx = abs(drop.rect.centerx - self.rect.centerx)
            dy = abs(drop.rect.centery - self.rect.centery)
            if dx > AI_LOOT_SEEK_RANGE_X or dy > AI_LOOT_SEEK_RANGE_Y:
                continue

            score = -(dx * 0.7 + dy * 1.1)
            if drop.type == "weaponbox":
                score += 120 if self.weapon in HANDGUN_WEAPONS else 45
            else:
                if drop.name == "life" and self.lives < 3:
                    score += 130
                elif self.ability == "None":
                    score += 80
                else:
                    score += 30

            if score > best_score:
                best_score = score
                best_drop = drop
        return best_drop

    def _choose_recovery_platform(self):
        best = None
        best_score = 10**9
        for p in PLATFORM_RECTS:
            if p.top >= self.rect.bottom:
                continue
            below_by = self.rect.bottom - p.top
            if below_by < AI_RECOVER_MIN_BELOW or below_by > AI_RECOVER_MAX_BELOW:
                continue
            dx = abs(self.rect.centerx - p.centerx)
            if dx > AI_RECOVER_MAX_X:
                continue
            score = below_by * 1.3 + dx * 0.7
            if score < best_score:
                best_score = score
                best = p
        return best

    def _run_ai_brain(self, now, players, bullets):
        """GM2-style AI: sets simulated key flags each frame."""
        self.ai_key_left = False
        self.ai_key_right = False
        self.ai_key_jump = False
        self.ai_key_down = False

        if self.ai_target is None or self.ai_target.lives <= 0 or now > self.ai_target_until:
            self.ai_target = self._choose_ai_target(players)
            self.ai_target_until = now + random.randint(800, 1800)
        target = self.ai_target
        if target is None:
            return

        # Domination objective bias: contest active captures and trigger inactive flags.
        objective_x = None
        objective_y = None
        force_objective = False
        dom = _state.get("domination", {})
        self_in_zone = False
        urgent_contest = False
        if dom and not dom.get("match_over", False):
            flag_rect, zone_center, zone_radius = _flag_spawn_and_zone()
            def in_zone(p):
                return (
                    (_visible_player_rect(p).centerx - zone_center[0]) ** 2
                    + (_visible_player_rect(p).centery - zone_center[1]) ** 2
                    <= zone_radius ** 2
                )
            self_in_zone = (
                (_visible_player_rect(self).centerx - zone_center[0]) ** 2
                + (_visible_player_rect(self).centery - zone_center[1]) ** 2
                <= zone_radius ** 2
            )
            any_in_zone = any(
                in_zone(p)
                for p in players
            )
            enemy_zone_targets = [p for p in players if p.team != self.team and in_zone(p)]
            enemy_in_zone = len(enemy_zone_targets) > 0
            ally_prog = dom.get("progress", {}).get("ally", 0.0)
            enemy_prog = dom.get("progress", {}).get("enemy", 0.0)

            if not dom.get("capture_active", False):
                objective_x = flag_rect.centerx
                objective_y = flag_rect.centery
                force_objective = True
            elif enemy_in_zone:
                # Contest by pressuring the actual enemy inside zone, not just center point.
                focus = min(
                    enemy_zone_targets,
                    key=lambda p: abs(p.rect.centerx - self.rect.centerx) + abs(p.rect.centery - self.rect.centery),
                )
                objective_x = focus.rect.centerx
                objective_y = focus.rect.centery
                force_objective = True
                urgent_contest = not self_in_zone
            elif (not any_in_zone) or enemy_in_zone or ally_prog > enemy_prog or self_in_zone:
                objective_x = zone_center[0]
                objective_y = zone_center[1]
                force_objective = True
                urgent_contest = False

        recover_platform = self._choose_recovery_platform()
        if (
            not self.on_ground
            and self.vy > 0.5
            and self.jumps_remaining > 0
            and recover_platform is not None
            and not self._has_near_ground_below(120)
        ):
            rec_dx = recover_platform.centerx - self.rect.centerx
            if rec_dx > 10:
                self.ai_key_right = True
            elif rec_dx < -10:
                self.ai_key_left = True
            self.facing_right = rec_dx >= 0
            if now >= self.ai_next_jump_time:
                self.ai_key_jump = True
                self.ai_next_jump_time = now + 380
            return

        if force_objective:
            dx = objective_x - self.rect.centerx
            dy = objective_y - self.rect.centery
            self.ai_optimal_x = objective_x
            self.ai_optimal_until = now + 240
            self.ai_resting = False
        else:
            loot_target = self._choose_ai_loot_target()
            if loot_target is not None:
                dx = loot_target.rect.centerx - self.rect.centerx
                dy = loot_target.rect.centery - self.rect.centery
                self.ai_optimal_x = loot_target.rect.centerx
                self.ai_optimal_until = now + 160
                if (
                    loot_target.type == "weaponbox"
                    and dy >= AI_LOOT_DROP_MIN_DY
                    and abs(dx) <= AI_LOOT_DROP_ALIGN_X
                    and self.on_ground
                ):
                    self.ai_key_down = True
                else:
                    self.ai_optimal_x = loot_target.rect.centerx
            else:
                dx = target.rect.centerx - self.rect.centerx
                dy = target.rect.centery - self.rect.centery
                self._refresh_ai_ranges(now)
                # Vertical pursuit: when target is below, align before dropping down.
                if dy > 55:
                    drop_x = self._best_drop_x_for_chase(target.rect.centerx)
                    if drop_x is not None:
                        self.ai_optimal_x = drop_x
                    else:
                        self.ai_optimal_x = target.rect.centerx
                    self.ai_optimal_until = now + 220

        if self.ai_resting and not force_objective:
            if now < self.ai_rest_until:
                return
            self.ai_resting = False

        if now > self.ai_optimal_until and not force_objective:
            preferred_range = random.randint(self.ai_min_range, self.ai_max_range)
            offset = preferred_range if dx < 0 else -preferred_range
            raw_optimal = target.rect.centerx + offset
            self.ai_optimal_x = max(40, min(WIDTH - 40, raw_optimal))
            self.ai_optimal_until = now + random.randint(600, 1400)

        half_w = self.rect.width // 2 + 20
        ground_left = self._probe_ground(self.rect.centerx - half_w)
        ground_right = self._probe_ground(self.rect.centerx + half_w)

        if abs(self.rect.centerx - self.ai_prev_x) < 2:
            self.ai_idle_ticks += 1
        else:
            self.ai_idle_ticks = 0
        self.ai_prev_x = self.rect.centerx

        if self.ai_idle_ticks > 25 and self.on_ground and not force_objective:
            self.ai_optimal_until = 0
            self.ai_idle_ticks = 0
            if ground_left and ground_right and now >= self.ai_next_jump_time:
                self.ai_key_jump = True
                self.ai_next_jump_time = now + 600
            return

        capture_hold = force_objective and dom.get("capture_active", False)
        hold_deadzone = 24 if capture_hold else 12
        gap = self.rect.centerx - self.ai_optimal_x
        if abs(gap) > hold_deadzone:
            want_right = gap < 0
            if want_right:
                if ground_right or force_objective:
                    self.ai_key_right = True
            else:
                if ground_left or force_objective:
                    self.ai_key_left = True

        # In objective mode, if forward ground probe fails near an edge, try a gap-crossing jump.
        if force_objective and self.on_ground and now >= self.ai_next_jump_time and self.jumps_remaining > 0:
            toward_right = gap < 0
            blocked_ahead = (toward_right and not ground_right) or ((not toward_right) and not ground_left)
            if blocked_ahead and abs(dy) <= 55:
                self.ai_key_jump = True
                self.ai_next_jump_time = now + 340

        # Urgent contest: if enemy is actively in zone, force platform transitions.
        if urgent_contest and self.on_ground:
            if dy > 45 and self._has_safe_drop_below():
                self.ai_key_down = True
            elif dy < -45 and self.jumps_remaining > 0 and now >= self.ai_next_jump_time:
                self.ai_key_jump = True
                self.ai_next_jump_time = now + 340

        self.facing_right = dx >= 0

        # If target is clearly below, drop to chase when aligned and safe.
        if (
            dy > 55
            and self.on_ground
            and abs(self.rect.centerx - self.ai_optimal_x) <= AI_LOOT_DROP_ALIGN_X
            and self._has_safe_drop_below()
        ):
            self.ai_key_down = True

        # Jump for higher targets, with a more reliable second jump while airborne.
        if now >= self.ai_next_jump_time and self.jumps_remaining > 0:
            if self.on_ground and dy < -45:
                self.ai_key_jump = True
                self.ai_next_jump_time = now + 420
            elif (not self.on_ground) and dy < -20 and self.vy >= -2.0:
                self.ai_key_jump = True
                self.ai_next_jump_time = now + 260

        # If vertical mismatch is too high to shoot, force level transition (jump/drop) to re-engage.
        if abs(dy) > AI_SHOOT_VERTICAL_TOL:
            self.ai_optimal_x = target.rect.centerx
            self.ai_optimal_until = now + 220
            if self.on_ground and dy > AI_SHOOT_VERTICAL_TOL and self._has_safe_drop_below():
                self.ai_key_down = True
            elif self.on_ground and dy < -AI_SHOOT_VERTICAL_TOL and self.jumps_remaining > 0 and now >= self.ai_next_jump_time:
                self.ai_key_jump = True
                self.ai_next_jump_time = now + 320

        incoming = any(
            b.team != self.team
            and abs(int(b.y) - self.rect.centery) <= 30
            and (
                (b.vx > 0 and b.x < self.rect.centerx and self.rect.centerx - b.x < AI_DODGE_RADIUS)
                or (b.vx < 0 and b.x > self.rect.centerx and b.x - self.rect.centerx < AI_DODGE_RADIUS)
            )
            for b in bullets
        )
        # Dodge by dropping first when safe; otherwise use jump (including aerial jumps).
        # While holding an active capture zone, avoid panic-dodging out of it.
        if incoming and now >= self.ai_next_jump_time and not (capture_hold and self_in_zone):
            if self.on_ground and self._has_safe_drop_below():
                self.ai_key_down = True
                self.ai_next_jump_time = now + 450
            elif self.jumps_remaining > 0:
                self.ai_key_jump = True
                self.ai_next_jump_time = now + 500

    def _probe_ground(self, probe_x):
        """Returns True if there is a platform under probe_x near the player's feet."""
        return any(
            p.left <= probe_x <= p.right
            and -8 <= p.top - self.rect.bottom <= 48
            for p in PLATFORM_RECTS
        )

    def _refresh_ai_ranges(self, now):
        if now < self.ai_range_until:
            return
        self.ai_min_range = random.randint(95, 170)
        self.ai_max_range = random.randint(230, 340)
        if self.ai_max_range <= self.ai_min_range:
            self.ai_max_range = self.ai_min_range + 80
        self.ai_range_until = now + random.randint(900, 1800)

    def _has_ground_ahead(self, move_dir):
        probe_x = self.rect.centerx + move_dir * (self.rect.width // 2 + 18)
        return any(
            p.left <= probe_x <= p.right
            and abs(p.top - self.rect.bottom) <= 30
            for p in PLATFORM_RECTS
        )

    def _has_safe_drop_below(self, probe_x=None):
        cx = self.rect.centerx if probe_x is None else int(probe_x)
        return any(
            p.left <= cx <= p.right
            and 14 <= (p.top - self.rect.bottom) <= 170
            for p in PLATFORM_RECTS
        )

    def _best_drop_x_for_chase(self, target_x):
        if self.current_platform_idx is None:
            return self.rect.centerx if self._has_safe_drop_below() else None
        cur = PLATFORM_RECTS[self.current_platform_idx]
        candidates = []
        for x in range(cur.left + 12, cur.right - 11, 18):
            if self._has_safe_drop_below(x):
                candidates.append(x)
        if not candidates:
            return self.rect.centerx if self._has_safe_drop_below() else None
        return min(candidates, key=lambda x: abs(x - target_x))

    def _has_near_ground_below(self, max_drop=120):
        cx = self.rect.centerx
        return any(
            p.left <= cx <= p.right
            and 0 <= (p.top - self.rect.bottom) <= max_drop
            for p in PLATFORM_RECTS
        )

    def _spawn_burst(self, direction, bullets, aim_vy=0.0):
        # Use visible bounds size (not full padded rect) so muzzle stays close to sprite.
        vis = self.image.get_bounding_rect(min_alpha=120)
        vis_w = vis.width if vis.width > 0 else self.rect.width
        vis_h = vis.height if vis.height > 0 else self.rect.height
        vis_top = self.rect.y + vis.y if vis.height > 0 else self.rect.top
        muzzle_x = self.rect.centerx + direction * (vis_w // 2 + 6)
        muzzle_y = vis_top + int(vis_h * self.muzzle_height_ratio)
        # Recoil belongs to shooting itself, not hit-confirm.
        self.vx += -direction * self.pushback_force
        kb_y = -2.5
        for _ in range(self.pellet_count):
            spread = random.randint(-self.recoil_spread_px, self.recoil_spread_px)
            bullets.append(_Bullet(self, muzzle_x, muzzle_y + spread, direction,
                                   self.blowback_force, kb_y, self.team, vy=aim_vy))
        _play_shot_sfx(self.weapon)

    def try_shoot(self, keys, bullets):
        if self.is_ai:
            return
        shoot_down = keys[self.controls["SHOOT"]]
        now = pygame.time.get_ticks()
        if (
            shoot_down
            and now - self.last_shot_time >= self.shot_cooldown_ms
            and self.reloading_until == 0
        ):
            direction = 1 if self.facing_right else -1
            self.shots_fired += 1
            self._spawn_burst(direction, bullets)
            self.last_shot_time = now
            self.current_ammo -= 1
            if self.current_ammo <= 0:
                if self.auto_reload:
                    self.reloading_until = now + self.reload_time_ms
                    _play_reload_sfx()
                else:
                    frames = _load_frames(self.gender, self.handgun_weapon)
                    if frames:
                        self._set_weapon_frames(frames)
                        self.frame_idx = 0
                        self.image = self.stand_right if self.facing_right else self.stand_left
                    self.apply_weapon_profile(self.handgun_weapon)
        self.prev_shoot_down = shoot_down

    def try_shoot_ai(self, players, bullets):
        if not self.is_ai:
            return
        target = self._choose_ai_target(players)
        if target is None:
            return
        now = pygame.time.get_ticks()
        if self.reloading_until != 0 or now - self.last_shot_time < self.shot_cooldown_ms:
            return

        distx = target.rect.centerx - self.rect.centerx
        if abs(distx) > AI_SHOOT_RANGE:
            return
        if abs(target.rect.centery - self.rect.centery) > AI_SHOOT_VERTICAL_TOL:
            return

        target_dir = 1 if distx >= 0 else -1
        facing_dir = 1 if self.facing_right else -1
        if target_dir != facing_dir:
            self.facing_right = target_dir > 0
            self.ai_turn_shoot_until = now + AI_TURN_SHOOT_DELAY_MS
            return
        if now < self.ai_turn_shoot_until:
            return
        direction = facing_dir

        # Horizontal-only shot (no vertical component)
        self.shots_fired += 1
        self._spawn_burst(direction, bullets, aim_vy=0.0)
        # AI should keep pressure while firing instead of drifting backward from recoil.
        self.vx += direction * (self.pushback_force * AI_SHOOT_FORWARD_COMP)
        self.last_shot_time = now
        self.current_ammo -= 1
        if self.current_ammo <= 0:
            if self.auto_reload:
                self.reloading_until = now + self.reload_time_ms
                _play_reload_sfx()
            else:
                frames = _load_frames(self.gender, self.handgun_weapon)
                if frames:
                    self._set_weapon_frames(frames)
                    self.frame_idx = 0
                    self.image = self.stand_right if self.facing_right else self.stand_left
                self.apply_weapon_profile(self.handgun_weapon)


def _draw_hud(screen):
    name_font = pygame.font.SysFont("arial", 16, True)
    info_font = pygame.font.SysFont("arial", 13)
    players = _state.get("players", [])

    n = max(1, len(players))
    margin_x = 15
    gap = 8
    box_height = 44
    available_w = WIDTH - margin_x * 2 - gap * (n - 1)
    box_width = max(180, min(300, available_w // n))

    start_x = margin_x
    y = HEIGHT - 15 - box_height

    for i, player in enumerate(players):
        x = start_x + i * (box_width + gap)

        box = pygame.Rect(x, y, box_width, box_height)
        hud_surface = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
        hud_surface.fill((0, 0, 0, 120))
        screen.blit(hud_surface, (x, y))
        pygame.draw.rect(screen, (255, 255, 255), box, 2)

        name_text = name_font.render(player.label, True, (255, 255, 255))
        screen.blit(name_text, (x + 8, y + 4))

        inf_font = pygame.font.SysFont("arial", 22, bold=True)
        inf_text = inf_font.render("∞", True, (230, 40, 40))
        inf_rect = inf_text.get_rect(midright=(x + box_width - 8, y + 13))
        screen.blit(inf_text, inf_rect)

        weapon_text = info_font.render(f"Wpn: {player.weapon}", True, (200, 200, 255))
        screen.blit(weapon_text, (x + 8, y + 24))

        time_left = max(0, (player.ability_end - pygame.time.get_ticks()) // 1000)
        ability_text = info_font.render(
            f"Ab: {player.ability} ({time_left}s)", True, (200, 255, 200)
        )
        ab_rect = ability_text.get_rect(midright=(x + box_width - 8, y + 30))
        screen.blit(ability_text, ab_rect)


def _flag_spawn_and_zone():
    # Use platform selected during reset (based on P1 spawn lane).
    plat_idx = _state.get("domination", {}).get("flag_platform_idx", 0)
    plat = PLATFORM_RECTS[plat_idx]
    flag_rect = FLAG_DRAW_IMAGE.get_rect(midbottom=(plat.centerx, plat.top))
    flag_rect.y += FLAG_Y_OFFSET
    zone_center = flag_rect.center
    zone_radius = max(94, FLAG_DRAW_IMAGE.get_width() // 2 + 92)
    return flag_rect, zone_center, zone_radius


def _visible_player_rect(player):
    # Use only non-transparent sprite bounds for gameplay checks.
    vis = player.image.get_bounding_rect(min_alpha=60)
    if vis.width > 0 and vis.height > 0:
        return pygame.Rect(
            player.rect.x + vis.x,
            player.rect.y + vis.y,
            vis.width,
            vis.height,
        )
    return player.rect


class _Bullet:
    def __init__(self, owner, x, y, direction, knockback_x, knockback_y, team, vy=0.0):
        self.owner = owner
        self.team = team
        self.direction = 1 if direction >= 0 else -1
        self.x = float(x)
        self.y = float(y)
        self.vx = float(self.direction * BULLET_SPEED)
        self.vy = float(vy)  # vertical component for angled AI shots
        self.knockback_x = knockback_x
        self.knockback_y = knockback_y
        self.spawn_time = pygame.time.get_ticks()

    def update(self):
        self.x += self.vx
        self.y += self.vy

    def is_expired(self, now):
        return now - self.spawn_time > BULLET_LIFETIME_MS

    def hits_rect(self, rect):
        return self._segment_rect().colliderect(rect)

    def draw(self, screen):
        import math
        head_x = int(self.x)
        head_y = int(self.y)

        speed = math.hypot(self.vx, self.vy) or 1
        norm_vx = self.vx / speed
        norm_vy = self.vy / speed
        tail_x = int(self.x - norm_vx * BULLET_LENGTH)
        tail_y = int(self.y - norm_vy * BULLET_LENGTH)

        glow_r = max(2, BULLET_GLOW_THICKNESS // 2)
        core_r = max(1, BULLET_THICKNESS // 2)

        mid_frac = max(3, BULLET_LENGTH // 3)
        glow_mid_x = int(self.x - norm_vx * mid_frac)
        glow_mid_y = int(self.y - norm_vy * mid_frac)

        perp_x = -norm_vy
        perp_y = norm_vx

        glow_poly = [
            (tail_x, tail_y),
            (int(glow_mid_x + perp_x * glow_r), int(glow_mid_y + perp_y * glow_r)),
            (int(glow_mid_x - perp_x * glow_r), int(glow_mid_y - perp_y * glow_r)),
        ]
        core_poly = [
            (tail_x, tail_y),
            (int(glow_mid_x + perp_x * core_r), int(glow_mid_y + perp_y * core_r)),
            (int(glow_mid_x - perp_x * core_r), int(glow_mid_y - perp_y * core_r)),
        ]

        pygame.draw.polygon(screen, BULLET_GLOW_COLOR, glow_poly)
        pygame.draw.polygon(screen, BULLET_COLOR, core_poly)
        pygame.draw.circle(screen, BULLET_GLOW_COLOR, (head_x, head_y), glow_r)
        pygame.draw.circle(screen, BULLET_COLOR, (head_x, head_y), core_r)

    def _segment_points(self):
        import math
        head_x = int(self.x)
        head_y = int(self.y)
        speed = math.hypot(self.vx, self.vy) or 1
        tail_x = int(self.x - (self.vx / speed) * BULLET_LENGTH)
        tail_y = int(self.y - (self.vy / speed) * BULLET_LENGTH)
        return (head_x, head_y), (tail_x, tail_y)

    def _segment_rect(self):
        start, end = self._segment_points()
        left = min(start[0], end[0])
        top = min(start[1], end[1]) - BULLET_GLOW_THICKNESS // 2
        width = max(1, abs(end[0] - start[0]))
        height = max(BULLET_GLOW_THICKNESS, abs(end[1] - start[1]) + BULLET_GLOW_THICKNESS)
        return pygame.Rect(left, top, width, height)


def _update_bullets():
    bullets = _state.get("bullets", [])
    players = _state.get("players", [])
    now = pygame.time.get_ticks()

    for bullet in bullets[:]:
        bullet.update()

        if (
            bullet.is_expired(now)
            or bullet.x < -20
            or bullet.x > WIDTH + 20
            or bullet.y < -20
            or bullet.y > HEIGHT + 20
        ):
            bullets.remove(bullet)
            continue

        if any(p.collidepoint(int(bullet.x), int(bullet.y)) for p in PLATFORM_RECTS):
            bullets.remove(bullet)
            continue

        hit_player = None
        for target in players:
            if target is bullet.owner or target.team == bullet.team:
                continue
            if bullet.hits_rect(_visible_player_rect(target)):
                hit_player = target
                break

        if hit_player is not None:
            now2 = pygame.time.get_ticks()
            # Skip if target is still invincible (GM2's freepass)
            if now2 < hit_player.freepass_until or hit_player.has_spawn_shield(now2):
                bullets.remove(bullet)
                continue
            bullet.owner.shots_hit += 1
            # GM2: overwrite target's vx entirely (don't add to it)
            direction = 1 if bullet.vx > 0 else -1
            _play_hit_sfx()
            _state["effects"].append(
                # Use HitEffect here when a bullet connects.
                HitEffect(int(bullet.x), int(bullet.y))
            )
            _state["effects"].append(
                # Use HitTextEffect here for floating impact feedback text.
                HitTextEffect(int(bullet.x) - direction * 18, int(bullet.y) - 10, direction)
            )
            hit_player.last_hit_by = bullet.owner
            hit_player.vx = direction * bullet.knockback_x
            hit_player.vy = min(hit_player.vy, bullet.knockback_y)
            hit_player.on_ground = False
            # Grant invincibility frames so burst fire doesn't lock someone in place
            hit_player.freepass_until = now2 + FREEPASS_MS
            bullets.remove(bullet)


def _draw_bullets(screen):
    for bullet in _state.get("bullets", []):
        bullet.draw(screen)


def _update_domination(players):
    global _last_capture_tick
    now = pygame.time.get_ticks()
    dt = max(0.0, (now - _last_capture_tick) / 1000.0)
    _last_capture_tick = now

    dom = _state["domination"]

    if dom["capture_winner"] is not None:
        if now < dom["capture_winner_until"]:
            return

        # Respawn flag on another platform and restart capture race.
        current = dom["flag_platform_idx"]
        choices = [i for i in range(len(PLATFORM_RECTS)) if i != current]
        if choices:
            dom["flag_platform_idx"] = random.choice(choices)
        for side in dom["progress"].keys():
            dom["progress"][side] = 0.0
        dom["capture_active"] = False
        dom["capture_winner"] = None
        dom["capture_winner_until"] = 0
        dom["capture_started_at"] = 0

    if dom["match_over"]:
        return

    flag_rect, zone_center, zone_radius = _flag_spawn_and_zone()

    # Capture starts only after someone touches the flag sprite.
    if not dom["capture_active"]:
        touched = any(_visible_player_rect(p).colliderect(flag_rect) for p in players)
        if touched:
            dom["capture_active"] = True
            dom["capture_started_at"] = now
        else:
            return

    capture_ids = dom["progress"].keys()

    # Capture area is the grey circle only.
    inside = [
        p for p in players
        if p.team in capture_ids
        if (
            (_visible_player_rect(p).centerx - zone_center[0]) ** 2
            + (_visible_player_rect(p).centery - zone_center[1]) ** 2
            <= zone_radius ** 2
        )
    ]
    if len(inside) == 0:
        # If nobody stays in the zone, cancel this capture attempt.
        for side in dom["progress"].keys():
            dom["progress"][side] = 0.0
        dom["capture_active"] = False
        dom["capture_started_at"] = 0
        return

    teams_inside = {p.team for p in inside}
    if len(teams_inside) != 1:
        # Contested zone: both teams present, progress pauses.
        return

    capture_team = next(iter(teams_inside))
    other_team = "enemy" if capture_team == "ally" else "ally"
    if dom["progress"][other_team] > 0.0:
        dom["progress"][other_team] = 0.0
    rate = 30.0  # percent per second
    dom["progress"][capture_team] = min(
        100.0,
        dom["progress"][capture_team] + rate * dt
    )
    if dom["progress"][capture_team] >= 100.0:
        capturers = [p for p in inside if p.team == capture_team]
        if capturers:
            capturer = min(
                capturers,
                key=lambda p: (
                    (_visible_player_rect(p).centerx - zone_center[0]) ** 2
                    + (_visible_player_rect(p).centery - zone_center[1]) ** 2
                ),
            )
            capturer.flags_captured += 1
        _play_capture_sfx()
        dom["capture_winner"] = capture_team
        dom["capture_winner_until"] = now + 1200
        dom["scores"][capture_team] += 1
        if dom["scores"][capture_team] >= dom["target_flags"]:
            dom["match_over"] = True
            dom["final_winner"] = capture_team


def _draw_domination_ui(screen, draw_zone=True, draw_bar=True):
    flag_rect, zone_center, zone_radius = _flag_spawn_and_zone()
    dom = _state["domination"]

    if draw_zone and dom["capture_active"] and not dom["match_over"]:
        # Visual capture area indicator (grey circle).
        now = pygame.time.get_ticks()
        start = dom.get("capture_started_at", now) or now
        t = min(1.0, max(0.0, (now - start) / 320.0))
        anim_radius = max(1, int(zone_radius * t))
        zone_layer = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.circle(zone_layer, (170, 170, 170, 70), zone_center, anim_radius)
        pygame.draw.circle(zone_layer, (210, 210, 210, 150), zone_center, anim_radius, 2)
        screen.blit(zone_layer, (0, 0))

    if not draw_bar:
        return

    ally_p = dom["progress"]["ally"]
    enemy_p = dom["progress"]["enemy"]
    capture_winner = dom["capture_winner"]

    # Single shared progress bar (used by both ally/enemy teams), anchored above flag.
    bar_w = 110
    bar_h = 12
    x = flag_rect.centerx - bar_w // 2
    y = flag_rect.top - 28
    x = max(8, min(WIDTH - bar_w - 8, x))
    y = max(8, y)

    if ally_p > enemy_p:
        active_progress = ally_p
        fill_color = (90, 150, 240)
        status = f"ALLY CAPTURING {int(active_progress)}%"
        txt_color = (255, 255, 255)
    elif enemy_p > ally_p:
        active_progress = enemy_p
        fill_color = (220, 90, 90)
        status = f"ENEMY CAPTURING {int(active_progress)}%"
        txt_color = (255, 255, 255)
    elif ally_p > 0:
        active_progress = ally_p
        fill_color = (185, 185, 185)
        status = f"CONTESTED {int(active_progress)}%"
        txt_color = (255, 230, 160)
    else:
        active_progress = 0.0
        fill_color = (120, 120, 120)
        status = "CAPTURE 0%"
        txt_color = (220, 220, 220)

    if capture_winner is not None:
        who = "ALLY" if capture_winner == "ally" else "ENEMY"
        status = f"{who} CAPTURED"
        txt_color = (255, 220, 120)

    pygame.draw.rect(screen, (25, 25, 35), (x, y, bar_w, bar_h))
    pygame.draw.rect(screen, fill_color, (x, y, int(bar_w * (active_progress / 100.0)), bar_h))
    pygame.draw.rect(screen, (255, 255, 255), (x, y, bar_w, bar_h), 2)

    ui_font = pygame.font.SysFont("arial", 15, bold=True)
    t = ui_font.render(status, True, txt_color)
    ts = ui_font.render(status, True, (0, 0, 0))
    tr = t.get_rect(center=(x + bar_w // 2, y - 10))
    sr = ts.get_rect(center=(tr.centerx + 2, tr.centery + 2))
    screen.blit(ts, sr)
    screen.blit(t, tr)

    # Match HUD: score + flag target / result.
    hud_font = pygame.font.SysFont("arial", 18, bold=True)
    ally_score = dom["scores"]["ally"]
    enemy_score = dom["scores"]["enemy"]
    target_flags = dom["target_flags"]
    if dom["match_over"]:
        msg = f"{dom['final_winner'].upper()} WINS  {ally_score}-{enemy_score}"
        col = (255, 225, 120)
    else:
        col = (240, 240, 240)
        msg = f"ALLY {ally_score} - {enemy_score} ENEMY   FIRST TO {target_flags}"
    score_t = hud_font.render(msg, True, col)
    score_s = hud_font.render(msg, True, (0, 0, 0))
    r = score_t.get_rect(center=(WIDTH // 2, 22))
    rs = score_s.get_rect(center=(r.centerx + 2, r.centery + 2))
    screen.blit(score_s, rs)
    screen.blit(score_t, r)


def _draw_pause_overlay(screen):
    global _resume_rect, _exit_rect

    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 140))
    screen.blit(overlay, (0, 0))

    panel = pygame.Rect(WIDTH // 2 - 185, HEIGHT // 2 - 125, 370, 250)
    pygame.draw.rect(screen, (232, 232, 232), panel)
    pygame.draw.rect(screen, (20, 20, 20), panel, 3)

    title_font = _hit_font(42)
    button_font = _hit_font(26)

    title_shadow = title_font.render("GAME PAUSED", True, (0, 0, 0))
    title_text = title_font.render("GAME PAUSED", True, (255, 255, 255))
    screen.blit(title_shadow, title_shadow.get_rect(center=(panel.centerx + 2, panel.y + 52)))
    screen.blit(title_text, title_text.get_rect(center=(panel.centerx, panel.y + 50)))

    mouse_pos = pygame.mouse.get_pos()
    _resume_rect = pygame.Rect(panel.x + 48, panel.y + 96, panel.w - 96, 54)
    _exit_rect = pygame.Rect(panel.x + 48, panel.y + 170, panel.w - 96, 40)

    for rect, label, base_fill, hover_fill, text_color in (
        (_resume_rect, "RESUME GAME", (150, 150, 150), (120, 120, 120), (255, 255, 255)),
        (_exit_rect, "EXIT GAME", (185, 20, 20), (145, 10, 10), (255, 255, 255)),
    ):
        hovered = rect.collidepoint(mouse_pos)
        fill = hover_fill if hovered else base_fill
        pygame.draw.rect(screen, fill, rect)
        pygame.draw.rect(screen, (35, 35, 35), rect, 2)
        shadow = button_font.render(label, True, (0, 0, 0))
        text = button_font.render(label, True, text_color)
        text_bounds = text.get_bounding_rect()
        shadow_bounds = shadow.get_bounding_rect()

        text_pos = (
            rect.centerx - text_bounds.width // 2 - text_bounds.x,
            rect.centery - text_bounds.height // 2 - text_bounds.y,
        )
        shadow_pos = (
            rect.centerx - shadow_bounds.width // 2 - shadow_bounds.x + 2,
            rect.centery - shadow_bounds.height // 2 - shadow_bounds.y + 2,
        )
        screen.blit(shadow, shadow_pos)
        screen.blit(text, text_pos)


def _draw_match_summary(screen, players):
    dom = _state["domination"]
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(210)
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (0, 0))

    title_font_big = pygame.font.SysFont("arial", 90, True)
    subtitle_font = pygame.font.SysFont("arial", 30, True)
    stat_font = pygame.font.SysFont("arial", 26)
    hint_font = pygame.font.SysFont("arial", 24)

    player_win = dom.get("final_winner") == "ally"
    if player_win:
        title = title_font_big.render("VICTORY", True, (255, 215, 0))
        subtitle = subtitle_font.render("Flag Captured Successfully", True, (255, 255, 255))
    else:
        title = title_font_big.render("DEFEAT", True, (230, 80, 80))
        subtitle = subtitle_font.render("The Enemy Secured The Arena", True, (255, 255, 255))

    screen.blit(title, title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 190)))
    screen.blit(subtitle, subtitle.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 126)))

    players_to_show = [p for p in players if not p.is_ai]

    for idx, p in enumerate(players_to_show):
        acc = int((p.shots_hit / p.shots_fired) * 100) if p.shots_fired > 0 else 0
        panel_w = 320
        panel_h = 285

        if len(players_to_show) == 1:
            panel_x = WIDTH // 2 - panel_w // 2
        else:
            panel_x = WIDTH // 2 - panel_w - 40 if idx == 0 else WIDTH // 2 + 40

        panel_y = HEIGHT // 2 - 78
        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((15, 15, 25, 180))
        screen.blit(panel, (panel_x, panel_y))
        pygame.draw.rect(screen, (200, 200, 200), (panel_x, panel_y, panel_w, panel_h), 1)

        name_font = pygame.font.SysFont("arial", 32, True)
        name = name_font.render(p.label, True, (255, 255, 255))
        screen.blit(name, name.get_rect(center=(panel_x + panel_w // 2, panel_y + 30)))

        pygame.draw.line(
            screen,
            (120, 120, 120),
            (panel_x + 30, panel_y + 60),
            (panel_x + panel_w - 30, panel_y + 60),
            1,
        )

        stats = [
            ("Kills", p.kills),
            ("Falls", p.falls),
            ("Accuracy", f"{acc}%"),
            ("Flags Captured", p.flags_captured),
            ("Pickups", p.pickups),
        ]

        for i, (label, value) in enumerate(stats):
            y = panel_y + 95 + i * 38
            label_text = stat_font.render(label, True, (180, 180, 180))
            value_text = stat_font.render(str(value), True, (255, 255, 255))
            screen.blit(label_text, (panel_x + 34, y - 15))
            screen.blit(value_text, (panel_x + panel_w - 60, y - 15))

    hint = hint_font.render("Press ESC to return to level select", True, (180, 180, 180))
    screen.blit(hint, hint.get_rect(center=(WIDTH // 2, panel_y + panel_h + 34)))


def _freeze_end_scene(players):
    _stop_walk_sfx()
    _state["bullets"].clear()
    _state["effects"].clear()
    for player in players:
        player.vx = 0
        player.vy = 0
        player.ai_key_left = False
        player.ai_key_right = False
        player.ai_key_jump = False
        player.ai_key_down = False


def change_weapon_animation(player, weapon):
    frames = _load_frames(player.gender, weapon)
    if frames:
        player._set_weapon_frames(frames)
        player.frame_idx = 0
        player.image = player.stand_right if player.facing_right else player.stand_left
    player.apply_weapon_profile(weapon)


def reset(
    player1,
    player2,
    mode,
    p1_gender,
    p2_gender,
    p1_gun,
    p2_gun,
    controls_p1,
    controls_p2,
):
    global _finished, _state, drop_manager, _last_capture_tick, _round_start_tick
    global _paused
    _finished = False
    _paused = False
    _init_snow()
    p1_frames = _load_frames(p1_gender, p1_gun)
    p2_frames = _load_frames(p2_gender, p2_gun)

    def pick_spawn_platform_idx(px):
        candidates = [i for i, p in enumerate(PLATFORM_RECTS) if p.left <= px <= p.right]
        if candidates:
            return min(candidates, key=lambda i: PLATFORM_RECTS[i].top)
        return min(range(len(PLATFORM_RECTS)), key=lambda i: abs(PLATFORM_RECTS[i].centerx - px))

    p1_spawn_x, p1_spawn_y = _random_spawn_point()
    flag_platform_idx = pick_spawn_platform_idx(p1_spawn_x)

    p1 = _Player("P1", p1_spawn_x, player1, controls_p1, p1_frames, p1_gender, team="ally", is_ai=False)
    p1.spawn_x, p1.spawn_y = p1_spawn_x, p1_spawn_y
    p1.rect.midbottom = (p1_spawn_x, p1_spawn_y)
    p1_weapon = _normalize_gun(p1_gun)
    p1.handgun_weapon = p1_weapon if p1_weapon in HANDGUN_WEAPONS else "glock17"
    p1.weapon = p1_weapon
    p1.apply_weapon_profile(p1_weapon)
    _state = {
        "mode": mode,
        "domination": {
            "progress": {"ally": 0.0, "enemy": 0.0},
            "scores": {"ally": 0, "enemy": 0},
            "capture_active": False,
            "capture_winner": None,
            "capture_winner_until": 0,
            "capture_started_at": 0,
            "flag_platform_idx": flag_platform_idx,
            "target_flags": FLAG_TARGET_2P if mode == "2P" else FLAG_TARGET_1P,
            "match_over": False,
            "final_winner": None,
        },
        "players": [p1],
        "bullets": [],
        "effects": [],
    }
    now = pygame.time.get_ticks()
    _round_start_tick = now
    p1.activate_spawn_shield(now)
    _play_respawn_sfx()
    if mode == "2P":
        p2_spawn_x, p2_spawn_y = _random_spawn_point([p1_spawn_x])
        p2 = _Player("P2", p2_spawn_x, player2, controls_p2.copy(), p2_frames, p2_gender, team="ally", is_ai=False)
        p2.spawn_x, p2.spawn_y = p2_spawn_x, p2_spawn_y
        p2.rect.midbottom = (p2_spawn_x, p2_spawn_y)
        p2_weapon = _normalize_gun(p2_gun)
        p2.handgun_weapon = p2_weapon if p2_weapon in HANDGUN_WEAPONS else "glock17"
        p2.weapon = p2_weapon
        p2.apply_weapon_profile(p2_weapon)
        _state["players"].append(p2)
        p2.activate_spawn_shield(now)
        _play_respawn_sfx()

    snow_frames = _load_frames("snowman", "M4A1")
    taken_x = [p1_spawn_x]
    if mode == "2P":
        taken_x.append(p2_spawn_x)
    ai_spawn_x, ai_spawn_y = _random_spawn_point(taken_x)
    snowman = _Player("ENEMY", ai_spawn_x, "Snowman", {}, snow_frames, "snowman", team="enemy", is_ai=True)
    snowman.spawn_x, snowman.spawn_y = ai_spawn_x, ai_spawn_y
    snowman.rect.midbottom = (ai_spawn_x, ai_spawn_y)
    snowman.handgun_weapon = "glock17"
    snowman.apply_weapon_profile("M4A1")
    _state["players"].append(snowman)
    snowman.activate_spawn_shield(now)
    _play_respawn_sfx()

    load_drop_assets()
    drop_manager = DropManager(
        PLATFORM_RECTS,
        allowed_abilities=[
            "speedUp",
            "slowDown",
            "jumpHigher",
            "tripleJump",
            "larger",
            "smaller",
        ],
    )
    _last_capture_tick = now + ROUND_COUNTDOWN_MS


def is_finished():
    return _finished


def is_hovering_clickable(pos):
    if _paused:
        return _resume_rect.collidepoint(pos) or _exit_rect.collidepoint(pos)
    return False


def handle_click(pos):
    global _paused, _finished
    if not _paused:
        return
    if _resume_rect.collidepoint(pos):
        _paused = False
    elif _exit_rect.collidepoint(pos):
        _stop_walk_sfx()
        _paused = False
        _finished = True


def handle_key(key):
    global _finished, _paused
    if key == pygame.K_ESCAPE:
        if _state.get("domination", {}).get("match_over", False):
            _stop_walk_sfx()
            _finished = True
        else:
            _paused = not _paused
        return
    if key == pygame.K_BACKSPACE:
        _stop_walk_sfx()
        _finished = True


def draw(screen, title_font, menu_font, small_font):
    _load_level_assets()
    bg = pygame.transform.scale(BG_IMAGE, (WIDTH, HEIGHT))
    screen.blit(bg, (0, 0))
    _update_and_draw_snow(screen)
    screen.blit(PLATFORM_IMAGE, (60, 140))
    players = _state.get("players", [])
    now = pygame.time.get_ticks()
    countdown_left = (_round_start_tick + ROUND_COUNTDOWN_MS) - now
    if countdown_left > 0:
        # Adjust countdown timing/text styling here.
        flag_rect, _, _ = _flag_spawn_and_zone()
        screen.blit(FLAG_DRAW_IMAGE, flag_rect)
        for player in players:
            player.draw(screen)
        _stop_walk_sfx()

        seconds_left = countdown_left // 1000 + 1
        if countdown_left <= 500:
            countdown_text = "GO"
            font_size = 130
            color = (255, 215, 0)
        else:
            countdown_text = str(min(3, seconds_left))
            font_size = 120
            color = (255, 255, 255)

        font = pygame.font.SysFont("arial", font_size, True)
        shadow = font.render(countdown_text, True, (0, 0, 0))
        text = font.render(countdown_text, True, color)
        screen.blit(shadow, shadow.get_rect(center=(WIDTH // 2 + 3, HEIGHT // 2 + 3)))
        screen.blit(text, text.get_rect(center=(WIDTH // 2, HEIGHT // 2)))
        return

    if _paused:
        _draw_domination_ui(screen, draw_zone=True, draw_bar=False)
        flag_rect, _, _ = _flag_spawn_and_zone()
        screen.blit(FLAG_DRAW_IMAGE, flag_rect)
        for player in players:
            player.draw(screen)
        _draw_bullets(screen)
        for effect in _state.get("effects", []):
            effect.draw(screen)
        _draw_domination_ui(screen, draw_zone=False, draw_bar=True)
        if drop_manager:
            drop_manager.draw(screen)
        _draw_hud(screen)
        _stop_walk_sfx()
        _draw_pause_overlay(screen)
        return

    keys = pygame.key.get_pressed()

    # Update capture state first, then draw domination layers by depth.
    _update_domination(_state["players"])
    if _state.get("domination", {}).get("match_over", False):
        _freeze_end_scene(players)
        _draw_domination_ui(screen, draw_zone=True, draw_bar=False)
        flag_rect, _, _ = _flag_spawn_and_zone()
        screen.blit(FLAG_DRAW_IMAGE, flag_rect)
        for player in players:
            player.draw(screen)
        if drop_manager:
            drop_manager.draw(screen)
        _draw_domination_ui(screen, draw_zone=False, draw_bar=True)
        _draw_hud(screen)
        _draw_match_summary(screen, players)
        return

    _draw_domination_ui(screen, draw_zone=True, draw_bar=False)
    flag_rect, _, _ = _flag_spawn_and_zone()
    screen.blit(FLAG_DRAW_IMAGE, flag_rect)

    for player in players:
        player.update(keys, players, _state["bullets"])
        if player.is_ai:
            player.try_shoot_ai(players, _state["bullets"])
        else:
            player.try_shoot(keys, _state["bullets"])
        player.draw(screen)

    walking = any(p.on_ground and abs(p.vx) > 0.6 for p in players)
    if walking:
        _play_walk_sfx()
    else:
        _stop_walk_sfx()

    _update_bullets()
    _draw_bullets(screen)

    for effect in _state.get("effects", [])[:]:
        effect.update()
        effect.draw(screen)
        if effect.finished():
            _state["effects"].remove(effect)

    _draw_domination_ui(screen, draw_zone=False, draw_bar=True)

    if drop_manager:
        drop_manager.update(_state["players"], change_weapon_animation)
        drop_manager.draw(screen)

    _draw_hud(screen)


