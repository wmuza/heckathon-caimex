"""Screenshots of every screen, light or dark, for checking the look.

  uv run python tools/shots.py http://127.0.0.1:8010 out_dir [light|dark]

Also reports any horizontal overflow and any script error on each screen.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from browser import Browser  # noqa: E402

SCREENS = [
    ("patient_phone", "/", 390, 800, 1.0), ("patient_720p_large_text", "/", 360, 640, 1.3),
    ("nurse_desktop", "/nurse", 1366, 900, 1.0), ("nurse_phone", "/nurse", 390, 800, 1.0),
    ("engine_desktop", "/engine", 1366, 900, 1.0), ("engine_phone", "/engine", 390, 800, 1.0),
    ("check_phone", "/check", 390, 800, 1.0), ("check_desktop", "/check", 1100, 800, 1.0),
    ("demo_projector", "/demo", 1600, 900, 1.0),
]


async def main() -> None:
    base, out = sys.argv[1], Path(sys.argv[2])
    theme = sys.argv[3] if len(sys.argv) > 3 else "light"
    out.mkdir(parents=True, exist_ok=True)
    b = Browser()
    try:
        for name, path, w, h, scale in SCREENS:
            pg = await b.page(w, h, mobile=w < 600)
            await pg.init_script(f"try{{localStorage.setItem('mukoti-theme','{theme}')}}catch(e){{}}")
            if scale != 1.0:
                await pg.init_script("document.addEventListener('DOMContentLoaded',()=>"
                                     f"document.documentElement.style.fontSize='{scale * 100}%')")
            await pg.goto(base + path, settle=3.5)
            await pg.shot(out / f"{name}_{theme}.png")
            over = await pg.overflow()
            print(name, "OVERFLOW %dpx" % over if over > 0 else "ok", pg.errors or "", pg.console or "")
            await pg.close()
    finally:
        b.close()


asyncio.run(main())
