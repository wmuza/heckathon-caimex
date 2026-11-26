"""Settings. Everything can be changed from the environment or the .env file."""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load_env() -> None:
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


_load_env()

WEB = ROOT / "web"
SAMPLES = ROOT / "samples"
EVAL = ROOT / "eval"
DATA = Path(os.environ.get("MUKOTI_DATA", ROOT / "data"))
TTS_DIR = DATA / "tts"
AUDIO_DIR = DATA / "audio"
STORE = DATA / "sessions.json"
VOICE_CHECK = DATA / "voicecheck.jsonl"

BASE = os.environ.get("CAIMEX_BASE_URL", "https://api.caimex.ai/v1")
API_KEY = os.environ.get("CAIMEX_API_KEY", "")

STT_MODEL = os.environ.get("MUKOTI_STT_MODEL", "languages-lab-stt-large-1.3")
TTS_MODEL = os.environ.get("MUKOTI_TTS_MODEL", "languages-lab-tts-large-1.3")
TTS_VOICE = os.environ.get("MUKOTI_TTS_VOICE", "getrude")
CHAT_MODEL = os.environ.get("MUKOTI_CHAT_MODEL", "deepseek-v4-flash")
NOTE_MODEL = os.environ.get("MUKOTI_NOTE_MODEL", CHAT_MODEL)
DECISION_MODEL = os.environ.get("MUKOTI_DECISION_MODEL", "d3-nano")

# The second opinion raises the level when it is this sure of a higher one.
SECOND_OPINION_RAISE_AT = float(os.environ.get("MUKOTI_SECOND_OPINION_RAISE_AT", "0.6"))

# The nurse's queue asks for this PIN when it is set. Leave empty on a laptop demo.
NURSE_PIN = os.environ.get("MUKOTI_NURSE_PIN", "")

# A fee waiver, a second supply on one ticket and a change to a stock count need this PIN.
# The default is for a laptop demo only: set your own before real use.
SUPERVISOR_PIN = os.environ.get("MUKOTI_SUPERVISOR_PIN", "2468")
SUPERVISOR_PIN_IS_DEMO = "MUKOTI_SUPERVISOR_PIN" not in os.environ

# The province this clinic is in, for the national warnings it receives.
PROVINCE = os.environ.get("MUKOTI_PROVINCE", "Manicaland")

# Visits older than this are deleted, recordings included, when the server starts.
KEEP_HOURS = float(os.environ.get("MUKOTI_KEEP_HOURS", "24"))

LANGS = ("sn", "en")
