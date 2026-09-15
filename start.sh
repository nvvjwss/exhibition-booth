#!/usr/bin/env bash
# Exhibition Booth — one-shot startup script
# Connects the robot (081→191, per project_robot_hardware_status memory), forwards port 8080,
# clears stale LibreOffice locks, and launches app.py.
# Run: ./start.sh   (from anywhere; script cd's into its own directory)
set -uo pipefail
cd "$(dirname "$0")"

ROBOT_SERIAL="EAB001UBT50000191"
ROBOT_PKG="com.siamlab.alphamini"
BOOTH_PORT=5002
ROBOT_PORT=8080
AUDIO_MODE="${AUDIO_MODE:-both}"    # override: AUDIO_MODE=robot ./start.sh (robot speaker only)

log() { echo "[start.sh] $*"; }
die() { echo "[start.sh] ERROR: $*" >&2; exit 1; }

# ---------------------------------------------------------------
# 1. Make sure the robot is visible over USB first
# ---------------------------------------------------------------
log "Checking for robot over USB ($ROBOT_SERIAL)..."
if ! adb devices -l | grep -q "$ROBOT_SERIAL.*device "; then
    die "Robot $ROBOT_SERIAL not found over USB. Plug it in via USB first, then re-run."
fi

# ---------------------------------------------------------------
# 2. Battery check
# ---------------------------------------------------------------
BATTERY=$(adb -s "$ROBOT_SERIAL" shell dumpsys battery | grep -oP 'level: \K\d+')
log "Battery: ${BATTERY:-unknown}%"
if [ -n "${BATTERY:-}" ] && [ "$BATTERY" -lt 20 ]; then
    die "Battery too low ($BATTERY%). Charge before running the booth."
fi

# ---------------------------------------------------------------
# 3. Get robot WiFi IP, switch to WiFi ADB (retry — this step is flaky on timing)
# ---------------------------------------------------------------
ROBOT_IP=$(adb -s "$ROBOT_SERIAL" shell ip addr show wlan0 | grep -oP 'inet \K[\d.]+')
[ -n "$ROBOT_IP" ] || die "Robot has no WiFi IP — connect it to WiFi from the robot's screen first."
log "Robot WiFi IP: $ROBOT_IP"

adb -s "$ROBOT_SERIAL" tcpip 5555 >/dev/null
for i in 1 2 3 4 5; do
    if adb connect "$ROBOT_IP:5555" 2>&1 | grep -q "connected"; then
        log "Connected to $ROBOT_IP:5555 over WiFi (attempt $i)"
        break
    fi
    log "Connect attempt $i failed, retrying in 1s..."
    sleep 1
    [ "$i" -eq 5 ] && die "Could not connect to robot over WiFi after 5 tries."
done
ROBOT_TARGET="$ROBOT_IP:5555"

# ---------------------------------------------------------------
# 4. Relaunch the app cleanly (force-stop first, avoids session-id collisions)
# ---------------------------------------------------------------
log "Restarting SiamAI app on robot..."
adb -s "$ROBOT_TARGET" shell am force-stop "$ROBOT_PKG"
sleep 1
adb -s "$ROBOT_TARGET" shell "monkey -p $ROBOT_PKG -c android.intent.category.LAUNCHER 1" >/dev/null

# ---------------------------------------------------------------
# 5. Port forward + verify
# ---------------------------------------------------------------
log "Forwarding tcp:$ROBOT_PORT..."
adb -s "$ROBOT_TARGET" forward "tcp:$ROBOT_PORT" "tcp:$ROBOT_PORT"

sleep 2  # give CameraServer a moment to come up after relaunch
for i in 1 2 3 4 5; do
    if curl -s -m 2 "http://localhost:$ROBOT_PORT/ping" | grep -q pong; then
        log "Robot HTTP server responding (pong)."
        break
    fi
    log "Ping attempt $i failed, retrying in 2s..."
    sleep 2
    [ "$i" -eq 5 ] && die "Robot not responding on :$ROBOT_PORT/ping after 5 tries. Check the app opened on-screen."
done

# ---------------------------------------------------------------
# 5b. Launch scrcpy to mirror the robot screen
# ---------------------------------------------------------------
if command -v scrcpy >/dev/null 2>&1; then
    log "Launching scrcpy..."
    pgrep -af "scrcpy" >/dev/null 2>&1 && pkill -9 -f "scrcpy" && sleep 1
    nohup scrcpy -s "$ROBOT_TARGET" > /tmp/scrcpy.log 2>&1 &
    log "scrcpy launched (PID $!)."
else
    log "WARNING: scrcpy not found on PATH — skipped."
fi

# ---------------------------------------------------------------
# 6. Clear stale LibreOffice locks (from any previous kill -9)
# ---------------------------------------------------------------
log "Clearing stale LibreOffice locks..."
rm -f ~/.config/libreoffice/4/.lock decks/.~lock*.pptx# 2>/dev/null

# ---------------------------------------------------------------
# 7. Kill any leftover app.py / soffice from a previous run
# ---------------------------------------------------------------
for pid in $(pgrep -f "python3 app.py" 2>/dev/null || true); do
    if [ "$(readlink "/proc/$pid/cwd" 2>/dev/null)" = "$(pwd)" ]; then
        log "Killing stale exhibition-booth process (PID $pid)..."
        kill -9 "$pid" 2>/dev/null
    fi
done
pkill -9 soffice.bin 2>/dev/null || true
sleep 1

# ---------------------------------------------------------------
# 8. Launch app.py
# ---------------------------------------------------------------
log "Starting app.py (AUDIO_MODE=$AUDIO_MODE)..."
AUDIO_MODE="$AUDIO_MODE" nohup python3 app.py > /tmp/booth_app.log 2>&1 &
APP_PID=$!
log "app.py PID: $APP_PID (log: /tmp/booth_app.log)"

log "Waiting for Flask to come up..."
for i in $(seq 1 20); do
    CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:$BOOTH_PORT/" 2>/dev/null)
    if [ "$CODE" = "200" ]; then
        log "exhibition-booth is up: http://localhost:$BOOTH_PORT/"
        break
    fi
    sleep 1
    [ "$i" -eq 20 ] && die "app.py did not come up after 20s. Check /tmp/booth_app.log"
done

# ---------------------------------------------------------------
# 9. Launch Deskreen (window still needs manual interaction — see below)
# ---------------------------------------------------------------
log "Launching Deskreen..."
pgrep -af deskreen >/dev/null 2>&1 && pkill -9 -f deskreen && sleep 1
DESKREEN_APPIMAGE=$(ls ~/Downloads/deskreen-ce-*.AppImage 2>/dev/null | head -1)
if [ -n "$DESKREEN_APPIMAGE" ]; then
    nohup "$DESKREEN_APPIMAGE" --no-sandbox > /tmp/deskreen.log 2>&1 &
    log "Deskreen launched (PID $!). Its window should appear on screen now."
else
    log "WARNING: no deskreen-ce-*.AppImage found in ~/Downloads — skipped."
fi

# ---------------------------------------------------------------
# 10. Manual steps that cannot be automated (GUI-only)
# ---------------------------------------------------------------
cat <<'EOF'

======================================================================
DONE. Robot + Flask server + Deskreen are running. Two things still need YOU:

  1. Deskreen window is open on screen — read the URL/QR shown there
     (changes every launch) and open it in Chrome on the Android display,
     then click "Select App Window to Share" and pick the Impress window.
     (this cannot be scripted — GUI-only)

  2. If using an external speaker, connect it (AUDIO_MODE=both/screen):
       bluetoothctl connect 50:1B:6A:ED:55:B0
       pactl set-default-sink bluez_output.50_1B_6A_ED_55_B0.1
======================================================================
EOF
