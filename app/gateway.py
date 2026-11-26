"""Every call Mukoti makes to the CAIMEx gateway goes through here.

Each call returns its result and a small record of what it cost: which service,
which model answered, how long it took and the price the gateway reported. The
records are kept with the visit, so the nurse's screen and the Engine page can
show exactly how CAIMEx was used.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import re
import time

import httpx

from . import config


class GatewayError(Exception):
    pass


client: httpx.AsyncClient | None = None

# The gateway sends no cost with speech calls (measured 2026-11-25), so those
# are worked out from the catalogue's own prices. load_prices() refreshes them.
PRICES = {"stt_per_minute": 0.2247, "tts_per_1m_chars": 0.12}


def start() -> None:
    global client
    if not config.API_KEY:
        raise RuntimeError("CAIMEX_API_KEY is not set. Put it in .env")
    client = httpx.AsyncClient(
        base_url=config.BASE, headers={"Authorization": f"Bearer {config.API_KEY}"},
        timeout=httpx.Timeout(100, connect=30),      # each caller sets its own, shorter limit
        limits=httpx.Limits(max_keepalive_connections=8, keepalive_expiry=120),
    )


async def stop() -> None:
    if client is not None:
        await client.aclose()


async def keep_warm() -> None:
    """Opening a connection to the gateway took 8 to 15 s at the venue; a reused
    one answers in 1 to 2 s. Keep four open (a turn's calls can overlap)."""
    while True:
        try:
            assert client is not None
            await asyncio.gather(*(client.get("/models", params={"kind": "stt"}) for _ in range(4)))
        except Exception:
            pass
        await asyncio.sleep(20)


async def _post(path: str, **kw) -> httpx.Response:
    """POST with one retry on the statuses the gateway says are safe to retry."""
    assert client is not None
    last: Exception | None = None
    for _ in range(2):
        try:
            r = await client.post(path, **kw)
        except httpx.TimeoutException as e:      # never wait twice for a call that stalled
            raise GatewayError(f"{path}: {type(e).__name__}") from e
        except httpx.HTTPError as e:
            last = GatewayError(f"{path}: {type(e).__name__}")
        else:
            if r.status_code < 400:
                return r
            last = GatewayError(f"{path} returned {r.status_code}: {r.text[:200]}")
            if r.status_code not in (429, 502, 503, 504):
                break
        await asyncio.sleep(1.0)
    raise last or GatewayError(path)


def _cost(r: httpx.Response, body: dict | None = None) -> float | None:
    v = r.headers.get("x-caimex-cost-usd")
    if v is None and body:
        v = (body.get("usage") or {}).get("cost")
    try:
        return float(v) if v is not None else None
    except (TypeError, ValueError):
        return None


def _call(step: str, service: str, model: str, t0: float, cost: float | None = None, **extra) -> dict:
    return {"step": step, "service": service, "model": model, "ms": round((time.time() - t0) * 1000),
            "cost": cost, "at": time.time(), **extra}


def seconds_of(audio: bytes, mime: str) -> float | None:
    """How long a clip is. Exact for WAV; for the MP3 our own voice model makes
    (96 kbit/s), close enough. None when it cannot be told."""
    if audio[:4] == b"RIFF" and audio[8:12] == b"WAVE" and len(audio) > 44:
        rate = int.from_bytes(audio[28:32], "little")       # bytes per second
        return (len(audio) - 44) / rate if rate else None
    if "mpeg" in mime or "mp3" in mime:
        return len(audio) * 8 / 96000
    return None


async def transcribe(audio: bytes, filename: str, mime: str, lang: str) -> tuple[str, dict]:
    t0 = time.time()
    r = await _post(
        "/audio/transcriptions",
        data={"model": config.STT_MODEL, "language": lang},
        files={"file": (filename, audio, mime)},
    )
    body = r.json()
    secs, cost = seconds_of(audio, mime), _cost(r, body)
    priced = cost is None and secs is not None
    if priced:
        cost = round(secs / 60 * PRICES["stt_per_minute"], 6)
    return (body.get("text") or "").strip(), _call(
        "hear", "/v1/audio/transcriptions", config.STT_MODEL, t0, cost, bytes=len(audio),
        seconds=round(secs, 2) if secs is not None else None, from_price_list=priced)


def tts_path(text: str, lang: str, voice: str):
    key = hashlib.sha256(f"{config.TTS_MODEL}|{voice}|{lang}|{text}".encode()).hexdigest()[:24]
    return config.TTS_DIR / f"{key}.mp3"


async def speak(text: str, lang: str, voice: str | None = None) -> tuple[bytes, dict]:
    """Speech as MP3. Cached on disk, so a fixed line is only ever made once."""
    voice = voice or config.TTS_VOICE
    t0 = time.time()
    path = tts_path(text, lang, voice)
    if path.exists():
        return path.read_bytes(), _call("speak", "/v1/audio/speech", config.TTS_MODEL, t0, 0.0,
                                        cached=True, chars=len(text))
    r = await _post(
        "/audio/speech",
        json={"model": config.TTS_MODEL, "voice": voice, "language": lang, "input": text,
              "response_format": "mp3", "stream": False},
    )
    if "audio" not in r.headers.get("content-type", "") or len(r.content) < 800:
        raise GatewayError("/audio/speech did not return audio")       # never save a bad line for good
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(r.content)
    cost = _cost(r)
    priced = cost is None
    if priced:
        cost = round(len(text) / 1e6 * PRICES["tts_per_1m_chars"], 8)
    return r.content, _call("speak", "/v1/audio/speech", config.TTS_MODEL, t0, cost,
                            cached=False, chars=len(text), from_price_list=priced)


def parse_json(text: str) -> dict:
    text = re.sub(r"^```(?:json)?|```$", "", (text or "").strip(), flags=re.M).strip()
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise GatewayError("the model did not return JSON")
    try:
        out = json.loads(text[start:end + 1])
    except ValueError as e:
        raise GatewayError(f"the model returned broken JSON ({e})") from e
    if not isinstance(out, dict):
        raise GatewayError("the model did not return a JSON object")
    return out


async def chat_json(step: str, model: str, system: str, messages: list[dict], max_tokens: int,
                    think: bool = False) -> tuple[dict, dict]:
    """One chat call that must answer with a JSON object.

    The self-hosted chat model reasons out of sight before it answers, even
    with reasoning_effort "none", which costs 4 to 7 seconds a turn and can
    use up max_tokens before any answer is written. `enable_thinking: false`
    is what switches it off (measured: 1.3 s against 6 s). The live interview
    runs without thinking; the nurse's note runs with it, so max_tokens there
    must leave room for both.
    """
    t0 = time.time()
    body = {
        "model": model,
        "messages": [{"role": "system", "content": system}, *messages],
        "max_tokens": max_tokens,
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }
    if not think:
        body["enable_thinking"] = False
        body["chat_template_kwargs"] = {"enable_thinking": False}
    r = await _post("/chat/completions", json=body)
    data = r.json()
    usage = data.get("usage") or {}
    call = _call(step, "/v1/chat/completions", data.get("model") or model, t0, _cost(r, data),
                 tokens_in=usage.get("prompt_tokens"), tokens_out=usage.get("completion_tokens"),
                 thinking=think)
    content = (data.get("choices") or [{}])[0].get("message", {}).get("content") or ""
    return parse_json(content), call


async def decide(step: str, state: str, questions: dict) -> tuple[dict, dict]:
    """Typed answers with probabilities from the Decisions endpoint."""
    t0 = time.time()
    r = await _post("/decisions", json={"model": config.DECISION_MODEL, "state": state,
                                        "questions": questions})
    data = r.json()
    return data.get("answers") or {}, _call(step, "/v1/decisions", data.get("model") or config.DECISION_MODEL,
                                            t0, _cost(r, data))


async def load_prices() -> None:
    """Read the speech prices from the gateway's catalogue."""
    try:
        for m in await catalogue():
            p = m.get("pricing") or {}
            if m["id"] == config.STT_MODEL and p.get("stt_per_minute"):
                PRICES["stt_per_minute"] = float(p["stt_per_minute"])
            if m["id"] == config.TTS_MODEL and p.get("tts_per_1m_chars"):
                PRICES["tts_per_1m_chars"] = float(p["tts_per_1m_chars"])
    except Exception:
        pass


async def catalogue() -> list[dict]:
    """The gateway's own description of the models we use (where each is hosted)."""
    assert client is not None
    r = await client.get("/models", params={"kind": "all"})
    data = r.json()
    return data.get("data", data) if isinstance(data, dict) else data
