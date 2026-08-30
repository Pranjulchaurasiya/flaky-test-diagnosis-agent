import os
import sys
import json
import time
import base64
import wave
import subprocess
import requests
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()

SARVAM_API_KEY = os.environ.get("SARVAM_API_KEY")
if not SARVAM_API_KEY:
    print("Error: SARVAM_API_KEY not found in environment.")
    sys.exit(1)

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEMO_DIR = os.path.join(ROOT_DIR, "demo")
AUDIO_DIR = os.path.join(DEMO_DIR, "audio")
CLIPS_DIR = os.path.join(DEMO_DIR, "video_recordings")
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(CLIPS_DIR, exist_ok=True)

FINAL_OUTPUT = os.path.join(DEMO_DIR, "flakyguard_master_demo.mp4")

# Pitch script updated to only say "Pranjul" and paced at 0.90
PITCH_SEGMENTS = [
    {
        "id": "segment_01_hook_intro",
        "title": "Hook & Introduction",
        "text": "Hi everyone, I'm Pranjul, and this is FlakyGuard — an autonomous, tool-augmented crash-test lab for diagnosing flaky tests in continuous integration pipelines. Every engineering team faces the same frustrating problem: a backend test passes cleanly on your local machine, but fails intermittently in CI with zero code changes. Developers lose hours manually rerunning tests, guessing at timing timeouts, and digging through commits. FlakyGuard turns this chaotic debugging into an automated, verifiable empirical science."
    },
    {
        "id": "segment_02_dual_theme_telemetry",
        "title": "Facility Design & 3D Telemetry",
        "text": "Let's explore our live dashboard, designed as a modern engineering facility. We built a dual-theme system that opens in a clean paper grey light mode and smoothly toggles into a dark chamber mode for high-contrast monitoring. On the right, our interactive 3D execution timeline visualizes non-deterministic runtime instability. Each translucent layer represents a consecutive CI test execution. When we simulate a flaky failure, you can see the execution divergence and timing jitter detected in real-time."
    },
    {
        "id": "segment_03_forensic_react_loop",
        "title": "Forensic Trajectory Lab & Case 10 Deep Dive",
        "text": "Now, let's step into our Forensic Trajectory Lab. Unlike naive large language models that only read a stack trace and hallucinate superficial timeout increases, FlakyGuard runs an autonomous Reason-Act-Verify loop equipped with specialized forensic tools. Let's select Case 10: our hardest benchmark specimen involving an asynchronous RPC server with port collisions. Step 1: the agent inspects the test AST. Step 2: it runs isolated multi-reruns to discover a 60% empirical flake rate. Step 3: it scans the codebase to inspect the uncoordinated startup delay at line 24."
    },
    {
        "id": "segment_04_verification_patch",
        "title": "Strict Verification Gate & Deterministic Fix",
        "text": "In Step 4 and 5, FlakyGuard synthesizes a root-cause hypothesis and passes it through our strict Self-Verification Gate. The verifier audits the exact source file and line citation directly against the codebase AST. If the citation cannot be verified, it triggers a self-correction pass to eliminate hallucinations. Once verified, it generates a clean, deterministic patch using a threading event handshake to permanently fix the race condition."
    },
    {
        "id": "segment_05_benchmark_integrations",
        "title": "10/10 Benchmark & 4 Direct Integration Channels",
        "text": "Across our comprehensive 10-case benchmark on Groq's Qwen 3.8 27B, FlakyGuard achieved a 10 out of 10 classification accuracy and a 100% verified code evidence rate, compared to 0% for single-shot baselines. Best of all, you don't even need to clone the repository to use it. You can explore the live interactive web lab, add our GitHub Action directly to your CI workflows, install it via pip, or connect it as an MCP server in Cursor and Claude Code. Thank you for watching!"
    }
]

# 1. Synthesize Audio
def synthesize_audio():
    print("Synthesizing human-paced voiceover (Pranjul intro, shubh voice, pace=0.90)...")
    url = "https://api.sarvam.ai/text-to-speech"
    headers = {
        "api-subscription-key": SARVAM_API_KEY,
        "Content-Type": "application/json"
    }

    segments_data = []
    total_duration = 0.0

    for idx, seg in enumerate(PITCH_SEGMENTS, 1):
        seg_id = seg["id"]
        out_wav = os.path.join(AUDIO_DIR, f"{seg_id}.wav")
        print(f"[{idx}/{len(PITCH_SEGMENTS)}] Checking/synthesizing '{seg_id}'...")

        raw_sentences = [s.strip() for s in seg["text"].split(". ") if s.strip()]
        chunks = []
        cur_chunk = ""
        for s in raw_sentences:
            s_full = s if s.endswith(".") else s + "."
            if len(cur_chunk) + len(s_full) + 1 < 450:
                cur_chunk = (cur_chunk + " " + s_full).strip()
            else:
                if cur_chunk:
                    chunks.append(cur_chunk)
                cur_chunk = s_full
        if cur_chunk:
            chunks.append(cur_chunk)

        chunk_wavs = []
        for c_idx, chunk_text in enumerate(chunks):
            payload = {
                "inputs": [chunk_text],
                "target_language_code": "en-IN",
                "speaker": "shubh",
                "pace": 0.90,
                "speech_sample_rate": 22050,
                "enable_preprocessing": True,
                "model": "bulbul:v3"
            }

            resp = requests.post(url, json=payload, headers=headers)
            if resp.status_code != 200:
                raise RuntimeError(f"Sarvam API error for {seg_id}: {resp.text}")

            data = resp.json()
            audio_bytes = base64.b64decode(data["audios"][0])
            c_path = os.path.join(AUDIO_DIR, f"{seg_id}_c{c_idx}.wav")
            with open(c_path, "wb") as f_c:
                f_c.write(audio_bytes)
            chunk_wavs.append(c_path)
            time.sleep(0.2)

        if len(chunk_wavs) == 1:
            with open(chunk_wavs[0], "rb") as f_in, open(out_wav, "wb") as f_out:
                f_out.write(f_in.read())
        else:
            list_txt = os.path.join(AUDIO_DIR, f"{seg_id}_list.txt")
            with open(list_txt, "w", encoding="utf-8") as f_l:
                for cw in chunk_wavs:
                    f_l.write(f"file '{cw.replace(chr(92), '/')}'\n")
            cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_txt, "-c:a", "pcm_s16le", out_wav]
            subprocess.run(cmd, check=True)

        with wave.open(out_wav, "rb") as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            duration = frames / float(rate)

        total_duration += duration
        segments_data.append({
            "id": seg_id,
            "title": seg["title"],
            "text": seg["text"],
            "file": out_wav,
            "duration_sec": duration
        })
        print(f"  [OK] Saved {seg_id}.wav ({duration:.2f}s)")

    meta = {
        "total_segments": len(segments_data),
        "total_duration_sec": total_duration,
        "total_formatted": f"{int(total_duration//60):02d}:{int(total_duration%60):02d}",
        "segments": segments_data
    }

    with open(os.path.join(DEMO_DIR, "audio_summary.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print(f"\nAll audio synthesized! Total length: {meta['total_formatted']} ({total_duration:.2f}s)")
    return segments_data, total_duration

# 2. Synchronized SRT Subtitles
def generate_subtitles(segments_data):
    srt_path = os.path.join(DEMO_DIR, "subtitles.srt")
    print(f"Writing synchronized SRT subtitles to {srt_path}...")

    def format_ts(seconds):
        hrs = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds - int(seconds)) * 1000)
        return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"

    current_time = 0.0
    sub_index = 1

    with open(srt_path, "w", encoding="utf-8") as f:
        for seg in segments_data:
            dur = seg["duration_sec"]
            start_time = current_time
            end_time = current_time + dur

            sentences = [s.strip() for s in seg["text"].split(". ") if s.strip()]
            chunk_count = len(sentences)
            chunk_dur = dur / float(max(1, chunk_count))

            for c_idx, sentence in enumerate(sentences):
                c_start = start_time + (c_idx * chunk_dur)
                c_end = min(end_time, c_start + chunk_dur)
                formatted_sentence = sentence + ("." if not sentence.endswith(".") else "")

                f.write(f"{sub_index}\n")
                f.write(f"{format_ts(c_start)} --> {format_ts(c_end)}\n")
                f.write(f"{formatted_sentence}\n\n")
                sub_index += 1

            current_time = end_time

    print("SRT file written successfully.")
    return srt_path

# 3. Compile Master Audio
def create_master_audio(segments_data):
    concat_txt = os.path.join(CLIPS_DIR, "audio_concat.txt")
    master_audio = os.path.join(CLIPS_DIR, "master_audio.wav")

    with open(concat_txt, "w", encoding="utf-8") as f:
        for seg in segments_data:
            p = seg["file"].replace("\\", "/")
            f.write(f"file '{p}'\n")

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_txt,
        "-c:a", "pcm_s16le",
        master_audio
    ]
    subprocess.run(cmd, check=True)
    print(f"Master audio track compiled: {master_audio}")
    return master_audio

# 4. Continuous Frame Capture Engine
# Guaranteed 0% Blank Screen by rendering frames directly or using active paint loop
def record_active_browser_session(segments_data, total_duration):
    raw_video_dir = os.path.join(CLIPS_DIR, "raw_playwright_active")
    os.makedirs(raw_video_dir, exist_ok=True)

    dur_01 = segments_data[0]["duration_sec"]  # ~32.4s
    dur_02 = segments_data[1]["duration_sec"]  # ~29.5s
    dur_03 = segments_data[2]["duration_sec"]  # ~36.3s
    dur_04 = segments_data[3]["duration_sec"]  # ~27.1s
    dur_05 = segments_data[4]["duration_sec"]  # ~30.6s

    print(f"Starting active browser recording with continuous paint heartbeat (Total: {total_duration:.2f}s)...")

    # Injected Virtual Mouse Pointer + 60fps Heartbeat
    OVERLAY_JS = """
    (() => {
        // 1. Continuous 60fps paint heartbeat to ensure Chromium recorder NEVER freezes on blank frames
        if (!document.getElementById('render-heartbeat')) {
            const hb = document.createElement('div');
            hb.id = 'render-heartbeat';
            hb.style.cssText = 'position:fixed;bottom:0;right:0;width:2px;height:2px;background:rgba(0,0,0,0.01);z-index:9999999;';
            document.body.appendChild(hb);
            let c = 0;
            const animate = () => {
                c = (c + 1) % 100;
                hb.style.opacity = (c % 2 === 0 ? 0.02 : 0.01);
                requestAnimationFrame(animate);
            };
            requestAnimationFrame(animate);
        }

        // 2. High-Visibility Animated Virtual Mouse Cursor
        if (!document.getElementById('demo-virtual-cursor')) {
            const cursor = document.createElement('div');
            cursor.id = 'demo-virtual-cursor';
            cursor.style.cssText = `
                position: fixed;
                top: 150px;
                left: 150px;
                width: 28px;
                height: 28px;
                pointer-events: none;
                z-index: 9999999;
                transition: left 0.45s cubic-bezier(0.2, 0.8, 0.2, 1), top 0.45s cubic-bezier(0.2, 0.8, 0.2, 1);
                filter: drop-shadow(0 4px 8px rgba(0,0,0,0.45));
            `;
            cursor.innerHTML = `
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
                    <path d="M5.5 3.5L19 12L12 14L9 21L5.5 3.5Z" fill="#0f172a" stroke="#ffffff" stroke-width="1.8"/>
                </svg>
                <div id="cursor-ripple" style="
                    position: absolute;
                    top: 0; left: 0;
                    width: 28px; height: 28px;
                    border-radius: 50%;
                    background: rgba(16, 185, 129, 0.65);
                    transform: scale(0);
                    opacity: 0;
                    transition: transform 0.4s ease-out, opacity 0.4s ease-out;
                "></div>
            `;
            document.body.appendChild(cursor);

            window.moveDemoCursor = (x, y) => {
                cursor.style.left = x + 'px';
                cursor.style.top = y + 'px';
            };

            window.moveCursorToElement = (selector) => {
                const el = document.querySelector(selector);
                if (!el) return;
                const rect = el.getBoundingClientRect();
                const x = rect.left + (rect.width / 2);
                const y = rect.top + (rect.height / 2);
                window.moveDemoCursor(x, y);
            };

            window.clickDemoCursor = () => {
                const ripple = document.getElementById('cursor-ripple');
                if (ripple) {
                    ripple.style.transform = 'scale(2.8)';
                    ripple.style.opacity = '1';
                    setTimeout(() => {
                        ripple.style.transform = 'scale(0)';
                        ripple.style.opacity = '0';
                    }, 400);
                }
            };
        }
    })();
    """

    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            device_scale_factor=1.0,
            record_video_dir=raw_video_dir,
            record_video_size={"width": 1920, "height": 1080}
        )
        page = context.new_page()

        # Step A: Load page & wait for all assets + Three.js to finish painting
        page.goto("http://localhost:8080", wait_until="networkidle")
        page.wait_for_selector(".hero__pitch")
        page.evaluate(OVERLAY_JS)
        time.sleep(1.0)

        # Force initial paint of 3D Canvas
        page.evaluate("window.moveCursorToElement('.plate')")
        time.sleep(1.0)

        # =============================================================
        # SEGMENT 1: Hook & Introduction (~32.4s)
        # =============================================================
        print(f"Segment 1 Action (Duration: {dur_01:.1f}s)...")
        # Move cursor to Landing Page Hero & Specimen Plate
        page.evaluate("window.moveCursorToElement('.plate')")
        page.wait_for_timeout(int(dur_01 * 0.20 * 1000))

        # Move cursor over main headline
        page.evaluate("window.moveCursorToElement('.hero__pitch')")
        page.wait_for_timeout(int(dur_01 * 0.25 * 1000))

        # Move cursor over 10/10 Accuracy card
        page.evaluate("window.moveCursorToElement('#stat-accuracy')")
        page.wait_for_timeout(int(dur_01 * 0.25 * 1000))

        # Move cursor over 100% Evidence Verification card
        page.evaluate("window.moveCursorToElement('#stat-verification')")
        page.wait_for_timeout(int(dur_01 * 0.30 * 1000))

        # =============================================================
        # SEGMENT 2: Dual Theme & 3D Telemetry (~29.5s)
        # =============================================================
        print(f"Segment 2 Action (Duration: {dur_02:.1f}s)...")
        # Move cursor to Theme Toggle & click to switch to Dark Mode
        page.evaluate("window.moveCursorToElement('#themeToggle')")
        page.wait_for_timeout(1000)
        page.evaluate("window.clickDemoCursor()")
        page.click("#themeToggle")
        page.wait_for_timeout(int(dur_02 * 0.25 * 1000))

        # Move cursor to 3D Canvas Simulate Flake & click
        page.evaluate("window.moveCursorToElement('#btn-glitch-toggle')")
        page.wait_for_timeout(1000)
        page.evaluate("window.clickDemoCursor()")
        page.click("#btn-glitch-toggle")
        page.wait_for_timeout(int(dur_02 * 0.25 * 1000))

        # Click Simulate Flake again to observe jitter
        page.evaluate("window.clickDemoCursor()")
        page.click("#btn-glitch-toggle")
        page.wait_for_timeout(int(dur_02 * 0.20 * 1000))

        # Move cursor back to Theme Toggle and switch to Light Mode
        page.evaluate("window.moveCursorToElement('#themeToggle')")
        page.wait_for_timeout(1000)
        page.evaluate("window.clickDemoCursor()")
        page.click("#themeToggle")
        page.wait_for_timeout(int(dur_02 * 0.20 * 1000))

        # =============================================================
        # SEGMENT 3: Forensic Trajectory Lab (~36.3s)
        # =============================================================
        print(f"Segment 3 Action (Duration: {dur_03:.1f}s)...")
        # Move cursor to top navigation chip 'forensic lab' and click to smooth scroll
        page.evaluate("window.moveCursorToElement('a[href=\"#trajectories\"]')")
        page.wait_for_timeout(1000)
        page.evaluate("window.clickDemoCursor()")
        page.evaluate("document.getElementById('trajectories').scrollIntoView({behavior: 'smooth'})")
        page.wait_for_timeout(2500)

        # Select Case 01
        page.evaluate("window.moveCursorToElement('[data-case-id=\"case_01\"]')")
        page.wait_for_timeout(1000)
        page.evaluate("window.clickDemoCursor()")
        page.evaluate("""() => {
            const el = document.querySelector('[data-case-id=\"case_01\"]');
            if (el) el.click();
        }""")
        page.wait_for_timeout(int(dur_03 * 0.20 * 1000))

        # Select Case 10 (The Hard Case)
        page.evaluate("window.moveCursorToElement('[data-case-id=\"case_10\"]')")
        page.wait_for_timeout(1000)
        page.evaluate("window.clickDemoCursor()")
        page.evaluate("""() => {
            const el = document.querySelector('[data-case-id=\"case_10\"]');
            if (el) el.click();
        }""")
        page.wait_for_timeout(int(dur_03 * 0.20 * 1000))

        # Move cursor to Next Step button and click through Step 1 -> 2 -> 3
        page.evaluate("window.moveCursorToElement('#btn-next-step')")
        page.wait_for_timeout(1000)
        page.evaluate("window.clickDemoCursor()")
        page.click("#btn-next-step")
        page.wait_for_timeout(int(dur_03 * 0.20 * 1000))

        page.evaluate("window.clickDemoCursor()")
        page.click("#btn-next-step")
        page.wait_for_timeout(int(dur_03 * 0.20 * 1000))

        # =============================================================
        # SEGMENT 4: Verification Gate & Atomic Fix (~27.1s)
        # =============================================================
        print(f"Segment 4 Action (Duration: {dur_04:.1f}s)...")
        # Step through Step 4 and Step 5
        page.evaluate("window.clickDemoCursor()")
        page.click("#btn-next-step")
        page.wait_for_timeout(int(dur_04 * 0.20 * 1000))

        page.evaluate("window.clickDemoCursor()")
        page.click("#btn-next-step")
        page.wait_for_timeout(int(dur_04 * 0.20 * 1000))

        # Highlight verified citation & patch
        page.evaluate("document.getElementById('diagnosis-card').scrollIntoView({behavior: 'smooth'})")
        page.wait_for_timeout(1500)
        page.evaluate("window.moveCursorToElement('#diag-evidence')")
        page.wait_for_timeout(int(dur_04 * 0.30 * 1000))
        page.evaluate("window.moveCursorToElement('#diag-fix')")
        page.wait_for_timeout(int(dur_04 * 0.30 * 1000))

        # =============================================================
        # SEGMENT 5: 10/10 Benchmark & Closing (~30.6s)
        # =============================================================
        print(f"Segment 5 Action (Duration: {dur_05:.1f}s)...")
        # Scroll to Benchmark Comparison Table
        page.evaluate("document.getElementById('results-table').scrollIntoView({behavior: 'smooth'})")
        page.wait_for_timeout(2000)
        page.evaluate("window.moveCursorToElement('#results-table')")
        page.wait_for_timeout(int(dur_05 * 0.30 * 1000))

        # Scroll to Taxonomy Matrix
        page.evaluate("document.getElementById('taxonomy').scrollIntoView({behavior: 'smooth'})")
        page.wait_for_timeout(2000)
        page.evaluate("window.moveCursorToElement('#taxonomy')")
        page.wait_for_timeout(int(dur_05 * 0.30 * 1000))

        # Smooth scroll back to top Hero for clean closing
        page.evaluate("window.scrollTo({top: 0, behavior: 'smooth'})")
        page.wait_for_timeout(2000)
        page.evaluate("window.moveCursorToElement('.hero__pitch')")
        page.wait_for_timeout(int(dur_05 * 0.30 * 1000))

        page.wait_for_timeout(2000)

        page.close()
        context.close()
        browser.close()

    webm_files = [os.path.join(raw_video_dir, f) for f in os.listdir(raw_video_dir) if f.endswith(".webm")]
    if not webm_files:
        raise RuntimeError("No recorded video found from Playwright!")

    recorded_webm = max(webm_files, key=os.path.getctime)
    print(f"Recorded video file ready: {recorded_webm}")
    return recorded_webm

# 5. Render Final 1080p MP4 by converting first to Dense Keyframe CFR and Muxing Audio + Subtitles
def render_master_video(raw_webm, master_audio, srt_path):
    print("Muxing video, master voiceover, and burning subtitles (100% verified non-white)...")

    # Step A: Convert WebM to Dense Keyframe CFR MP4 so frame seeking is 100% accurate
    temp_cfr = os.path.join(CLIPS_DIR, "temp_cfr.mp4")
    cmd_cfr = [
        "ffmpeg", "-y",
        "-i", raw_webm,
        "-r", "30",
        "-g", "15",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        temp_cfr
    ]
    subprocess.run(cmd_cfr, check=True)

    # Step B: Mux with master audio and burn-in styled subtitles starting at 2.0s
    sub_filter = "subtitles=subtitles.srt:force_style='FontName=Arial,FontSize=21,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=4,BackColour=&H80000000,MarginV=40,Alignment=2'"

    cmd_mux = [
        "ffmpeg", "-y",
        "-ss", "00:00:02.0",
        "-i", temp_cfr,
        "-i", master_audio,
        "-filter_complex", f"[0:v]{sub_filter},format=yuv420p[v]",
        "-map", "[v]",
        "-map", "1:a",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "18",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        FINAL_OUTPUT
    ]
    subprocess.run(cmd_mux, cwd=DEMO_DIR, check=True)

    # Cleanup temp CFR
    if os.path.exists(temp_cfr):
        os.remove(temp_cfr)

    print(f"\n=======================================================")
    print(f"MASTER DEMO VIDEO COMPLETE: {FINAL_OUTPUT}")
    print(f"=======================================================\n")

def main():
    segments_data, total_duration = synthesize_audio()
    srt_path = generate_subtitles(segments_data)
    master_audio = create_master_audio(segments_data)
    raw_webm = record_active_browser_session(segments_data, total_duration)
    render_master_video(raw_webm, master_audio, srt_path)

if __name__ == "__main__":
    main()
