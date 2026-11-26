"""The safety net: fixed danger-sign rules, and how the checks are combined.

Four independent checks look at every visit:

1. these rules, on the patient's own words as they are spoken;
2. the interview model, which can raise an alarm in the middle of the talk;
3. the note model, which drafts a level when it writes the nurse's note;
4. a second, smaller model that reads the finished English note cold.

The final level is the highest any of them gives. A missed emergency is the
failure that matters, so the net is deliberately wide: it will sometimes raise
a case that a nurse then steps down. Only the nurse can lower a level.

The signs are drawn from the published tools listed in SOURCES. The wording of
the Shona patterns is ours. NOT clinically validated: a clinician must review
the list, and a native speaker the patterns, before any real use.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

LEVELS = ("routine", "urgent", "emergency")

# Which published tool each sign is drawn from. docs/SOURCES.md has the full
# references, the pages and the licences. "own" means no published tool is
# cited: the sign is there out of caution, on our judgement alone.
SOURCES = {
    "iitt": "WHO, ICRC and MSF, Interagency Integrated Triage Tool (red and yellow criteria)",
    "imci": "WHO, IMCI chart booklet 2014 (general danger signs)",
    "etat": "WHO, ETAT manual 2005 (priority signs)",
    "anc": "WHO, Pregnancy, childbirth, postpartum and newborn care 2015 (danger signs)",
    "own": "Mukoti's own caution, no published tool cited",
}


def rank(level: str) -> int:
    return LEVELS.index(level) if level in LEVELS else 0


def highest(levels: list[str]) -> str:
    return max(levels, key=rank) if levels else "routine"


@dataclass(frozen=True)
class Rule:
    level: str
    key: str
    label: str
    source: str
    # Each alternative is a tuple of terms that must all be present. A term is a
    # regular expression. A term that starts with "!" is already a negative
    # form ("haasi kufema") and is not put through the negation check.
    sn: tuple = ()
    en: tuple = ()


def _alts(*alts) -> tuple:
    return tuple((a,) if isinstance(a, str) else tuple(a) for a in alts)


NOT_MEDICINE = r"(?! (mushonga|mishonga|mapiritsi|piritsi|doro|hwahwa|fodya))"

RULES: list[Rule] = [
    Rule("emergency", "breathing", "Difficulty breathing", "iitt",
         sn=_alts(r"\w*(tadz|netsek|nets|omerw|shay|tambur)\w* (ne|pa)?(ku)?(fema|breath\w*|bh?[ie]?ridh\w*)",
                  r"!\bha\w* (ku)?fem[aei]\b", r"!\bha\w*fem[ei]\b",
                  r"!\bha\w*(gon[ei]|kwanis[ei]) kufema", r"!\bha\w* (ku)?(gona|kwanisa) kufema",
                  r"\w*(pererw|per)\w* (ne)?mweya", r"kushaya mweya", r"\w*kwev\w* mweya",
                  r"\bmbabvu (\w+ ){0,2}\w*pind\w* mukati"),
         en=_alts(r"(difficult\w*|trouble|problems?|struggl\w*|hard|battling|labou?red) "
                  r"(of |to |with |in )?breath\w*",
                  r"short\w* of breath", r"!(cannot|can't|can not|unable to|not able to) breathe",
                  r"!(not|isn't|isnt|stopped) breathing", r"gasping", r"chok(ing|ed)")),
    Rule("emergency", "convulsions", "Fits or convulsions", "iitt",
         sn=_alts(r"\w*pfari\b", r"\bma ?fits\b", r"\w*gwinh\w*", r"\w*zvipusha\b", r"\w*vhunduk\w* muviri",
                  r"\bmuviri (\w+ ){0,2}\w*deder\w*", r"\bfuro (\w+ ){0,3}muromo\b"),
         en=_alts(r"convuls\w*", r"seizure\w*", r"\bfits?\b", r"fitting")),
    Rule("emergency", "unconscious", "Cannot be woken, or very drowsy", "iitt",
         sn=_alts(r"!\bha\w* (ku)?muk[aei]\b", r"!\bha\w*chamuk[aei]\b", r"!\bhaa\w*muk[ei]\b",
                  r"!\basingamuk\w*", r"!\bha\w* (ku)?pindur[aei]\b", r"!\bha\w* (ku)?(gona|kwanisa) kumuka",
                  r"!\bha\w*davir[aei]\b", r"!\bha\w* (ku)?davir[aei]\b"),
         en=_alts(r"unconscious", r"!not waking",
                  r"!(will not|won't|cannot|can't|could not|couldn't|does not|doesn't|did not|didn't|unable to) "
                  r"(be )?(wake|woken|waken|waking)",
                  r"unresponsive", r"lethargic", r"very (drowsy|sleepy)",
                  r"!(not|isn't|isnt|stopped) (answering|responding)")),
    Rule("urgent", "fainted", "Fainted or confused", "iitt",
         sn=_alts(r"\w*fend[ae]\b", r"\w*fendeuk\w*", r"\w*faint\w*", r"\w*kolaps\w*|\w*collaps\w*", r"\w*rasik\w* (ne)?pfungwa",
                  r"\w*taura zvisinganzwisisik\w*", r"\w*vhiringidzik\w*"),
         en=_alts(r"fainted", r"passed out", r"collapsed", r"confused", r"not making sense")),
    Rule("emergency", "bleeding", "Heavy bleeding", "iitt",
         sn=_alts(r"\bropa (\w+ ){0,3}(rakawand\w*|zhinji|zvakanyany\w*|rakanyany\w*|zvakawand\w*)",
                  r"\bropa (\w+ ){0,2}\w*erer\w*",
                  # "the blood will not stop": a negative form, so not put through the negation check
                  r"!\bropa (\w+ ){0,3}(risingamir\w*|hariper\w*|harisi (kuda )?kumira|haridi kumira|harimir[ei])",
                  r"\w*rutsa ropa", r"\w*(vh?omit)\w* ropa",
                  r"\w*bleed\w* (\w+ ){0,2}(zvakanyany\w*|zvakawand\w*|heavy)"),
         en=_alts(r"(heavy|severe|a lot of|lots of|profuse|uncontrolled) bleeding",
                  r"bleeding (heavily|a lot|profusely)", r"vomit\w* blood", r"haemorrhag\w*|hemorrhag\w*",
                  r"!bleed\w* (\w+ ){0,1}(will not|won't|does not|doesn't|would not|wouldn't|has not|hasn't|not) stop\w*",
                  r"!(will not|won't|cannot|can't|would not|wouldn't) stop bleeding",
                  (r"bleed\w*|blood", r"!(not|isn't|isnt) stopping"))),
    Rule("emergency", "pregnancy_bleeding", "Bleeding in pregnancy", "anc",
         sn=_alts((r"\b(pamuviri|nhumbu|mimba)\b|pregn[ae]n\w*", r"\bropa\b|\w*bleed\w*|\bblood\b|\w*spott\w*")),
         en=_alts((r"pregnan\w*", r"bleed\w*|blood|spott\w*"))),
    Rule("emergency", "poison", "Poisoning or snake bite", "iitt",
         sn=_alts(r"\w*chepfu\b", r"mushonga we(makonzo|zvipembenene|mombe)", r"\w*parafini\b",
                  r"\w*rum\w* (ne ?)?(nyoka|snake)", r"\w*poison\w*|\w*poizeni\b", r"\bnyoka (\w+ ){0,1}\w*rum\w*"),
         en=_alts(r"poison\w*", r"snake ?bite|bitten by a snake", r"paraffin", r"overdose",
                  r"swallowed (rat|pesticide|bleach|tablets|pills)")),
    Rule("emergency", "self_harm", "Thoughts of self-harm", "own",
         sn=_alts(r"\w*zviuray\w*", r"\w*zvisungirir\w*", r"\w*zvikuvadz\w*",
                  r"(ndinoda|ndoda|ndiri kuda|ndava kuda) kufa", r"zviri ?nani (\w+ ){0,1}ndisisipo",
                  r"\w*neta ne ?upenyu"),
         en=_alts(r"suicid\w*", r"self[ -]?harm", r"kill (myself|himself|herself|themselves)",
                  r"want(s)? to die", r"end(ing)? (my|his|her) life", r"end(ing)? it all",
                  r"better off dead")),
    # IMCI general danger signs. Third person only (haasi, haachagoni...):
    # "handisi kunwa mushonga" is an adult saying they take no medicine.
    Rule("emergency", "cannot_drink", "Child cannot drink or vomits everything", "imci",
         sn=_alts(r"!\bhaa?ch?\w*(gon[ei]|kwanis[ei]) ku(nwa|yamwa|dya)\b" + NOT_MEDICINE,
                  r"!\bhaa\w* ?(ku)?(nwa|yamwa)\b" + NOT_MEDICINE, r"!\bhaa\w*(nw|yamw)[ei]\b",
                  r"!\bha\w* (ku)?(gona|kwanisa) ku(nwa|yamwa)\b" + NOT_MEDICINE,
                  r"\w*tadza ku(nwa|yamwa)\b" + NOT_MEDICINE,
                  r"\w*ramb\w* (zamu|mukaka|kuyamwa|kunwa)\b",
                  r"\b(zvese|zvose) zvaanodya (\w+ ){0,4}\w*rutsa",
                  r"\w*rutsa (zvese|zvose|zvinhu zvese|zvinhu zvose|zvaanodya zvese|zvaanodya zvose)",
                  r"\w*vh?omit\w* (zvese|zvose|zvinhu zvese|zvinhu zvose|everything)",
                  r"\w*rutsa everything"),
         en=_alts(r"!(unable|cannot|can't|not able|too weak) to (drink|breastfeed|feed|suck)",
                  r"!not (drinking|breastfeeding|feeding)", r"!(refus\w*|stopped) (to )?(drink\w*|breastfeed\w*|feed\w*)",
                  r"vomit\w* everything")),
    Rule("urgent", "chest_pain", "Chest pain", "iitt",
         sn=_alts(r"\bchipfuva\b (\w+ ){0,3}\w*(rwadz|vhiring|band|tsvind)\w*",
                  r"\w*(rwadz|vhiring|band|tsvind)\w* (\w+ ){0,3}(mu|pa)?(chipfuva|chest)\b",
                  r"\bchest\b (\w+ ){0,3}\w*(rwadz|vhiring|band|tsvind)\w*",
                  r"\bchipfuva\b (\w+ ){0,3}\w*pain\w*"),
         en=_alts(r"chest (\w+ ){0,3}(pain\w*|tight\w*|hurt\w*)",
                  r"(pain\w*|tight\w*|crushing) (\w+ ){0,3}chest")),
    Rule("urgent", "injury", "Serious injury or burn", "iitt",
         sn=_alts(r"\btsaona\b", r"\w*tyok\w*", r"\w*tsv\w* (\w+ ){0,2}ne(moto|mvura|mafuta)",
                  r"\w*baiw\w* (\w+ ){0,2}ne(banga|chigero|bakatwa)", r"\w*cheker\w*"),
         en=_alts(r"accident", r"broken (bone|arm|leg)", r"fracture\w*", r"\bburn(s|t|ed)?\b",
                  r"stabbed", r"deep (cut|wound)", r"head injury")),
    # The tool's rule is "any two of": altered mental state, stiff neck, fever, headache.
    Rule("emergency", "stiff_neck_fever", "Stiff neck with fever or headache", "iitt",
         sn=_alts((r"\b(mutsipa|neck|neki)\b (\w+ ){0,3}\w*(oma|omarar)\w*",
                   r"\w*pisa muviri|\bfivha\b|\bfever\b|\bmusoro\b|\bhead ?a(che|ck)\w*|\bhedhek\w*")),
         en=_alts((r"stiff neck|neck (is )?stiff\w*", r"fever|headache|\bhot\b"))),
    Rule("urgent", "stiff_neck", "Stiff neck", "iitt",
         sn=_alts(r"\b(mutsipa|neck|neki)\b (\w+ ){0,3}\w*(oma|omarar)\w*",
                  r"\w*(oma|omarar)\w* (\w+ ){0,2}(mutsipa|neck|neki)\b"),
         en=_alts(r"stiff neck", r"neck (is )?stiff\w*")),
    Rule("urgent", "young_baby", "Baby only days or weeks old", "etat",
         sn=_alts(r"\b(mwana|mucheche|kacheche)\b (\w+ ){0,3}(ane|ave ne|wema|ava nema|ave nema) ?(ma)?(vhiki|zuva)\w*",
                  r"\b(mwana|mucheche|kacheche)\b (\w+ ){0,3}(ane|ave ne)mwedzi mumwe\b"),
         en=_alts(r"\b(\w+)[- ](days?|weeks?)[- ]old\b", r"\bnewborn\b",
                  r"\b(baby|infant|child|son|daughter)\b (\w+ ){0,3}(is|aged) (\w+ ){0,1}(days?|weeks?)\b")),
    Rule("urgent", "blood", "Blood in stool, urine, vomit or cough", "own",
         sn=_alts(r"\b(manyoka|tsvina|weti)\b (\w+ ){0,3}ropa\b",
                  r"\bropa\b (\w+ ){0,3}(mu|pa|mune|ne)?(manyoka|tsvina|weti)\b", r"\w*kosora ropa"),
         en=_alts(r"blood\w* (in |with )?(the |my |his |her )?(stool|urine|diarrh\w*|vomit|sputum)",
                  r"bloody (stool|urine|diarrh\w*)", r"cough\w* (up )?blood")),
    Rule("urgent", "assault", "Reports sexual assault", "iitt",
         sn=_alts(r"\bchibharo\b"),
         en=_alts(r"\braped?\b", r"sexual(ly)? assault\w*")),
    # No patterns: raised only by answer_sign(), when the patient says yes to "have you seen any blood?"
    Rule("urgent", "bleeding_yes", "Bleeding (answered yes when asked)", "own"),
]
BY_KEY = {r.key: r for r in RULES}

SN_NEG = re.compile(r"^(ha(ndi|u|a|i|ti|mu|va|zvi|pa|ri|chi|ku)\w*|hapana|hapasina|pasina|asina|asiri|handiti)$")
EN_NEG = re.compile(r"^(no|not|without|denies|denied|deny|never|none|nor|neither|\w+n't|cannot|isnt|doesnt|hasnt)$")
# A plain "is / has" between a denial and the sign ends the denial:
# "handina simba ndiri kutadza kufema" (I have no strength, I cannot breathe).
SN_AFF = re.compile(r"^(ndiri|uri|ari|tiri|muri|vari|ndava|wava|ava|tava|mava|vava|ndine|une|ane|tine|mune|vane|anenge)$")
EN_AFF = re.compile(r"^(is|are|was|were|am|keeps|kept|still)$")
# "has not stopped convulsing", "can't stop vomiting blood": a denial of stopping is not a denial.
STOPPING = {"stop", "stopped", "stopping", "cease", "ceased"}
CLAUSE = re.compile(r"[.,;:!?\n]| uye | asi | but | and | however ")


def _norm(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "").lower()
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return text.replace("’", "'")


# "tablets for fits", "mapiritsi epfari": a medicine named after an illness is
# not a report of the illness. The illness word is taken out before scanning.
NAMED_MEDICINE = re.compile(
    r"\b((tablets?|pills?|medicine|medication|treatment) for (the |my |his |her )?)\w+"
    r"|\b((ma)?piritsi )e?\w+")


def _clauses(text: str) -> list[str]:
    out = []
    text = NAMED_MEDICINE.sub(lambda m: m.group(1) or m.group(4), _norm(text))
    for part in CLAUSE.split(text):
        part = re.sub(r"[^a-z0-9' ]+", " ", part)
        part = re.sub(r"\s+", " ", part).strip()
        if part:
            out.append(part)
    return out


def _denied(clause: str, m: re.Match, neg: re.Pattern, aff: re.Pattern, window: int) -> bool:
    """Is this match denied? ("haana pfari", "no difficulty breathing", "mutsipa hauna kuoma")"""
    inside = m.group(0).split()[:-1]
    if any(neg.match(tok) for tok in inside):
        return True
    before = clause[:m.start()].split()[-window:]
    for i in range(len(before) - 1, -1, -1):        # nearest word first
        tok = before[i]
        if neg.match(tok):
            return not (i + 1 < len(before) and before[i + 1] in STOPPING)
        if aff.match(tok):
            return False
    return False


def _present(term: str, clauses: list[str], neg: re.Pattern, aff: re.Pattern, window: int) -> bool:
    """Is the term stated, and not denied, in some clause?"""
    guard = not term.startswith("!")
    rx = _rx(term.lstrip("!"))
    for clause in clauses:
        for m in rx.finditer(clause):
            if not guard or not _denied(clause, m, neg, aff, window):
                return True
    return False


_CACHE: dict[str, re.Pattern] = {}


def _rx(pattern: str) -> re.Pattern:
    if pattern not in _CACHE:
        _CACHE[pattern] = re.compile(pattern)
    return _CACHE[pattern]


def scan(text: str, lang: str = "sn") -> list[Rule]:
    """Every danger sign stated in the text. `lang` picks the pattern set:
    Shona text is checked with the Shona patterns and, because patients mix
    languages, with the English ones too."""
    clauses = _clauses(text)
    hits = []
    for rule in RULES:
        found = False
        if lang == "sn":
            found = any(all(_present(t, clauses, SN_NEG, SN_AFF, 3) for t in alt) for alt in rule.sn)
        if not found:
            found = any(all(_present(t, clauses, EN_NEG, EN_AFF, 4) for t in alt) for alt in rule.en)
        if found:
            hits.append(rule)
    return hits


YES = re.compile(r"^\W*(hongu|ehe+|ho+ngu|yes|yeah|yep|ndizvozvo|ndizvo|zvakanyanya|chaizvo|kwazvo)\b")
NO = re.compile(r"^\W*(kwete|aiwa|no|nope|bodo|hazvisi|haisi)\b")
FINE = re.compile(r"\b(zvakanaka|well|fine|normal\w*|okay|ok)\b")
# topic of the question -> (the answer that is a danger sign, the rule it raises)
ANSWERS = {
    "breathing": (YES, "breathing"),
    "fits": (YES, "convulsions"),
    "drinking": (NO, "cannot_drink"),
    "bleeding": (YES, "bleeding_yes"),
    "neck": (YES, "stiff_neck"),
}


def answer_sign(topic: str | None, answer: str) -> Rule | None:
    """A bare "Hongu" to "Are you struggling to breathe?" is a danger sign,
    though the answer itself names none. The rules read the question too."""
    if topic not in ANSWERS:
        return None
    pattern, key = ANSWERS[topic]
    text = _norm(answer)
    if pattern.search(text) and not (pattern is YES and FINE.search(text)):
        return BY_KEY[key]
    return None


def scan_all(texts: list[tuple[str, str]]) -> list[Rule]:
    """Scan (text, lang) pairs and return each rule once, most serious first."""
    seen: dict[str, Rule] = {}
    for text, lang in texts:
        for rule in scan(text, lang):
            seen.setdefault(rule.key, rule)
    return sorted(seen.values(), key=lambda r: -rank(r.level))


def second_opinion_level(probabilities: dict, raise_at: float) -> str | None:
    """The level the second model is sure enough of to count, or None.

    It only counts when its probability for 'emergency', or for 'urgent or
    worse', reaches the threshold. Below that it is shown but changes nothing.
    """
    try:
        p = [float(probabilities.get(str(i), 0)) for i in range(3)]
    except (TypeError, ValueError):
        return None
    if p[2] >= raise_at:
        return "emergency"
    if p[1] + p[2] >= raise_at:
        return "urgent"
    return "routine"


@dataclass
class Check:
    name: str
    level: str | None      # None: this check did not run
    detail: str = ""
    extra: dict = field(default_factory=dict)

    def public(self) -> dict:
        return {"name": self.name, "level": self.level, "detail": self.detail, **self.extra}


def combine(checks: list[Check]) -> dict:
    """The final level is the highest any check gives. If none ran, 'urgent':
    a visit nobody could assess goes ahead of the queue, not to the back."""
    ran = [c for c in checks if c.level in LEVELS]
    level = highest([c.level for c in ran]) if ran else "urgent"
    top = [c.name for c in ran if c.level == level]
    return {
        "level": level,
        "checks": [c.public() for c in checks],
        "agreed": len({c.level for c in ran}) <= 1,
        "raised_by": top if ran and len(top) < len(ran) else [],
    }
