# Exhibition Booth

A robot-driven slide presentation control panel for Siam.AI's exhibition booth.

Visitors tap a topic button on an iPad. Each tap does two things at once:

1. The Alpha Mini humanoid robot standing next to the booth **speaks an explanation** of that topic out loud (with matching gestures).
2. The projector/TV screen next to it **jumps to the matching PowerPoint slide** automatically.

The iPad is just a remote: the robot and the slides react almost instantly to whatever topic is picked, with no visitor training needed.

## How it works

- `app.py`: Flask server. Holds the list of topics (`TOPICS`), serves the web UI, and on each button press: tells the robot to play the topic's audio/gesture (`ROBOT_BASE_URL`) and tells LibreOffice Impress to jump to the topic's slide.
- `impress_controller.py`: drives a running LibreOffice Impress instance via the UNO API to jump slides.
- `templates/index.html`, `static/`: the iPad-facing web UI (HTML/CSS/JS).
- `booth_content/`: pre-rendered voice audio (mp3/wav) per topic, played on the robot or through an external speaker.
- `decks/`: the PowerPoint decks that Impress displays.
- `start.sh`: one-shot script that connects to the robot over USB→WiFi ADB, relaunches the robot app, mirrors its screen with scrcpy, launches Deskreen (for screen-sharing the slide deck), and starts `app.py`.

## Requirements

- Linux machine with the Alpha Mini robot connected over USB
- Python 3 + pip
- `adb` (`android-tools-adb` / `platform-tools`)
- `scrcpy` (optional, for mirroring the robot's screen)
- LibreOffice (Impress): used to display and drive the slide deck
- A [Deskreen](https://deskreen.com/) AppImage in `~/Downloads/`: used to screen-share the Impress window to the venue's display
- A PowerPoint deck at `~/Downloads/siam.ai powerpoint.pptx` (or set `DECK_PATH`)

## Install

```bash
git clone https://github.com/nvvjwss/exhibition-booth.git
cd exhibition-booth
pip install -r requirements.txt
```

Make sure `adb`, `scrcpy`, and LibreOffice are installed and on your `PATH` (e.g. on Debian/Ubuntu: `sudo apt install android-tools-adb scrcpy libreoffice`).

Open LibreOffice Impress with the deck you want to present (`~/Downloads/siam.ai powerpoint.pptx` by default) before starting the app: `impress_controller.py` connects to an already-running Impress instance.

## Usage

Plug the robot in over USB, then run:

```bash
./start.sh
```

This will:
1. Check the robot is connected and charged
2. Switch the robot connection from USB to WiFi ADB
3. Relaunch the robot app
4. Forward the robot's HTTP port and confirm it's responding
5. Launch `scrcpy` to mirror the robot's screen (if installed)
6. Start `app.py` (the Flask server), reachable at `http://localhost:5002`
7. Launch Deskreen so you can screen-share the Impress window to the venue's display

Two manual steps remain after that (shown at the end of the script):
- Open the Deskreen URL/QR shown on screen from the venue's display device and select the Impress window to share
- Connect the external Bluetooth speaker, if using one

### Environment variables

- `AUDIO_MODE`: `both` (default), `robot` (robot speaker only), or `screen` (external speaker only)
- `ROBOT_BASE_URL`: base URL of the robot's HTTP server (default `http://localhost:8080`)
- `DECK_PATH`: path to the PowerPoint deck (default `~/Downloads/siam.ai powerpoint.pptx`)

Example:
```bash
AUDIO_MODE=robot ./start.sh
```
