"""Binary search in ~5 s (engine B example). Render:
python engines/manim/render.py examples/maths-binary-search/binary_search.py BinarySearch --fmt 9x16 --timing work/phrases.json
The steps are COMPUTED here (not typed in), so the picture always matches the algorithm."""
from studio import *

DATA, TARGET = [3, 8, 12, 17, 21, 26, 30, 35], 26


def search(data, target):
    lo, hi, steps = 0, len(data) - 1, []
    while lo <= hi:
        mid = (lo + hi) // 2
        steps.append((lo, hi, mid))
        if data[mid] == target:
            return steps
        lo, hi = (mid + 1, hi) if data[mid] < target else (lo, mid - 1)
    return steps


class BinarySearch(Scene):
    def construct(self):
        steps = search(DATA, TARGET)
        assert DATA[steps[-1][2]] == TARGET
        title = text("Binary search", 52, weight="BOLD")
        sub = text(f"find {TARGET} in a sorted list", 30, C.muted)
        head = VGroup(title, sub).arrange(DOWN, buff=0.15)
        fit_width(head, 0.95).move_to([SAFE["cx"], SAFE["top"] - head.height / 2 - 0.1, 0])

        cells = VGroup(*[VGroup(RoundedRectangle(width=1, height=1, corner_radius=0.16, fill_color=C.box(0), fill_opacity=1, stroke_width=0),
                                text(str(v), 40, C.box_text, "BOLD")) for v in DATA]).arrange(RIGHT, buff=0.14)
        for c in cells:
            c[1].move_to(c[0])
        idx = VGroup(*[text(str(i), 22, C.muted).next_to(c, DOWN, buff=0.12) for i, c in enumerate(cells)])
        row = VGroup(cells, idx)
        fit_width(row, 0.97).move_to([SAFE["cx"], SAFE["cy"] - (0.35 if FW < FH else 0.1), 0])
        self.add(head, row)                                       # frame 0 already shows the problem (the hook)

        arrow = Arrow(UP, DOWN, color=C.highlight, buff=0, stroke_width=6, max_tip_length_to_length_ratio=0.35).scale(0.45)
        label = text("mid", 26, C.highlight)

        def point_at(i):
            a = arrow.copy().next_to(cells[i], UP, buff=0.12)
            return a, label.copy().next_to(a, UP, buff=0.06)

        note = None
        for k, (lo, hi, mid) in enumerate(steps):
            base = 2 * k if k == 0 else 4                         # phrase indexes: 0 "Middle:", 1 value, ... 4 "Next middle:", 5 value
            wait_until(self, T.start(base, 0.15 + 3 * k))
            a, l = point_at(mid)
            if k == 0:
                self.play(GrowArrow(a), FadeIn(l), run_time=0.35)
                cur = (a, l)
            else:
                self.play(cur[0].animate.move_to(a), cur[1].animate.move_to(l), run_time=0.45)
            wait_until(self, T.start(base + 1, 0.6 + 3 * k))
            self.play(cells[mid][0].animate.set_fill(C.highlight), cells[mid][1].animate.set_color(C.on_highlight), run_time=0.3)
            if DATA[mid] == TARGET:
                wait_until(self, T.start(6, 4.8))
                done = text(f"Found at index {mid}  ·  {len(steps)} steps", 30, C.good, "BOLD")
                fit_width(done, 0.95).next_to(row, DOWN, buff=0.45)
                self.play(cells[mid][0].animate.set_fill(C.good), FadeIn(done, shift=UP * 0.2), *( [FadeOut(note)] if note else []), run_time=0.4)
                break
            sign = "<" if DATA[mid] < TARGET else ">"
            wait_until(self, T.start(2, 1.4))
            note = text(f"{DATA[mid]} {sign} {TARGET}", 34, C.bad, "BOLD").next_to(row, DOWN, buff=0.45)
            self.play(FadeIn(note, shift=UP * 0.2), run_time=0.3)
            wait_until(self, T.start(3, 2.1))
            drop = range(lo, mid + 1) if DATA[mid] < TARGET else range(mid, hi + 1)
            self.play(*[cells[i].animate.set_opacity(0.18) for i in drop], *[idx[i].animate.set_opacity(0.18) for i in drop], run_time=0.5)
            self.play(FadeOut(note), run_time=0.25)
            note = None
        wait_until(self, (T.duration or 5.6))
