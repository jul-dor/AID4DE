# 4_Interactive_Event_Log_Exploration.py

import os
import sys

import streamlit as st
import pandas as pd

# Allow imports from project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.state import init_session_state
from utils.interactive_exploration import (
    suggest_visualizations,
    run_generated_visualization,
)

# --- Page setup ---
st.set_page_config(page_title="Interactive Event Log Exploration", layout="wide")
init_session_state()

st.title("Interactive Event Log Exploration")
st.markdown(
    """
The Interactive Event Log Exploration lets you **generate additional, on-demand visualizations**
based on your analysis question.  
Suggestions are created by the LLM and executed directly on the uploaded event log.
"""
)

# --- Guards ---
if "df" not in st.session_state or "question_data" not in st.session_state:
    st.error("Please upload data and provide a question on the main page.")
    st.stop()

df: pd.DataFrame = st.session_state["df"]
case_id_key = st.session_state["case_id_key"]
activity_key = st.session_state["activity_key"]
timestamp_key = st.session_state["timestamp_key"]
resource_key = st.session_state.get("resource_key")

# show context
col1, col2 = st.columns([1, 2])
col1.markdown(f"📁 **{st.session_state.uploaded_file_name}**")
col2.markdown(f"❓ **Question:** {st.session_state.question_data}")
st.markdown("---")

# --- init session containers for this page ---
st.session_state.setdefault("ix_viz_suggestions", [])
st.session_state.setdefault("ix_selected_viz_labels", [])

# list of visualizations already covered on other pages (prompt hint)
EXCLUDED_VIZ_LABELS = [
    "absolute activity frequency",
    "relative activity frequency",
    "absolute case frequency",
    "relative case frequency",
    "event attribute frequency",
    "case length distribution",
    "events per time",
    "daily event distribution",
    "weekly event distribution",
    "monthly event distribution",
    "yearly event distribution",
    "dotted chart",
    "case duration distribution",
    "task responsibility heatmap",
    "resource attribute frequency",
    "start activities",
    "end activities",
    "DECLARE model",
    "footprint model",
    "BPMN model",
    "case variant distribution",
]

# --- Suggestions section ---
st.subheader("🔍 Suggested Visualizations")

st.caption(
    "Based on your analysis question, the assistant can suggest additional visualizations "
    "that were **not** shown on the initial exploration pages yet."
)

if st.button("💡 Generate visualization suggestions"):
    with st.spinner("Generating suggestions based on your question..."):
        st.session_state["ix_viz_suggestions"] = suggest_visualizations(
            st.session_state.question_data,
            EXCLUDED_VIZ_LABELS,
        )
        st.session_state["ix_selected_viz_labels"] = []  # reset selection on new suggestion run

suggestions = st.session_state.get("ix_viz_suggestions", [])

if suggestions:
    st.write("💬 Based on your question, these additional visualizations could be insightful:")

    # Multi-select style with buttons (toggles)
    for i, suggestion in enumerate(suggestions):
        key = f"ix_sugg_{i}"
        is_selected = suggestion in st.session_state["ix_selected_viz_labels"]

        with st.container():
            cols = st.columns([0.1, 0.9])
            if cols[0].checkbox("", value=is_selected, key=key):
                if suggestion not in st.session_state["ix_selected_viz_labels"]:
                    st.session_state["ix_selected_viz_labels"].append(suggestion)
            else:
                if suggestion in st.session_state["ix_selected_viz_labels"]:
                    st.session_state["ix_selected_viz_labels"].remove(suggestion)

            cols[1].markdown(f"**{suggestion}**")

    st.markdown("---")

# --- Generated plots for selected suggestions ---
selected_viz = st.session_state.get("ix_selected_viz_labels", [])

if selected_viz:
    st.subheader("📈 Generated Plots")

    for suggestion in selected_viz:
        st.markdown(f"### 🔹 {suggestion}")
        with st.spinner("Building visualization..."):
            run_generated_visualization(
                suggestion,
                df,
                case_id_key=case_id_key,
                activity_key=activity_key,
                timestamp_key=timestamp_key,
                resource_key=resource_key,
            )
        st.markdown("---")
else:
    st.info("Select one or more suggested visualizations above to generate them on the event log.")
