"""Write docs/SHONA_TO_CHECK.md: every Shona sentence in the product, for a native speaker to read.

  uv run python tools/shona_sheet.py
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from app import prompts  # noqa: E402

out = ["# Shona to check", "",
       "Every Shona sentence in Mukoti, with the English it is meant to say. All of it was written by an AI",
       "assistant. A native speaker should read each line aloud and mark anything wrong, stiff or unclear.",
       "Made by `tools/shona_sheet.py`; edit the sentences in the files named, then run it again.", ""]


def table(title, where, rows):
    out.extend([f"## {title}", "", f"In `{where}`.", "", "| Shona | Meant to say | OK? |", "|---|---|---|"])
    out.extend(f"| {sn} | {en} |  |" for sn, en in rows)
    out.append("")


table("What the helper says: fixed lines", "app/prompts.py",
      [(prompts.LINES["sn"][k], prompts.LINES["en"][k]) for k in prompts.LINES["sn"]])
table("What the helper says to a patient at home (online visits)", "app/prompts.py",
      [(prompts.ONLINE_LINES["sn"][k], prompts.ONLINE_LINES["en"][k]) for k in prompts.ONLINE_LINES["sn"]])
table("The status page a patient at home comes back to", "app/prompts.py",
      [(prompts.STATUS_SAY["sn"][k], prompts.STATUS_SAY["en"][k]) for k in prompts.STATUS_SAY["sn"]])
table("What the helper says: the questions", "app/prompts.py",
      [(prompts.BANK["sn"][k], prompts.BANK["en"][k]) for k in prompts.BANK["sn"]])

from app import voice  # noqa: E402

table("Calling a ticket in the waiting room (the number is put in)", "app/prompts.py",
      [(voice.call_text("sn", k, 14), voice.call_text("en", k, 14)) for k in prompts.CALLS["sn"]])
table("How to take a medicine, said at the pharmacy", "app/prompts.py",
      [(prompts.HOW_SAY["sn"][k], prompts.HOW_SAY["en"][k]) for k in prompts.HOW_SAY["sn"]])
table("A warning for a community, when the national picture shows a risk", "app/prompts.py",
      [(prompts.WARN_SAY["sn"][k], prompts.WARN_SAY["en"][k]) for k in prompts.WARN_SAY["sn"]])
table("Ticket numbers in words", "app/voice.py",
      [(voice.number_words(n), str(n)) for n in (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 15, 20, 21, 30, 45, 99, 100, 101, 110, 125)])

html = (ROOT / "web" / "index.html").read_text()
block = lambda lang: html[html.index(f"  {lang}: {{"):html.index("  },", html.index(f"  {lang}: {{"))]
PAIR = re.compile(r"(\w+): (?:'((?:[^'\\]|\\.)*)'|\"((?:[^\"\\]|\\.)*)\")")


def pairs(text):
    return {k: a or b for k, a, b in PAIR.findall(text)}


sn, en = pairs(block("sn")), pairs(block("en"))
table("The patient's screen", "web/index.html", [(sn[k], en.get(k, "")) for k in sn])

html = (ROOT / "web" / "status.html").read_text()
sn, en = pairs(block("sn")), pairs(block("en"))
table("The status page's own words", "web/status.html", [(sn[k], en.get(k, "")) for k in sn])

data = json.loads((ROOT / "samples" / "patients.json").read_text())
table("Sample patients: answers every Shona patient shares", "samples/patients.json",
      [(data["defaults"]["sn"][k], data["defaults"]["en"].get(k, "")) for k in data["defaults"]["sn"]])
rows = []
for p in data["patients"]:
    if p["lang"] == "sn":
        rows.append((p["opening"], f"({p['title']}) opening line"))
        rows.extend((v, f"answer about: {k}") for k, v in p["answers"].items())
table("Sample patients: their own lines", "samples/patients.json", rows)

(ROOT / "docs" / "SHONA_TO_CHECK.md").write_text("\n".join(out) + "\n")
print("lines to check:", sum(1 for line in out if line.startswith("| ") and not line.startswith("| Shona")))
