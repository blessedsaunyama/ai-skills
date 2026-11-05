# Formats, sizes and safe zones

| Key | Final size | Preview size | Best for | UI safe zone at final size (top, bottom, left, right px) |
|---|---|---|---|---|
| `9x16` | 1080x1920 | 720x1280 | TikTok, Reels, Shorts, Stories, WhatsApp Status | 220, 420, 60, 140 |
| `16x9` | 1920x1080 | 1280x720 | YouTube, projector/TV | 54, 54, 96, 96 |
| `1x1` | 1080x1080 | 720x720 | Facebook/Instagram feed, WhatsApp chats | 60, 140, 60, 60 |
| `4x5` | 1080x1350 | 720x900 | Instagram/Facebook feed | 70, 160, 60, 60 |

- Keep faces, captions and key props **inside** the safe zone: the platform's buttons and captions cover the rest.
- 9:16: stage action in depth and keep the ground around 60–65 % of the height, so captions sit over the ground instead of the action.
- 16:9: fill the sides; a projector crops the edges. Put code and output side by side.
- 1:1 and 4:5: like 9:16 but shorter: fewer stacked items; 1:1 suits side-by-side layouts too.
- Burned-in captions sit just above the bottom safe margin: keep the bottom ~20 % of the safe area free of key content.
- **BEST mode** (default for py2d): one render per format, each with its own camera (`camera_<fmt>` in scene.json).
- **FAST mode:** one master render, cropped by `python shared/formats.py crop master.mp4 9x16,16x9`. Cheaper, but the framing is a compromise. Use it for the engines that are slow (Toon 3D, Blender).
- Tools: `python shared/formats.py table | size <fmt> <quality> | safe <fmt> | crop <video> <fmts>`.
