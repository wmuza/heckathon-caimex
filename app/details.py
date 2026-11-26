"""The patient's details beside the note: age, sex, weight and height.

No model is used here and none sees these values. The age is read out of what
the patient said by the fixed number tables below. Sex, weight and height are
never taken from speech: a member of staff enters them against the ticket
number, on the vitals page or the nurse's page. Nothing here changes the
urgency level.

No name is kept. The ticket number links the visit to the clinic's own register.

The Shona number words were written by an AI assistant and must be read by a
native speaker before real use.
"""

from __future__ import annotations

import re
import time
import unicodedata

EMPTY = {"age": None, "sex": None, "weight": None, "height": None, "bp": None, "area": None}

ONES = {
    1: "rimwe mumwe imwe motsi poshi chimwe one",
    2: "maviri miviri vaviri mairi piri mbiri two",
    3: "matatu mitatu vatatu tatu nhatu three",
    4: "mana mina ina four",
    5: "mashanu mishanu shanu five",
    6: "matanhatu mitanhatu tanhatu six",
    7: "manomwe minomwe nomwe seven",
    8: "masere misere sere eight",
    9: "mapfumbamwe mipfumbamwe pfumbamwe nine",
}
WORD = {w: n for n, words in ONES.items() for w in words.split()}
TEENS = dict(zip("ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split(), range(10, 20)))
TENS = dict(zip("twenty thirty forty fifty sixty seventy eighty ninety".split(), range(20, 100, 10)))
UNIT = {
    "years": "makore gore years year yrs",
    "months": "mwedzi months month",
    "weeks": "mavhiki vhiki masvondo svondo weeks week",
    "days": "mazuva zuva days day",
}
UNIT_OF = {w: u for u, words in UNIT.items() for w in words.split()}
# The largest value that is believed for each unit. Outside it the words are kept and the number is not.
AGE_MAX = {"years": 120, "months": 60, "weeks": 104, "days": 120}
HAS = set("ane ndine une mune vane tine ava ave ndava wava".split())
UNKNOWN = re.compile(r"\b(handizivi|hatizivi|handichazivi|handina chokwadi|(do not|don't|dont) know|not sure)\b")

# The ranges a typed measurement must fall in. The label on the key pad gives the unit.
RANGE = {"weight": (1.0, 250.0, "kg"), "height": (45.0, 220.0, "cm")}
# Blood pressure, upper over lower, in mmHg. Outside these a reading is a typing slip and is refused.
BP_UPPER, BP_LOWER = (50, 300), (30, 200)
# Readings that are kept with a warning for the nurse. These are the commonly used limits for a
# very high reading (180 upper or 120 lower) and a low one (upper under 90). No clinician has
# reviewed them. The warning does not change the urgency level.
BP_VERY_HIGH, BP_LOW_UPPER = (180, 120), 90
CHILD_HEAVY_KG = 40          # a child above this is weighed again: 6.5 keyed as 65 is the dangerous slip
SEXES = ("female", "male")
SOURCES = ("said", "measured", "entered")


def _tokens(text: str) -> list[str]:
    text = unicodedata.normalize("NFKD", text or "").lower()
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"(\d)[- ]?(years?|yrs?|months?|weeks?|days?)\b", r"\1 \2", text)      # "3-year-old", "3yrs"
    return re.findall(r"\d+(?:\.\d+)?|[a-z']+", text)


def _one(tok: str) -> int | None:
    """A word for 1 to 9, with or without the joining "ne" ("nemashanu")."""
    if tok in WORD:
        return WORD[tok]
    for prefix in ("ne", "na"):
        if tok.startswith(prefix) and tok[len(prefix):] in WORD:
            return WORD[tok[len(prefix):]]
    return None


def _numbers(toks: list[str]) -> list[tuple[int, int, float]]:
    """Every number in the tokens, as (first token, token after the last, value)."""
    out, i = [], 0
    while i < len(toks):
        t, j, n = toks[i], i + 1, None
        nxt = _one(toks[i + 1]) if i + 1 < len(toks) else None
        if re.fullmatch(r"\d+(\.\d+)?", t):
            n = float(t)
        elif t == "makumi" and nxt is not None:           # makumi matatu = 30
            n, j = nxt * 10, i + 2
            if j < len(toks) and toks[j][:2] in ("ne", "na") and _one(toks[j]) is not None:
                n, j = n + _one(toks[j]), j + 1           # ... nemashanu = 35
        elif t in ("gumi", "negumi"):
            n = 10
            if nxt is not None and toks[i + 1][:2] in ("ne", "na"):
                n, j = 10 + nxt, i + 2                    # gumi nemaviri = 12
        elif t in TEENS:
            n = TEENS[t]
        elif t in TENS:
            n = TENS[t]
            if nxt is not None and toks[i + 1] in WORD:   # thirty five
                n, j = n + nxt, i + 2
        elif _one(t) is not None and t in WORD:
            n = WORD[t]
        if n is None:
            i += 1
        else:
            out.append((i, j, float(n)))
            i = j
    return out


def _clean(n: float) -> int | float:
    return int(n) if float(n).is_integer() else round(n, 1)


def parse_age(text: str, asked: bool) -> dict | None:
    """The age in a patient's sentence.

    `asked` is true when the sentence answers the age question: then a bare
    number is an age in years. Elsewhere only a number with its unit beside it
    ("makore matatu", "3 years") counts, and only if there is exactly one such
    phrase, so "I am 30 and my child is 3" is left for the nurse to read.

    Returns None when the sentence holds no age. A value of None with the words
    kept means the patient answered but no believable number was heard.
    """
    raw = (text or "").strip()
    toks = _tokens(raw)
    found = []
    for i, j, n in _numbers(toks):
        before = UNIT_OF.get(toks[i - 1]) if i > 0 else None
        after = UNIT_OF.get(toks[j]) if j < len(toks) else None
        # Outside the age question a length of time ("it began three days ago") must not pass for an age:
        # the words have to say someone HAS that many years ("ane makore matatu") or is that old ("3 years old").
        has = before and i > 1 and toks[i - 2] in HAS
        old = after and j + 1 < len(toks) and toks[j + 1] == "old"
        if asked or has or old:
            found.append((n, before or after))
        elif i > 0 and toks[i - 1] in ("am", "aged") and not after and float(n).is_integer():
            found.append((n, "years"))              # "I am 21 and ...": a bare number after "am" is an age in years
    with_unit = [(n, u) for n, u in found if u]
    if not with_unit and "gore" in toks and (asked or toks[max(toks.index("gore") - 1, 0)] in HAS):          # "gore" with no number beside it is one year ("ane gore")
        with_unit = [(1.0, "years")]
    if asked:
        pick = with_unit[0] if with_unit else (found[0][0], "years") if found else None
    else:
        pick = with_unit[0] if len(with_unit) == 1 else None
    if pick is None:
        if asked and re.search(r"\w", raw):
            return {"value": None, "unit": None, "source": "said", "raw": raw[:120],
                    "flag": "The patient does not know" if UNKNOWN.search(raw.lower()) else "No number was heard: ask"}
        return None
    n, unit = pick
    if n < 0 or n > AGE_MAX[unit] or (unit != "years" and not float(n).is_integer()):
        return {"value": None, "unit": None, "source": "said", "raw": raw[:120], "flag": "Not a believable age: ask"}
    return {"value": _clean(n), "unit": unit, "source": "said", "raw": raw[:120], "flag": None}


def is_child(details: dict, child_flag: bool) -> bool:
    age = (details or {}).get("age") or {}
    if age.get("value") is not None:
        return age["unit"] != "years" or age["value"] < 13
    return bool(child_flag)


class Refused(ValueError):
    """A typed value that is not kept. The message is shown to the member of staff."""


def entry(field: str, value, unit: str | None = None, source: str = "measured", child: bool = False) -> dict | None:
    """Check one value a member of staff typed. None clears the field."""
    if field not in EMPTY:
        raise Refused("Unknown detail")
    if value is None or value == "":
        return None
    now = time.time()
    if field == "area":                     # where the patient lives, to the ward and no finer
        from .surveillance import AREAS
        if value not in AREAS:
            raise Refused("Choose the area from the list")
        return {"value": value, "unit": None, "source": "entered", "at": now, "flag": None}
    if field == "sex":
        if value not in SEXES:
            raise Refused("Choose female or male")
        return {"value": value, "unit": None, "source": "entered", "at": now, "flag": None}
    if field == "bp":
        m = re.fullmatch(r"\s*(\d{2,3})\s*/\s*(\d{2,3})\s*", str(value))
        if not m:
            raise Refused("Type the upper number, a slash, then the lower number, like 120/80")
        up, low = int(m[1]), int(m[2])
        if not BP_UPPER[0] <= up <= BP_UPPER[1] or not BP_LOWER[0] <= low <= BP_LOWER[1]:
            raise Refused(f"The upper number must be {BP_UPPER[0]} to {BP_UPPER[1]} and the lower {BP_LOWER[0]} to {BP_LOWER[1]}")
        if low >= up:
            raise Refused("The upper number must be larger than the lower number")
        flag = "Very high reading: measure again and tell the nurse" if up >= BP_VERY_HIGH[0] or low >= BP_VERY_HIGH[1] \
            else "Low reading: measure again and tell the nurse" if up < BP_LOW_UPPER else None
        return {"value": f"{up}/{low}", "upper": up, "lower": low, "unit": "mmHg", "source": "measured", "at": now, "flag": flag}
    try:
        n = float(str(value).replace(",", "."))
    except ValueError:
        raise Refused("That is not a number")
    if n != n or n in (float("inf"), float("-inf")):
        raise Refused("That is not a number")
    if field == "age":
        unit = unit if unit in AGE_MAX else "years"
        if n < 0 or n > AGE_MAX[unit] or (unit != "years" and not n.is_integer()):
            raise Refused(f"An age in {unit} must be between 0 and {AGE_MAX[unit]}")
        return {"value": _clean(n), "unit": unit, "source": "entered", "at": now, "flag": None}
    low, high, unit = RANGE[field]
    if not low <= n <= high:
        raise Refused(f"{field.capitalize()} must be between {_clean(low)} and {_clean(high)} {unit}")
    flag = "Heavy for a child: weigh again" if field == "weight" and child and n > CHILD_HEAVY_KG else None
    return {"value": round(n, 1) if field == "weight" else _clean(round(n)), "unit": unit,
            "source": source if source in ("measured", "said") else "measured", "at": now, "flag": flag}
