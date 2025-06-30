# Importing libraries
import streamlit as st
import pm4py
from openai import AzureOpenAI
from dotenv import load_dotenv
import os

# Setting up the streamlit page
st.set_page_config(page_title="Interactive Event Log Exploration", layout = "wide")
st.title("Interactive Event Log Exploration")
st.markdown("""The Interactive Event Log Exploration enables you to generate new plots based on LLM suggestions""")

# Sending error message if no event dataset and analysis question are uploaded
if "df" not in st.session_state or "question_data" not in st.session_state:
    st.error("Please upload data and provide a question on the main page.")
    st.stop()

if "selected_visualizations" not in st.session_state:
    st.session_state["selected_visualizations"] = []

# Showing the name of the uploaded event dataset and the uploaded analysis question
col1, col2 = st.columns([1, 2])
col1.markdown(f"📁 **{st.session_state.uploaded_file_name}**")
col2.markdown(f"❓ **Question:** {st.session_state.question_data}")

st.markdown("---")

# Load environment variables
load_dotenv()

# Azure OpenAI client
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
)

# Generate suggestions for visualizations
def get_visualization_suggestions(question: str, excluded_charts: list) -> list:
    excluded_str = ", ".join(excluded_charts)
    system_prompt = f"""
    You are a data assistant specialized in event log analysis. Based on the user's analysis question, suggest between 3 and 10 insightful visualization ideas. The visualizations should support the user to check if the event log is valid for its intended purpose. Avoid suggesting the following chart types: {excluded_str}.
    Return only a clean bullet list with short and precise explanations. Each suggestion should be unique and data-insightful.
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"My analysis question is: {question}"}
    ]
    response = client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_MODEL"),
        messages=messages
    )
    suggestions_raw = response.choices[0].message.content
    suggestions = [line.lstrip("-• ").strip() for line in suggestions_raw.splitlines() if line.strip()]
    return suggestions[:10]

# Header for suggested visualizations
st.subheader("🔍 Suggested Visualizations")

# Show visualizations suggestions in the interface
if "question_data" in st.session_state and st.session_state.question_data.strip():
    question = st.session_state.question_data

    # List of excluded visualizations (shown already in the data_exploration section)
    excluded_viz = ["absolute activity frequency", "relative activity frequency", "absolute case frequency", "relative case frequency", "event attribute frequency", "case length distribution", 
                    "events per time", "daily event distribution", "weekly event distribution", "monthly event distribution", "yearly event distribution", "dotted chart cases by time", 
                    "case duration distribution", "task responsibility heatmap", "resource attribute frequency"]

    if st.button("💡 Generate Visualization Suggestions"):
        with st.spinner("Generating suggestions..."):
            suggestions = get_visualization_suggestions(question, excluded_viz)
            st.session_state["viz_suggestions"] = suggestions

# Mark chosen visualizaitons
if "viz_suggestions" in st.session_state:
    st.write("💬 Based on your question, here are some useful visualizations to consider:")

    selected = st.session_state.get("selected_visualization", None)

    if "selected_visualizations" not in st.session_state:
        st.session_state["selected_visualizations"] = []

    for i, suggestion in enumerate(st.session_state.viz_suggestions):
        button_label = f"📊 {suggestion}"
        is_selected = suggestion == selected

        with st.container():
            if st.button(button_label, key=f"sugg_{i}"):
                if suggestion not in st.session_state["selected_visualizations"]:
                    st.session_state["selected_visualizations"].append(suggestion)
            
            if suggestion in st.session_state["selected_visualizations"]: 
                st.success(f"✅ You selected: **{suggestion}**. See the corresponding plot & its statistics below.")

st.markdown("---")

# Show selected visualizations
if st.session_state["selected_visualizations"]:
    st.markdown("---")
    st.subheader("📈 Generated Plots")

    for selected_viz in st.session_state["selected_visualizations"]:
        st.markdown(f"### 🔹 {selected_viz}")