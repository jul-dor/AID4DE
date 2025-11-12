# Importing libraries
from datetime import datetime
import streamlit as st

# Integrating utility functions
from utils.state import init_session_state
from utils.export import build_pdf_bytes

# Setting up the streamlit page
st.set_page_config(page_title="PDF-Export", layout = "wide")

# Ensure session scaffolding exists
init_session_state()

st.title("PDF-Export")
st.markdown("""Export your conducted data validation as a PDF report.""")

# --- Quick status checks (what's available in memory) ---
items = st.session_state.get("viz_images", {}).get("items", [])
feedbacks = st.session_state.get("feedbacks", {})
question_data = (st.session_state.get("question_data") or "").strip()

# --- Export action ---
st.subheader("Generate PDF")

# Tip: We only export images + feedback (no viz metadata).
st.caption("The report includes each visualization with its corresponding free-text feedback (no additional metadata).")

export_btn = st.button("⬇️ Export conducted data validation", type="primary")

if export_btn:
    try:
        # Build PDF (bytes in-memory)
        pdf_bytes = build_pdf_bytes()

        # Suggest a clean filename with timestamp
        filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

        # Streamlit download button to deliver the PDF to the user
        st.download_button(
            label="Download PDF",
            data=pdf_bytes,
            file_name=filename,
            mime="application/pdf",
            type="primary",
        )
        st.success(f"PDF '{filename}' was generated!")
    except Exception as e:
        # Show clear error if something went wrong (e.g., no visuals in cache)
        st.error(f"Export failed: {e}")
        