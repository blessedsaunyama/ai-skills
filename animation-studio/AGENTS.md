# For AI coding agents (Codex, OpenCode, Gemini CLI, Claude Code, ...)

This folder is the **animation-studio** skill. To use it:

1. **Read `SKILL.md` first and follow it step by step.** It is a short router: it tells you which other files to load (one content pack, one style, one engine README) and in which order.
2. The skill folder is the folder that contains `SKILL.md`. Run every tool with a path relative to it (e.g. `python "<skill folder>/shared/hwcheck.py"`) and keep paths quoted.
3. Never skip the hardware check (`shared/hwcheck.py`) or the estimate (`shared/estimate.py`) before rendering, and never run two renders at once.
4. Ask the user before installing, deleting or overwriting anything. Python packages go only into `<skill folder>/.venv` via `shared/setup_check.py --install`.
5. Never invent Bible verses, quotes, APIs, versions or facts. Fetch or run them, or mark them UNVERIFIED.
