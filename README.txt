FONT BEING USED

Century Gothic
- Used for the small hover description bar text on the main menu.

Futura Now Headline Condensed Black
- Used for major menu headings and main menu button labels.

Avenir Next Condensed Bold
- Used as the general in-game UI font for buttons, labels, player setup text, and other interface text.


PROJECT STRUCTURE

main.py
- Main entry point of the game.
- Handles the main loop, game state flow, event handling, and switching between menus and levels.

app_config.py
- Shared configuration file.
- Stores asset paths, colors, screen size, state names, font helpers, and shared UI/game constants.

ui_helpers.py
- Shared UI drawing helper file.
- Contains reusable text, button, input box, outline, logo, and small UI helper functions.

menu_screens.py
- Menu and setup screen rendering file.
- Draws the main menu, level select, player setup, history page, and controls/settings page.

audio_manager.py
- Handles launcher and menu audio.
- Controls menu click sound, menu/storyboard/level background music, smoother music looping, and global menu-side audio behavior.

sfx_manager.py
- Handles in-game sound effects.
- Used by gameplay files for handgun and non-handgun gunshots, reloads, walking, hits, respawn, capture, and other gameplay SFX.

storyboard.py
- Controls the story / intro sequence.
- Handles story pages, snow overlay, fade effects, and skip behavior.

Level_1.py
- Level 1 gameplay file.
- Contains the elimination mode logic, player and AI behavior, combat, respawn flow, HUD, and post-game summary for Level 1.

Level_2.py
- Level 2 gameplay file.
- Contains the flag capture mode logic, player and AI behavior, capture system, HUD, and post-game summary for Level 2.

drops.py
- Handles item / pickup spawning and collection.
- Used for weapon boxes and ability pickups.

resize_and_scale.py
- Utility script for resizing or scaling game images.

resize_abilities.py
- Utility script for resizing ability-related assets.

Assets/
- Stores all game resources such as backgrounds, sounds, fonts, characters, guns, story images, and ability images.
