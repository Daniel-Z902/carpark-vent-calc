"""Report writers: Excel (mirrors the workbook layout), HTML and PDF."""

from carpark_vent.report.excel import write_excel
from carpark_vent.report.html import render_html, write_html

__all__ = ["write_excel", "write_html", "render_html", "write_pdf"]


def write_pdf(result, path):  # lazy import: reportlab is an optional extra
    from carpark_vent.report.pdf import write_pdf as _w

    return _w(result, path)
