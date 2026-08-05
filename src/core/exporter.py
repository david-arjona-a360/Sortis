from datetime import datetime

from PySide6.QtPrintSupport import QPrinter, QPrintDialog
from PySide6.QtGui import QTextDocument, QFont
from PySide6.QtWidgets import QFileDialog, QMessageBox

from src.models.request import Request


def export_to_pdf(requests, parent_widget):
    path, _ = QFileDialog.getSaveFileName(parent_widget, "Export to PDF", "requests.pdf", "PDF (*.pdf)")
    if not path:
        return
    html = "<html><head><meta charset='utf-8'></head><body>"
    html += "<h1>Request Report</h1>"
    html += f"<p>Generated: {datetime.now():%Y-%m-%d %H:%M}</p>"
    html += "<hr>"
    for req in requests:
        html += f"<h3>{req.id}</h3>"
        html += f"<p>Date: {req.date}<br>"
        html += f"Requestor: {req.requestor_name} ({req.requestor_email})<br>"
        html += f"Department: {req.department}<br>"
        html += f"Position: {req.position}<br>"
        html += f"Current: {req.current_employee or 'N/A'}<br>"
        html += f"Proposed: {req.proposed_employee}</p><hr>"
    html += "</body></html>"

    doc = QTextDocument()
    doc.setDefaultFont(QFont("Segoe UI", 10))
    doc.setHtml(html)
    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
    printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
    printer.setOutputFileName(path)
    doc.print_(printer)


def export_to_xlsx(requests, parent_widget):
    import openpyxl
    path, _ = QFileDialog.getSaveFileName(parent_widget, "Export to Excel", "requests.xlsx", "Excel (*.xlsx)")
    if not path:
        return
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Requests"
    headers = ["ID", "Date", "Requestor", "Email", "Department",
               "Position", "Current Employee", "Proposed Employee", "Created At"]
    ws.append(headers)
    for req in requests:
        ws.append([
            req.id, req.date, req.requestor_name, req.requestor_email,
            req.department, req.position, req.current_employee,
            req.proposed_employee, req.created_at,
        ])
    wb.save(path)
