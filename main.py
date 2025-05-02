# Importing libraries
import streamlit as st
import pandas as pd
import pm4py
import tempfile

# Setting up the streamlit page
st.set_page_config(page_title = "EDE4DE", layout ="wide")
st.title("👋 Welcome")
st.markdown("""Welcome to **EDE4DE** - your tool to evaluate the representativeness of event data""")

uploaded_file = st.file_uploader("Upload your CSV or XES file", type=["csv", "xes"])

# If a file is uploaded: process it
if uploaded_file is not None and "uploaded_file_name" not in st.session_state:
    try:
        # Progress bar for the data upload
        progress_placeholder = st.empty()
        progress_bar = progress_placeholder.progress(0)

        with st.spinner("Uploading and processing file..."):
        
            # Preprocessing of the csv file
            if uploaded_file.name.endswith(".csv"):
                df_raw = pd.read_csv(uploaded_file)
                progress_bar.progress(30)
                st.session_state.uploaded_file_type = '.csv'
                case_id_key = 'Case ID'
                activity_key = 'Activity'
                timestamp_key = 'Complete Timestamp'
                df = pm4py.format_dataframe(df_raw, case_id = case_id_key, activity_key = activity_key, timestamp_key = timestamp_key)
            
            # Preprocessing of the xes file
            elif uploaded_file.name.endswith(".xes"):
                with tempfile.NamedTemporaryFile(delete=False, suffix = ".xes") as tmp_file:
                    tmp_file.write(uploaded_file.read())
                    tmp_file_path = tmp_file.name
                progress_bar.progress(30)
                st.session_state.uploaded_file_type = '.xes'
                case_id_key = 'case:concept:name'
                activity_key = 'concept:name'
                timestamp_key = 'time:timestamp'
                df_raw = pm4py.read_xes(tmp_file_path)
                progress_bar.progress(60)
                df = pm4py.format_dataframe(df_raw, case_id = case_id_key, activity_key = activity_key, timestamp_key = timestamp_key)
            else:
                st.warning("❗ The uploaded file must be in .csv or .xes format.")
                st.stop()
        
            # Update progress bar
            progress_bar.progress(100)

        # Delete progress bar after data upload
        progress_placeholder.empty()
        
        # Update the session state
        st.session_state.df = df
        st.session_state.uploaded_file_name = uploaded_file.name

    except Exception as e:
        st.error(f"❌ Error: {e}")

# Success report about event data upload & preview
if "uploaded_file_name" in st.session_state:
    st.success(f"✅ File '{st.session_state.uploaded_file_name}' uploaded successfully!")
    st.info(f"Current file: **{st.session_state.uploaded_file_name}**")
    st.dataframe(st.session_state.df.head(), use_container_width=True)

# Text area for analysis question
question = st.text_area("Analysis question:")
if question:
    st.session_state.question_data = question
    st.success("✅ Question saved!")

# TODO: Checking if the event data fulfills the basic requirements of the analysis question (e.g., having a resource column if the analysis question demands a social network analysis)
# TODO: Enable upload of a new dataset & analysis question within the session and corresponding analysis (automatical adjustment of event data and analysis question in session state)