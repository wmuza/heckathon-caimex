"""End-to-end check of the patient screen in a real browser.

  uv run python tools/e2e.py http://127.0.0.1:8000 out_dir tests/fixtures/shona_sentence.wav

The fixture is one Shona sentence in the synthetic voice "getrude", with a second
of silence before it and six after. Give its full path: Chrome needs one.

1. A sample patient: the whole visit plays by itself, to the ticket.
2. With mic.wav: Chrome plays that file as the microphone, so the hands-free
   listening (start by itself, stop on silence) is exercised for real.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from browser import Browser  # noqa: E402

VISIBLE = "(id)=>!document.getElementById(id).hidden"


async def sample(base: str, out: Path) -> bool:
    b = Browser()
    try:
        pg = await b.page(390, 800, mobile=True)
        await pg.goto(base + "/")
        await pg.shot(out / "e2e_1_welcome.png")
        await pg.click("#samples")
        assert await pg.wait("document.querySelectorAll('#pick button').length > 0", 20), "no sample patients listed"
        await pg.shot(out / "e2e_2_samples.png", full=False)
        await pg.js("[...document.querySelectorAll('#pick button')].find(b=>b.textContent.includes('stopped drinking')).click()")
        assert await pg.wait("!document.getElementById('talk').hidden", 30), "the talk did not start"
        shots = 0
        for i in range(240):
            await asyncio.sleep(0.5)
            said = await pg.js("document.getElementById('saidText').textContent")
            if said and said != "…" and shots < 2 and i > 8:
                shots += 1
                await pg.shot(out / f"e2e_3_talk_{shots}.png", full=False)
                await asyncio.sleep(6)
            if await pg.js("!document.getElementById('done').hidden"):
                break
        done = await pg.js("!document.getElementById('done').hidden")
        await pg.shot(out / "e2e_4_ticket.png", full=False)
        hist = await pg.js("[...document.querySelectorAll('#hist p')].map(p=>p.textContent)")
        print("   English captions shown:", await pg.js("!!document.getElementById('questionEn').textContent"))
        print("SAMPLE finished:", done, "| lines:", len(hist), "| ticket:", await pg.js("document.getElementById('doneTagText').textContent"))
        for line in hist:
            print("   ", line)
        print("   errors:", pg.errors, pg.console)
        return bool(done) and not pg.errors
    finally:
        b.close()


async def mic(base: str, out: Path, wav: str) -> bool:
    b = Browser(mic_wav=wav)
    try:
        pg = await b.page(390, 800, mobile=True)
        await pg.goto(base + "/")
        await pg.click("#go")
        assert await pg.wait("!document.getElementById('talk').hidden", 30), "the talk did not start"
        got_rec = await pg.wait("document.getElementById('micWrap').classList.contains('rec')", 40)
        await asyncio.sleep(2)
        await pg.shot(out / "e2e_5_listening.png", full=False)
        heard = await pg.wait("(()=>{const t=document.getElementById('saidText').textContent;return t&&t!=='…'})()", 60)
        said = await pg.js("document.getElementById('saidText').textContent")
        await asyncio.sleep(2.5)
        q = await pg.js("document.getElementById('question').textContent")
        await pg.shot(out / "e2e_6_answered.png", full=False)
        print("MIC opened by itself:", got_rec, "| stopped on silence and heard:", heard)
        print("   heard:", said)
        print("   next question:", q, "|", await pg.js("document.getElementById('qof').textContent"))
        print("   errors:", pg.errors, pg.console)
        await pg.click("#finish")
        return bool(got_rec and heard) and not pg.errors
    finally:
        b.close()


async def main() -> None:
    base, out = sys.argv[1], Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    ok = True if "--mic-only" in sys.argv else await sample(base, out)
    if len(sys.argv) > 3:
        ok = await mic(base, out, sys.argv[3]) and ok
    sys.exit(0 if ok else 1)


asyncio.run(main())
