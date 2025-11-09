from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
import streamlit as st
from .media import rl_image_from_bytes

def build_pdf_bytes():
    """Create report with visualizations and the linked free-text feedback (under the image)."""
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
    story.append(Spacer(1, 0.5 * cm))

    # Optional: include question/context if present
    q = (st.session_state.get("question_data") or "").strip()
    if q:
        story.append(Paragraph("Context / Question", styles["Heading2"]))
        story.append(Paragraph(q.replace("\n", "<br/>"), styles["Normal"]))
        story.append(Spacer(1, 0.5 * cm))

    story.append(Paragraph("Visualizations and Feedback", styles["Heading2"]))
    story.append(Spacer(1, 0.2 * cm))

    feedbacks = st.session_state.get("feedbacks", {})

    # Keep original insertion order
    for item in items:
        title = item.get("title") or item.get("key")
        key   = item.get("key", "")
        data  = item.get("bytes")

        story.append(Paragraph(f"<b>{title}</b>", styles["Heading3"]))
        if data:
            story.append(rl_image_from_bytes(data, max_width_pt=16*cm))
        else:
            story.append(Paragraph("[Image missing]", styles["Normal"]))
        story.append(Spacer(1, 0.2 * cm))

        # Find matching feedback: feedback_key contains viz key
        feedback_text = None
        for fb_key, fb in feedbacks.items():
            if key and key in fb_key:
                t = (fb.get("text") or "").strip()
                if t:
                    feedback_text = t
                    break

        if feedback_text:
            story.append(Paragraph("<b>Feedback:</b>", styles["Normal"]))
            story.append(Paragraph(feedback_text.replace("\n", "<br/>"), styles["Normal"]))
        else:
            story.append(Paragraph("<b>Feedback:</b> – (no comment provided)", styles["Normal"]))

        story.append(Spacer(1, 0.7 * cm))

    doc.build(story)
    buf.seek(0)
    return buf.getvalue()