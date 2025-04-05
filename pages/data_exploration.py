import streamlit as st
from datetime import datetime
import io

st.set_page_config(page_title="Data Exploration", layout="wide")
st.title("🔍 Data Exploration")

if "df" not in st.session_state or "question_data" not in st.session_state:
    st.error("Please upload data and provide a question on the main page.")
    st.stop()

# Header
col1, col2 = st.columns([1, 2])
col1.markdown(f"📁 **{st.session_state.uploaded_file_name}**")
col2.markdown(f"❓ **Question:** {st.session_state.question_data}")

st.markdown("---")

# Suggestions
with st.expander("💡 Show Suggestions"):
    st.write("💬 Here is a list of potential questions to ask about the uploaded event data based on the question raised :-)")
    st.markdown("""
    Suggestion overview:
    - Suggestion 1 
    - Suggestion 2 
    - Suggestion 3
    """)
#TODO: Establish connection to LLM and question    

st.markdown("---")

# Chat + Plots
col_left, col_right = st.columns([1, 1])
with col_left:
    st.subheader("🧠 Chatbot")
    user_input = st.text_input("Ask another question:")
    if user_input:
        st.write(f"**You:** {user_input}")
        st.write("🤖 Bot: (Here comes the response)")
        # TODO: Chatbot Integration HERE

with col_right:
    st.subheader("📈 Graphics")
    st.write("🔧 Plots to be shown here including functionality for annotation!")
    # TODO: Dynamische Grafiken auf Basis des Datensatzes

st.markdown("---")
if st.button("⬇️ Export chat + plots as PDF"):
        buffer = io.BytesIO()
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{now}.pdf"
        st.success(f"PDF '{filename}' was generated!")
        # TODO: PDF-Generierung mit Chatverlauf + Plots einfügen
