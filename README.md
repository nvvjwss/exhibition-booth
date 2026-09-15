# Exhibition Booth

Robot-driven slide control panel for Siam.AI's booth. Tap a topic on the iPad: the Alpha Mini robot speaks about it, and the projector jumps to the matching slide.

## Structure

- `app.py`: Flask server, topic list, triggers robot audio + slide jump
- `impress_controller.py`: drives LibreOffice Impress via UNO
- `templates/`, `static/`: iPad web UI
- `booth_content/`: per-topic voice audio
- `decks/`: PowerPoint decks
- `start.sh`: connects robot, mirrors screen, starts everything

## Requirements

- Linux + Alpha Mini robot over USB
- Python 3, `adb`, `scrcpy` (optional), LibreOffice
- Deskreen AppImage in `~/Downloads/`
- PowerPoint deck at `~/Downloads/siam.ai powerpoint.pptx` (or set `DECK_PATH`)

## Install

```bash
git clone https://github.com/nvvjwss/exhibition-booth.git
cd exhibition-booth
pip install -r requirements.txt
```

Open the deck in LibreOffice Impress before starting the app.

## Usage

```bash
./start.sh
```

Then: open the Deskreen link on the display device and share the Impress window; connect the Bluetooth speaker if used.

### Env vars

- `AUDIO_MODE`: `both` (default) / `robot` / `screen`
- `ROBOT_BASE_URL`: default `http://localhost:8080`
- `DECK_PATH`: default `~/Downloads/siam.ai powerpoint.pptx`
