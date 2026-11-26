"""Run one visit against a running server and print what happened.

  uv run python tools/try_visit.py "Ndine musoro uri kurwadza" "Kubva nezuro" ...
  uv run python tools/try_visit.py --audio clip.webm "Kubva nezuro"

Each argument is one patient turn. With --audio the first turn is that file.
"""

import json
import sys
import time

import httpx

BASE = "http://127.0.0.1:8000"


def main() -> None:
    args = sys.argv[1:]
    audio = None
    if args and args[0] == "--audio":
        audio, args = args[1], args[2:]
    c = httpx.Client(base_url=BASE, timeout=120)
    v = c.post("/api/visits").json()
    print(f"Visit {v['number']} ({v['id']})\nMukoti: {v['text']}  [audio: {'yes' if v['audio'] else 'NO'}]")
    turns = ([("audio", audio)] if audio else []) + [("text", a) for a in args]
    done = False
    for kind, value in turns:
        if done:
            break
        t0 = time.time()
        if kind == "audio":
            kw = {"files": {"audio": ("turn.webm", open(value, "rb"), "audio/webm")}}
        else:
            kw = {"data": {"text": value}}
        with c.stream("POST", f"/api/visits/{v['id']}/turn", **kw) as r:
            for line in r.iter_lines():
                if not line.strip():
                    continue
                ev = json.loads(line)
                dt = time.time() - t0
                if ev["type"] == "heard":
                    print(f"Patient ({dt:.1f}s): {ev['text']}")
                elif ev["type"] == "reply":
                    done = ev["done"]
                    print(f"Mukoti ({dt:.1f}s): {ev['text']}  done={ev['done']} alarm={ev['alarm']}")
                elif ev["type"] == "audio":
                    print(f"   voice ready at {dt:.1f}s ({'ok' if ev['b64'] else 'MISSING'})")
                elif ev["type"] == "timing":
                    print(f"   timing {ev}")
                elif ev["type"] == "error":
                    print("ERROR", ev["message"])
    if not done:
        c.post(f"/api/visits/{v['id']}/end")
    for _ in range(60):
        s = c.get(f"/api/visits/{v['id']}").json()
        if s["status"] != "summarising":
            break
        time.sleep(1)
    print("\nStatus:", s["status"], "| triage:", json.dumps(s["triage"]), "| alarm:", s["alarm"], "| error:", s["error"])
    print(json.dumps(s["note"], ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
