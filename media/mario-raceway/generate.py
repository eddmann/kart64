#!/usr/bin/env python3
"""Regenerate matching screenshots from the complete source videos.

Run with `uv run --no-project media/mario-raceway/generate.py`.
Requires ffmpeg, ffprobe and cwebp on PATH; uses only the Python standard library.
"""
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MODES = {
    "landscape": ("Landscape full screen", 13.65),
    "portrait": ("Portrait with buttons", 14.80),
    "tour": ("Portrait Tour", 14.24),
}
SECTIONS = [
    ("first-bend", "First bend", 12),
    ("second-lap", "Second-lap drift", 50),
]


def run(*args):
    subprocess.run(args, check=True)


def describe(path):
    probe = json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries",
        "stream=width,height:format=duration", "-of", "json", str(path),
    ]))
    return {
        "file": str(path.relative_to(ROOT)),
        "bytes": path.stat().st_size,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "width": probe["streams"][0]["width"],
        "height": probe["streams"][0]["height"],
        **({"duration": float(probe["format"]["duration"])}
           if "duration" in probe["format"] else {}),
    }


def main():
    manifest = {
        "course": "Mario Raceway",
        "texture_pack": "mk64-reloaded-phone-karts128.o2r",
        "capture_date": "2026-10-07",
        "environment": "iOS 26 Simulator, Home Screen PWA",
        "steering": "Existing test autopilot; not manually driven",
        "audio": "Silent",
        "alignment": "Same race-clock sections; visually checked within 0.1 seconds. Approximate across independent captures.",
        "sources": {},
        "sections": [],
    }
    for mode, (label, offset) in MODES.items():
        source = ROOT / "sources" / f"{mode}.mp4"
        manifest["sources"][mode] = {
            "label": label, "race_clock_zero_seconds": offset, **describe(source),
        }
    for section_id, label, screenshot_time in SECTIONS:
        section = {
            "id": section_id, "label": label,
            "screenshot_race_seconds": screenshot_time,
            "modes": {},
        }
        for mode, (_, offset) in MODES.items():
            source = ROOT / "sources" / f"{mode}.mp4"
            shot = ROOT / "screenshots" / f"{section_id}-{mode}.webp"
            shot.parent.mkdir(exist_ok=True)
            with tempfile.TemporaryDirectory() as temporary:
                frame = Path(temporary) / "frame.png"
                run("ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                    "-ss", str(offset + screenshot_time), "-i", str(source),
                    "-frames:v", "1", str(frame))
                run("cwebp", "-quiet", "-q", "88", str(frame), "-o", str(shot))
            section["modes"][mode] = {
                "screenshot_source_seconds": round(offset + screenshot_time, 3),
                "screenshot": describe(shot),
            }
        manifest["sections"].append(section)
    (ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print("Generated 6 matching gameplay screenshots.")


if __name__ == "__main__":
    main()
