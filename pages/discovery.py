# Importing libraries
import streamlit as st
import pm4py
from openai import AzureOpenAI
import os
from dotenv import load_dotenv
import base64
import pandas as pd

# Setting up the streamlit page
st.set_page_config(page_title="Discovery", layout="wide")
st.title("Discovery")
st.markdown("""The interactive Process Map View enables you to get insights into process of the logged event data!""")

# Sending error message if no event dataset and analysis question are uploaded
if "df" not in st.session_state or "question_data" not in st.session_state:
    st.error("Please upload data and provide a question on the main page.")
    st.stop()

# Enable connection to LLM
load_dotenv()

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
)

# Function for filtering the event log
@st.cache_data
def filter_variants_for_coverage (df, coverage_threshold):
    variants_count = pm4py.get_variants(
        df,
        activity_key= 'Activity',
        case_id_key = 'Case ID',
        timestamp_key = 'Complete Timestamp'
    )

    sorted_variants = sorted(variants_count.items(), key = lambda x: x[1], reverse = True)

    total_cases = sum(count for _, count in sorted_variants)

    selected_variants = set()
    cumulative_cases = 0

    for variant, count in sorted_variants:
        cumulative_cases += count
        selected_variants.add(variant)
        if cumulative_cases/total_cases >= coverage_threshold:
            break
    
    case_variants = df.groupby('Case ID')['Activity'].apply(tuple)
    
    selected_case_ids = case_variants[case_variants.isin(selected_variants)].index

    filtered_df = df[df['Case ID'].isin(selected_case_ids)].copy()

    return filtered_df

# Slides for choosing the coverage threshold
coverage = st.slider(
    "Select variant coverage threshold (%) for process model:",
    min_value = 50,
    max_value = 100,
    value = 80,
    step = 10
) / 100

# Generating the dataframe with the demanded coverage threshold 
filtered_df = filter_variants_for_coverage(st.session_state["df"], coverage)

# Generating, saving and showing the discovered process model
bpmn_model_filtered = pm4py.discover_bpmn_inductive(filtered_df)

file_path = 'bpmn_model_filtered.png'
bpmn_model_filtered_image = pm4py.vis.save_vis_bpmn(
    bpmn_model_filtered,
    file_path = file_path,
)

st.image('bpmn_model_filtered.png', caption = f'Filtered process model ({int(coverage*100)}% coverage)')

st.markdown("---")

# Generate a base64 image of the filtered process model
def encode_image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

base64_image = encode_image_to_base64(file_path)

# Establish connection to the LLM and generate an explanation of the process model in natural language
completion = client.chat.completions.create(
    model=os.getenv("AZURE_OPENAI_MODEL"),
    messages=[
        {
            "role": "system",
            "content": "You are an expert in process science. Explain BPMN models clearly and concisely.",
        },
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Please explain the process shown in the following BPMN diagram."},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{base64_image}"
                    },
                },
            ],
        },
    ],
    max_tokens=1500
)

explanation = completion.choices[0].message.content

# Displying the generated explanation on the streamlit interface
with st.spinner("Generating an explanation of the process model in natural language ..."):
    st.markdown("### 📋 Model Description")
    st.markdown(explanation)

st.markdown("---")

# TODO: Generate more process-centric statistics for the filtered_df
st.markdown("### 📊 Statistics about the process model")

summary_stats = {}

if st.session_state.uploaded_file_type == '.csv':
    case_id_key = 'Case ID'
    activity_key = 'Activity'
    timestamp_key = 'Complete Timestamp'
else:
    case_id_key = 'case:concept:name'
    activity_key = 'concept:name'
    timestamp_key = 'time:timestamp'

start_activities = pm4py.get_start_activities(
    filtered_df,
    activity_key= activity_key,
    case_id_key = case_id_key,
    timestamp_key = timestamp_key
)

sorted_starts = sorted(start_activities.items(), key = lambda x: x[1], reverse = True)

total_starts = sum(start_activities.values())

most_frequent_start = max(start_activities, key = start_activities.get)
probability = start_activities[most_frequent_start] / total_starts
    
for i, (event, count) in enumerate(sorted_starts[:3], start=1):
    probability = count / total_starts
    summary_stats[f"Typical starting event #{i}"] = f"{event}: {probability:.2%}"

end_activities = pm4py.get_end_activities(
    filtered_df,
    activity_key= activity_key,
    case_id_key = case_id_key,
    timestamp_key = timestamp_key
)   

sorted_ends = sorted(end_activities.items(), key = lambda x: x[1], reverse = True)

total_ends = sum(end_activities.values())

most_frequent_end = max(end_activities, key = end_activities.get)
probability_end = end_activities[most_frequent_end] / total_ends

for i, (event,count) in enumerate(sorted_ends[:3], start = 1):
    probability_end = count / total_ends
    summary_stats[f"Typical ending event #{i}"] = f"{event}: {probability_end:.2%}"

summary_df = pd.DataFrame(list(summary_stats.items()), columns=["Statistic", "Value"])
st.dataframe(summary_df, hide_index = True)

st.markdown("---")

st.markdown("### DECLARE model of the event log")

declare_model = pm4py.discover_declare(filtered_df)

def render_declare_model(declare_model):
    for constraint_type, entries in declare_model.items():
        with st.expander(f"📐 {constraint_type.title()} Constraints"):
            rows = []
            for activities, metrics in entries.items():
                if isinstance(activities, tuple):
                    activity_str = " → ".join(activities)
                else:
                    activity_str = activities
                rows.append({
                    "Constraint": activity_str,
                    "Support": metrics["support"],
                    "Confidence": f"{metrics['confidence']} ({metrics['confidence'] / metrics['support']:.2%})" if metrics["support"] > 0 else "0%"
                })
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True)

st.markdown(render_declare_model(declare_model))









#TODO: Build some filtering options
# get_variants(st.session_state["df"])


# def get_variants(df):
#     variants = pm4py.get_variants(
#         df,
#         activity_key= 'Activity',
#         case_id_key = 'Case ID',
#         timestamp_key = 'Complete Timestamp'
#     )
#     return variants

# def get_num_variants(variants):
#     num_variants = len (variants)
#     return num_variants


