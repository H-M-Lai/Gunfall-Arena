# Gunfall Arena

Gunfall Arena is a Christmas-themed 2D action game built with Python and Pygame.  
The game features two playable levels with different objectives, including elimination combat and flag capture, supported by visual and audio special effects.

## Features

- Christmas-themed game environment
- Storyboard and menu system
- Two different gameplay levels
- Level 1: Elimination mode
- Level 2: Flag Capture mode
- AI-controlled enemies
- Background music and sound effects
- Visual effects such as snowfall, hit particles, reload ring, and spawn shield
- Post-game summary statistics

## Project Structure

- `main.py` - main entry point and game flow controller
- `app_config.py` - shared constants, paths, and configuration
- `audio_manager.py` - menu and background music management
- `sfx_manager.py` - gameplay sound effects
- `menu_screens.py` - menu and selection screen rendering
- `ui_helpers.py` - reusable UI drawing helpers
- `storyboard.py` - storyboard scenes and transitions
- `Level_1.py` - Level 1 gameplay logic
- `Level_2.py` - Level 2 gameplay logic
- `drops.py` - pickups and drop system

## Requirements

- Python 3.x
- Pygame

## How to Run

1. Install Python 3.x
2. Install Pygame:
   ```bash
   pip install pygame
