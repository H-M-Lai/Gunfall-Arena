import os
import pygame
import numpy as np

import sfx_manager as sfx
from app_config import (
    CLICK_SOUND_PATH,
    MENU_BGM_PATH,
    STORYBOARD_BGM_PATH,
    LEVEL_1_BGM_PATH,
    LEVEL_2_BGM_PATH,
    MAIN_MENU,
    STORYBOARD,
    LEVEL_SELECT,
    MODE_SELECT,
    HISTORY_PAGE,
    CONTROL_PAGE,
    LEVEL_1_PAGE,
    LEVEL_2_PAGE,
)


class AudioManager:
    def __init__(self):
        self._click_sound = None
        self._current_music_key = None
        self._current_music_mode = None
        self._loop_bgm_cache = {}
        self._bgm_channel = None

    def preload_ui_audio(self):
        self._ensure_mixer_ready()
        self._load_click_sfx()
        self._get_bgm_channel()

    def _ensure_mixer_ready(self):
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            return True
        except pygame.error:
            return False

    def _load_click_sfx(self):
        if self._click_sound is not None:
            return
        if not os.path.exists(CLICK_SOUND_PATH):
            return
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            raw_click = pygame.mixer.Sound(CLICK_SOUND_PATH)
            self._click_sound = self._trim_leading_silence(raw_click)
            self._click_sound.set_volume(0.6)
        except pygame.error:
            self._click_sound = None

    def _get_bgm_channel(self):
        if not self._ensure_mixer_ready():
            return None
        # A dedicated channel avoids some of pygame.mixer.music's rougher loop restarts.
        if self._bgm_channel is None:
            self._bgm_channel = pygame.mixer.Channel(7)
        return self._bgm_channel

    def _trim_sound_edges(
        self, sound, silence_ratio=0.02, min_threshold=200, trim_start=True, trim_end=False
    ):
        try:
            arr = pygame.sndarray.array(sound)
            if arr.ndim > 1:
                mono = np.max(np.abs(arr), axis=1)
            else:
                mono = np.abs(arr)
            if mono.size == 0:
                return sound

            threshold = max(min_threshold, int(mono.max() * silence_ratio))
            non_silent = np.flatnonzero(mono > threshold)
            if non_silent.size == 0:
                return sound

            start_idx = int(non_silent[0]) if trim_start else 0
            end_idx = int(non_silent[-1]) + 1 if trim_end else mono.size

            if start_idx <= 0 and end_idx >= mono.size:
                return sound

            trimmed = arr[start_idx:end_idx]
            if trimmed.size == 0:
                return sound
            return pygame.sndarray.make_sound(trimmed.copy())
        except (pygame.error, ValueError):
            return sound

    def _trim_leading_silence(self, sound, silence_ratio=0.02, min_threshold=200):
        return self._trim_sound_edges(
            sound,
            silence_ratio=silence_ratio,
            min_threshold=min_threshold,
            trim_start=True,
            trim_end=False,
        )

    def _load_loop_bgm(self, track_path):
        if track_path in self._loop_bgm_cache:
            return self._loop_bgm_cache[track_path]
        if not os.path.exists(track_path) or not self._ensure_mixer_ready():
            return None
        try:
            # Trim quiet padding once so repeating tracks loop more cleanly.
            sound = pygame.mixer.Sound(track_path)
            sound = self._trim_sound_edges(sound, trim_start=True, trim_end=True)
            self._loop_bgm_cache[track_path] = sound
            return sound
        except pygame.error:
            self._loop_bgm_cache[track_path] = None
            return None

    def play_click(self, sound_enabled):
        if not sound_enabled:
            return
        self._load_click_sfx()
        if self._click_sound is not None:
            self._click_sound.play()

    def apply_sound_enabled(self, level_1, level_2, sound_enabled):
        level_1.set_sound_enabled(sound_enabled)
        level_2.set_sound_enabled(sound_enabled)

    def _play_bgm(self, track_path, music_key, volume=0.55):
        if self._current_music_key == music_key and self._current_music_mode == "music":
            if not pygame.mixer.music.get_busy():
                pygame.mixer.music.play(-1, fade_ms=350)
            return
        if not self._ensure_mixer_ready() or not os.path.exists(track_path):
            return
        try:
            channel = self._get_bgm_channel()
            if channel is not None:
                channel.fadeout(250)
            pygame.mixer.music.load(track_path)
            pygame.mixer.music.set_volume(volume)
            pygame.mixer.music.play(-1, fade_ms=350)
            self._current_music_key = music_key
            self._current_music_mode = "music"
        except pygame.error:
            self._current_music_key = None
            self._current_music_mode = None

    def _play_loop_bgm(self, track_path, music_key, volume=0.5):
        channel = self._get_bgm_channel()
        sound = self._load_loop_bgm(track_path)
        if channel is None or sound is None:
            self._play_bgm(track_path, music_key, volume=volume)
            return

        if self._current_music_key == music_key and self._current_music_mode == "sound":
            if not channel.get_busy():
                channel.play(sound, loops=-1, fade_ms=350)
            channel.set_volume(volume)
            return

        pygame.mixer.music.fadeout(250)
        channel.stop()
        channel.set_volume(volume)
        channel.play(sound, loops=-1, fade_ms=350)
        self._current_music_key = music_key
        self._current_music_mode = "sound"

    def stop_bgm(self):
        if not pygame.mixer.get_init():
            self._current_music_key = None
            self._current_music_mode = None
            return
        pygame.mixer.music.fadeout(200)
        channel = self._get_bgm_channel()
        if channel is not None:
            channel.fadeout(200)
        self._current_music_key = None
        self._current_music_mode = None

    def sync_music_to_state(self, music_enabled, game_state):
        if not music_enabled:
            self.stop_bgm()
            return
        if game_state == STORYBOARD:
            self._play_loop_bgm(STORYBOARD_BGM_PATH, "storyboard")
        elif game_state == LEVEL_1_PAGE:
            self._play_loop_bgm(LEVEL_1_BGM_PATH, "level_1", volume=0.55)
        elif game_state == LEVEL_2_PAGE:
            self._play_loop_bgm(LEVEL_2_BGM_PATH, "level_2", volume=0.55)
        elif game_state in (
            MAIN_MENU,
            LEVEL_SELECT,
            MODE_SELECT,
            HISTORY_PAGE,
            CONTROL_PAGE,
        ):
            self._play_loop_bgm(MENU_BGM_PATH, "menu")
        else:
            self.stop_bgm()

    def stop_active_level_audio(self):
        if pygame.mixer.get_init():
            sfx.stop_all()
