# Gunfall Arena

Gunfall Arena is a Christmas-themed 2D action game built with Python and Pygame. It combines a full menu-and-story flow with two gameplay modes, visual effects, and responsive audio feedback.

## Overview

The project includes:

- a main menu, level select, controls page, and player setup flow
- a storyboard introduction with themed presentation
- two playable levels with different objectives
- AI-controlled snowman enemies
- visual and audio effects for combat, movement, and UI feedback
- post-match summary screens with player statistics

## Game Modes

### Level 1: Elimination

Players must knock the enemy snowmen off the arena until their lives are depleted.

### Level 2: Flag Capture

Players compete to capture flag objectives before the enemy team reaches the score target.

## Highlights

- Christmas-themed environments and assets
- snowfall, hit particles, floating hit text, dust, wind streaks, spawn shield bubble, and reload ring
- separate background music for menu, storyboard, Level 1, and Level 2
- weapon-specific firing sounds for handguns and non-handguns
- AI behavior, respawn logic, pickups, weapon handling, and end-game summaries

## Tech Stack

- Python
- Pygame

## Project Structure

- `main.py` - main entry point, game loop, and state flow
- `app_config.py` - shared constants, paths, fonts, and configuration
- `menu_screens.py` - menu, level select, player setup, and settings rendering
- `ui_helpers.py` - reusable UI drawing helpers
- `storyboard.py` - story pages, transitions, and snow overlay
- `audio_manager.py` - menu click sound and background music control
- `sfx_manager.py` - gameplay sound effect management
- `Level_1.py` - elimination mode gameplay logic
- `Level_2.py` - flag capture mode gameplay logic
- `drops.py` - pickup and drop system
- `resize_and_scale.py` - utility script for resizing or scaling game images
- `resize_abilities.py` - utility script for resizing ability assets
- `Assets/` - game art, audio, fonts, and other runtime assets

## Fonts Used

- `Century Gothic` - used for the small hover description text on the main menu
- `Futura Now Headline Condensed Black` - used for major menu headings and main menu button labels
- `Avenir Next Condensed Bold` - used as the general in-game UI font for buttons, labels, and player setup text

## Requirements

- Python 3.x
- Pygame

## Installation

Install Pygame:

```bash
pip install pygame
```

## How to Run

Start the game with:

```bash
python main.py
```

## Notes

- Controls can be adjusted from the in-game controls page.
- Some external keyboards may handle multi-key input combinations differently.
- The repository keeps the runtime assets needed to play the game and excludes oversized raw/source asset folders.
