import logging
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import escape

from .models import ReportHistory

logger = logging.getLogger(__name__)


def _fetch_chart_data(chart):
    """Execute chart query and return columns + rows + pre-rendered HTML table."""
    from django.db import connection

    if not chart.dataset:
        return {"columns": [], "rows": [], "table_html": "", "error": "No dataset assigned to chart."}

    dataset = chart.dataset
    config = chart.config or {}

    if not dataset.table_name:
        return {"columns": [], "rows": [], "table_html": "", "error": "Dataset has no table_name configured."}

    try:
        sql = f'SELECT * FROM "{dataset.table_name}"'
        where = []
        filters = config.get("filters", [])
        params = []
        for f in filters:
            col = f.get("column", "")
            op = f.get("operator", "eq")
            val = f.get("value", "")
            safe_col = col.replace('"', '""')
            if op == "eq":
                where.append(f'"{safe_col}" = %s')
                params.append(val)
            elif op == "gt":
                where.append(f'"{safe_col}" > %s')
                params.append(val)
            elif op == "gte":
                where.append(f'"{safe_col}" >= %s')
                params.append(val)
            elif op == "lt":
                where.append(f'"{safe_col}" < %s')
                params.append(val)
            elif op == "lte":
                where.append(f'"{safe_col}" <= %s')
                params.append(val)
            elif op == "contains":
                where.append(f'"{safe_col}" LIKE %s')
                params.append(f"%{val}%")
        if where:
            sql += " WHERE " + " AND ".join(where)

        limit = config.get("limit", 100)
        sql += f" LIMIT {limit}"

        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            columns = [col_desc[0] for col_desc in cursor.description] if cursor.description else []
            raw_rows = cursor.fetchall() or []
            rows = [dict(zip(columns, row)) for row in raw_rows]

        # Build HTML table
        html = '<table><thead><tr>'
        for c in columns:
            html += f'<th>{escape(c)}</th>'
        html += '</tr></thead><tbody>'
        for row in rows[:20]:
            html += '<tr>'
            for c in columns:
                html += f'<td>{escape(str(row.get(c, "")))}</td>'
            html += '</tr>'
        html += '</tbody></table>'
        if len(rows) > 20:
            html += f'<p class="meta">Showing first 20 of {len(rows)} rows</p>'

        return {"columns": [{"name": c} for c in columns], "rows": rows, "table_html": html, "error": None}
    except Exception as e:
        logger.exception(f"Error fetching data for chart {chart.id}")
        return {"columns": [], "rows": [], "table_html": "", "error": str(e)}


def generate_report(report):
    """
    Generate a scheduled report.
    Returns a dict with 'html' content and optionally 'pdf_path'.
    """
    dashboard = report.dashboard
    charts_data = []

    if dashboard.layout and "charts" in dashboard.layout:
        from charts.models import Chart

        chart_ids = []
        chart_items = []
        for item in dashboard.layout["charts"]:
            chart_id = item.get("chart_id") or item.get("chartId")
            if chart_id:
                chart_ids.append(chart_id)
                chart_items.append(item)

        charts_map: dict[int, Chart] = {}
        if chart_ids:
            for chart in Chart.objects.select_related("dataset").filter(id__in=chart_ids):
                charts_map[chart.id] = chart

        for item in chart_items:
            chart_id = item.get("chart_id") or item.get("chartId")
            chart = charts_map.get(chart_id)
            if chart:
                chart_data = _fetch_chart_data(chart)
                charts_data.append({
                    "chart": chart,
                    "chart_data": chart_data,
                    "layout": item,
                })

    html_content = render_to_string("reports/dashboard_report.html", {
        "report_name": report.name,
        "dashboard": dashboard,
        "charts_data": charts_data,
        "generated_at": timezone.now(),
    })

    return {"html": html_content}


def send_report_email(report, html_content, file_path=None):
    """Email the report to its recipients."""
    recipients = list(report.recipients.values_list("email", flat=True))
    if not recipients:
        logger.warning(f"No recipients for report {report.id}")
        return False

    subject = f"Report: {report.name}"
    send_mail(
        subject,
        "",
        settings.DEFAULT_FROM_EMAIL or "noreply@example.com",
        recipients,
        html_message=html_content,
        fail_silently=False,
    )
    return True


def generate_and_send(report):
    """Generate report, send email, and store history record."""
    try:
        result = generate_report(report)
        html_content = result.get("html", "")
        sent = send_report_email(report, html_content)
        report.last_sent = timezone.now()
        report.save(update_fields=["last_sent"])
        ReportHistory.objects.create(
            report=report,
            recipients_count=report.recipients.count(),
            format=report.format,
            status="sent" if sent else "failed",
            rendered_html=html_content,
        )
        return {"status": "sent", "message": "Report generated and sent."}
    except Exception as e:
        logger.exception(f"Error generating report {report.id}")
        ReportHistory.objects.create(
            report=report,
            recipients_count=report.recipients.count(),
            format=report.format,
            status="failed",
            error_message=str(e),
            rendered_html="",
        )
        raise
