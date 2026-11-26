"""Character and word error rates, for checking the recogniser on real voices."""

from __future__ import annotations

import re
import unicodedata


def normalise(text: str) -> str:
    text = unicodedata.normalize("NFKC", text or "").lower().replace("’", "'")
    text = re.sub(r"[^\w' ]+", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


def _distance(a, b) -> int:
    prev = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        cur = [i]
        for j, y in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (x != y)))
        prev = cur
    return prev[-1]


def cer(reference: str, heard: str) -> float | None:
    """Character error rate against the reference, as a fraction. None if the reference is empty."""
    ref, hyp = normalise(reference), normalise(heard)
    return _distance(ref, hyp) / len(ref) if ref else None


def wer(reference: str, heard: str) -> float | None:
    ref, hyp = normalise(reference).split(), normalise(heard).split()
    return _distance(ref, hyp) / len(ref) if ref else None
