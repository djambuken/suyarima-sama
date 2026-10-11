# Suyarima-sama

A small Python/Pygame visual inspired by the supplied image: a charcoal field of drifting, outlined purple and green geometry. The scene and supplied looping video start immediately when the app opens. Hold **Space** to summon a continuous cascade of glowing red digits.

## Run

1. Use Python 3.10 or newer.
2. Install the dependencies with `python -m pip install -r requirements.txt`.
3. The supplied video is at `assets/loop.mp4` (H.264 MP4 recommended) and loops automatically. Without it, the procedural animated background remains active. OpenCV is only used for video playback.
4. Start the app with `python suyarima-sama.py`.
The window is resizable and titled **suyarima-sama**. The top-left HUD shows **SPACE BAR = NUMBERS**; hold **Space** for a stream of red falling numbers, or tap for a small burst. Close the window to quit.

The reference image's style is recreated with procedural shapes. Replace `assets/loop.mp4` to use different footage.
