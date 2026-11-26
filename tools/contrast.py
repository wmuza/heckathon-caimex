"""Measure the contrast of every text and control colour pair in web/app.css.

  uv run python tools/contrast.py

Text must reach 4.5:1 (WCAG AA); controls, large text and disabled labels 3:1.
"""
import re
import sys
from pathlib import Path

css = (Path(__file__).parent.parent / "web" / "app.css").read_text()


def tokens(block: str) -> dict:
    return {k: v.strip() for k, v in re.findall(r"(--[\w-]+):\s*(#[0-9A-Fa-f]{6})\s*;", block)}


light = tokens(css[css.index(':root, [data-theme="light"]'):css.index('[data-theme="dark"]')])
dark = {**light, **tokens(css[css.index('[data-theme="dark"]'):css.index("* { box-sizing")])}


def lum(hex_: str) -> float:
    def ch(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (int(hex_[i:i + 2], 16) for i in (1, 3, 5))
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)


def ratio(a: str, b: str) -> float:
    x, y = sorted((lum(a), lum(b)), reverse=True)
    return (x + 0.05) / (y + 0.05)


# (text or mark, background, least ratio, what it is)
PAIRS = [
    ("--ink", "--page", 4.5, "body text on the page"), ("--ink", "--panel", 4.5, "body text on a panel"),
    ("--ink", "--band", 4.5, "title on the band"), ("--ink-2", "--page", 4.5, "quiet text on the page"),
    ("--ink-2", "--panel", 4.5, "quiet text on a panel"), ("--ink-2", "--panel-sunk", 4.5, "quiet text on a sunk panel"),
    ("--ink-2", "--band", 4.5, "quiet text on the band"), ("--ink-2", "--neutral-tint", 4.5, "quiet text in the segment control"),
    ("--ink-on", "--blue-fill", 4.5, "label on the primary button"), ("--ink-on", "--red-fill", 4.5, "label on Stop and the emergency tag"),
    ("--blue-ink", "--panel", 4.5, "link on a panel"), ("--blue-ink", "--page", 4.5, "link on the page"),
    ("--blue-ink", "--selected", 4.5, "blue tag text"), ("--ink", "--selected", 4.5, "patient's words on the selected ground"),
    ("--ink-2", "--selected", 4.5, "label in the patient's bubble"),
    ("--red-ink", "--red-tint", 4.5, "alarm text"), ("--red-ink", "--panel", 4.5, "emergency number on the ticket"),
    ("--green-ink", "--green-tint", 4.5, "routine tag"), ("--warn-ink", "--warn-tint", 4.5, "urgent tag"),
    ("--neutral-ink", "--neutral-tint", 4.5, "neutral tag"),
    ("--disabled-ink", "--disabled", 3.0, "disabled label"), ("--ghost-edge", "--panel", 3.0, "edge of a secondary button"),
    ("--field-edge", "--panel", 3.0, "edge of a field"), ("--blue-fill", "--page", 3.0, "primary button against the page"),
    ("--blue-fill", "--panel", 3.0, "progress pip and selection ring"), ("--warn-dot", "--warn-tint", 3.0, "urgent dot"),
    ("--green-dot", "--green-tint", 3.0, "routine dot"), ("--neutral-dot", "--neutral-tint", 3.0, "neutral dot"),
    ("--ghost-edge", "--page", 3.0, "switch track when off"), ("--focus", "--panel", 3.0, "focus ring"),
]

bad = 0
for name, theme in (("light", light), ("dark", dark)):
    for fg, bg, need, what in PAIRS:
        r = ratio(theme[fg], theme[bg])
        ok = r >= need
        bad += not ok
        if not ok or "-v" in sys.argv:
            print(f"{'ok  ' if ok else 'FAIL'} {name:5s} {r:5.2f} (needs {need}) {what}: {fg} {theme[fg]} on {bg} {theme[bg]}")
print(f"{2 * len(PAIRS) - bad} of {2 * len(PAIRS)} pairs pass")
sys.exit(1 if bad else 0)
