# Content pack: General story / ad

Load this file when CONTENT = General story/ad (fables, moral stories, history moments, product or event promos). Default style: **Flat 2D** (Storybook for gentle stories, Modern vector for ads, Stickman for quick comedy). Worked example: `examples/general-wave-back/`.

## 1. Rules (non-negotiable)
1. **Anything presented as true must be verified.** Dates, numbers, quotes, records and "did you know" facts need a reliable source (encyclopaedia, official site, museum, published research) listed in `sources.md`. If you can't verify it, cut it or say "it is said that".
2. **Legends are labelled.** Folk tales, myths and unconfirmed stories are introduced with "Legend says...", "The story goes...", or "One tale tells..." — never stated as history.
3. **No real living people as characters.** Invent names and faces. Historical figures who died long ago may appear only in factual, respectful scenes, with sources. No look-alikes of celebrities.
4. **No brand logos, trademarks or copyrighted characters** in the picture (no famous mascots, no logo-like shapes). For ads, the user's OWN brand is fine if they supply it and confirm they own it.
5. **Ads use the brand kit** (docs/branding.md): watermark and end card ON by default; contact details only from the saved brand (never invented).
6. **Ads must be honest:** no invented reviews, prices, discounts, awards or "best in" claims; only claims the user gives and confirms. Add "Terms apply" or similar only if the user asks.
7. **Kind content:** no stereotypes for laughs, no mocking real groups; violence implied only (cutaways, sound), as in the Bible pack.

## 2. Structure (every story, any length)
**Hook → Setting → Escalation → Turn → Payoff.**
| Beat | Share of time | What it does |
|---|---|---|
| Hook | first 2–3 s | The most intriguing image or line (a question, a problem, a surprise). No "Once upon a time" warm-up for social video |
| Setting | ~15 % | Who, where, what they want, in one or two lines |
| Escalation | ~40 % | Each beat raises the stakes or the curiosity |
| Turn | ~15 % | The surprise, decision or reveal (gets the music change and the push-in) |
| Payoff | ~15 % | The result + the takeaway (moral, call to action for ads) in one short sentence |
Length ≈ 3.7 words/s (30 s ≈ 110 words). Short sentences, numbers as words, nothing the picture already says.

## 3. Shot list and scene
`shotlist.md`: `| # | Time (s) | Beat | Script words | Visual | Camera | SFX / music |`. One shot per phrase; vary shot size (wide → medium → close-up on the turn). Characters: `person` with `"outfit": "modern"` (shirt, pants, hair) or robes for period stories; `house`, `tree`, `bubble` for speech, `title` for cards. Sound: `sound.py music --mood playful` (comedy, kids) or `warm` (heart-warming), SFX on actions.

## 4. Deliverables
`script.txt` (copyable block with beats marked in the notes, word count, length) · `shotlist.md` · `sources.md` (every fact claim + its source; "none: fiction" for pure fiction) · captions `.srt` · the MP4(s).

## 5. Self-check
- [ ] Every factual claim has a source, or is cut / labelled "legend says"
- [ ] No real living people, look-alikes, logos or copyrighted characters
- [ ] Ad claims come from the user and were confirmed
- [ ] The five beats are present; the hook works without sound (strong first image)
