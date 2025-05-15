from datetime import datetime
import io
import streamlit as st

# Setting up the streamlit page
st.set_page_config(page_title="PDF-Export", layout = "wide")
st.title("PDF-Export")
st.markdown("""The PDF-Export enables you to export your conducted data validation""")
st.markdown("---")

# Sending error message if no event dataset and analysis question are uploaded
if "df" not in st.session_state or "question_data" not in st.session_state:
    st.error("Please upload data and provide a question on the main page.")
    st.stop()

# TODO: Chat und Plots in PDF Export durch Import des Session State berücksichtigen
if st.button("⬇️ Export conducted data validation"):
        buffer = io.BytesIO()
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{now}.pdf"
        st.success(f"PDF '{filename}' was generated!")
        