import os
import sys
import json
import time
import base64
import wave
import urllib.request
from typing import Dict, Any, List

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

SARVAM_API_KEY = os.environ.get("SARVAM_API_KEY", "").strip()
if not SARVAM_API_KEY:
    raise ValueError("FATAL: SARVAM_API_KEY environment variable is missing. Please configure it in .env.")

SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "narration.json")
AUDIO_DIR = os.path.join(os.path.dirname(__file__), "audio")
os.makedirs(AUDIO_DIR, exist_ok=True)

def get_wav_duration(file_path: str) -> float:
    with wave.open(file_path, "rb") as wf:
        frames = wf.getnframes()
        rate = wf.getframerate()
        return round(frames / float(rate), 3)

def generate_voiceover():
    with open(SCRIPT_PATH, "r", encoding="utf-8") as f:
        segments: List[Dict[str, Any]] = json.load(f)

    print(f"Loaded {len(segments)} narration segments from {SCRIPT_PATH}")
    print(f"Using Sarvam AI TTS: model='bulbul:v3', speaker='shubh', language='en-IN'")
    print("=" * 70)

    url = "https://api.sarvam.ai/text-to-speech"
    headers = {
        "api-subscription-key": SARVAM_API_KEY,
        "Content-Type": "application/json"
    }

    results = []
    total_duration = 0.0

    for idx, seg in enumerate(segments, 1):
        seg_id = seg["segment_id"]
        title = seg["title"]
        text = seg["text"]
        target_dur = seg.get("target_duration_sec", 0)

        print(f"\n[{idx}/{len(segments)}] Synthesizing {seg_id}: '{title}'...")
        print(f"      Text length: {len(text)} chars | Target: ~{target_dur}s")

        payload = {
            "text": text,
            "target_language_code": "en-IN",
            "speaker": "shubh",
            "model": "bulbul:v3"
        }

        t0 = time.time()
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                status_code = resp.status
                resp_data = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            print(f"      ERROR calling Sarvam TTS: {e}")
            raise RuntimeError(f"Sarvam API call failed for {seg_id}: {e}") from e

        api_latency = round(time.time() - t0, 3)
        audios = resp_data.get("audios", [])
        if not audios:
            raise ValueError(f"No audio returned by Sarvam API for {seg_id}. Response: {resp_data}")

        raw_wav = base64.b64decode(audios[0])
        out_wav_path = os.path.join(AUDIO_DIR, f"{seg_id}.wav")
        with open(out_wav_path, "wb") as f:
            f.write(raw_wav)

        actual_duration = get_wav_duration(out_wav_path)
        total_duration += actual_duration

        print(f"      Status: {status_code} OK (API Latency: {api_latency}s)")
        print(f"      Saved: {out_wav_path} ({len(raw_wav)} bytes)")
        print(f"      Actual Audio Duration: {actual_duration}s")

        results.append({
            "segment_id": seg_id,
            "title": title,
            "file": out_wav_path,
            "duration_sec": actual_duration,
            "text": text
        })

    print("\n" + "=" * 70)
    print("                 VOICEOVER GENERATION SUMMARY")
    print("=" * 70)
    for r in results:
        print(f"  {r['segment_id']}: {r['duration_sec']:6.2f}s  |  {r['title']}")

    mins = int(total_duration // 60)
    secs = int(total_duration % 60)
    print("-" * 70)
    print(f"TOTAL DURATION: {total_duration:.2f}s ({mins:02d}:{secs:02d})")
    print(f"Target Budget:  180s - 225s (03:00 - 03:45)")
    print(f"Hard Ceiling:   240s (04:00)")

    if total_duration > 240:
        print(f"WARNING: Total duration exceeds 4:00 hard ceiling by {total_duration - 240:.2f}s!")
    elif total_duration > 225:
        print(f"NOTICE: Total duration slightly exceeds 3:45 target by {total_duration - 225:.2f}s.")
    else:
        print("PERFECT: Total duration is within the 03:00 - 03:45 target range.")

    summary_file = os.path.join(os.path.dirname(__file__), "audio_summary.json")
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump({
            "total_duration_sec": total_duration,
            "total_formatted": f"{mins:02d}:{secs:02d}",
            "segments": results
        }, f, indent=2)

if __name__ == "__main__":
    generate_voiceover()
