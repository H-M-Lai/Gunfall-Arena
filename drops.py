import pygame
import random
import os
import math

SPAWN_INTERVAL = 10000
DESPAWN_TIME = 5000
ABILITY_DURATION = 8000

ASSET_DIR = os.path.join(os.path.dirname(__file__), "Assets")
ABILITY_DIR = os.path.join(ASSET_DIR, "ability")

ABILITY_IMAGES = {}
BOX_IMAGE = None

# Matches the structure used by the character asset folders.
WEAPONS = [
    "MP5",
    "M4A1",
    "M870",
    "scar-h",
    "ump45",
]


def load_drop_assets():

    global ABILITY_IMAGES, BOX_IMAGE

    ABILITY_IMAGES = {
        "speedUp": pygame.image.load(
            os.path.join(ABILITY_DIR, "speedUp.png")
        ).convert_alpha(),
        "slowDown": pygame.image.load(
            os.path.join(ABILITY_DIR, "slowDown.png")
        ).convert_alpha(),
        "jumpHigher": pygame.image.load(
            os.path.join(ABILITY_DIR, "jumpHigher.png")
        ).convert_alpha(),
        "tripleJump": pygame.image.load(
            os.path.join(ABILITY_DIR, "tripleJump.png")
        ).convert_alpha(),
        "larger": pygame.image.load(
            os.path.join(ABILITY_DIR, "larger.png")
        ).convert_alpha(),
        "smaller": pygame.image.load(
            os.path.join(ABILITY_DIR, "smaller.png")
        ).convert_alpha(),
        "life": pygame.image.load(
            os.path.join(ABILITY_DIR, "life.png")
        ).convert_alpha(),
    }

    BOX_IMAGE = pygame.image.load(
        os.path.join(ABILITY_DIR, "weaponBox.png")
    ).convert_alpha()


class DropItem:

    def __init__(self, type, name, x, y, image):

        self.type = type
        self.name = name

        # Images are already normalized to the target size, so no extra scaling is needed.
        self.image = image
        self.glow_radius = max(self.image.get_width(), self.image.get_height()) // 2 + 8

        self.base_x = x
        self.base_y = y

        self.rect = self.image.get_rect(midbottom=(x, y))
        self.mask = pygame.mask.from_surface(self.image)

        self.spawn_time = pygame.time.get_ticks()

        # Floating animation parameters.
        self.float_speed = random.uniform(0.003, 0.005)
        self.float_height = random.randint(6, 10)

    def update(self):

        t = pygame.time.get_ticks()

        float_y = self.base_y + math.sin(t * self.float_speed) * self.float_height

        self.rect.midbottom = (self.base_x, float_y)

    def draw(self, screen):

        screen.blit(self.image, self.rect)

    def expired(self):

        return pygame.time.get_ticks() - self.spawn_time > DESPAWN_TIME


class DropManager:

    def __init__(self, platforms, allowed_abilities=None):

        self.platforms = platforms
        self.drops = []
        self.last_spawn = pygame.time.get_ticks()
        # Levels can narrow this list, for example to disable life drops in Level 2.
        if allowed_abilities is None:
            self.allowed_abilities = list(ABILITY_IMAGES.keys())
        else:
            self.allowed_abilities = [
                ability for ability in allowed_abilities if ability in ABILITY_IMAGES
            ]

    def spawn_drop(self):

        platform = random.choice(self.platforms)

        x = random.randint(platform.left + 30, platform.right - 30)
        y = platform.top - 35

        can_spawn_ability = bool(self.allowed_abilities)

        if can_spawn_ability and random.random() < 0.5:

            ability = random.choice(self.allowed_abilities)
            drop = DropItem("ability", ability, x, y, ABILITY_IMAGES[ability])

        else:

            drop = DropItem("weaponbox", None, x, y, BOX_IMAGE)

        self.drops.append(drop)

    def update(self, players, change_weapon_func):

        now = pygame.time.get_ticks()

        if now - self.last_spawn > SPAWN_INTERVAL:

            self.spawn_drop()
            self.last_spawn = now

        for drop in self.drops[:]:

            drop.update()

            if drop.expired():

                self.drops.remove(drop)
                continue

            for player in players:

                player_mask = pygame.mask.from_surface(player.image)
                offset = (drop.rect.x - player.rect.x, drop.rect.y - player.rect.y)

                if player_mask.overlap(drop.mask, offset):
                    player.pickups += 1

                    if drop.type == "ability":
                        # Spawn-protected players ignore ability effects briefly.
                        if hasattr(
                            player, "has_spawn_shield"
                        ) and player.has_spawn_shield(now):
                            continue

                        player.ability = drop.name
                        player.ability_end = now + ABILITY_DURATION

                        if drop.name == "speedUp":
                            player.speed = player.base_speed * 1.6

                        elif drop.name == "slowDown":
                            player.speed = player.base_speed * 0.5

                        elif drop.name == "jumpHigher":
                            player.jump_power = player.base_jump * 1.35

                        elif drop.name == "tripleJump":
                            player.max_jumps = 3

                        elif drop.name == "larger":
                            if hasattr(player, "apply_size_scale"):
                                player.apply_size_scale(1.4)
                            else:
                                player.walk_right = [
                                    pygame.transform.scale(
                                        f,
                                        (
                                            int(f.get_width() * 1.4),
                                            int(f.get_height() * 1.4),
                                        ),
                                    )
                                    for f in player.walk_right
                                ]
                                player.walk_left = [
                                    pygame.transform.scale(
                                        f,
                                        (
                                            int(f.get_width() * 1.4),
                                            int(f.get_height() * 1.4),
                                        ),
                                    )
                                    for f in player.walk_left
                                ]

                        elif drop.name == "smaller":
                            if hasattr(player, "apply_size_scale"):
                                player.apply_size_scale(0.65)
                            else:
                                player.walk_right = [
                                    pygame.transform.scale(
                                        f,
                                        (
                                            int(f.get_width() * 0.65),
                                            int(f.get_height() * 0.65),
                                        ),
                                    )
                                    for f in player.walk_right
                                ]
                                player.walk_left = [
                                    pygame.transform.scale(
                                        f,
                                        (
                                            int(f.get_width() * 0.65),
                                            int(f.get_height() * 0.65),
                                        ),
                                    )
                                    for f in player.walk_left
                                ]

                        elif drop.name == "life":
                            player.lives += 1

                    elif drop.type == "weaponbox":

                        weapon = random.choice(WEAPONS)

                        player.weapon = weapon

                        # Important: refresh the player's animation after changing weapons.
                        change_weapon_func(player, weapon)

                    self.drops.remove(drop)
                    break

    def draw(self, screen):

        for drop in self.drops:
            drop.draw(screen)
