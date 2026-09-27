import asyncio
from unittest import mock

import pytest

from backend.services import report_service

try:
    import weasyprint  # noqa: F401  -- needs system pango, not just the wheel
except OSError as exc:  # pragma: no cover
    pytest.skip(f"weasyprint system libraries unavailable: {exc}", allow_module_level=True)


def test_render_pdf_produces_a_pdf():
    pdf = asyncio.run(report_service.render_pdf("# Title\n\n- a\n- b\n\n| a | b |\n|---|---|\n| 1 | 2 |\n"))
    assert pdf.startswith(b"%PDF-")


def test_render_pdf_never_fetches_embedded_resources():
    # The report is LLM output over untrusted search results: an injected
    # metadata-endpoint image or a file:// read must never reach the network
    # or the disk. WeasyPrint swallows fetch exceptions as warnings, so assert
    # on the call record rather than relying on an exception surfacing.
    md = (
        "![x](http://169.254.169.254/latest/meta-data/)\n\n"
        "<img src='file:///etc/passwd'>\n\n"
        "<link rel='stylesheet' href='http://internal.example/x.css'>\n"
    )
    with mock.patch("urllib.request.OpenerDirector.open") as opened:
        pdf = asyncio.run(report_service.render_pdf(md))
    assert not opened.called
    assert pdf.startswith(b"%PDF-")
    assert b"root:" not in pdf
