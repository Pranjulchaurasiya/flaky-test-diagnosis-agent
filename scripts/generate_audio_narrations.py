import os
import sys
import json
import time
import base64
import requests
from dotenv import load_dotenv

load_dotenv()

SARVAM_API_KEY = os.environ.get("SARVAM_API_KEY")
if not SARVAM_API_KEY:
    print("Error: SARVAM_API_KEY not found in environment.")
    sys.exit(1)

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "demo")
AUDIO_DIR = os.path.join(OUTPUT_DIR, "audio")
os.makedirs(AUDIO_DIR, exist_ok=True)

# 5 Focused Segments (~130 seconds total)
SCRIPT_SEGMENTS = [
    {
        "id": "segment_01_intro",
        "title": "Introduction & The Flaky Test Problem",
        "text": "Hi, I'm Pranjul Chaurasiya, and this is FlakyGuard — the autonomous crash-test lab for CI flaky tests. When a test passes locally but fails intermittently in CI, engineers lose hours guessing at timing issues. FlakyGuard turns flaky test post-mortems into an exact empirical science."
    },
    {
        "id": "segment_02_ui_telemetry",
        "title": "Dual Theme UI & 3D Instability Stack",
        "text": "Here on our live dashboard, you can see our dual-theme facility design. Watch as we toggle smoothly between Light and Dark mode. Above the stats is our interactive 3D execution timeline, where translucent layers simulate consecutive CI test executions. When we click Simulate Flake, you can see runtime divergence in real-time."
    },
    {
        "id": "segment_03_forensic_lab",
        "title": "Forensic Trajectory Lab & Case 10 Deep Dive",
        "text": "Let's dive into our Forensic Trajectory Lab. Unlike naive LLMs that only guess from error traces, FlakyGuard runs an autonomous Reason-Act-Verify loop. Watch as we select Case 10: Socket TIME_WAIT Port Collision. The agent uses the Test Runner tool to measure the empirical flake rate, uses the Code Search tool to inspect the async startup routine, and pinpoints line 24 as the uncoordinated delay."
    },
    {
        "id": "segment_04_verification_patch",
        "title": "Strict Verification Gate & Deterministic Fix",
        "text": "Next, the diagnosis passes through our strict Self-Verification Gate. The verifier audits the exact source file and line citation directly against the AST to ensure zero percent hallucination. It then synthesizes a deterministic code patch using a threading event handshake to permanently eliminate the race."
    },
    {
        "id": "segment_05_benchmark_closing",
        "title": "10/10 Benchmark & 4 Direct Usage Channels",
        "text": "Across our 10-case benchmark on Groq Qwen 3.8 27B, FlakyGuard achieved 10 out of 10 classification accuracy and a 100 percent verified code evidence rate compared to zero percent for the baseline. You can use FlakyGuard right now on our live web lab, via our GitHub Action in CI, with pip install flakyguard, or as an MCP server in Cursor and Claude Code. Thank you!"
    }
]

def generate_audio_segments():
    print(f"Generating {len(SCRIPT_SEGMENTS)} audio segments using Sarvam AI TTS (shubh voice)...")
    url = "https://api.sarvam.ai/text-to-speech"
    headers = {
        "api-subscription-key": SARVAM_API_KEY,
        "Content-Type": "application/json"
    }

    results = []
    total_sec = 0

    for idx, seg in enumerate(SCRIPT_SEGMENTS, 1):
        seg_id = seg["id"]
        out_wav = os.path.join(AUDIO_DIR, f"{seg_id}.wav")
        print(f"Synthesizing [{idx}/{len(SCRIPT_SEGMENTS)}] {seg_id}...")

        payload = {
            "inputs": [seg["text"]],
            "target_language_code": "en-IN",
            "speaker": "shubh",
            "pace": 1.05,
            "speech_sample_rate": 22050,
            "enable_preprocessing": True,
            "model": "bulbul:v3"
        }

        resp = requests.post(url, json=payload, headers=headers)
        if resp.status_code != 200:
            print(f"Error {resp.status_code}: {resp.text}")
            # Try subh as fallback speaker name if needed
            payload["speaker"] = "subh"
            resp = requests.post(url, json=payload, headers=headers)
            if resp.status_code != 200:
                raise RuntimeError(f"Sarvam API failed for segment {seg_id}: {resp.text}")

        data = resp.json()
        audio_b64 = data["audios"][0]
        audio_bytes = base64.b64decode(audio_b64)

        with open(out_wav, "wb") as f:
            f.write(audio_bytes)

        # Get duration using ffprobe or wave module
        import wave
        with wave.open(out_wav, "rb") as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            duration = frames / float(rate)

        total_sec += duration
        results.append({
            "segment_id": seg_id,
            "title": seg["title"],
            "text": seg["text"],
            "file": out_wav,
            "duration_sec": duration
        })
        print(f"  -> Generated {out_wav} ({duration:.2f}s)")
        time.sleep(0.5)

    meta = {
        "total_segments": len(results),
        "total_duration_sec": total_sec,
        "total_formatted": f"{int(total_sec//60):02d}:{int(total_sec%60):02d}",
        "segments": results
    }

    meta_path = os.path.join(OUTPUT_DIR, "audio_summary.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print(f"\nAll audio generated! Total Duration: {meta['total_formatted']} ({total_sec:.2f}s)")
    return meta

if __name__ == "__main__":
    generate_audio_segments()
