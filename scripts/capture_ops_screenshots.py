"""One-off script: captures Flower and Grafana screenshots for the README.
Not part of the app; run manually against a live `docker compose up` stack.

    python scripts/capture_ops_screenshots.py
"""

import asyncio
from pathlib import Path

from playwright.async_api import async_playwright

OUT_DIR = Path(__file__).resolve().parent.parent / "docs" / "screenshots"
OUT_DIR.mkdir(parents=True, exist_ok=True)


async def main() -> None:
    async with async_playwright() as p:
        browser = await p.chromium.launch()

        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await context.new_page()
        await page.goto(
            "http://localhost:3001/login",
            wait_until="load",
            timeout=30000,
        )
        await page.locator('input[name="user"]').fill("admin")
        await page.locator('input[name="password"]').fill("admin")
        await page.locator('button[type="submit"]').click()
        await page.wait_for_timeout(1500)

        await page.goto(
            "http://localhost:3001/d/abf6204b-e04d-47de-9548-288b7be8fade/deepresearch?orgId=1&refresh=5s",
            wait_until="load",
            timeout=30000,
        )
        await page.wait_for_timeout(6000)
        shot = OUT_DIR / "06-grafana.png"
        await page.screenshot(path=str(shot))
        print(f"captured {shot}")
        await context.close()

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
