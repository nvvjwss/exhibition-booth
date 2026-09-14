const statusbar = document.getElementById("statusbar");
const eq = document.getElementById("eq");
const phaseLabel = document.getElementById("phaseLabel");
const topicLabelBar = document.getElementById("topicLabelBar");
const hintText = document.getElementById("hintText");
const stopBtn = document.getElementById("stopBtn");

const PHASE_TEXT = {
  loading: "กำลังส่งคำสั่งไปที่ A1 และจอสไลด์",
  playing: "A1 กำลังเล่าเรื่องนี้อยู่",
  error: "ส่งคำสั่งไม่สำเร็จ ลองใหม่อีกครั้ง",
};

let activeBtn = null;

function setActive(btn) {
  if (activeBtn && activeBtn !== btn) activeBtn.classList.remove("active");
  activeBtn = btn;
  if (btn) btn.classList.add("active");
}

function showBar(show) {
  statusbar.classList.toggle("show", show);
}

function runEq(on) {
  eq.classList.toggle("on", on);
}

document.querySelectorAll(".topic-btn").forEach((btn) => {
  btn.addEventListener("click", async () => {
    const label = btn.querySelector(".topic-label")?.textContent.trim() || btn.textContent.trim();

    setActive(btn);
    showBar(true);
    runEq(false);
    phaseLabel.textContent = "READY";
    topicLabelBar.textContent = label;
    hintText.textContent = "โปรดรอสักครู่ ไม่ต้องกดซ้ำ";
    phaseLabel.textContent = PHASE_TEXT.loading;

    try {
      const res = await fetch(`/api/play/${btn.dataset.topicId}`, { method: "POST" });
      if (!res.ok) throw new Error("bad response");
      phaseLabel.textContent = PHASE_TEXT.playing;
      hintText.textContent = "กดหัวข้ออื่นเพื่อเปลี่ยนได้ทันที";
      runEq(true);
    } catch (e) {
      phaseLabel.textContent = PHASE_TEXT.error;
      hintText.textContent = "";
      runEq(false);
    }
  });
});

stopBtn.addEventListener("click", async () => {
  runEq(false);
  showBar(false);
  setActive(null);
  try {
    await fetch("/api/stop", { method: "POST" });
  } catch (e) {
    // เงียบไว้ — ปุ่มหยุดไม่ต้องโชว์ error ให้ผู้ใช้เห็น
  }
});
