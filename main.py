import streamlit as st
import pandas as pd

st.set_page_config(page_title = "EDE4DE", layout ="wide")
st.title("👋 Welcome")

st.markdown("""
Welcome to **EDE4DE** - your tool for interactive event data preparation
""")

if "uploaded_file_name" in st.session_state:
    st.info(f"✅ Current file: **{st.session_state.uploaded_file_name}**")
    if "df" in st.session_state:
        st.dataframe(st.session_state.df.head())

uploaded_file = st.file_uploader("Upload your CSV or JSON file", type=["csv", "json"])
if uploaded_file:
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_json(uploaded_file)
        st.session_state.df = df
        st.session_state.uploaded_file_name = uploaded_file.name
        st.success(f"✅ File '{uploaded_file.name}' uploaded successfully!")
    except Exception as e:
        st.error(f"❌ Error: {e}")

question = st.text_area("Analysis question:")
if question:
    st.session_state.question_data = question
    st.success("✅ Question saved!")