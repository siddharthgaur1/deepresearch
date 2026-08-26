import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import Response

from backend.api.routes.auth import require_api_key
from backend.core.database import get_db
from backend.schemas.report import ReportResponse
from backend.services import report_service

router = APIRouter(prefix="/reports", tags=["reports"], dependencies=[Depends(require_api_key)])


@router.get("/{job_id}", response_model=ReportResponse)
async def get_report(job_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> ReportResponse:
    report = await report_service.get_report_by_job(db, job_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found (job may still be running)")
    return report


@router.get("/{job_id}/pdf")
async def get_report_pdf(job_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> Response:
    report = await report_service.get_report_by_job(db, job_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found (job may still be running)")
    pdf_bytes = await report_service.render_pdf(report.markdown)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="report-{job_id}.pdf"'},
    )
