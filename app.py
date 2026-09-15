# app.py — กดปุ่ม -> ไปสไลด์ที่กำหนด + เล่นเสียงบนหุ่น
# รัน: python3 app.py

import os
import subprocess
import threading
import time
from pathlib import Path

import requests
from flask import Flask, jsonify, render_template

import impress_controller as impress

app = Flask(__name__)

BOOTH_CONTENT = Path(__file__).parent / "booth_content"
ROBOT_BASE_URL = os.environ.get("ROBOT_BASE_URL", "http://localhost:8080")
ROBOT_AUDIO_URL = ROBOT_BASE_URL + "/play_audio"
ROBOT_EMOTE_URL = ROBOT_BASE_URL + "/emote"
ROBOT_STOP_URL = ROBOT_BASE_URL + "/stop"

# "screen" = เล่นเสียงผ่านลำโพงภายนอกที่เสียบกับเครื่องนี้โดยตรงเท่านั้น (หุ่นไม่ขยับท่าทางประกอบเพราะไม่ได้รับเสียง)
# "robot"  = ส่งเสียงไปเล่นที่ลำโพงหุ่นเท่านั้น (หุ่นขยับท่าทางประกอบได้ปกติ)
# "both"   = เล่นทั้งสองที่พร้อมกัน (ลำโพงนอกดังขึ้น + หุ่นยังขยับท่าทางประกอบได้ปกติ)
AUDIO_MODE = os.environ.get("AUDIO_MODE", "both")
DECK_PATH = os.environ.get("DECK_PATH", str(Path(__file__).parent / "decks" / "siam.ai powerpoint.pptx"))
IDLE_SLIDE = 1

_desktop = None  # เก็บไว้ใช้ซ้ำ ไม่เชื่อมต่อ UNO ใหม่ทุกครั้งที่กดปุ่ม

_current_audio_proc = None  # Popen ของ ffplay ตอนนี้ (โหมด screen เท่านั้น)
_sequence_generation = 0  # เพิ่มเลขทุกครั้งที่กดปุ่มใหม่/กดหยุด เพื่อยกเลิก sequence thread เก่าที่ยังรันค้างอยู่
_sequence_lock = threading.Lock()


def _bump_generation():
    global _sequence_generation
    with _sequence_lock:
        _sequence_generation += 1
        return _sequence_generation


def stop_playback():
    """หยุดเสียง/สไลด์ที่กำลังเล่นอยู่ ไม่ว่าจะเป็นเสียงเดี่ยวหรือ sequence"""
    generation = _bump_generation()  # ทำให้ loop ของ play_sequence ที่รันอยู่ (ถ้ามี) เช็คแล้วออกจาก loop ทันที

    # /stop ฝั่งแอปหุ่น: หยุดเสียง (audioPlayer/currentPlayer) + ยกเลิก gesture/action ที่กำลังเล่น + ยืนตรง
    # เรียกเสมอไม่ว่า AUDIO_MODE จะเป็นอะไร เพราะท่าทาง/gesture วิ่งอยู่บนหุ่นเสมอ
    try:
        requests.post(ROBOT_STOP_URL, timeout=5)
    except requests.exceptions.RequestException:
        pass

    # หยุด ffplay บนเครื่องนี้เสมอ (เผื่อ introduce_muja ที่เล่นผ่านลำโพงเครื่องนี้เสมอไม่ว่า AUDIO_MODE จะเป็นอะไร)
    global _current_audio_proc
    if _current_audio_proc is not None and _current_audio_proc.poll() is None:
        _current_audio_proc.terminate()
    subprocess.run(["pkill", "-f", "ffplay"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    return generation


def get_desktop():
    global _desktop
    if _desktop is None:
        ctx = impress.connect()
        _desktop = impress.get_desktop(ctx)
    return _desktop

TOPICS = [
    {"id": "introduce_muja", "section": "About A1", "label": "Introducing A1", "emoji": "🤖", "image": "introducing-a1.png", "emote": "introduce_muja"},
    {"id": "who_is_siamai", "section": "About Siam AI", "label": "Who is Siam.AI", "emoji": "🏢", "cover_image": "who-is-siamai.jpg", "slide": 2},
    {"id": "our_vision", "section": "About Siam AI", "label": "Our Vision", "emoji": "🔭", "cover_image": "our-vision.png", "slide": 3},
    {"id": "siam_ai_landmark", "section": "Siam AI Landmark", "label": "Siam AI Landmark", "emoji": "📍", "cover_image": "siam-ai-landmark.png", "slide": 62},
    {"id": "cloud_service_model", "section": "Product and Services", "label": "Cloud service model", "emoji": "☁️", "image": "cloud-service-model.png", "sequence": True},
    {"id": "siam_gpt", "section": "Product and Services", "label": "SIAM GPT", "emoji": "💬", "image": "siam-gpt.png", "sequence": True},
    {"id": "compute_we_have", "section": "Product and Services", "label": "Compute we have", "emoji": "🖥️", "image": "compute-we-have.png", "sequence": True},
    {"id": "network_storage", "section": "Product and Services", "label": "High performance network and storage", "emoji": "🌐", "image": "network-storage.jpeg", "sequence": True},
    {"id": "data_center_partners", "section": "Data center partners", "label": "Data center partners", "emoji": "🤝", "cover_image": "data-center-partners.jpg", "slide": 26},
    {"id": "robot_we_have", "section": "Robotics", "label": "Robot we have", "emoji": "🦿", "image": "robot-we-have.png", "slide": 37},
    {"id": "galbot_g1", "section": "Robotics", "label": "Galbot G1", "emoji": "🦾", "image": "galbot-g1.png", "sequence": True},
    {"id": "unitree_g1", "section": "Robotics", "label": "Unitree G1", "emoji": "🚶", "image": "unitree-g1.png", "sequence": True},
    {"id": "unitree_b2", "section": "Robotics", "label": "Unitree B2 and B2-W", "emoji": "🐕", "image": "unitree-b2.png", "slide": 45},
    {"id": "ai_innovations", "section": "Others", "label": "AI innovations and Use cases", "emoji": "💡", "cover_image": "ai-innovations.jpg", "sequence": True},
]
TOPICS_BY_ID = {t["id"]: t for t in TOPICS}


# section ที่ควรเป็นการ์ด hero สีฟ้าใหญ่ (แม้จะมีปุ่มเดียว section อื่นที่มีปุ่มเดียว เช่น
# "Data center partners" ให้เป็นการ์ดขาวปกติ ไม่ใช่ hero)
FEATURED_SECTIONS = {"About A1", "Others"}

# section ที่ควรไฮไลต์เป็นการ์ดไล่สีฟ้าเหมือน hero แต่ขนาดปกติ (ไม่ใช่การ์ดใหญ่)
ACCENT_SECTIONS = {"Product and Services"}


def sections():
    grouped = {}
    for t in TOPICS:
        grouped.setdefault(t["section"], []).append(t)
    all_sections = [{"title": title, "topics": topics} for title, topics in grouped.items()]
    for i, s in enumerate(all_sections):
        s["num"] = i + 1
        s["featured"] = s["title"] in FEATURED_SECTIONS
        s["accent"] = s["title"] in ACCENT_SECTIONS
    return all_sections


# กลุ่มคอลัมน์ตายตัว (ไม่ให้ browser auto-balance สูง/ต่ำเอง) — คอลัมน์ 1: About A1 + About Siam AI + Siam AI Landmark,
# คอลัมน์ 2: Product and Services + Data center partners, คอลัมน์ 3: Robotics + Others
COLUMN_GROUPS = [[0, 1, 2], [3, 4], [5, 6]]


def sections_by_column():
    all_sections = sections()
    return [[all_sections[i] for i in group] for group in COLUMN_GROUPS]


def play_audio_file(path: Path, generation: int, to_robot: bool = None, to_screen: bool = None):
    if not path.exists():
        return
    # เช็คก่อนยิงเสียงออกจริงว่ายังเป็นปุ่มล่าสุดอยู่ไหม กันกรณีกด 2 ปุ่มติดกันเร็วๆ แล้ว thread
    # ของปุ่มเก่าเพิ่งจะมาถึงตอนนี้ (หลังปุ่มใหม่ส่ง /stop + เสียงของตัวเองไปแล้ว) จนเสียงทับ/สลับกัน
    if generation != _sequence_generation:
        return
    # ปกติอิงตาม AUDIO_MODE แต่บางจุด (เช่น introduce_muja) จะบังคับปลายทางเฉพาะเจาะจงแทน
    if to_robot is None:
        to_robot = AUDIO_MODE in ("robot", "both")
    if to_screen is None:
        to_screen = AUDIO_MODE in ("screen", "both")
    # ส่งไปหุ่น เพื่อให้หุ่นขยับท่าทางประกอบเสียงพูดได้ (onAudioStart/onAudioStop)
    if to_robot:
        try:
            requests.post(ROBOT_AUDIO_URL, data=path.read_bytes(),
                          headers={"Content-Type": "audio/mpeg"}, timeout=10)
        except requests.exceptions.RequestException:
            pass
    # เล่นผ่านลำโพงบลูทูธ/ภายนอกที่เสียบกับเครื่องนี้ — ให้เสียงดังชัดกว่าลำโพงหุ่น
    if to_screen:
        global _current_audio_proc
        _current_audio_proc = subprocess.Popen(
            ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", str(path)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )


def play_sound(topic_id: str, generation: int):
    voice_path = BOOTH_CONTENT / topic_id / "voice.mp3"
    play_audio_file(voice_path, generation)


def audio_duration(path: Path) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True,
    )
    try:
        return float(result.stdout.strip())
    except ValueError:
        return 5.0


SEQUENCES = {
    "cloud_service_model": [
        (6, "slide_1.mp3"),
        (7, "slide_2.mp3"),
        (8, "slide_3.mp3"),
        (9, "slide_4.mp3"),
        (10, "slide_5.mp3"),
        (11, "slide_6.mp3"),
        (12, "slide_7.mp3"),
        (13, "slide_8.mp3"),
        (14, "slide_9.mp3"),
    ],
    "compute_we_have": [
        (17, "slide_1.mp3"),
        (18, "slide_2.mp3"),
        (19, "slide_3.mp3"),
        (20, "slide_4.mp3"),
        (21, "slide_5.mp3"),
        (22, "slide_6.mp3"),
    ],
    "network_storage": [
        (23, "slide_1.mp3"),
        (24, "slide_2.mp3"),
    ],
    "siam_gpt": [
        (27, "slide_1.mp3"),
        (29, "slide_2.mp3"),
        (30, "slide_3.mp3"),
    ],
    "galbot_g1": [
        (38, "slide_1.mp3"),
        (39, "slide_2.mp3"),
        (40, "slide_3.mp3"),
        (41, "slide_4.mp3"),
    ],
    "unitree_g1": [
        (42, "slide_1.mp3"),
        (43, "slide_2.mp3"),
    ],
    "ai_innovations": [
        (54, "slide_1.mp3"),
        (53, "slide_2.mp3"),
    ],
}


def play_sequence(topic_id: str, generation: int):
    sequence_dir = BOOTH_CONTENT / topic_id
    sequence = SEQUENCES[topic_id]
    slides = [slide_num for slide_num, _ in sequence]
    durations = [audio_duration(sequence_dir / name) for _, name in sequence]
    cumulative = []
    total = 0.0
    for d in durations:
        total += d
        cumulative.append(total)

    if generation != _sequence_generation:
        return  # ถูกกดปุ่มอื่นแทรกระหว่างรอ generation นี้ก่อนเริ่มเล่นจริง

    impress.open_and_goto(get_desktop(), DECK_PATH, slides[0])
    play_audio_file(sequence_dir / "full.mp3", generation)

    start_time = time.time()
    for i in range(1, len(slides)):
        remaining = cumulative[i - 1] - (time.time() - start_time)
        if remaining > 0:
            time.sleep(remaining)
        if generation != _sequence_generation:
            return  # ถูกกดหยุด หรือมีปุ่มอื่นถูกกดแทรกระหว่างนี้ ให้เลิกเปลี่ยนสไลด์ต่อ
        impress.open_and_goto(get_desktop(), DECK_PATH, slides[i])


@app.route("/")
def index():
    return render_template("index.html", columns=sections_by_column())


@app.route("/api/play/<topic_id>", methods=["POST"])
def play(topic_id):
    topic = TOPICS_BY_ID.get(topic_id)
    if topic is None:
        return jsonify({"success": False}), 404

    generation = stop_playback()  # หยุดเสียง/gesture/sequence เก่าก่อนเสมอ กันเสียงทับกันเวลากดปุ่มใหม่ระหว่างที่ปุ่มก่อนหน้ายังเล่นอยู่

    if "emote" in topic:
        try:
            requests.post(f"{ROBOT_EMOTE_URL}/{topic['emote']}", timeout=10)
        except requests.exceptions.RequestException:
            pass
        # emote นี้เล่นเสียงพากย์จากไฟล์บนตัวหุ่นเอง (ลำโพงหุ่นเบา) — เล่นเสียงเดียวกันซ้ำผ่านลำโพงบลูทูธ
        # ของเครื่องนี้ด้วยเสมอ (ไม่ส่งไปหุ่นซ้ำ เพราะหุ่นเล่นเสียงของตัวเองอยู่แล้ว)
        voice_path = BOOTH_CONTENT / topic_id / "voice.mp3"
        threading.Thread(
            target=play_audio_file, args=(voice_path, generation),
            kwargs={"to_robot": False, "to_screen": True}, daemon=True,
        ).start()
        return jsonify({"success": True})

    if "sequence" in topic:
        threading.Thread(target=play_sequence, args=(topic_id, generation), daemon=True).start()
        return jsonify({"success": True})

    impress.open_and_goto(get_desktop(), topic.get("deck", DECK_PATH), topic["slide"])
    threading.Thread(target=play_sound, args=(topic_id, generation), daemon=True).start()

    return jsonify({"success": True})


@app.route("/api/stop", methods=["POST"])
def stop():
    stop_playback()
    return jsonify({"success": True})


if __name__ == "__main__":
    impress.open_and_goto(get_desktop(), DECK_PATH, IDLE_SLIDE)
    app.run(host="0.0.0.0", port=5002, debug=False)
