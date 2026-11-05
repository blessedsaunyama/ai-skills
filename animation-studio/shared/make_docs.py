#!/usr/bin/env python3
"""Generate docs/tools/<tool>.md and docs/editors.md from shared/tools.yaml.

  python shared/make_docs.py
The install sections are produced by the same planner the skill uses at run time (tools.plan) on each OS profile,
so the docs can't disagree with what the skill offers. Re-run after editing tools.yaml.
"""
import os, sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import SKILL_DIR, utf8  # noqa: E402
from sysprofile import SIMULATIONS  # noqa: E402
import tools  # noqa: E402

TARGETS = [("Windows (winget, else Chocolatey or Scoop)", dict(SIMULATIONS["ubuntu"], os="win", os_name="Windows 10/11", managers=["winget", "choco", "scoop"],
                                                             shell="powershell", family=None, native_manager=None)),
           ("macOS (Homebrew; Apple Silicon and Intel)", SIMULATIONS["macos-arm"]),
           ("Ubuntu / Debian / Linux Mint / Pop!_OS", SIMULATIONS["ubuntu"]),
           ("Fedora / RHEL family", SIMULATIONS["fedora"]),
           ("Arch / Manjaro / EndeavourOS", SIMULATIONS["arch"]),
           ("openSUSE", SIMULATIONS["opensuse"])]


def install_block(key, prof):
    t = tools.REG[key]
    if prof["os"] not in t.get("os", []):
        return "Not available on this system."
    p = tools.plan(key, dict(prof, simulated="docs"))
    out = []
    if p["steps"]:
        out.append("```")
        out += [c for c, _ in p["steps"]]
        out.append("```")
        if p["manager"] and "verifiable" in p["manager"]:
            out.append("_The package name could not be verified automatically for this system: the first line searches for it; install only what it finds._")
    if p["manual"]:
        out.append(p["manual"])
    if p["note"]:
        out.append(f"Note: {p['note']}")
    return "\n".join(out)


def tool_page(key, t):
    L = [f"# {t['name']}", "", t["purpose"], "",
         f"- **Kind:** {t['kind']} · **Free:** {t.get('free', 'yes')} · **Systems:** {', '.join({'win': 'Windows', 'mac': 'macOS', 'linux': 'Linux'}[o] for o in t.get('os', []))}",
         f"- **Official download:** {t.get('download', '')}", "",
         "## How animation-studio uses it", t["skill_use"], ""]
    if t.get("project"):
        L += [f"Project file: `{t['project']}`" + (" (opens directly)" if t.get("opens_automatically") else " (import it in the editor)" if t["project"] != "none" else " (none: editor pack)"), ""]
    L += ["## Check whether it is installed", "```", f"python shared/tools.py status --kind {t['kind']}", "```", ""]
    if t.get("install", {}).get("same_as") or t.get("detect", {}).get("same_as"):
        ref = t.get("install", {}).get("same_as") or t["detect"]["same_as"]
        L += ["## Install", f"Installed together with [{tools.REG[ref]['name']}]({ref}.md).", ""]
    else:
        L += ["## Install", "The skill shows the right command for the detected system (`python shared/tools.py cmd " + key + "`) and asks before running anything.", ""]
        for title, prof in TARGETS:
            L += [f"### {title}", install_block(key, prof), ""]
        L += ["### Any Linux (Flatpak / Snap)"]
        inst = t.get("install", {})
        if inst.get("flatpak"):
            L += ["```", f"flatpak install --user -y flathub {inst['flatpak']}", "```"]
        if inst.get("snap"):
            L += ["```", f"sudo snap install {inst['snap']}", "```"]
        if not (inst.get("flatpak") or inst.get("snap")):
            L += ["No Flatpak or Snap package."]
        L += [""]
    L += ["## Troubleshooting"] + [f"- {x}" for x in t.get("troubleshoot", ["Run `python shared/tools.py status` and follow the message."])] + [""]
    L += [f"_Generated from shared/tools.yaml by shared/make_docs.py. Package names verified on 2026-11-05 (see tools.yaml)._", ""]
    return "\n".join(L)


def editors_page():
    eds = [(k, t) for k, t in tools.REG.items() if t["kind"] == "editor"]
    L = ["# Video editors", "", "Ask for **Output: Project file for an editor** (or **Both**) and animation-studio builds a project for ONE editor: every shot on the video track in order, voice / music / SFX on separate audio tracks, captions as a subtitle track or .srt, same fps and size as the MP4. Each project is checked before it is handed over.", "",
         "| Editor | Free? | Windows | macOS | Linux | Project file | Opens automatically? | Check done by the skill |", "|---|---|---|---|---|---|---|---|"]
    checks = {"kdenlive": "Kdenlive renders it itself (--render): size, fps, length, picture vs MP4, audio", "shotcut": "full render with MLT (Shotcut's engine): size, fps, length, picture vs MP4, audio", "openshot": "parse + timing (experimental)",
              "davinci-resolve": "parse + timing", "blender-vse": "re-opened in Blender + strip count + timing", "capcut": "editor pack files present"}
    for k, t in eds:
        osl = t.get("os", [])
        L.append(f"| [{t['name']}](tools/{k}.md) | {t.get('free', 'yes')} | {'✅' if 'win' in osl else '—'} | {'✅' if 'mac' in osl else '—'} | "
                 f"{'✅' if 'linux' in osl else '—'} | `{t['project']}` | {'yes' if t.get('opens_automatically') else ('import: File > Import > Timeline' if t['project'] == '.fcpxml' else 'no: editor pack')} | {checks.get(k, '')} |")
    L += ["", "**Editor pack** (CapCut, or any editor without a supported project format): numbered shot clips, audio stems, the .srt, the finished MP4 and `EDIT_GUIDE.txt` with drag-in steps.",
          "", "Commands:", "```", "python shared/tools.py status --kind editor          # what's installed here",
          "python shared/editors.py prepare --frames ... --shots ... --final ... --out editor/<Title>",
          "python shared/editors.py export editor/<Title>/timeline.json --editor kdenlive", "```", ""]
    return "\n".join(L)


def main():
    utf8()
    d = SKILL_DIR / "docs" / "tools"; d.mkdir(parents=True, exist_ok=True)
    for key, t in tools.REG.items():
        (d / f"{key}.md").write_text(tool_page(key, t), encoding="utf-8")
    (SKILL_DIR / "docs" / "editors.md").write_text(editors_page(), encoding="utf-8")
    print(f"wrote {len(tools.REG)} tool pages + docs/editors.md")


if __name__ == "__main__":
    main()
