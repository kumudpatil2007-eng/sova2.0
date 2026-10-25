import datetime
import html
from pathlib import Path
from typing import Optional, List

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
    HRFlowable
)
from reportlab.pdfgen import canvas

from .models import DocumentStructure, DocumentSection, DocumentTable, DocumentCodeBlock


# Palette
NAVY_PRIMARY = colors.HexColor("#1E3A8A")
SLATE_ACCENT = colors.HexColor("#2563EB")
TEXT_PRIMARY = colors.HexColor("#1E293B")
TEXT_MUTED = colors.HexColor("#64748B")
BORDER_LIGHT = colors.HexColor("#E2E8F0")
BG_LIGHT = colors.HexColor("#F8FAFC")
BG_SUMMARY = colors.HexColor("#EFF6FF")
BG_CODE = colors.HexColor("#F1F5F9")


def escape_xml(text: str) -> str:
    """Escapes XML entities so ReportLab Paragraphs render safely without crashes."""
    if not text:
        return ""
    return html.escape(str(text))


class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas that computes total page count dynamically
    and draws professional running headers and footers on every page.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count: int):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(TEXT_MUTED)

        page_width, page_height = letter
        margin = 54  # 0.75 in

        # 1. Running Header (on all pages)
        self.drawRightString(
            page_width - margin,
            page_height - 38,
            "SOVA Sovereign Document Intelligence | Air-Gapped Internal"
        )
        self.setStrokeColor(BORDER_LIGHT)
        self.setLineWidth(0.6)
        self.line(margin, page_height - 43, page_width - margin, page_height - 43)

        # 2. Running Footer (on all pages)
        self.line(margin, 46, page_width - margin, 46)
        self.drawString(
            margin,
            33,
            "Confidential | Generated Locally on On-Premise Node"
        )
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(page_width - margin, 33, page_str)

        self.restoreState()


def generate_pdf(doc_struct: DocumentStructure, output_path: str) -> str:
    """
    Generates a publication-grade PDF report from a DocumentStructure model
    using ReportLab flowables and dynamic NumberedCanvas.
    """
    out_file = Path(output_path).resolve()
    out_file.parent.mkdir(parents=True, exist_ok=True)

    # Document Geometry: Letter size with 0.75-inch margins
    margin = 54  # 0.75 in (54 pt)
    printable_width = letter[0] - (margin * 2)  # ~504 pt

    doc = SimpleDocTemplate(
        str(out_file),
        pagesize=letter,
        leftMargin=margin,
        rightMargin=margin,
        topMargin=margin,
        bottomMargin=margin
    )

    # Styles
    styles = getSampleStyleSheet()

    style_title = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=22,
        leading=26,
        textColor=NAVY_PRIMARY,
        spaceAfter=4
    )

    style_subtitle = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=12,
        leading=16,
        textColor=TEXT_MUTED,
        spaceAfter=10
    )

    style_meta = ParagraphStyle(
        "DocMeta",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=TEXT_MUTED
    )

    style_h1 = ParagraphStyle(
        "DocH1",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        textColor=NAVY_PRIMARY,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )

    style_h2 = ParagraphStyle(
        "DocH2",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11.5,
        leading=15,
        textColor=SLATE_ACCENT,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )

    style_h3 = ParagraphStyle(
        "DocH3",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=14,
        textColor=TEXT_PRIMARY,
        spaceBefore=8,
        spaceAfter=3,
        keepWithNext=True
    )

    style_body = ParagraphStyle(
        "DocBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=14,
        textColor=TEXT_PRIMARY,
        spaceAfter=6
    )

    style_bullet = ParagraphStyle(
        "DocBullet",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=13.5,
        textColor=TEXT_PRIMARY,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=3
    )

    style_num = ParagraphStyle(
        "DocNum",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=13.5,
        textColor=TEXT_PRIMARY,
        leftIndent=18,
        firstLineIndent=-12,
        spaceAfter=3
    )

    style_th = ParagraphStyle(
        "DocTH",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=colors.white
    )

    style_td = ParagraphStyle(
        "DocTD",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11.5,
        textColor=TEXT_PRIMARY
    )

    style_code = ParagraphStyle(
        "DocCode",
        parent=styles["Normal"],
        fontName="Courier",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#0F172A")
    )

    story = []

    # 1. Document Title
    story.append(Spacer(1, 4))
    story.append(Paragraph(escape_xml(doc_struct.title), style_title))

    # Subtitle
    if doc_struct.subtitle:
        story.append(Paragraph(escape_xml(doc_struct.subtitle), style_subtitle))

    # Metadata Strip
    author_str = doc_struct.author or "SOVA Sovereign Intelligence"
    date_str = doc_struct.date or datetime.date.today().strftime("%d %B %Y")
    class_str = doc_struct.confidentiality or "Air-Gapped Internal"

    meta_content = (
        f"<b>Author:</b> {escape_xml(author_str)} &nbsp;&nbsp;|&nbsp;&nbsp; "
        f"<b>Date:</b> {escape_xml(date_str)} &nbsp;&nbsp;|&nbsp;&nbsp; "
        f"<b>Classification:</b> {escape_xml(class_str)}"
    )
    story.append(Paragraph(meta_content, style_meta))
    story.append(Spacer(1, 6))

    # Divider Line
    story.append(HRFlowable(
        width="100%",
        thickness=1.5,
        color=NAVY_PRIMARY,
        spaceBefore=2,
        spaceAfter=10
    ))

    # 2. Executive Summary Callout (if present)
    if doc_struct.summary:
        sum_html = (
            f"<b><font color='#2563EB'>EXECUTIVE SUMMARY</font></b><br/><br/>"
            f"{escape_xml(doc_struct.summary)}"
        )
        sum_p = Paragraph(sum_html, style_body)
        sum_table = Table([[sum_p]], colWidths=[printable_width])
        sum_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), BG_SUMMARY),
            ('BOX', (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
            ('LINELEFT', (0, 0), (0, -1), 3.0, SLATE_ACCENT),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ]))
        story.append(sum_table)
        story.append(Spacer(1, 10))

    # 3. Document Sections
    for s_idx, sec in enumerate(doc_struct.sections):
        # Heading
        h_style = style_h1 if sec.level == 1 else (style_h2 if sec.level == 2 else style_h3)
        story.append(Paragraph(escape_xml(sec.heading), h_style))

        # Paragraphs
        for para in sec.paragraphs:
            if not para.strip():
                continue
            story.append(Paragraph(escape_xml(para.strip()), style_body))

        # Bullet Points
        for bullet in sec.bullet_points:
            if not bullet.strip():
                continue
            b_text = f"&bull;&nbsp;&nbsp;{escape_xml(bullet.strip())}"
            story.append(Paragraph(b_text, style_bullet))

        # Numbered List
        for num_item in sec.numbered_list:
            if not num_item.strip():
                continue
            story.append(Paragraph(escape_xml(num_item.strip()), style_num))

        # Tables
        for tbl in sec.tables:
            if not tbl.headers and not tbl.rows:
                continue

            if tbl.caption:
                cap_style = ParagraphStyle(
                    "Cap",
                    parent=style_body,
                    fontName="Helvetica-Bold",
                    fontSize=8.5,
                    textColor=SLATE_ACCENT,
                    spaceBefore=4,
                    spaceAfter=2,
                    keepWithNext=True
                )
                story.append(Paragraph(f"Table: {escape_xml(tbl.caption)}", cap_style))

            num_cols = len(tbl.headers) if tbl.headers else (len(tbl.rows[0]) if tbl.rows else 1)
            col_width = printable_width / max(num_cols, 1)
            col_widths = [col_width] * num_cols

            table_data = []

            # Headers
            if tbl.headers:
                hdr_row = [Paragraph(escape_xml(str(h)), style_th) for h in tbl.headers]
                table_data.append(hdr_row)

            # Rows
            for row in tbl.rows:
                cell_row = [
                    Paragraph(escape_xml(str(row[c] if c < len(row) else "")), style_td)
                    for c in range(num_cols)
                ]
                table_data.append(cell_row)

            t_flowable = Table(table_data, colWidths=col_widths, repeatRows=1 if tbl.headers else 0)
            t_style = [
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LINEBELOW', (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
            ]

            if tbl.headers:
                t_style.extend([
                    ('BACKGROUND', (0, 0), (-1, 0), NAVY_PRIMARY),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ])

            # Zebra striping
            row_start = 1 if tbl.headers else 0
            for r in range(row_start, len(table_data)):
                if (r - row_start) % 2 == 0:
                    t_style.append(('BACKGROUND', (0, r), (-1, r), BG_LIGHT))

            t_flowable.setStyle(TableStyle(t_style))
            story.append(Spacer(1, 4))
            story.append(t_flowable)
            story.append(Spacer(1, 8))

        # Code Blocks
        for cb in sec.code_blocks:
            if not cb.code.strip():
                continue
            code_lines_all = cb.code.strip().split('\n')
            chunk_size = 25
            for c_start in range(0, len(code_lines_all), chunk_size):
                code_chunk = code_lines_all[c_start:c_start + chunk_size]
                chunk_escaped = escape_xml('\n'.join(code_chunk)).replace('\n', '<br/>')
                code_p = Paragraph(f"<code>{chunk_escaped}</code>", style_code)
                code_table = Table([[code_p]], colWidths=[printable_width])
                code_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), BG_CODE),
                    ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('LEFTPADDING', (0, 0), (-1, -1), 8),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ]))
                story.append(Spacer(1, 3))
                story.append(code_table)
                story.append(Spacer(1, 4))

        # Page Break
        if sec.page_break_after and s_idx < len(doc_struct.sections) - 1:
            story.append(PageBreak())

    # Build PDF with dynamic NumberedCanvas
    doc.build(story, canvasmaker=NumberedCanvas)
    return str(out_file)
