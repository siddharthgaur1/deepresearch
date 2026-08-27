"""One-off script: drives the running DeepResearch UI with Playwright to
capture screenshots (and a stitched GIF) for the README. Not part of the
app; run manually against a live `docker compose up` stack.

    python scripts/capture_demo.py
"""

import asyncio
import json
import urllib.request
from pathlib import Path

from playwright.async_api import async_playwright

OUT_DIR = Path(__file__).resolve().parent.parent / "docs" / "screenshots"
OUT_DIR.mkdir(parents=True, exist_ok=True)

QUERY = "What are the tradeoffs between RAG and fine-tuning for domain-specific chatbots?"
API_URL = "http://localhost:8000"
API_KEY = "dev-key"


def submit_job(query: str) -> str:
    req = urllib.request.Request(
        f"{API_URL}/jobs",
        data=json.dumps({"query": query}).encode(),
        headers={"Content-Type": "application/json", "x-api-key": API_KEY},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)["job_id"]


def get_job_status(job_id: str) -> str:
    req = urllib.request.Request(f"{API_URL}/jobs/{job_id}", headers={"x-api-key": API_KEY})
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)["status"]


async def main() -> None:
    frames: list[Path] = []
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1280, "height": 800})
        page.on("pageerror", lambda exc: print(f"[pageerror] {exc}"))

        await page.goto(f"{API_URL.replace('8000', '3000')}", wait_until="load", timeout=120000)
        await page.wait_for_timeout(1000)
        home_shot = OUT_DIR / "01-home.png"
        await page.screenshot(path=str(home_shot))
        frames.append(home_shot)
        print(f"captured {home_shot}")

        textarea = page.locator("textarea")
        await textarea.wait_for(state="visible", timeout=30000)
        await textarea.click()
        await textarea.fill(QUERY)
        typed_shot = OUT_DIR / "02-query-typed.png"
        await page.screenshot(path=str(typed_shot))
        frames.append(typed_shot)
        print(f"captured {typed_shot}")

        # Submit via the API directly rather than clicking through the UI —
        # the click/hydration timing was flaky under CPU load from Ollama +
        # the rest of the stack; this is just as real a smoke test of the
        # backend and sidesteps that flakiness for capturing screenshots.
        job_id = submit_job(QUERY)
        print(f"submitted job {job_id}")
        await page.goto(f"http://localhost:3000/jobs/{job_id}", wait_until="load", timeout=60000)
        await page.wait_for_timeout(2500)

        job_shot = None
        for i in range(8):
            await page.wait_for_timeout(4000)
            shot = OUT_DIR / f"03-job-feed-{i}.png"
            await page.screenshot(path=str(shot))
            frames.append(shot)
            print(f"captured {shot}")
            if job_shot is None and i >= 1:
                job_shot = shot
            if get_job_status(job_id) == "done":
                break

        if job_shot:
            (OUT_DIR / "03-job-feed.png").write_bytes(job_shot.read_bytes())

        for _ in range(60):
            if get_job_status(job_id) == "done":
                break
            await page.wait_for_timeout(3000)

        await page.goto(f"http://localhost:3000/reports/{job_id}", wait_until="load", timeout=60000)
        await page.wait_for_timeout(2000)
        report_shot = OUT_DIR / "04-report.png"
        await page.screenshot(path=str(report_shot), full_page=True)
        frames.append(report_shot)
        print(f"captured {report_shot}")

        await browser.close()

    build_gif(frames)


def build_gif(frames: list[Path]) -> None:
    from PIL import Image

    images = []
    for f in frames:
        if not f.exists():
            continue
        img = Image.open(f).convert("RGB")
        img.thumbnail((960, 720))
        images.append(img)

    if not images:
        return

    gif_path = OUT_DIR / "demo.gif"
    images[0].save(
        gif_path,
        save_all=True,
        append_images=images[1:],
        duration=[1400] * len(images),
        loop=0,
    )
    print(f"wrote {gif_path}")


if __name__ == "__main__":
    asyncio.run(main())
