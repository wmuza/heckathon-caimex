"""A very small driver for Google Chrome over its debugging protocol.

Used by tools/shots.py and tools/e2e.py so that checking the screens needs
nothing beyond Chrome itself and the `websockets` package.
"""

from __future__ import annotations

import asyncio
import base64
import json
import shutil
import socket
import subprocess
import tempfile
import urllib.request
from pathlib import Path

import websockets

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class Browser:
    def __init__(self, mic_wav: str | None = None):
        self.port = _free_port()
        self.dir = tempfile.mkdtemp(prefix="mukoti-chrome-")
        args = [CHROME, "--headless=new", f"--remote-debugging-port={self.port}", f"--user-data-dir={self.dir}",
                "--no-first-run", "--disable-gpu", "--hide-scrollbars", "--mute-audio",
                "--autoplay-policy=no-user-gesture-required",
                "--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream", "about:blank"]
        if mic_wav:      # Chrome's audio process is sandboxed and cannot read the file otherwise
            args.insert(-1, f"--use-file-for-fake-audio-capture={mic_wav}%noloop")
            args.insert(-1, "--disable-features=AudioServiceSandbox")
        self.proc = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    async def page(self, width: int, height: int, scale: float = 2, mobile: bool = False) -> "Page":
        for _ in range(60):
            try:
                req = urllib.request.Request(f"http://127.0.0.1:{self.port}/json/new?about:blank", method="PUT")
                info = json.loads(urllib.request.urlopen(req, timeout=2).read())
                break
            except Exception:
                await asyncio.sleep(0.25)
        else:
            raise RuntimeError("Chrome did not start")
        ws = await websockets.connect(info["webSocketDebuggerUrl"], max_size=None)
        pg = Page(ws)
        await pg.start()
        await pg.send("Emulation.setDeviceMetricsOverride", width=width, height=height,
                      deviceScaleFactor=scale, mobile=mobile)
        return pg

    def close(self) -> None:
        self.proc.terminate()
        try:
            self.proc.wait(timeout=5)
        except Exception:
            self.proc.kill()
        shutil.rmtree(self.dir, ignore_errors=True)


class Page:
    def __init__(self, ws):
        self.ws, self.n, self.waiting, self.errors, self.console = ws, 0, {}, [], []

    async def start(self) -> None:
        self.reader = asyncio.create_task(self._read())
        for domain in ("Page", "Runtime", "Log"):
            await self.send(f"{domain}.enable")

    async def _read(self) -> None:
        try:
            async for raw in self.ws:
                m = json.loads(raw)
                if "id" in m and m["id"] in self.waiting:
                    self.waiting.pop(m["id"]).set_result(m)
                elif m.get("method") == "Runtime.exceptionThrown":
                    d = m["params"]["exceptionDetails"]
                    self.errors.append((d.get("exception") or {}).get("description") or d.get("text"))
                elif m.get("method") == "Runtime.consoleAPICalled" and m["params"]["type"] in ("error", "warning"):
                    self.console.append(" ".join(str(a.get("value", a.get("description", ""))) for a in m["params"]["args"]))
                elif m.get("method") == "Log.entryAdded" and m["params"]["entry"]["level"] == "error":
                    self.console.append(m["params"]["entry"]["text"] + " " + m["params"]["entry"].get("url", ""))
        except Exception:
            pass

    async def send(self, method: str, **params):
        self.n += 1
        fut = asyncio.get_running_loop().create_future()
        self.waiting[self.n] = fut
        await self.ws.send(json.dumps({"id": self.n, "method": method, "params": params}))
        m = await asyncio.wait_for(fut, 60)
        if "error" in m:
            raise RuntimeError(f"{method}: {m['error']}")
        return m["result"]

    async def init_script(self, source: str) -> None:
        await self.send("Page.addScriptToEvaluateOnNewDocument", source=source)

    async def goto(self, url: str, settle: float = 1.5) -> None:
        await self.send("Page.navigate", url=url)
        await asyncio.sleep(settle)

    async def js(self, expression: str):
        r = await self.send("Runtime.evaluate", expression=expression, awaitPromise=True,
                            returnByValue=True, userGesture=True)
        if "exceptionDetails" in r:
            raise RuntimeError(str(r["exceptionDetails"].get("exception", {}).get("description"))[:300])
        return r["result"].get("value")

    async def click(self, selector: str) -> None:
        await self.js(f"document.querySelector({json.dumps(selector)}).click()")

    async def wait(self, expression: str, timeout: float = 30, every: float = 0.25) -> bool:
        for _ in range(int(timeout / every)):
            if await self.js(expression):
                return True
            await asyncio.sleep(every)
        return False

    async def shot(self, path: str | Path, full: bool = True) -> None:
        r = await self.send("Page.captureScreenshot", format="png", captureBeyondViewport=full)
        Path(path).write_bytes(base64.b64decode(r["data"]))

    async def overflow(self) -> int:
        return await self.js("document.documentElement.scrollWidth - document.documentElement.clientWidth")

    async def close(self) -> None:
        self.reader.cancel()
        await self.ws.close()
