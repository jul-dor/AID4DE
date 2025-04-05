import streamlit as st

st.set_page_config(page_title="Manual", layout="wide")
st.title("📘 Manual")

st.info("""
### Purpose of the tool
        
This tool allows domain experts to:
- Explore event data without deep technical knowledge
- Ask questions using natural language
- Validate and prepare event data for Process Mining
        
### How to use this app

1. Go to **Home** to upload your dataset and formulate your question.
2. Then, open **Data Exploration** to chat and explore.
3. Return here anytime for guidance.  
Enjoy exploring your event data! 🎯
""")