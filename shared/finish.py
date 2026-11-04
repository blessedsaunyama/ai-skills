#!/usr/bin/env python3
"""Encode frames (+ audio) to MP4, then run QA. Works the same for every engine and on every OS.

  python shared/finish.py FRAMES_DIR OUT.mp4 [--audio mix.wav] [--quality preview|final] [--fps 30]
                          [--ass caps_9x16.ass] [--srt caps.srt] [--end-card]

- No --audio: a silent stereo track is added (platforms expect an audio stream).
- Audio is loudness-normalised to -14 LUFS (social video standard) unless --no-loudnorm.
- --ass burns styled captions in (made by shared/captions.py). --srt adds a soft subtitle track viewers can switch on.
- --end-card appends a 1.5 s "Made with animation-studio" card. Opt-in only: never add it unless the user asked.
- QA: duration/size check, black and frozen spans, loudness, and OUT_qa.jpg (a contact sheet of the video).
Runs ffmpeg at low priority. Needs ffmpeg + ffprobe (found on PATH or in the usual install folders).
"""
import argparse, os, re, subprocess, sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import SKILL_DIR, low_priority, need_tool, utf8  # noqa: E402

CRF = {"preview": ("veryfast", "21"), "final": ("slow", "17")}


def filter_path(p):
    """Escape a path for an ffmpeg filter argument (Windows drive colons and quotes)."""
    return Path(p).resolve().as_posix().replace(":", r"\:").replace("'", r"\'")


def end_card(ffmpeg, out, preset, crf, fps):
    """Append a short, quiet credit card (Pillow draws it with a system font)."""
    sys.path.insert(0, str(SKILL_DIR / "engines" / "py2d"))
    from PIL import Image, ImageDraw
    from canvas import font
    probe = subprocess.run([need_tool("ffprobe"), "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                            "-of", "csv=p=0", str(out)], capture_output=True, text=True).stdout.strip().split(",")
    W, H = int(probe[0]), int(probe[1])
    card = out.with_name(out.stem + "_endcard.png")
    im = Image.new("RGB", (W, H), (21, 21, 26)); d = ImageDraw.Draw(im)
    u = min(W, H) / 1080
    d.text((W / 2, H / 2 - 20 * u), "Made with", font=font(40 * u, "regular"), fill=(170, 170, 180), anchor="mm")
    d.text((W / 2, H / 2 + 40 * u), "animation-studio", font=font(64 * u), fill=(255, 255, 255), anchor="mm")
    im.save(card)
    tmp = out.with_suffix(".card.mp4")
    subprocess.run([ffmpeg, "-v", "error", "-y", "-i", str(out), "-loop", "1", "-framerate", str(fps), "-t", "1.5", "-i", str(card),
                    "-f", "lavfi", "-t", "1.5", "-i", "anullsrc=r=48000:cl=stereo",
                    "-filter_complex", "[0:v]setsar=1[a0];[1:v]format=yuv420p,setsar=1,fade=t=in:st=0:d=0.3[c];[a0][0:a][c][2:a]concat=n=2:v=1:a=1[v][a]",
                    "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", preset, "-crf", crf, "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(tmp)], check=True)
    os.replace(tmp, out); card.unlink(missing_ok=True)


def main():
    utf8()
    ap = argparse.ArgumentParser()
    ap.add_argument("frames"); ap.add_argument("out"); ap.add_argument("--audio"); ap.add_argument("--quality", default="final")
    ap.add_argument("--fps", type=int, default=30); ap.add_argument("--srt"); ap.add_argument("--ass")
    ap.add_argument("--end-card", action="store_true"); ap.add_argument("--no-loudnorm", action="store_true")
    a = ap.parse_args()
    ffmpeg, ffprobe = need_tool("ffmpeg"), need_tool("ffprobe")
    low_priority()
    out = Path(a.out); out.parent.mkdir(parents=True, exist_ok=True)
    pattern = str(Path(a.frames) / "f%04d.jpg")
    if not (Path(a.frames) / "f0000.jpg").exists():
        sys.exit(f"no f0000.jpg in {a.frames}")
    preset, crf = CRF.get(a.quality, CRF["final"])
    cmd = [ffmpeg, "-v", "error", "-y", "-framerate", str(a.fps), "-i", pattern]
    cmd += ["-i", a.audio] if a.audio else ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo"]
    if a.ass:
        cmd += ["-vf", f"ass='{filter_path(a.ass)}'"]
    cmd += ["-map", "0:v:0", "-map", "1:a:0"]
    if a.audio and not a.no_loudnorm:                     # two-pass loudnorm: measure, then correct exactly (one pass undershoots short clips)
        target = "I=-14:TP=-1.5:LRA=11"
        meas = subprocess.run([ffmpeg, "-hide_banner", "-i", a.audio, "-af", f"loudnorm={target}:print_format=json", "-f", "null", "-"],
                              capture_output=True, text=True).stderr
        m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", meas, re.S)
        if m:
            import json
            j = json.loads(m.group(0))
            target += (f":measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}"
                       f":measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true")
        cmd += ["-af", f"loudnorm={target}"]
    cmd += ["-c:v", "libx264", "-preset", preset, "-crf", crf, "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
            "-ar", "48000", "-shortest", "-movflags", "+faststart", str(out)]
    subprocess.run(cmd, check=True)
    if a.end_card:
        end_card(ffmpeg, out, preset, crf, a.fps)
    if a.srt:
        tmp = out.with_suffix(".subs.mp4")
        subprocess.run([ffmpeg, "-v", "error", "-y", "-i", str(out), "-i", a.srt, "-map", "0", "-map", "1", "-c", "copy",
                        "-c:s", "mov_text", "-metadata:s:s:0", "language=eng", str(tmp)], check=True)
        os.replace(tmp, out)
    # ---- QA ----
    info = subprocess.run([ffprobe, "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height,r_frame_rate",
                           "-of", "compact", str(out)], capture_output=True, text=True).stdout.strip()
    print(info)
    err = subprocess.run([ffmpeg, "-i", str(out), "-vf", "freezedetect=n=0.0005:d=0.6,blackdetect=d=0.1", "-an", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    issues = re.findall(r"(freeze_start: [\d.]+|black_start:[\d.]+)", err)
    print("QA black/frozen spans:", ", ".join(issues) if issues else "none",
          "(a still span is fine if it matches a pause; black at the very end = end-card fade)" if issues else "")
    if a.audio:
        lo = subprocess.run([ffmpeg, "-i", str(out), "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
        m = re.findall(r"I:\s+(-?[\d.]+) LUFS", lo)
        print(f"QA loudness: {m[-1]} LUFS (target -14)" if m else "QA loudness: n/a")
    qa = out.with_name(out.stem + "_qa.jpg")
    subprocess.run([ffmpeg, "-v", "error", "-y", "-i", str(out), "-vf", "fps=2,scale='if(gt(iw,ih),320,180)':-2,tile=6x2",
                    "-frames:v", "1", str(qa)], check=True)
    print(f"{out}  ({out.stat().st_size / 1e6:.1f} MB)\nQA sheet: {qa}")


if __name__ == "__main__":
    main()
