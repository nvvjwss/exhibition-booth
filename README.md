# Exhibition Booth

แผงควบคุมสไลด์ที่ขับเคลื่อนด้วยหุ่นยนต์ สำหรับบูธของ Siam.AI กดเลือกหัวข้อบน iPad หุ่นยนต์ Alpha Mini จะพูดอธิบาย และโปรเจกเตอร์จะเปลี่ยนไปสไลด์ที่ตรงกัน

## โครงสร้างโปรเจกต์

- `app.py`: Flask server, รายการหัวข้อ, สั่งหุ่นพูด + เปลี่ยนสไลด์
- `impress_controller.py`: ควบคุม LibreOffice Impress ผ่าน UNO
- `templates/`, `static/`: หน้าเว็บ UI สำหรับ iPad
- `booth_content/`: เสียงพากย์แต่ละหัวข้อ
- `decks/`: ไฟล์ PowerPoint
- `start.sh`: เชื่อมต่อหุ่นยนต์, mirror หน้าจอ, เริ่มระบบทั้งหมด

## สิ่งที่ต้องมี

- เครื่อง Linux + หุ่นยนต์ Alpha Mini ต่อผ่าน USB
- Python 3, `adb`, `scrcpy` (ถ้าต้องการ), LibreOffice
- Deskreen AppImage ไว้ที่ `~/Downloads/`
- ไฟล์ PowerPoint ที่ `~/Downloads/siam.ai powerpoint.pptx` (หรือกำหนดเองผ่าน `DECK_PATH`)

## ติดตั้ง

```bash
git clone https://github.com/nvvjwss/exhibition-booth.git
cd exhibition-booth
pip install -r requirements.txt
```

เปิดไฟล์สไลด์ใน LibreOffice Impress ก่อนรันแอป

## วิธีใช้

```bash
./start.sh
```

จากนั้น: เปิดลิงก์ Deskreen บนจอที่จะแสดงผล แล้ว share หน้าต่าง Impress; ต่อลำโพง Bluetooth ถ้าใช้

### ตัวแปรสภาพแวดล้อม (Env vars)

- `AUDIO_MODE`: `both` (ค่าเริ่มต้น) / `robot` / `screen`
- `ROBOT_BASE_URL`: ค่าเริ่มต้น `http://localhost:8080`
- `DECK_PATH`: ค่าเริ่มต้น `~/Downloads/siam.ai powerpoint.pptx`
