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
# Long English for staff (the forecast briefing) is read by an English voice model. The clinic's own
# voice is a Shona voice: it read "between 0 and 11" as "zero endereveni" (measured 2026-11-26).
STAFF_TTS_MODEL = os.environ.get("MUKOTI_STAFF_TTS_MODEL", "tts-1")
STAFF_TTS_VOICE = os.environ.get("MUKOTI_STAFF_TTS_VOICE", "nova")
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

# Online visits, from home (/?online=1). The emergency number is said to a patient at home with a danger
# sign. 994 is the ambulance number commonly given for Zimbabwe: confirm it for the clinic's area before use.
EMERGENCY_NUMBER = os.environ.get("MUKOTI_EMERGENCY_NUMBER", "994")
ONLINE_PER_HOUR = 3                                                   # from one device (address)
ONLINE_PER_DAY = int(os.environ.get("MUKOTI_ONLINE_PER_DAY", "100"))  # for the whole clinic

LANGS = ("sn", "en")
