#!/usr/bin/env python3
"""Editor projects from a finished render: Kdenlive, Shotcut, OpenShot, DaVinci Resolve (FCPXML), Blender VSE, or a generic pack.

1) prepare: cut the render into shot clips + audio stems + captions, and write timeline.json (shared by every editor)
  python shared/editors.py prepare --frames FRAMES_DIR --shots "0-74:wide,75-149:close" --final out/Title_9x16.mp4
         [--voice voice.wav] [--music music.wav] [--sfx sfx.wav] [--srt out/Title.srt] [--fps 30] --out editor/Title
2) export: write the project for ONE editor and validate it
  python shared/editors.py export editor/Title/timeline.json --editor kdenlive|shotcut|openshot|resolve|blender-vse|pack [--open-check]
Validation: a Kdenlive project is rendered BY KDENLIVE ITSELF (kdenlive --render) and a Shotcut project by MLT (Shotcut's
engine); size, fps, length, picture (shots in order) and audio must match the final MP4. OpenShot/FCPXML are parsed and their length checked. Blender VSE
is re-opened in Blender and its strips counted. --open-check also starts the editor with the project and checks it stays open.
Media paths in projects are absolute, so keep the folder where it is (or relink in the editor).
"""
import argparse, json, os, shutil, subprocess, sys, time, uuid
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from common import OS, SKILL_DIR, find_tool, need_tool, run, utf8  # noqa: E402

EDITORS = ["kdenlive", "shotcut", "openshot", "resolve", "blender-vse", "pack"]


def probe_duration(path):
    out = subprocess.run([need_tool("ffprobe"), "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True).stdout.strip()
    return float(out) if out else 0.0


# ---------------------------------------------------------------- prepare
def prepare(a):
    ff = need_tool("ffmpeg")
    out = Path(a.out).resolve(); media = out / "media"; media.mkdir(parents=True, exist_ok=True)
    fps = a.fps
    shots = []
    for i, part in enumerate(a.shots.split(","), 1):
        rng, _, name = part.partition(":")
        f0, f1 = (int(x) for x in rng.split("-"))
        clip = media / f"{i:02d}_{(name or 'shot').replace(' ', '-')}.mp4"
        subprocess.run([ff, "-v", "error", "-y", "-framerate", str(fps), "-start_number", str(f0), "-i", str(Path(a.frames) / "f%04d.jpg"),
                        "-frames:v", str(f1 - f0 + 1), "-c:v", "libx264", "-crf", "16", "-g", "15", "-pix_fmt", "yuv420p",
                        "-movflags", "+faststart", str(clip)], check=True)
        shots.append({"name": name or f"shot {i}", "file": str(clip), "start": f0, "frames": f1 - f0 + 1})
    audio = {}
    for k in ("voice", "music", "sfx"):
        src = getattr(a, k)
        if src:
            dst = media / f"{k}.wav"
            subprocess.run([ff, "-v", "error", "-y", "-i", src, "-ar", "48000", "-ac", "2", str(dst)], check=True)   # editors prefer 48 kHz stereo
            audio[k] = {"file": str(dst), "frames": int(round(probe_duration(dst) * fps))}
    srt = None
    if a.srt:
        srt = str(media / Path(a.srt).name); shutil.copy2(a.srt, srt)
    probe = subprocess.run([need_tool("ffprobe"), "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                            "-of", "csv=p=0", a.final], capture_output=True, text=True).stdout.strip().split(",")
    total = sum(s["frames"] for s in shots)
    tl = {"title": out.name, "fps": fps, "width": int(probe[0]), "height": int(probe[1]), "frames": total,
          "final": str(Path(a.final).resolve()), "final_seconds": probe_duration(a.final), "shots": shots, "audio": audio, "captions": srt}
    (out / "timeline.json").write_text(json.dumps(tl, indent=1), encoding="utf-8")
    print(f"timeline: {len(shots)} shots, {total} frames ({total / fps:.2f} s), audio: {', '.join(audio) or 'none'}, captions: {'yes' if srt else 'no'}")
    print(out / "timeline.json")


# ---------------------------------------------------------------- MLT helpers (Kdenlive + Shotcut)
def _prop(el, name, value):
    p = ET.SubElement(el, "property", name=name); p.text = str(value); return p


def _producer(root, pid, path, frames, extra):
    p = ET.SubElement(root, "producer", id=pid, **{"in": "0", "out": str(frames - 1)})
    _prop(p, "length", frames); _prop(p, "eof", "pause"); _prop(p, "resource", path); _prop(p, "mlt_service", "avformat-novalidate")
    _prop(p, "seekable", 1); _prop(p, "audio_index", -1 if extra.get("video_only") else 0)
    _prop(p, "video_index", -1 if extra.get("audio_only") else 0)
    for k, v in extra.get("props", {}).items():
        _prop(p, k, v)
    return p


def _profile(root, tl):
    from math import gcd
    g = gcd(tl["width"], tl["height"])
    ET.SubElement(root, "profile", description=f"{tl['width']}x{tl['height']} {tl['fps']} fps", width=str(tl["width"]), height=str(tl["height"]),
                  progressive="1", sample_aspect_num="1", sample_aspect_den="1", display_aspect_num=str(tl["width"] // g),
                  display_aspect_den=str(tl["height"] // g), frame_rate_num=str(tl["fps"]), frame_rate_den="1", colorspace="709")


STOCK_PROFILES = {(1920, 1080, 30): "atsc_1080p_30", (1280, 720, 30): "atsc_720p_30", (1080, 1920, 30): "vertical_hd_30",
                  (1920, 1080, 25): "atsc_1080p_25", (1280, 720, 25): "atsc_720p_25", (1920, 1080, 60): "atsc_1080p_60", (1080, 1920, 60): "vertical_hd_60"}


def kdenlive_profile(tl, dst):
    """A stock MLT profile name when one matches, otherwise a custom profile file next to the project (Kdenlive accepts its path)."""
    key = (tl["width"], tl["height"], tl["fps"])
    if key in STOCK_PROFILES:
        return STOCK_PROFILES[key]
    from math import gcd
    g = gcd(tl["width"], tl["height"])
    pf = Path(dst).with_name(f"profile_{tl['width']}x{tl['height']}_{tl['fps']}")
    lines = [f"description={tl['width']}x{tl['height']} {tl['fps']} fps (animation-studio)", f"frame_rate_num={tl['fps']}", "frame_rate_den=1",
             f"width={tl['width']}", f"height={tl['height']}", "progressive=1", "sample_aspect_num=1", "sample_aspect_den=1",
             f"display_aspect_num={tl['width'] // g}", f"display_aspect_den={tl['height'] // g}", "colorspace=709"]
    pf.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return pf.resolve().as_posix()


def write_kdenlive(tl, dst):
    """Kdenlive document version 1.04 (Kdenlive 22 layout): Kdenlive 23+ upgrades it to its sequence format on open."""
    root = ET.Element("mlt", LC_NUMERIC="C", producer="main_bin", version="7.0.0", root=str(Path(dst).parent))
    _profile(root, tl)
    bin_items, nid = [], 2
    clips = []                                   # (bin producer id, kdenlive id, path, frames, kind)
    for i, s in enumerate(tl["shots"]):
        clips.append((f"producer{len(clips)}", nid, s["file"], s["frames"], "video")); nid += 1
    for k, au in tl["audio"].items():
        clips.append((f"producer{len(clips)}", nid, au["file"], au["frames"], k)); nid += 1
    for pid, kid, path, frames, kind in clips:
        _producer(root, pid, path, frames, {"video_only": kind == "video", "audio_only": kind != "video",
                                             "props": {"kdenlive:id": kid, "kdenlive:clip_type": 2 if kind == "video" else 1,
                                                       "kdenlive:folderid": -1, "kdenlive:clipname": Path(path).name}})
    mb = ET.SubElement(root, "playlist", id="main_bin")
    for k, v in (("kdenlive:docproperties.profile", kdenlive_profile(tl, dst)), ("kdenlive:docproperties.version", "1.04"), ("kdenlive:docproperties.kdenliveversion", "22.08.0"),
                 ("kdenlive:docproperties.audioChannels", 2), ("kdenlive:docproperties.documentid", int(time.time() * 1000)),
                 ("kdenlive:docproperties.position", 0), ("kdenlive:docproperties.zoom", 8), ("kdenlive:docproperties.verticalzoom", 1),
                 ("kdenlive:docproperties.activeTrack", 0), ("kdenlive:docproperties.enableproxy", 0), ("kdenlive:expandedFolders", ""),
                 ("kdenlive:documentnotes", f"Made with animation-studio. Shots: {', '.join(s['name'] for s in tl['shots'])}."),
                 ("xml_retain", 1)):
        _prop(mb, k, v)
    for pid, kid, path, frames, kind in clips:
        ET.SubElement(mb, "entry", producer=pid, **{"in": "0", "out": str(frames - 1)})
    blk = ET.SubElement(root, "producer", id="black_track", **{"in": "0", "out": str(tl["frames"] - 1)})
    for k, v in (("length", 2147483647), ("eof", "continue"), ("resource", "black"), ("aspect_ratio", 1), ("mlt_service", "color"),
                 ("mlt_image_format", "rgba"), ("set.test_audio", 0)):
        _prop(blk, k, v)
    tracks, n = [], [0]

    def track(entries, audio, name):
        a_id, b_id = f"playlist{n[0]}", f"playlist{n[0] + 1}"; n[0] += 2
        insts = []
        for (pid, kid, path, frames, kind), start in entries:      # producers MUST be defined before the playlist that uses them
            inst = f"{pid}_t{len(tracks)}"
            _producer(root, inst, path, frames, {"video_only": not audio, "audio_only": audio,
                                                 "props": {"kdenlive:id": kid, "kdenlive:clip_type": 1 if audio else 2, "kdenlive:folderid": -1}})
            insts.append(inst)
        pa = ET.SubElement(root, "playlist", id=a_id)
        if audio:
            _prop(pa, "kdenlive:audio_track", 1)
        pos = 0
        for ((pid, kid, path, frames, kind), start), inst in zip(entries, insts):
            if start > pos:
                ET.SubElement(pa, "blank", length=str(start - pos))
            e = ET.SubElement(pa, "entry", producer=inst, **{"in": "0", "out": str(frames - 1)})
            _prop(e, "kdenlive:id", kid)
            pos = start + frames
        pb = ET.SubElement(root, "playlist", id=b_id)
        if audio:
            _prop(pb, "kdenlive:audio_track", 1)
        tr = ET.SubElement(root, "tractor", id=f"tractor{len(tracks)}", **{"in": "0"})
        if audio:
            _prop(tr, "kdenlive:audio_track", 1)
        _prop(tr, "kdenlive:track_name", name); _prop(tr, "kdenlive:trackheight", 67); _prop(tr, "kdenlive:timeline_active", 1)
        ET.SubElement(tr, "track", producer=a_id, hide="video" if audio else "audio")
        ET.SubElement(tr, "track", producer=b_id, hide="video" if audio else "audio")
        tracks.append((tr.get("id"), audio))

    by_kind = {c[4]: c for c in clips if c[4] != "video"}
    for k, label in (("sfx", "SFX"), ("music", "Music"), ("voice", "Voice")):       # Kdenlive lists audio tracks bottom-up
        if k in by_kind:
            track([(by_kind[k], 0)], True, label)
    vids, pos = [], 0
    for c, s in zip([c for c in clips if c[4] == "video"], tl["shots"]):
        vids.append((c, pos)); pos += s["frames"]
    track(vids, False, "Shots")
    main = ET.SubElement(root, "tractor", id="tractor_main", **{"in": "0", "out": str(tl["frames"] - 1)})
    ET.SubElement(main, "track", producer="black_track")
    for tid, _ in tracks:
        ET.SubElement(main, "track", producer=tid)
    for i, (tid, audio) in enumerate(tracks, 1):
        t = ET.SubElement(main, "transition", id=f"transition{i}")
        for k, v in (("a_track", 0), ("b_track", i), ("mlt_service", "mix" if audio else "qtblend"), ("kdenlive_id", "mix" if audio else "qtblend"),
                     ("internal_added", 237), ("always_active", 1)) + ((("accepts_blanks", 1), ("sum", 1)) if audio else ()):
            _prop(t, k, v)
    if tl.get("captions") and os.environ.get("AS_KDENLIVE_SUBFILTER"):   # experiment switch (see the test log)
        sub = Path(str(dst) + ".srt"); shutil.copy2(tl["captions"], sub)
        f = ET.SubElement(main, "filter", id="subtitles")
        for k, v in (("mlt_service", "avfilter.subtitles"), ("internal_added", 237), ("av.filename", sub.as_posix()), ("av.alpha", 1)):
            _prop(f, k, v)
    ET.ElementTree(root).write(dst, encoding="utf-8", xml_declaration=True)


def write_shotcut(tl, dst):
    root = ET.Element("mlt", LC_NUMERIC="C", version="7.0.0", title="Shotcut (animation-studio)", producer="main_bin")
    _profile(root, tl)
    mb = ET.SubElement(root, "playlist", id="main_bin")
    _prop(mb, "xml_retain", 1)
    bg = ET.SubElement(root, "producer", id="black", **{"in": "0", "out": str(tl["frames"] - 1)})
    for k, v in (("length", tl["frames"]), ("eof", "pause"), ("resource", "0"), ("aspect_ratio", 1), ("mlt_service", "color"),
                 ("mlt_image_format", "rgba"), ("set.test_audio", 0)):
        _prop(bg, k, v)
    bgp = ET.SubElement(root, "playlist", id="background")
    ET.SubElement(bgp, "entry", producer="black", **{"in": "0", "out": str(tl["frames"] - 1)})
    tracks = []
    for i, s in enumerate(tl["shots"]):                  # every producer is defined BEFORE the playlists that use it
        _producer(root, f"shot{i}", s["file"], s["frames"], {"video_only": True, "props": {"shotcut:caption": s["name"]}})
    for k, au in tl["audio"].items():
        _producer(root, f"audio_{k}", au["file"], au["frames"], {"audio_only": True, "props": {"shotcut:caption": k}})
    vp = ET.SubElement(root, "playlist", id="playlist0"); _prop(vp, "shotcut:video", 1); _prop(vp, "shotcut:name", "V1 Shots")
    for i, s in enumerate(tl["shots"]):
        ET.SubElement(vp, "entry", producer=f"shot{i}", **{"in": "0", "out": str(s["frames"] - 1)})
    tracks.append(("playlist0", False))
    for j, (k, au) in enumerate(tl["audio"].items(), 1):
        ap = ET.SubElement(root, "playlist", id=f"playlist{j}"); _prop(ap, "shotcut:audio", 1); _prop(ap, "shotcut:name", f"A{j} {k.title()}")
        ET.SubElement(ap, "entry", producer=f"audio_{k}", **{"in": "0", "out": str(au["frames"] - 1)})
        tracks.append((f"playlist{j}", True))
    tr = ET.SubElement(root, "tractor", id="tractor0", title="Shotcut version 26", **{"in": "0", "out": str(tl["frames"] - 1)})
    _prop(tr, "shotcut", 1); _prop(tr, "shotcut:projectAudioChannels", 2); _prop(tr, "shotcut:projectFolder", 0)
    ET.SubElement(tr, "track", producer="background")
    for pid, audio in tracks:
        ET.SubElement(tr, "track", producer=pid, **({"hide": "video"} if audio else {}))
    for i, (pid, audio) in enumerate(tracks, 1):
        t = ET.SubElement(tr, "transition", id=f"transition{i}")
        for k, v in (("a_track", 0), ("b_track", i), ("mlt_service", "mix"), ("always_active", 1), ("sum", 1)):
            _prop(t, k, v)
        if not audio:
            t2 = ET.SubElement(tr, "transition", id=f"blend{i}")
            for k, v in (("a_track", 0), ("b_track", i), ("version", "0.1"), ("mlt_service", "frei0r.cairoblend"), ("disable", 1)):
                _prop(t2, k, v)
    ET.ElementTree(root).write(dst, encoding="utf-8", xml_declaration=True)
    if tl.get("captions"):
        shutil.copy2(tl["captions"], Path(dst).with_suffix(".srt"))   # Shotcut: Timeline > Subtitles > Import


def write_fcpxml(tl, dst):
    """FCPXML 1.9 for DaVinci Resolve (File > Import > Timeline). Times are rational seconds (frames/fps)."""
    fps = tl["fps"]
    t = lambda f: f"{f}/{fps}s" if f else "0s"
    root = ET.Element("fcpxml", version="1.9")
    res = ET.SubElement(root, "resources")
    ET.SubElement(res, "format", id="r0", name=f"FFVideoFormat{tl['height']}p{fps}", frameDuration=f"1/{fps}s",
                  width=str(tl["width"]), height=str(tl["height"]))
    items = []
    for i, s in enumerate(tl["shots"], 1):
        a = ET.SubElement(res, "asset", id=f"v{i}", name=s["name"], start="0s", duration=t(s["frames"]), hasVideo="1", hasAudio="0", format="r0")
        ET.SubElement(a, "media-rep", kind="original-media", src=Path(s["file"]).as_uri())
        items.append(("v", i, s))
    for j, (k, au) in enumerate(tl["audio"].items(), 1):
        a = ET.SubElement(res, "asset", id=f"a{j}", name=k, start="0s", duration=t(au["frames"]), hasVideo="0", hasAudio="1", audioSources="1", audioChannels="2", audioRate="48000")
        ET.SubElement(a, "media-rep", kind="original-media", src=Path(au["file"]).as_uri())
    lib = ET.SubElement(root, "library"); ev = ET.SubElement(lib, "event", name=tl["title"])
    pr = ET.SubElement(ev, "project", name=tl["title"])
    seq = ET.SubElement(pr, "sequence", format="r0", duration=t(tl["frames"]), tcStart="0s", tcFormat="NDF", audioLayout="stereo", audioRate="48k")
    spine = ET.SubElement(seq, "spine")
    off = 0
    for n, (_, i, s) in enumerate(items):
        clip = ET.SubElement(spine, "asset-clip", ref=f"v{i}", name=s["name"], offset=t(off), start="0s", duration=t(s["frames"]), format="r0")
        if n == 0:                               # audio stems ride on the first clip as connected clips on lanes -1, -2, -3
            for j, (k, au) in enumerate(tl["audio"].items(), 1):
                ET.SubElement(clip, "asset-clip", ref=f"a{j}", name=k, lane=str(-j), offset="0s", start="0s", duration=t(au["frames"]))
        off += s["frames"]
    ET.ElementTree(root).write(dst, encoding="utf-8", xml_declaration=True)
    if tl.get("captions"):
        shutil.copy2(tl["captions"], Path(dst).with_suffix(".srt"))   # Resolve: File > Import > Subtitle


def write_openshot(tl, dst):
    """OpenShot .osp (JSON). Experimental: validated by parsing and timing; open it in OpenShot to confirm."""
    fps = tl["fps"]
    files, clips = [], []
    lay = {"video": 4000000, "voice": 3000000, "music": 2000000, "sfx": 1000000}
    pos = 0.0
    for s in tl["shots"]:
        fid = uuid.uuid4().hex[:10].upper(); dur = s["frames"] / fps
        files.append({"id": fid, "path": s["file"], "media_type": "video", "has_video": True, "has_audio": False, "duration": dur,
                      "width": tl["width"], "height": tl["height"], "fps": {"num": fps, "den": 1}, "video_length": str(s["frames"])})
        clips.append({"id": uuid.uuid4().hex[:10].upper(), "file_id": fid, "layer": lay["video"], "position": pos, "start": 0.0, "end": dur,
                      "duration": dur, "title": s["name"], "reader": {"path": s["file"], "has_video": True, "has_audio": False}})
        pos += dur
    for k, au in tl["audio"].items():
        fid = uuid.uuid4().hex[:10].upper(); dur = au["frames"] / fps
        files.append({"id": fid, "path": au["file"], "media_type": "audio", "has_video": False, "has_audio": True, "duration": dur})
        clips.append({"id": uuid.uuid4().hex[:10].upper(), "file_id": fid, "layer": lay[k], "position": 0.0, "start": 0.0, "end": dur,
                      "duration": dur, "title": k, "reader": {"path": au["file"], "has_video": False, "has_audio": True}})
    doc = {"id": "T0", "fps": {"num": fps, "den": 1}, "display_ratio": {"num": tl["width"], "den": tl["height"]},
           "pixel_ratio": {"num": 1, "den": 1}, "width": tl["width"], "height": tl["height"], "sample_rate": 48000, "channels": 2,
           "channel_layout": 3, "duration": tl["frames"] / fps, "files": files, "clips": clips, "effects": [], "markers": [],
           "layers": [{"id": f"L{i}", "number": n, "label": lbl, "lock": False} for i, (lbl, n) in
                      enumerate((("Shots", lay["video"]), ("Voice", lay["voice"]), ("Music", lay["music"]), ("SFX", lay["sfx"]))) ],
           "progress": [], "history": {"undo": [], "redo": []}, "version": {"openshot-qt": "3.0.0", "libopenshot": "0.4.0"}}
    Path(dst).write_text(json.dumps(doc, indent=1), encoding="utf-8")
    if tl.get("captions"):
        shutil.copy2(tl["captions"], Path(dst).with_suffix(".srt"))


BLENDER_VSE = r'''
import bpy, json, sys
tl = json.load(open(sys.argv[sys.argv.index("--") + 1], encoding="utf-8")); dst = sys.argv[sys.argv.index("--") + 2]
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.fps = tl["fps"]; sc.render.resolution_x = tl["width"]; sc.render.resolution_y = tl["height"]; sc.render.resolution_percentage = 100
sc.frame_start = 1; sc.frame_end = tl["frames"]
sc.view_settings.view_transform = "Standard"      # video editing: no AgX/Filmic tint on the clips
try:
    sc.view_settings.look = "None"
except Exception:
    pass
ed = sc.sequence_editor_create()
coll = ed.strips if hasattr(ed, "strips") else ed.sequences   # Blender 5: strips; 4.x: sequences
pos = 1
for s in tl["shots"]:
    st = coll.new_movie(name=s["name"], filepath=s["file"], channel=4, frame_start=pos)
    pos += s["frames"]
for ch, (k, au) in zip((1, 2, 3), tl["audio"].items()):
    coll.new_sound(name=k, filepath=au["file"], channel=ch, frame_start=1)
if tl.get("captions"):
    import re
    txt = open(tl["captions"], encoding="utf-8").read()
    for m in re.finditer(r"(\d+):(\d+):(\d+),(\d+) --> (\d+):(\d+):(\d+),(\d+)\s*\n(.+?)(?:\n\n|\Z)", txt, re.S):
        g = [int(x) for x in m.groups()[:8]]
        a = (g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000) * tl["fps"]; b = (g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000) * tl["fps"]
        t = coll.new_effect(name="cap", type="TEXT", channel=5, frame_start=int(a) + 1, length=max(1, int(b - a))) if bpy.app.version >= (4, 2, 0) else \
            coll.new_effect(name="cap", type="TEXT", channel=5, frame_start=int(a) + 1, frame_end=int(b) + 1)
        t.text = m.group(9).strip().replace("\n", " "); t.font_size = int(tl["height"] * 0.035); t.location = (0.5, 0.18)
        t.use_shadow = True
bpy.ops.wm.save_as_mainfile(filepath=dst)
print("VSE_OK", len(coll), "strips")
'''
BLENDER_RENDER = r'''
import bpy, sys
out = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene; r = sc.render; im = r.image_settings
try:
    im.media_type = "VIDEO"                      # Blender 5.x
except Exception:
    pass
im.file_format = "FFMPEG"
r.ffmpeg.format = "MPEG4"; r.ffmpeg.codec = "H264"; r.ffmpeg.audio_codec = "AAC"; r.ffmpeg.audio_channels = "STEREO"
r.filepath = out; r.use_file_extension = False
bpy.ops.render.render(animation=True)
print("VSE_RENDER_OK")
'''
BLENDER_CHECK = r'''
import bpy
ed = bpy.context.scene.sequence_editor; coll = ed.strips if hasattr(ed, "strips") else ed.sequences   # Blender 5: strips; 4.x: sequences
print("VSE_CHECK", len(coll), bpy.context.scene.frame_end, bpy.context.scene.render.fps, max(s.frame_final_end for s in coll) - 1)
'''


def write_blender_vse(tl, dst):
    blender = need_tool("blender")
    import tempfile
    sp = Path(tempfile.gettempdir()) / "as_vse.py"; sp.write_text(BLENDER_VSE, encoding="utf-8")
    tj = Path(tempfile.gettempdir()) / "as_vse.json"; tj.write_text(json.dumps(tl), encoding="utf-8")
    r = subprocess.run([blender, "-b", "--factory-startup", "--python-exit-code", "1", "-P", str(sp), "--", str(tj), str(dst)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if "VSE_OK" not in r.stdout:
        print(r.stdout[-1500:], r.stderr[-800:]); sys.exit("Blender VSE export failed")


def write_pack(tl, dst_dir):
    guide = [f"EDITOR PACK: {tl['title']}", "", f"Video: {tl['width']}x{tl['height']}, {tl['fps']} fps, {tl['frames'] / tl['fps']:.2f} s ({tl['frames']} frames)", "",
             "Works with any editor (CapCut, iMovie, Premiere, Clipchamp, VN, ...):",
             f"1. Create a new project at {tl['width']}x{tl['height']}, {tl['fps']} fps.",
             "2. Import everything in the media/ folder.",
             "3. Put the numbered shot clips on the main video track in order (01, 02, ...), with no gaps:"]
    pos = 0
    for s in tl["shots"]:
        guide.append(f"     {Path(s['file']).name:28s} at {pos / tl['fps']:6.2f} s, length {s['frames'] / tl['fps']:.2f} s ({s['name']})"); pos += s["frames"]
    guide += ["4. Put each audio stem on its own audio track, starting at 0.00 s:"] + \
             [f"     {Path(au['file']).name}  ({k})" for k, au in tl["audio"].items()] + \
             ["5. Captions: import the .srt file (CapCut: Text > Captions > Import / 'Auto captions' off), or skip if burned in.",
              "6. Export at the same size and fps. The finished MP4 is included for comparison.", "",
              "Music and sound effects were synthesized by animation-studio (no copyright claims). Voice: see the project notes."]
    (Path(dst_dir) / "EDIT_GUIDE.txt").write_text("\n".join(guide) + "\n", encoding="utf-8")


# ---------------------------------------------------------------- validation
def melt_for(editor):
    from registry import load
    T = load()["tools"]
    order = [editor, "shotcut" if editor == "kdenlive" else "kdenlive"]       # any MLT melt can check either project
    for p in [q for e in order for q in T[e]["detect"].get("melt", [])]:
        q = Path(os.path.expandvars(p.replace("%ProgramFiles%", os.environ.get("ProgramFiles", "C:/Program Files"))).replace("~", str(Path.home())))
        if q.exists():
            return str(q)
    return find_tool("melt")


def mlt_length(dst):
    root = ET.parse(dst).getroot()
    best = 0
    for pl in root.iter("playlist"):
        if pl.get("id") in ("main_bin", "background"):
            continue
        pos = 0
        for ch in pl:
            if ch.tag == "blank":
                pos += int(ch.get("length"))
            elif ch.tag == "entry":
                pos += int(ch.get("out")) - int(ch.get("in")) + 1
        best = max(best, pos)
    return best


def check(tl, editor, dst, open_check=False):
    fps, want = tl["fps"], tl["frames"]
    final_frames = round(tl["final_seconds"] * fps)
    rows = []
    if editor == "kdenlive" and editor_exe("kdenlive"):
        rows += kdenlive_render_check(tl, dst, final_frames)
    if editor in ("kdenlive", "shotcut"):
        ET.parse(dst)
        n = mlt_length(dst)
        vid = sum(s["frames"] for s in tl["shots"])
        rows.append(("XML parses", True, ""))
        rows.append(("video track length = final MP4", abs(vid - final_frames) <= 1, f"{vid} vs {final_frames} frames"))
        melt = melt_for(editor)
        if melt and editor == "shotcut":            # Shotcut plays projects with MLT itself: a full melt render is the real test
            chk = Path(dst).with_name("_melt_check.mp4"); chk.unlink(missing_ok=True)
            subprocess.run([melt, str(dst), "-consumer", f"avformat:{chk}", "vcodec=libx264", "acodec=aac", "real_time=0"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900)
            rows += compare_render(chk, tl, final_frames, "melt (Shotcut's engine)")
            chk.unlink(missing_ok=True)
        elif melt:
            chk = Path(dst).with_name("_check_2s.mp4")
            subprocess.run([melt, str(dst), "in=0", "out=59", "-consumer", f"avformat:{chk}", "vcodec=libx264", "acodec=aac", "real_time=0"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
            d = probe_duration(chk) if chk.exists() else 0
            rows.append(("melt renders 2 s", 1.9 <= d <= 2.1, f"{d:.2f} s ({Path(melt).name})"))
            chk.unlink(missing_ok=True)
        else:
            rows.append(("melt check", None, "melt not found (skipped)"))
    elif editor == "resolve":
        root = ET.parse(dst).getroot()
        dur = root.find(".//sequence").get("duration")
        f = int(dur.split("/")[0]) if "/" in dur else 0
        rows += [("FCPXML parses", True, "version " + root.get("version")), ("sequence length = final MP4", abs(f - final_frames) <= 1, f"{f} vs {final_frames} frames")]
    elif editor == "openshot":
        doc = json.loads(Path(dst).read_text(encoding="utf-8"))
        f = round(doc["duration"] * fps)
        rows += [("JSON parses", True, f"{len(doc['clips'])} clips"), ("project length = final MP4", abs(f - final_frames) <= 1, f"{f} vs {final_frames} frames")]
    elif editor == "blender-vse" and find_tool("blender"):
        import tempfile
        sp = Path(tempfile.gettempdir()) / "as_vse_check.py"; sp.write_text(BLENDER_CHECK, encoding="utf-8")
        out = run([need_tool("blender"), "-b", str(dst), "--factory-startup", "-P", str(sp)], timeout=300)
        line = next((l for l in out.splitlines() if l.startswith("VSE_CHECK")), "")
        rows.append((".blend re-opens in Blender", bool(line), line.replace("VSE_CHECK", "strips / end frame / fps / last frame:") if line else out[-300:]))
        rp = Path(tempfile.gettempdir()) / "as_vse_render.py"; rp.write_text(BLENDER_RENDER, encoding="utf-8")
        mp4 = Path(dst).resolve().with_name("_blender_check.mp4"); mp4.unlink(missing_ok=True)   # absolute: Blender resolves relative paths its own way
        run([need_tool("blender"), "-b", str(dst), "--factory-startup", "-P", str(rp), "--", str(mp4)], timeout=900)
        rows += compare_render(mp4, tl, final_frames, "Blender VSE")
        mp4.unlink(missing_ok=True)
    elif editor == "blender-vse":
        import tempfile
        sp = Path(tempfile.gettempdir()) / "as_vse_check.py"; sp.write_text(BLENDER_CHECK, encoding="utf-8")
        out = run([need_tool("blender"), "-b", str(dst), "--factory-startup", "-P", str(sp)], timeout=300)
        line = next((l for l in out.splitlines() if l.startswith("VSE_CHECK")), "")
        parts = line.split()
        ok = bool(parts) and abs(int(parts[2]) - final_frames) <= 1
        rows.append((".blend re-opens in Blender", bool(parts), f"{parts[1]} strips, end frame {parts[2]}, {parts[3]} fps" if parts else out[-300:]))
        rows.append(("timeline length = final MP4", ok, f"{parts[2] if parts else '?'} vs {final_frames} frames"))
    elif editor == "pack":
        rows.append(("EDIT_GUIDE.txt + media present", (Path(dst) / "EDIT_GUIDE.txt").exists(), ""))
    if open_check and editor in ("kdenlive", "shotcut", "openshot", "blender-vse"):
        rows.append(open_in_editor(editor, dst))
    return rows


def editor_exe(key):
    import glob
    from registry import load
    det = load()["tools"][key]["detect"]
    for c in det.get("commands", []):
        if find_tool(c):
            return find_tool(c)
    for p in det.get(OS, []):
        q = os.path.expandvars(p.replace("%ProgramFiles%", os.environ.get("ProgramFiles", "C:/Program Files")).replace("%LOCALAPPDATA%", os.environ.get("LOCALAPPDATA", ""))).replace("~", str(Path.home()))
        hits = glob.glob(q)
        if hits:
            return hits[0]
    return None


def frame_diff(a, b, fps, times):
    """Mean pixel difference (0-255) between two videos at the given times, over the top 70 % of the frame (captions excluded)."""
    import tempfile
    from PIL import Image, ImageChops, ImageStat
    ff = need_tool("ffmpeg"); out = []
    for t in times:
        ims = []
        for src in (a, b):
            f = Path(tempfile.gettempdir()) / f"as_fd_{len(ims)}.png"
            subprocess.run([ff, "-v", "error", "-y", "-ss", f"{t:.3f}", "-i", str(src), "-frames:v", "1", "-vf", "scale=180:-2", str(f)], check=True)
            ims.append(Image.open(f).convert("RGB"))
        w, h = ims[0].size
        box = (0, 0, w, int(h * 0.7))
        out.append(sum(ImageStat.Stat(ImageChops.difference(ims[0].crop(box), ims[1].resize((w, h)).crop(box))).mean) / 3)
    return out


def kdenlive_render_check(tl, dst, final_frames):
    """Render the project WITH KDENLIVE ITSELF (kdenlive --render) and compare it with the final MP4.
    This is the real test: it uses Kdenlive's own loader, so an empty timeline or a wrong profile shows up here."""
    exe = editor_exe("kdenlive")
    out = Path(dst).with_name("_kdenlive_check.mp4"); out.unlink(missing_ok=True)
    r = subprocess.run([exe, "--render", "--no-welcome", str(dst), str(out.resolve())], capture_output=True, timeout=900)
    if not out.exists():
        return [("Kdenlive renders the project itself", False, f"no output (exit {r.returncode}): Kdenlive could not load the project")]
    rows = compare_render(out, tl, final_frames, "Kdenlive")
    out.unlink(missing_ok=True)
    return rows


def compare_render(out, tl, final_frames, who):
    """Size, fps, length, picture (shots in order) and audio of a render made BY THE EDITOR'S ENGINE vs the final MP4."""
    if not Path(out).exists():
        return [(f"{who} renders the project", False, "no output")]
    info = subprocess.run([need_tool("ffprobe"), "-v", "error", "-select_streams", "v:0", "-count_frames", "-show_entries",
                           "stream=width,height,r_frame_rate,nb_read_frames", "-of", "csv=p=0", str(out)], capture_output=True, text=True).stdout.strip().split(",")
    w, h, rate, n = int(info[0]), int(info[1]), info[2], int(info[3])
    fps_ok = rate == f"{tl['fps']}/1"
    rows = [(f"{who} renders the project", True, f"{w}x{h} @ {rate}, {n} frames"),
            (f"{who}: size + fps = project", (w, h) == (tl["width"], tl["height"]) and fps_ok, f"{w}x{h} @ {rate} vs {tl['width']}x{tl['height']} @ {tl['fps']}")]
    rows.append((f"{who}: length = final MP4", abs(n - final_frames) <= 1, f"{n} vs {final_frames} frames"))
    if (w, h) == (tl["width"], tl["height"]):
        d = frame_diff(out, tl["final"], tl["fps"], [x * tl["frames"] / tl["fps"] for x in (0.1, 0.45, 0.55, 0.9)])
        rows.append((f"{who}: picture = final MP4 (shots in order)", max(d) < 12, "mean pixel difference " + ", ".join(f"{x:.1f}" for x in d) + " (0 = identical)"))
    lo = subprocess.run([need_tool("ffmpeg"), "-i", str(out), "-af", "volumedetect", "-f", "null", "-"], capture_output=True, text=True).stderr
    import re as _re
    m = _re.search(r"mean_volume: (-?[\d.]+) dB", lo)
    rows.append((f"{who}: audio tracks play", bool(m) and float(m.group(1)) > -50, f"mean volume {m.group(1)} dB" if m else "no audio"))
    return rows


def open_in_editor(editor, dst):
    """Start the editor with the project and check it is still running (and, on Windows, which window title it shows)."""
    from registry import load
    det = load()["tools"]["blender" if editor == "blender-vse" else editor]["detect"]
    exe = None
    for c in det.get("commands", []):
        exe = exe or find_tool(c)
    for p in det.get(OS, []):
        import glob
        q = os.path.expandvars(p.replace("%ProgramFiles%", os.environ.get("ProgramFiles", "C:/Program Files")).replace("%LOCALAPPDATA%", os.environ.get("LOCALAPPDATA", ""))).replace("~", str(Path.home()))
        hits = glob.glob(q)
        exe = exe or (hits[0] if hits else None)
    if not exe:
        return ("opens in the editor", None, "editor not found")
    proc = subprocess.Popen([exe, str(dst)])
    time.sleep(35)
    alive = proc.poll() is None
    title = ""
    if OS == "win" and alive:
        title = run(["powershell", "-NoProfile", "-Command", f"(Get-Process -Id {proc.pid}).MainWindowTitle"]).strip()
    if alive:
        proc.terminate()
    return ("opens in the editor", alive and (Path(dst).stem.lower() in title.lower() or not title), f"window: '{title}'" if title else ("running" if alive else "exited"))


def export(a):
    tl = json.loads(Path(a.timeline).read_text(encoding="utf-8"))
    base = Path(a.timeline).parent
    name = tl["title"]
    dst = {"kdenlive": base / f"{name}.kdenlive", "shotcut": base / f"{name}.mlt", "openshot": base / f"{name}.osp",
           "resolve": base / f"{name}.fcpxml", "blender-vse": base / f"{name}.blend", "pack": base}[a.editor]
    {"kdenlive": write_kdenlive, "shotcut": write_shotcut, "openshot": write_openshot, "resolve": write_fcpxml,
     "blender-vse": write_blender_vse, "pack": write_pack}[a.editor](tl, dst)
    if a.editor == "pack":
        shutil.copy2(tl["final"], base / Path(tl["final"]).name)
    print(f"{a.editor}: {dst}")
    rows = check(tl, a.editor, dst, a.open_check)
    print("| Check | Result | Detail |\n|---|---|---|")
    for n, ok, d in rows:
        print(f"| {n} | {'✅' if ok else ('➖' if ok is None else '❌')} | {d} |")
    if any(ok is False for _, ok, _ in rows):
        sys.exit(1)


def main():
    utf8()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prepare")
    p.add_argument("--frames", required=True); p.add_argument("--shots", required=True); p.add_argument("--final", required=True)
    p.add_argument("--voice"); p.add_argument("--music"); p.add_argument("--sfx"); p.add_argument("--srt"); p.add_argument("--fps", type=int, default=30)
    p.add_argument("--out", required=True)
    e = sub.add_parser("export")
    e.add_argument("timeline"); e.add_argument("--editor", required=True, choices=EDITORS); e.add_argument("--open-check", action="store_true")
    a = ap.parse_args()
    prepare(a) if a.cmd == "prepare" else export(a)


if __name__ == "__main__":
    main()
