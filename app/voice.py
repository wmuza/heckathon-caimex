"""Speech beyond the intake talk: calling the queue, saying how to take a medicine,
announcing an emergency to staff, and the doctor's dictation.

Everything spoken to a patient here is a sentence written in advance in
prompts.py, with only the ticket number put in. No model writes a word of it.
The voice is the same CAIMEx voice model as the intake, and each sentence is
synthesised once and then replayed from disk.

Ticket numbers are said in English words inside the Shona sentence ("Ticket fourteen"),
as people say them in everyday mixed Shona.
"""

from __future__ import annotations

import time

from . import prompts

SMALL = ("zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen "
         "fifteen sixteen seventeen eighteen nineteen").split()
TENS = "twenty thirty forty fifty sixty seventy eighty ninety".split()


def number_words(n: int) -> str:
    """A ticket number in English words, 1 to 199, as it is said in everyday mixed Shona. The voice
    reads the digits "14" as "one four" (measured 2026-11-26), so the words are written out.
    Beyond 199 the digits are left."""
    if not 1 <= n <= 199:
        return str(n)
    if n >= 100:
        rest = n - 100
        return "one hundred" if not rest else "one hundred and " + number_words(rest)
    if n < 20:
        return SMALL[n]
    tens, ones = divmod(n, 10)
    return TENS[tens - 2] if not ones else f"{TENS[tens - 2]} {SMALL[ones]}"


def call_text(lang: str, to: str, number: int) -> str:
    n = number_words(number) if lang == "sn" else str(number)
    return prompts.CALLS[lang][to].format(n=n)


def how_text(lang: str, how: str) -> str:
    table = prompts.HOW_SAY[lang]
    return table.get(how, table["As directed"])


def alarm_text(number: int, sign: str, online: bool = False) -> str:
    return (prompts.ALARM_SAY_ONLINE if online else prompts.ALARM_SAY).format(n=number, sign=sign)


def briefing_text(pred: dict, warnings: list[dict]) -> str:
    """The morning briefing for staff, in English, built from the computed numbers by fixed wording.
    No model writes it, so what is said always matches what is on the screen."""
    parts = [f"Good morning. This is the forecast for {pred['weekday']}, before the doors open."]
    for t in pred["today"][:3]:
        more = " That is more than usual." if t["above"] else ""
        parts.append(f"Expect about {t['expected']} patients with {t['name'].lower()}, between {t['lo']} and {t['hi']}.{more}")
    flagged = [s for s in pred["signals"] if s["level"] in ("confirmed", "likely")]
    if flagged:
        for s in flagged[:3]:
            word = "A confirmed rise" if s["level"] == "confirmed" else "A likely rise"
            parts.append(f"{word} in {s['name'].lower()} in {s['area']}: {s['seen']} cases in seven days, where about "
                         f"{round(s['usual'])} is usual.")
    else:
        parts.append("Nothing unusual is rising in the wards.")
    for w in warnings[:2]:
        parts.append(f"National warning for this province: {w['name'].lower()}, risk {w['score']} out of 100.")
    return " ".join(parts)


def warn_text(lang: str, disease: str) -> str:
    return prompts.WARN_SAY[lang][disease]


# ── The queue calls, for the waiting-room board ────────────────────────────

CALLS: list[dict] = []          # newest last; only the ticket number and where to go
PLACES = ("nurse", "doctor", "pharmacy")


def call(visit: dict, to: str) -> dict:
    """Call a ticket to the nurse, the doctor or the pharmacy. The board shows it and says it,
    in the patient's own language first."""
    if to not in PLACES:
        raise ValueError("Unknown place")
    if visit.get("online"):
        return None          # at home, not in the room: nothing is shown or said on the board. The clinic calls back.
    # The id is built on the clock, so it is never used twice, even after the server starts again. An id
    # that began at 1 each time made a board left open ignore new calls, and made the browser replay
    # the sound it had kept for an earlier call with the same id: the wrong ticket was said.
    row = {"id": max(int(time.time() * 1000), (CALLS[-1]["id"] + 1) if CALLS else 0), "at": time.time(),
           "number": visit["number"], "to": to,
           "langs": [visit["lang"]] + [l for l in ("sn", "en") if l != visit["lang"]]}
    CALLS.append(row)
    del CALLS[:-50]
    return row


def staff_lines() -> list[tuple[str, str]]:
    """The sentences that never change, as (text, language), so they can be made at start-up."""
    return [(t, lang) for table in (prompts.HOW_SAY, prompts.WARN_SAY) for lang in table for t in table[lang].values()]
