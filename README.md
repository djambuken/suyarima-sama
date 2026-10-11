# Suyarima-sama

A small Python/Pygame visual inspired by the supplied image: a charcoal field of drifting, outlined purple and green geometry. Enter the access code to open the scene. Add a video loop as a background, then hold **Space** to summon a continuous cascade of glowing red digits.

## Run

1. Use Python 3.10 or newer.
2. Install the dependencies with `python -m pip install -r requirements.txt`.
3. Optionally put a video at `assets/loop.mp4` (H.264 MP4 recommended). The video loops automatically; without it, the animated abstract background remains active. OpenCV is only used for video playback.
4. Start the app with `python main.py`.
5. The default access code is `suyarima`. Set `SUYARIMA_CODE` before launch to choose another local code.

The window is resizable. Press **Enter** to submit the code and **Esc** to quit from the entry screen. After unlocking, hold **Space** for a stream of red falling numbers; a tap summons a small burst.

The reference image was not available as a local asset in the repository, so its style is recreated with procedural shapes. Place the supplied loop video in `assets/loop.mp4` to use your own footage.
