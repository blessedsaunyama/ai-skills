# Animation styles, audiences and depicting sacred scenes

## 1. Style table
The kit engine renders **flat cartoon** (2D character cards in an inked, painted 3D world) and a **silhouette / backlit** treatment of the same scenes. Those are the user's chosen house styles. The other styles are listed so the skill can say honestly what would need another tool.

| Style | Best for | Mood | Kit can render? |
|---|---|---|---|
| **Flat 2D cartoon (house style)** | Children, youth, short videos | Bright, friendly | ✅ default |
| **Silhouette / backlit (house style, solemn scenes)** | Gethsemane, the cross, death, judgment, night scenes | Dramatic, reverent | ✅ (see §3) |
| Painted storybook / watercolor | Story time, all ages | Warm, gentle | ❌ needs another tool |
| Stylised 3D | Kids and teens, action stories | Cinematic | ❌ |
| Stained-glass motion | Adults, worship screens | Sacred, majestic | ❌ |
| Parallax on illustrations | Sermons, lessons | Documentary | ❌ |
| Whiteboard / chalk | Bible study, prophecy, sanctuary | Explanatory | ❌ |
| Claymation look | Young children | Playful | ❌ |
| Paper cut-out | Children, mixed audiences | Handmade | ❌ |
| Anime-inspired 2D | Youth | Energetic, emotional | ❌ |

If a user asks for a ❌ style, give the script package plus a style note and say the kit can't render it. Never pretend.

## 2. Audience settings (asked at intake every time)
| Audience | Words / sentence | Vocabulary | Pace | Humour | Danger / sorrow | Close with |
|---|---|---|---|---|---|---|
| Young children 3–7 | 5–9 | Everyday words; explain "den", "decree" in a phrase | Slower: 3.2 words/s | Gentle (animals, faces) | Off-screen; show safety and God's care right away | One short memory verse + "God loves/helps you" |
| Kids 8–12 | 8–13 | Simple, with KJV quotes kept short | 3.7 words/s | Light, never at sacred things | Implied (shadows, reactions, sound) | Memory verse + one challenge |
| Youth / teens | 10–16 | Fuller, honest about fear and courage | 3.8–4 words/s | Wry at most | Implied, emotionally real | A question to think about + verse |
| Whole congregation | 9–15 | Clear and dignified, KJV quotes welcome | 3.5 words/s | Very little | Implied, solemn | Verse + short appeal |

Word budget = seconds × pace (e.g. 45 s × 3.7 ≈ 165 words; 30 s for young children ≈ 95 words).

## 3. Silhouette / backlit treatment (in the kit)
For solemn beats, keep the same world and change the light and the cards:
- Add a light preset in `story.js` `LIGHTS`, e.g. `solemn: { az: 0, el: 6, sky: '#3b3150', ground: '#1a1420', hemi: 0.45, sun: '#ffb070', sunI: 3.2, fog: '#f0a070', fogNear: 30, fogFar: 400, skyTop: '#2a2245', skyHor: '#ff9a5a', sunDisc: '#fff0c8', sunSize: 0.004, sat: 0.95, vig: 0.38, shadowExt: 18 }`. Put the camera so the sun is **behind** the characters.
- Darken cards with the actor `tint`: `tint: '#2a2030'` for full silhouette, `'#6a5a6a'` for half-lit.
- Use slow moves (45+ frames), no comic secondary motion, and a low drone instead of the music loop.

## 4. Depicting sacred persons and moments
| Subject | How (user-approved) | Kit implementation |
|---|---|---|
| **God the Father** | Never a human figure, face or body. Show light, glory, a cloud, fire, wind, or a voice | `fxGlory` card (blob:false, shadow:false, s 4–10), white `flash`, a warm light preset, a rumble or soft chord in the SFX |
| **Jesus** | A full character with dignity: Middle-Eastern features, simple robe, warm and kind. Never comic, clumsy, or the butt of a joke. No halo needed | `bibleFront(p,'jesus',…)` with exprs `neutral`, `smile`, `relief`, `stern` (for the temple cleansing). Avoid `laugh`, `dazed`, `nervous`, `snore` |
| **Angels** | Majestic men in shining white. No baby cherubs. Wings only where the text describes winged beings (e.g. Isa 6:2, Ezek 1, 10). When the text says an angel appeared "as a man", no wings | `bibleFront(p,'angel',{glowK:1})`, plus `wings:true` only with a verse to justify it. Tag the look 🎨 |
| **Holy Spirit** | Only the forms the text gives: a dove (Matt 3:16), tongues of fire, a mighty wind (Acts 2) | A dove or flame fx card, wind SFX |
| **Satan / the serpent** | Never the comic hero, never cute, never glamorous. Keep screen time short | Dark tint, shadows, low angle |
| **Prophets and heroes** | Real people with real fear and faith. Don't make them superheroes | Normal expressions |
| **Prayer, worship** | Unhurried, respectful framing; no jokes in the same shot | Kneel by lowering the card (`y`), hands `cross` pose, soft light |

## 5. Violence, danger and death: implied only
Show the cause and the result, never the impact: a cutaway to watchers' faces, a shadow on a wall, a sound off-screen, then the aftermath far away (e.g. Goliath fallen, seen from a distance). No blood, no wounds, no visible killing or corpses up close. Beheadings, executions and the deaths of children or families (e.g. Dan 6:24) are **told in one restrained narration line, or left out** for young audiences. Say in the accuracy notes that they were left out, so nothing is quietly changed.

## 6. Setting and costume (Ancient Near East, tagged 🎨)
- Clothing: long robes and tunics, belts or sashes, head-cloths with a cord, mantles, sandals. Kings wear a mantle, rich colour and a simple crown. Soldiers wear leather or bronze, not Roman armour (unless the story is set in New Testament Judea, where Roman soldiers fit).
- Building in the kit: flat-roofed mud-brick and plaster houses (`tbox` + `plaster` texture), stone walls, palm and olive trees (trunk + sphere canopy), dry hills, wells, sheep pens. A den or pit: a stone-lined hollow with an opening above (Dan 6:17 mentions a stone laid on its mouth).
- Skin tones: Middle-Eastern and African-Asian range (the `BIBLE` outfits use olive and brown tones). Never Europeanise biblical characters by default.
- Anything the text doesn't state (colours, weather, faces, the size of the den) is 🎨 and must not contradict the text.

## 7. Music and sound for sacred stories
Rewrite the music section of `audio.py`: replace the march with a slow, warm bed (soft pad + plucked harp-like notes, 70–85 BPM, a major key for hope, minor for danger). Remove anything comic (the `cuckoo` effect). At the deliverance or turning point, the music stops, a soft swell follows, then it resumes in a brighter key. For a reverent tone, mix the bed with `mix.py --music-db -9` (never louder than −6).
