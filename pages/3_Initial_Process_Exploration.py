# Importing libraries
import os, sys, base64
import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from openai import AzureOpenAI

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Integrating utility functions
from utils.state import init_session_state, feedback_input, attach_text_to_visual
from utils.media import register_dataframe_as_image
from utils.process_exploration import (
    filter_variants_for_coverage,
    discover_bpmn_and_register,
    build_process_stats,
    render_declare_model,
    discover_footprints_and_register,
)

st.set_page_config(page_title="Initial Process Exploration", layout="wide")
init_session_state()

st.title("Initial Process Exploration")
st.markdown("The Initial Process Exploration enables you to get insights into the process of the logged event data!")

if "df" not in st.session_state or "question_data" not in st.session_state:
    st.error("Please upload data and provide a question on the main page.")
    st.stop()

df = st.session_state["df"]
case_id_key = st.session_state["case_id_key"]
activity_key = st.session_state["activity_key"]
timestamp_key = st.session_state["timestamp_key"]

load_dotenv()
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
)

coverage = st.slider("Select variant coverage threshold (%) for process model:", 50, 100, 80, 10) / 100.0

filtered_df = filter_variants_for_coverage(
    df, coverage_threshold=coverage,
    case_id_key=case_id_key, activity_key=activity_key, timestamp_key=timestamp_key
)

# --- BPMN Model ---
bpmn_png_path = discover_bpmn_and_register(
    filtered_df,
    case_id_key=case_id_key, activity_key=activity_key, timestamp_key=timestamp_key,
    coverage_threshold=coverage
)
st.image(bpmn_png_path, caption=f"Filtered process model ({int(coverage*100)}% coverage)")

st.markdown("---")

# LLM explanation for BPMN
def encode_image_to_base64(image_path: str) -> str:
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

base64_image = encode_image_to_base64(bpmn_png_path)
with st.spinner("Generating an explanation of the process model in natural language ..."):
    completion = client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_MODEL"),
        messages=[
            {"role": "system", "content": "You are an expert in process science. Explain BPMN models clearly and concisely."},
            {"role": "user", "content": [
                {"type": "text", "text": "Please explain the process shown in the following BPMN diagram."},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}},
            ]},
        ],
        max_tokens=1500
    )
explanation = completion.choices[0].message.content
st.markdown("### 📋 Model Description")
st.markdown(explanation)

attach_text_to_visual("proc_bpmn_filtered", "Model Description", kind="note", text=explanation)
fb_key_bpmn = "feedback_process_model"; fb_label_bpmn = "Does the process model & its description reflect your experience?"
feedback_input(fb_label_bpmn, fb_key_bpmn)
attach_text_to_visual("proc_bpmn_filtered", fb_label_bpmn, kind="feedback", from_input_key=fb_key_bpmn)

st.markdown("---")

# --- Stats ---
st.markdown("### 📊 Statistics about the process model")
stats_df = build_process_stats(filtered_df, case_id_key=case_id_key, activity_key=activity_key, timestamp_key=timestamp_key)
st.dataframe(stats_df, hide_index=True)

register_dataframe_as_image(stats_df, key="proc_stats_summary", title="Process-centric statistics")
fb_key_stats = "feedback_process_centric_statistics"; fb_label_stats = "Do the statistics reflect your experience?"
feedback_input(fb_label_stats, fb_key_stats)
attach_text_to_visual("proc_stats_summary", fb_label_stats, kind="feedback", from_input_key=fb_key_stats)

st.markdown("---")

# --- DECLARE Model ---
st.markdown("### DECLARE model of the event log")
render_declare_model(filtered_df)

fb_key_decl = "feedback_declare_model"
fb_label_decl = "Does the DECLARE Model reflect your experience?"
feedback_input(fb_label_decl, fb_key_decl)
attach_text_to_visual("proc_declare_summary", fb_label_decl, kind="feedback", from_input_key=fb_key_decl)

st.markdown("---")

# --- Footprints ---
st.markdown("### Footprint model of the event log")
discover_footprints_and_register(filtered_df, coverage_threshold=coverage)

legend_text = (
    "**Legend (row → column):**\n"
    "- `>` row precedes column (causal)\n"
    "- `<` column precedes row (inverse causal)\n"
    "- `||` parallel / any order\n"
    "- `#` no direct relation\n"
)
st.info(legend_text)

attach_text_to_visual("proc_footprints_filtered", "Legend", kind="legend", text=legend_text)
fb_key_fp = "feedback_footprint_model"; fb_label_fp = "Does the footprint model reflect your experience?"
feedback_input(fb_label_fp, fb_key_fp)
attach_text_to_visual("proc_footprints_filtered", fb_label_fp, kind="feedback", from_input_key=fb_key_fp)
