"""Screenshots for the pitch deck, taken from a live run of a sample patient.

  uv run python tools/deck_shots.py http://127.0.0.1:8010 out_dir
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from browser import Browser  # noqa: E402

PICK = ("[...document.getElementById('patient').contentWindow.document.querySelectorAll('#pick button')]"
        ".find(b=>b.textContent.includes(%r)).click()")
P = "document.getElementById('patient').contentWindow.document"


async def main() -> None:
    base, out = sys.argv[1], Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    b = Browser()
    try:
        # 1. The demo page: a child whose danger sign comes out on the third answer.
        pg = await b.page(1600, 900, scale=1.5)
        await pg.goto(base + "/demo", settle=4)
        await pg.js(f"{P}.getElementById('samples').click()")
        await pg.wait(f"{P}.querySelectorAll('#pick button').length > 0", 20)
        await pg.js(PICK % "stopped drinking")
        await pg.wait(f"{P}.getElementById('qof').textContent.includes('2')", 60)
        await asyncio.sleep(1.2)
        await pg.shot(out / "demo_question.png", full=False)
        await pg.wait(f"!{P}.getElementById('done').hidden", 120)
        await asyncio.sleep(5)
        await pg.shot(out / "demo_notice.png", full=False)
        # The nurse opens the new emergency from the notice.
        await pg.js("document.getElementById('nurse').contentWindow.document.getElementById('toastOpen')?.click()")
        await asyncio.sleep(2.5)
        await pg.shot(out / "demo_alarm.png", full=False)
        print("demo", pg.errors or "ok")
        await pg.close()

        # 2. The patient's phone, mid-question, with English captions.
        pg = await b.page(390, 780, scale=3, mobile=True)
        await pg.goto(base + "/?captions=1")
        await pg.click("#samples")
        await pg.wait("document.querySelectorAll('#pick button').length > 0", 20)
        await pg.js("[...document.querySelectorAll('#pick button')].find(b=>b.textContent.includes('headache and a cough')).click()")
        await pg.wait("document.getElementById('qof').textContent.includes('3')", 90)
        await asyncio.sleep(1.0)
        await pg.shot(out / "phone_question.png", full=False)
        await pg.wait("!document.getElementById('done').hidden", 180)
        await asyncio.sleep(0.5)
        await pg.shot(out / "phone_ticket.png", full=False)
        print("phone", pg.errors or "ok")
        await pg.close()

        # 3. The nurse's queue and the engine, as a judge sees them.
        pg = await b.page(1440, 900, scale=1.5)
        await pg.goto(base + "/nurse", settle=5)
        await pg.shot(out / "nurse.png", full=False)
        await pg.goto(base + "/engine", settle=4)
        await pg.shot(out / "engine.png", full=False)
        await pg.close()
    finally:
        b.close()


asyncio.run(main())
