import os
import pygame

BASE_DIR = os.path.dirname(__file__)
SFX_DIR = os.path.join(BASE_DIR, "Assets", "sound effect")

TOTAL_CHANNELS = 32

SFX_FILES = {
    "shot_handgun": "GunShoot.wav",
    "shot_rifle": "gun_shot.mp3",
    "reload": "Reload2.mp3",
    "jump": "jumping.mp3",
    "hit": "got_shot.mp3",
    "walk": "walking.mp3",
    "landing": "landing.mp3",
    "ability": "ability.mp3",
    "box": "box.mp3",
    "capture": "captured_flag.mp3",
    "respawn": "respawn.mp3",
}

SFX_VOLUMES = {
    "shot_handgun": 0.5,
    "shot_rifle": 0.5,
    "reload": 0.55,
    "jump": 0.5,
    "hit": 0.55,
    "walk": 0.7,
    "landing": 0.6,
    "ability": 0.6,
    "box": 0.6,
    "capture": 0.65,
    "respawn": 0.6,
}

# Pool sizes for overlap per SFX (walk is reserved looping channel).
SFX_POOLS = {
    "walk": 1,
    "shot_handgun": 3,
    "shot_rifle": 3,
    "hit": 3,
    "reload": 2,
    "jump": 2,
    "landing": 2,
    "ability": 2,
    "box": 2,
    "capture": 2,
    "respawn": 2,
}

_enabled = True
_channels_ready = False
_pools = {}
_pool_index = {}
_sounds = {}


def set_enabled(enabled):
    global _enabled
    _enabled = bool(enabled)
    if not _enabled:
        stop_loop("walk")


def ensure_ready():
    _ensure_channels()


def _ensure_channels():
    global _channels_ready, _pools, _pool_index
    if _channels_ready:
        return
    if not pygame.mixer.get_init():
        pygame.mixer.init()
    pygame.mixer.set_num_channels(TOTAL_CHANNELS)

    next_idx = 0
    for name, count in SFX_POOLS.items():
        chans = []
        for _ in range(count):
            if next_idx >= TOTAL_CHANNELS:
                break
            chans.append(pygame.mixer.Channel(next_idx))
            next_idx += 1
        _pools[name] = chans
        _pool_index[name] = 0
    _channels_ready = True


def _load_sound(name):
    if name in _sounds:
        return _sounds[name]
    filename = SFX_FILES.get(name)
    if not filename:
        _sounds[name] = None
        return None
    path = os.path.join(SFX_DIR, filename)
    if not os.path.exists(path):
        _sounds[name] = None
        return None
    try:
        snd = pygame.mixer.Sound(path)
        snd.set_volume(SFX_VOLUMES.get(name, 0.6))
        _sounds[name] = snd
        return snd
    except pygame.error:
        _sounds[name] = None
        return None


def _next_channel(name):
    chans = _pools.get(name) or []
    if not chans:
        return None
    idx = _pool_index.get(name, 0)
    ch = chans[idx % len(chans)]
    _pool_index[name] = idx + 1
    return ch


def play(name):
    if not _enabled:
        return
    _ensure_channels()
    snd = _load_sound(name)
    if snd is None:
        return
    ch = _next_channel(name)
    if ch is not None:
        ch.play(snd)


def start_loop(name):
    if not _enabled:
        return
    _ensure_channels()
    snd = _load_sound(name)
    if snd is None:
        return
    chans = _pools.get(name) or []
    if not chans:
        return
    ch = chans[0]
    if not ch.get_busy():
        ch.play(snd, loops=-1)


def stop_loop(name):
    chans = _pools.get(name) or []
    if not chans:
        return
    ch = chans[0]
    if ch.get_busy():
        ch.stop()


def stop_all():
    if not _channels_ready:
        return
    for chans in _pools.values():
        for ch in chans:
            ch.stop()
