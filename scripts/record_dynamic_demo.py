import os
import sys
import json
import time
import subprocess
from playwright.sync_api import sync_playwright

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEMO_DIR = os.path.join(ROOT_DIR, "demo")
AUDIO_DIR = os.path.join(DEMO_DIR, "audio")
CLIPS_DIR = os.path.join(DEMO_DIR, "video_recordings")
os.makedirs(CLIPS_DIR, exist_ok=True)

FINAL_OUTPUT = os.path.join(DEMO_DIR, "flakyguard_master_demo.mp4")

# Load audio metadata
with open(os.path.join(DEMO_DIR, "audio_summary.json"), "r", encoding="utf-8") as f:
    audio_meta = json.load(f)

segments = audio_meta["segments"]
print(f"Loaded {len(segments)} segments. Total duration: {audio_meta['total_duration_sec']:.2f}s")

# 1. Generate timestamped SRT file
def generate_srt():
    srt_path = os.path.join(DEMO_DIR, "subtitles.srt")
    print(f"Generating synchronized SRT subtitles at: {srt_path}...")
    
    current_time = 0.0
    with open(srt_path, "w", encoding="utf-8") as f:
        for idx, seg in enumerate(segments, 1):
            dur = seg["duration_sec"]
            start_sec = current_time
            end_sec = current_time + dur
            
            def format_ts(seconds):
                hrs = int(seconds // 3600)
                mins = int((seconds % 3600) // 60)
                secs = int(seconds % 60)
                millis = int((seconds - int(seconds)) * 1000)
                return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"

            # Break long text into 2-3 readable subtitle lines
            text = seg["text"]
            # Split by sentences or chunks
            sentences = [s.strip() for s in text.split(". ") if s.strip()]
            sub_count = len(sentences)
            sub_dur = dur / float(max(1, sub_count))
            
            for s_idx, sentence in enumerate(sentences):
                s_start = start_sec + (s_idx * sub_dur)
                s_end = min(end_sec, s_start + sub_dur)
                sub_text = sentence + ("." if not sentence.endswith(".") else "")
                
                f.write(f"{idx}_{s_idx+1}\n")
                f.write(f"{format_ts(s_start)} --> {format_ts(s_end)}\n")
                f.write(f"{sub_text}\n\n")
                
            current_time = end_sec

    print("SRT subtitles generated successfully.")
    return srt_path

# 2. Record dynamic browser video via Playwright
def record_browser_actions():
    raw_video_dir = os.path.join(CLIPS_DIR, "raw_playwright")
    os.makedirs(raw_video_dir, exist_ok=True)

    print("Launching Chromium to record dynamic live interaction...")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            device_scale_factor=1.0,
            record_video_dir=raw_video_dir,
            record_video_size={"width": 1920, "height": 1080}
        )
        page = context.new_page()
        page.goto("http://localhost:8080", wait_until="networkidle")
        time.sleep(1.0)

        # -------------------------------------------------------------
        # SEGMENT 1: Intro (0s -> ~16s)
        # -------------------------------------------------------------
        print("Acting Segment 1: Intro & Hero Overview...")
        time.sleep(3.0)
        # Highlight stats
        page.evaluate("window.scrollTo({top: 0, behavior: 'smooth'})")
        time.sleep(6.0)
        try:
            page.hover(".stat-cell", timeout=3000)
        except Exception:
            pass
        time.sleep(7.0)

        # -------------------------------------------------------------
        # SEGMENT 2: Dual Theme & 3D Telemetry (~16s -> ~34s)
        # -------------------------------------------------------------
        print("Acting Segment 2: Theme Toggle & 3D Simulation...")
        # Toggle to dark mode
        page.click("#themeToggle")
        time.sleep(4.0)
        # Click Simulate Flake on 3D stack
        page.click("#btn-glitch-toggle")
        time.sleep(4.0)
        # Click Simulate Flake again to show recovery
        page.click("#btn-glitch-toggle")
        time.sleep(4.0)
        # Toggle back to light mode
        page.click("#themeToggle")
        time.sleep(5.5)

        # -------------------------------------------------------------
        # SEGMENT 3: Forensic Trajectory Lab & Case 10 (~34s -> ~56s)
        # -------------------------------------------------------------
        print("Acting Segment 3: Forensic Trajectory Lab & Step Stepping...")
        # Smooth scroll to Forensic Lab
        page.evaluate("document.getElementById('trajectories').scrollIntoView({behavior: 'smooth'})")
        time.sleep(3.0)
        
        # Click Case 01
        page.evaluate("""() => {
            const el = document.querySelector('[data-case-id=\"case_01\"]');
            if (el) el.click();
        }""")
        time.sleep(3.5)

        # Click Case 10 (The Hard Case)
        page.evaluate("""() => {
            const el = document.querySelector('[data-case-id=\"case_10\"]');
            if (el) el.click();
        }""")
        time.sleep(4.0)

        # Step through trajectory steps (Step 1 -> Step 2 -> Step 3)
        page.click("#btn-next-step")
        time.sleep(3.5)
        page.click("#btn-next-step")
        time.sleep(3.5)
        page.click("#btn-next-step")
        time.sleep(4.0)

        # -------------------------------------------------------------
        # SEGMENT 4: Verification Gate & Patch (~56s -> ~71s)
        # -------------------------------------------------------------
        print("Acting Segment 4: Verification Gate & Atomic Code Patch...")
        # Step to Step 4 and Step 5
        page.click("#btn-next-step")
        time.sleep(3.0)
        page.click("#btn-next-step")
        time.sleep(3.0)
        # Scroll to diagnosis card & citation
        page.evaluate("document.getElementById('diagnosis-card').scrollIntoView({behavior: 'smooth'})")
        time.sleep(8.5)

        # -------------------------------------------------------------
        # SEGMENT 5: Benchmark 10/10 Table & 4 Integrations (~71s -> ~94s)
        # -------------------------------------------------------------
        print("Acting Segment 5: Benchmark Table & Closing...")
        # Scroll to Benchmark Comparison Table
        page.evaluate("document.getElementById('results-table').scrollIntoView({behavior: 'smooth'})")
        time.sleep(7.0)
        # Scroll down to Taxonomy Matrix
        page.evaluate("document.getElementById('taxonomy').scrollIntoView({behavior: 'smooth'})")
        time.sleep(8.0)
        # Scroll smoothly back to top Hero
        page.evaluate("window.scrollTo({top: 0, behavior: 'smooth'})")
        time.sleep(8.0)

        page.close()
        context.close()
        browser.close()
        print("Browser recording complete!")

    # Find recorded webm file
    webm_files = [os.path.join(raw_video_dir, f) for f in os.listdir(raw_video_dir) if f.endswith(".webm")]
    if not webm_files:
        raise RuntimeError("No recorded video found from Playwright!")
    
    recorded_webm = webm_files[0]
    print(f"Recorded video file: {recorded_webm}")
    return recorded_webm

# 3. Concatenate audio segments into a single master audio track
def combine_audio_track():
    concat_txt = os.path.join(CLIPS_DIR, "audio_concat.txt")
    master_audio = os.path.join(CLIPS_DIR, "master_audio.wav")
    
    with open(concat_txt, "w", encoding="utf-8") as f:
        for seg in segments:
            # Escape path for ffmpeg concat
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

# 4. Final Render: Mux video + master audio + styled subtitles into 1080p MP4
def render_final_video(raw_webm, master_audio, srt_file):
    print("Muxing video, master voiceover, and burning subtitles...")
    
    # Run FFmpeg inside DEMO_DIR so the subtitle filename is just 'subtitles.srt'
    sub_style = "subtitles=subtitles.srt:force_style='FontName=Arial,FontSize=20,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=4,BackColour=&H80000000,MarginV=35,Alignment=2'"

    cmd = [
        "ffmpeg", "-y",
        "-i", raw_webm,
        "-i", master_audio,
        "-filter_complex", f"[0:v]{sub_style},format=yuv420p[v]",
        "-map", "[v]",
        "-map", "1:a",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "18",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        "flakyguard_master_demo.mp4"
    ]
    print("Running FFmpeg render command in DEMO_DIR...")
    subprocess.run(cmd, cwd=DEMO_DIR, check=True)
    print(f"\n=======================================================")
    print(f"🎉 MASTER DEMO VIDEO COMPLETE: {FINAL_OUTPUT}")
    print(f"=======================================================\n")

def main():
    srt_path = generate_srt()
    raw_video = record_browser_actions()
    master_audio = combine_audio_track()
    render_final_video(raw_video, master_audio, srt_path)

if __name__ == "__main__":
    main()
