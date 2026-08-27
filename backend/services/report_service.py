import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.report import Report


async def get_report_by_job(db: AsyncSession, job_id: uuid.UUID) -> Report | None:
    result = await db.execute(select(Report).where(Report.job_id == job_id))
    return result.scalar_one_or_none()


def _block_remote_fetch(url: str, timeout: float = 10, ssl_context=None):
    """WeasyPrint fetches any <img src>/CSS url() it finds over the network
    by default. Report markdown is LLM output grounded in untrusted web
    search results, so a prompt-injected or malicious source could embed a
    resource URL pointing at an internal service or a cloud metadata
    endpoint (169.254.169.254) -- classic SSRF via document generation.
    Reports never legitimately embed remote resources, so blocking all
    fetches here is a pure safety net with no functional downside."""
    raise ValueError(f"remote resource fetching is disabled for report PDFs: {url}")


async def render_pdf(markdown: str) -> bytes:
    """Optional PDF export via WeasyPrint. Markdown -> HTML -> PDF, kept
    dependency-light (no full markdown extension stack) since reports are
    plain headings/paragraphs/lists."""
    import markdown as md
    from weasyprint import HTML

    html_body = md.markdown(markdown, extensions=["extra"])
    html = f"<html><body>{html_body}</body></html>"
    return HTML(string=html, url_fetcher=_block_remote_fetch).write_pdf()
