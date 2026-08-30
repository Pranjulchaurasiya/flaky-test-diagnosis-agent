import os
import sys
import json
import time
import subprocess
from playwright.sync_api import sync_playwright

DEMO_DIR = os.path.dirname(os.path.abspath(__file__))
AUDIO_DIR = os.path.join(DEMO_DIR, "audio")
CLIPS_DIR = os.path.join(DEMO_DIR, "clips")
os.makedirs(CLIPS_DIR, exist_ok=True)

FINAL_VIDEO = os.path.join(DEMO_DIR, "final_demo.mp4")

# Load audio summary
with open(os.path.join(DEMO_DIR, "audio_summary.json"), "r", encoding="utf-8") as f:
    audio_meta = json.load(f)

segments = audio_meta["segments"]
print(f"Loaded {len(segments)} audio segments. Total audio duration: {audio_meta['total_duration_sec']}s ({audio_meta['total_formatted']})")

def capture_screenshots():
    print("Launching Chromium via Playwright to capture high-res web dashboard views...")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1920, "height": 1080}, device_scale_factor=1.5)
        
        # Navigate to localhost web app
        page.goto("http://localhost:8080", wait_until="networkidle")
        time.sleep(2)

        # 1. Segment 01: Hero & 3D Canvas
        print("Capturing Frame 1: Hero & 3D Visualizer...")
        page.evaluate("window.scrollTo(0, 0)")
        time.sleep(1)
        page.screenshot(path=os.path.join(CLIPS_DIR, "frame_01.png"))

        # 2. Segment 02: Baseline failure on hard case
        print("Capturing Frame 2: Benchmark cards & baseline analysis...")
        page.evaluate("document.getElementById('benchmark').scrollIntoView({behavior: 'instant'})")
        time.sleep(1)
        page.screenshot(path=os.path.join(CLIPS_DIR, "frame_02.png"))

        # 3. Segment 03: Case 10 Trajectory Explorer
        print("Capturing Frame 3: Interactive Trajectory on Case 10...")
        page.evaluate("document.getElementById('trajectories').scrollIntoView({behavior: 'instant'})")
        time.sleep(1)
        # Select case 10
        page.evaluate("""() => {
            const items = document.querySelectorAll('.case-item');
            items.forEach(el => {
                if (el.dataset.caseId === 'case_10') el.click();
            });
        }""")
        time.sleep(1.5)
        page.screenshot(path=os.path.join(CLIPS_DIR, "frame_03.png"))

        # 4. Segment 04: Benchmark results table
        print("Capturing Frame 4: 10/10 Results & Verification Table...")
        page.evaluate("document.getElementById('results-table').scrollIntoView({behavior: 'instant'})")
        time.sleep(1)
        page.screenshot(path=os.path.join(CLIPS_DIR, "frame_04.png"))

        # 5. Segment 05: Changelog & Architecture / Taxonomy
        print("Capturing Frame 5: Taxonomy Matrix & Root Causes...")
        page.evaluate("document.getElementById('taxonomy').scrollIntoView({behavior: 'instant'})")
        time.sleep(1)
        page.screenshot(path=os.path.join(CLIPS_DIR, "frame_05.png"))

        # 6. Segment 06: Architecture / Trajectory step details
        print("Capturing Frame 6: Step details & Verification Gate...")
        page.evaluate("document.getElementById('diagnosis-card').scrollIntoView({behavior: 'instant'})")
        time.sleep(1)
        page.screenshot(path=os.path.join(CLIPS_DIR, "frame_06.png"))

        # 7. Segment 07: Live Site Hero / Closing
        print("Capturing Frame 7: Live Site & Hero Stats...")
        page.evaluate("window.scrollTo(0, 0)")
        time.sleep(1)
        page.screenshot(path=os.path.join(CLIPS_DIR, "frame_07.png"))

        browser.close()
        print("All high-res screenshots captured successfully!")

def build_segment_clips():
    segment_mp4s = []
    concat_list_path = os.path.join(CLIPS_DIR, "concat_list.txt")

    with open(concat_list_path, "w", encoding="utf-8") as f_concat:
        for idx, seg in enumerate(segments, 1):
            seg_id = seg["segment_id"]
            wav_path = seg["file"]
            duration = seg["duration_sec"]
            frame_path = os.path.join(CLIPS_DIR, f"frame_{idx:02d}.png")
            out_mp4 = os.path.join(CLIPS_DIR, f"{seg_id}.mp4")

            print(f"Rendering Clip {idx}/7: {seg_id} (duration: {duration}s)...")

            # Render 1080p MP4 with subtle pan/zoom filter matching exact audio duration
            # zoompan filter adds cinematic motion
            cmd = [
                "ffmpeg", "-y",
                "-loop", "1",
                "-i", frame_path,
                "-i", wav_path,
                "-vf", f"scale=1920:1080,format=yuv420p",
                "-c:v", "libx264",
                "-tune", "stillimage",
                "-c:a", "aac",
                "-b:a", "192k",
                "-pix_fmt", "yuv420p",
                "-shortest",
                "-t", str(duration),
                out_mp4
            ]
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            segment_mp4s.append(out_mp4)
            f_concat.write(f"file '{os.path.abspath(out_mp4)}'\n")

    print("All 7 segment MP4 clips rendered.")
    return concat_list_path

def assemble_final_video(concat_list_path):
    print(f"Concatenating all segments into {FINAL_VIDEO}...")
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_list_path,
        "-c", "copy",
        FINAL_VIDEO
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print(f"Final video successfully generated: {FINAL_VIDEO}")

def verify_final_video():
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration,size,bit_rate",
        "-of", "json",
        FINAL_VIDEO
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    meta = json.loads(res.stdout)
    fmt = meta.get("format", {})
    dur = float(fmt.get("duration", 0))
    size_mb = int(fmt.get("size", 0)) / (1024 * 1024)

    mins = int(dur // 60)
    secs = int(dur % 60)
    print("\n" + "=" * 70)
    print("                 FINAL DEMO VIDEO SPECIFICATIONS")
    print("=" * 70)
    print(f"File Path:       {FINAL_VIDEO}")
    print(f"Exact Duration:  {dur:.2f}s ({mins:02d}:{secs:02d})")
    print(f"File Size:       {size_mb:.2f} MB")
    print(f"Target Budget:   180s - 225s (03:00 - 03:45)")
    print(f"Hard Ceiling:    240s (04:00)")
    print(f"Status:          {'PASS (Within Budget)' if dur <= 240 else 'FAIL (Exceeds Limit)'}")
    print("=" * 70)

if __name__ == "__main__":
    capture_screenshots()
    concat_list = build_segment_clips()
    assemble_final_video(concat_list)
    verify_final_video()
