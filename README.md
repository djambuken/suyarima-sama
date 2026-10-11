# Suyarima-sama

ANIME LOOP + PYTHON

The app centers on its looping video, compact HUD, and Space-bar code effect. Hold **Space** to summon widely spaced, pixel-style Python snippets with numeric characters in a green terminal glow.

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

The app plays `assets/loop.mp4` as its background when available. If the video or OpenCV is unavailable, it uses a dark fallback background. OpenCV handles video playback.

The resizable window is titled **suyarima-sama**. The top-left HUD reads **SPACE BAR = CODE**. Tap **Space** for a small burst or hold it to summon code continuously. Close the window to quit.

Replace `assets/loop.mp4` to use different footage.
