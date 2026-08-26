import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.report import Report


async def get_report_by_job(db: AsyncSession, job_id: uuid.UUID) -> Report | None:
    result = await db.execute(select(Report).where(Report.job_id == job_id))
    return result.scalar_one_or_none()


async def render_pdf(markdown: str) -> bytes:
    """Optional PDF export via WeasyPrint. Markdown -> HTML -> PDF, kept
    dependency-light (no full markdown extension stack) since reports are
    plain headings/paragraphs/lists."""
    import markdown as md
    from weasyprint import HTML

    html_body = md.markdown(markdown, extensions=["extra"])
    html = f"<html><body>{html_body}</body></html>"
    return HTML(string=html).write_pdf()
