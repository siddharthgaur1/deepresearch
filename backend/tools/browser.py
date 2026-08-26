"""Playwright wrapper for full page fetch / JS-rendered content / screenshots.
Runs headless Chromium — free, no external service required."""

import logging

from playwright.async_api import async_playwright

logger = logging.getLogger("deepresearch.tools.browser")


async def fetch_rendered_page(url: str, screenshot: bool = False) -> dict:
    """Returns {"text": str, "screenshot_path": str | None}. Best-effort: on any
    failure returns empty text rather than raising, since a single dead link
    shouldn't fail the whole research run."""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, wait_until="networkidle", timeout=20_000)
            text = await page.inner_text("body")

            screenshot_path = None
            if screenshot:
                screenshot_path = f"/tmp/deepresearch_{abs(hash(url))}.png"
                await page.screenshot(path=screenshot_path, full_page=True)

            await browser.close()
            return {"text": text, "screenshot_path": screenshot_path}
    except Exception:
        logger.exception("browser_fetch_failed", extra={"url": url})
        return {"text": "", "screenshot_path": None}
