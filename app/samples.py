"""Made-up patients, for demonstrations without personal data and for the evaluation."""

from __future__ import annotations

import json

from . import config, gateway, visits

_DATA: dict | None = None


def data() -> dict:
    global _DATA
    if _DATA is None:
        _DATA = json.loads((config.SAMPLES / "patients.json").read_text())
    return _DATA


def all_patients() -> list[dict]:
    return data()["patients"]


def get(sample_id: str) -> dict | None:
    return next((p for p in all_patients() if p["id"] == sample_id), None)


def line(sample: dict, topic: str) -> str:
    """What this patient says when asked about a topic."""
    if topic == "main":
        return sample["opening"]
    return sample["answers"].get(topic) or data()["defaults"][sample["lang"]].get(topic) \
        or data()["defaults"][sample["lang"]]["other"]


async def voice(sample: dict, topic: str) -> bytes:
    """The line in a synthetic voice (never the voice Mukoti itself uses)."""
    mp3, _ = await gateway.speak(line(sample, topic), sample["lang"], sample.get("voice") or "rufaro")
    return mp3


async def run(sample: dict, spoken: bool = False) -> dict:
    """Play a whole visit for this patient through the real pipeline.

    With spoken=True each line is synthesised and sent through the recogniser,
    so the speech models are exercised too. Returns the finished visit.
    """
    s = visits.new(sample["lang"], sample=sample["id"])
    visits.save()
    topic = "main"
    for _ in range(12):
        kw = {"blob": await voice(sample, topic), "mime": "audio/mpeg"} if spoken \
            else {"text": line(sample, topic)}
        done = False
        async for ev in visits.take_turn(s, want_audio=False, **kw):
            if ev["type"] == "reply":
                done, topic = ev["done"], ev["topic"]
        if done or s["status"] != "talking":
            break
    else:
        visits.finish(s)
    return s
