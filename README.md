# Suyarima-sama

A small Python/Pygame digital-rain visual. The scene and supplied looping video start immediately; hold **Space** to summon spaced, pixel-style Python snippets with numeric code in a green terminal glow.

## Run

Use Python 3.10 or newer. On macOS or Linux, paste this into Terminal to download and run the app:

```sh
git clone https://github.com/djambuken/suyarima-sama.git
cd suyarima-sama
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python suyarima-sama.py
```

On Windows, activate the environment with `.venv\Scripts\activate` instead of `source .venv/bin/activate`.

The supplied video is at `assets/loop.mp4` (H.264 MP4 recommended) and loops automatically. Without it, the procedural animated background remains active. OpenCV is only used for video playback.

The window is resizable and titled **suyarima-sama**. The top-left HUD shows **SPACE BAR = NUMBERS**; hold **Space** for a stream of falling code, or tap for a small burst. Close the window to quit.

Replace `assets/loop.mp4` to use different footage.
