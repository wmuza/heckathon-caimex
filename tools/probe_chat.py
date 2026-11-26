"""Probe how the chat model behaves with different request options."""
import json, os, sys, time
import httpx
sys.path.insert(0, ".")
from app import config, prompts  # config loads .env
c = httpx.Client(base_url=config.BASE, headers={"Authorization": "Bearer " + os.environ["CAIMEX_API_KEY"]}, timeout=120)
c.get("/models?kind=stt")
msgs = [{"role": "system", "content": prompts.interview_system("sn")},
        {"role": "assistant", "content": prompts.LINES["sn"]["greeting"]},
        {"role": "user", "content": "Ndine musoro uri kurwadza zvakanyanya kubva nezuro, uye ndiri kunzwa kupisa muviri."}]
variants = {
    "json+none": {"reasoning_effort": "none", "response_format": {"type": "json_object"}},
    "none only": {"reasoning_effort": "none"},
    "json only": {"response_format": {"type": "json_object"}},
    "plain": {},
}
models = sys.argv[1:] or ["deepseek-v4-flash"]
for m in models:
    for name, extra in variants.items():
        t = time.time()
        r = c.post("/chat/completions", json={"model": m, "messages": msgs, "max_tokens": 300, "temperature": 0.2, **extra})
        dt = time.time() - t
        try:
            j = r.json(); msg = j["choices"][0]["message"]; u = j.get("usage", {})
            print(f"[{m} | {name}] {dt:.1f}s finish={j['choices'][0]['finish_reason']} out={u.get('completion_tokens')} "
                  f"reasoning={len(msg.get('reasoning_content') or '')}ch cost={r.headers.get('x-caimex-cost-usd')}\n   content={msg.get('content')!r}")
        except Exception as e:
            print(f"[{m} | {name}] {dt:.1f}s http={r.status_code} {r.text[:300]}")
