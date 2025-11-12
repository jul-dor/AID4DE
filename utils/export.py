# utils/export.py
from datetime import datetime
from reportlab.lib import colors    
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Paragraph, Spacer
import streamlit as st
from utils.media import rl_image_from_bytes

NO_COMMENT = "– (no comment provided)"

def _para(text: str, style):
    return Paragraph(text.replace("\n", "<br/>"), style)

def build_pdf_bytes() -> bytes:
    items_raw = st.session_state.get("viz_images", {}).get("items", [])
    if not items_raw:
        raise RuntimeError("No visualizations available for export.")

    # --- Deduplicate by 'key': keep last occurrence, preserve first-seen order
    order, latest = [], {}
    for it in items_raw:
        k = it.get("key")
        if k not in latest:
            order.append(k)
        latest[k] = it
    items = [latest[k] for k in order]

    from io import BytesIO
    buf = BytesIO()

    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        rightMargin=1.8*cm, leftMargin=1.8*cm,
        topMargin=1.8*cm, bottomMargin=1.8*cm
    )
    doc.title = "Data Validation Report"

    styles = getSampleStyleSheet()
    story = []

    # Header
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    story.append(Paragraph("Data Validation Report", styles["Title"]))
    story.append(_para(f"Generated: {now}", styles["Normal"]))
    q = (st.session_state.get("question_data") or "").strip()
    if q:
        story.append(Spacer(1, 0.25*cm))
        story.append(Paragraph("Context / Question", styles["Heading2"]))
        story.append(_para(q, styles["Normal"]))
    story.append(Spacer(1, 0.5*cm))

    # Helper: collect texts for a viz_key (notes & legend only)
    feedbacks = st.session_state.get("feedbacks", {})

    def _notes_and_legend_for(viz_key: str):
        """
        Return list of (kind,label,text) for 'note' and 'legend' with non-empty text.
        Ordered: note -> legend.
        """
        out = []
        for kind in ("note", "legend"):
            key = f"{kind}__{viz_key}"
            payload = feedbacks.get(key)
            if not payload:
                continue
            text = (payload.get("text") or "").strip()
            if not text:
                continue
            label = payload.get("label") or (kind.title() if kind != "legend" else "Legend")
            out.append((kind, label, text))
        # enforce order: note -> legend
        order = {"note": 0, "legend": 1}
        out.sort(key=lambda x: order.get(x[0], 99))
        return out

    def _feedback_text_for(viz_key: str) -> str:
        """
        Return the feedback text for viz_key (possibly empty/None).
        If missing or empty, caller will render the placeholder.
        """
        payload = feedbacks.get(f"feedback__{viz_key}")
        if not payload:
            return ""  # missing feedback
        return (payload.get("text") or "").strip()

    # Main loop (export in insertion order)
    for item in items:
        viz_key = item.get("key")
        title   = item.get("title") or viz_key
        data    = item.get("bytes")

        # Title
        story.append(Paragraph(f"<b>{title}</b>", styles["Heading3"]))

        # Image
        if data:
            story.append(rl_image_from_bytes(data, max_width_pt=16*cm))
        else:
            story.append(_para("[Image missing]", styles["Normal"]))
        story.append(Spacer(1, 0.15*cm))

        # Notes & Legend (only when text is present)
        for _, label, text in _notes_and_legend_for(viz_key):
            story.append(Paragraph(f"<b>{label}:</b>", styles["Normal"]))
            story.append(_para(text, styles["Normal"]))
            story.append(Spacer(1, 0.1*cm))

        # Feedback (ALWAYS shown; override label to 'Feedback')
        fb_text = _feedback_text_for(viz_key)
        story.append(Paragraph("<b>Feedback:</b>", styles["Normal"]))
        story.append(_para(fb_text if fb_text else NO_COMMENT, styles["Normal"]))
        story.append(Spacer(1, 0.5*cm))

    doc.build(story)
    buf.seek(0)
    return buf.getvalue()

def build_pdf_bytes() -> bytes:
    items = st.session_state.get("viz_images", {}).get("items", [])
    if not items:
        raise RuntimeError("No visualizations available for export.")

    from io import BytesIO
    buf = BytesIO()

    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        rightMargin=1.8*cm, leftMargin=1.8*cm,
        topMargin=1.8*cm, bottomMargin=1.8*cm
    )
    doc.title = "Data Validation Report"

    styles = getSampleStyleSheet()
    story = []

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    story.append(Paragraph("Data Validation Report", styles["Title"]))
    story.append(Paragraph(f"Generated: {now}", styles["Normal"]))
    q = (st.session_state.get("question_data") or "").strip()
    if q:
        story.append(Spacer(1, 0.25*cm))
        story.append(Paragraph("Context / Question", styles["Heading2"]))
        story.append(Paragraph(q.replace("\n", "<br/>"), styles["Normal"]))
    story.append(Spacer(1, 0.5*cm))

    feedbacks = st.session_state.get("feedbacks", {})
    def texts_for_viz(viz_key: str, kinds=("note","legend","feedback")):
        out = []
        order = {"note": 0, "legend": 1, "feedback": 2}
        for k, payload in feedbacks.items():
            for kind in kinds:
                if k == f"{kind}__{viz_key}":
                    label = payload.get("label") or kind.title()
                    text  = (payload.get("text") or "").strip()
                    out.append((kind, label, text if text else "– (no comment provided)"))
        out.sort(key=lambda x: order.get(x[0], 99))
        return out

    for item in items:
        viz_key = item.get("key")
        title   = item.get("title") or viz_key
        typ     = item.get("type")

        story.append(Paragraph(f"<b>{title}</b>", styles["Heading3"]))

        if typ == "rl_table":
            # --- Key/Value Tabelle mit automatischem Umbruch ---
            rows = item.get("rows", [])
            # Paragraphs für sauberes Wrapping
            def P(txt): 
                return Paragraph(str(txt).replace("\n", "<br/>"), styles["Normal"])
            data = [["Statistic", "Value"]] + [[P(k), P(v)] for k, v in rows]

            cw = item.get("col_widths_cm") or [6.0, 10.0]
            tbl = Table(data, colWidths=[cw[0]*cm, cw[1]*cm], hAlign="LEFT")
            tbl.setStyle(TableStyle([
                ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
                ("BACKGROUND", (0,0), (-1,0), colors.whitesmoke),
                ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
                ("VALIGN", (0,0), (-1,-1), "TOP"),
                ("LEFTPADDING", (0,0), (-1,-1), 4),
                ("RIGHTPADDING", (0,0), (-1,-1), 4),
                ("BOTTOMPADDING", (0,0), (-1,-1), 4),
                ("TOPPADDING", (0,0), (-1,-1), 4),
            ]))
            story.append(tbl)

        else:
            # fallback: Bild (PNG)
            data = item.get("bytes")
            if data:
                story.append(rl_image_from_bytes(data, max_width_pt=16*cm))
            else:
                story.append(Paragraph("[Image missing]", styles["Normal"]))

        story.append(Spacer(1, 0.15*cm))
        for kind, label, text in texts_for_viz(viz_key):
            story.append(Paragraph(f"<b>{label}:</b>", styles["Normal"]))
            story.append(Paragraph(text.replace("\n","<br/>"), styles["Normal"]))
            story.append(Spacer(1, 0.1*cm))
        story.append(Spacer(1, 0.5*cm))

    doc.build(story)
    buf.seek(0)
    return buf.getvalue()