# Importing libraries
import streamlit as st
import pm4py
from openai import AzureOpenAI
import os
from dotenv import load_dotenv
import base64
import pandas as pd

# Setting up the streamlit page
st.set_page_config(page_title="Initial Process Exploration", layout="wide")
st.title("Initial Process Exploration")
st.markdown("""The Initial Process Exploration enables you to get insights into process of the logged event data!""")

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

# Function for feedback area
def feedback_input(label, key):
    st.text_area(
        label=label,
        key=key,
        height=100,
        placeholder="Please share your thoughts..."
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

# Showing the generated BPMN model
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

# Extract the generated explanation
explanation = completion.choices[0].message.content

# Displying the generated explanation on the streamlit interface
with st.spinner("Generating an explanation of the process model in natural language ..."):
    st.markdown("### 📋 Model Description")
    st.markdown(explanation)

# Feedback area
feedback_input("Does the process model & its description reflect your experience?", "feedback_process_model")

st.markdown("---")

# TODO: Generate further process-centric statistics for the filtered_df
# Summary of process-centric statistics 
st.markdown("### 📊 Statistics about the process model")

summary_stats = {}

# Retrieve start activities of the event data
start_activities = pm4py.get_start_activities(
    filtered_df, 
    activity_key = st.session_state["activity_key"], 
    case_id_key = st.session_state["case_id_key"],
    timestamp_key = st.session_state["timestamp_key"]
)

# Calculate the percentage of the typical starting events (top 3 if applicable)
sorted_starts = sorted(start_activities.items(), key = lambda x: x[1], reverse = True)

total_starts = sum(start_activities.values())

most_frequent_start = max(start_activities, key = start_activities.get)
probability = start_activities[most_frequent_start] / total_starts
    
for i, (event, count) in enumerate(sorted_starts[:3], start=1):
    probability = count / total_starts
    summary_stats[f"Typical starting event #{i}"] = f"{event}: {probability:.2%}"

# Retrieve end activities of the event data
end_activities = pm4py.get_end_activities(
    filtered_df,
    activity_key = st.session_state["activity_key"], 
    case_id_key = st.session_state["case_id_key"],
    timestamp_key = st.session_state["timestamp_key"]
)   

# Calculate the percentage of the typical ending events (top 3 if applicable)
sorted_ends = sorted(end_activities.items(), key = lambda x: x[1], reverse = True)

total_ends = sum(end_activities.values())

most_frequent_end = max(end_activities, key = end_activities.get)
probability_end = end_activities[most_frequent_end] / total_ends

for i, (event,count) in enumerate(sorted_ends[:3], start = 1):
    probability_end = count / total_ends
    summary_stats[f"Typical ending event #{i}"] = f"{event}: {probability_end:.2%}"

# Show the summary of process-centric statistics
summary_df = pd.DataFrame(list(summary_stats.items()), columns=["Statistic", "Value"])
st.dataframe(summary_df, hide_index = True)

# Feedback area
feedback_input("Do the statistics reflect your experience?", "feedback_process_centric_statistics")

st.markdown("---")

# DECLARE model
st.markdown("### DECLARE model of the event log")

# Relevant constraints for visualization
RELEVANT_CONSTRAINTS = {
    "existence": "These constraints specify how often an activity must occur in a case (e.g., at least once, at most once).",
    "response": "If one activity occurs, another must eventually follow in the same case.",
    "precedence": "An activity can only occur if another activity has occurred earlier in the case.",
}

# Discover declare model
declare_model = pm4py.discover_declare(filtered_df)

# Pre-process declare model and add explanations
def render_declare_model(declare_model):
    for constraint_type, explanation in RELEVANT_CONSTRAINTS.items():
        if constraint_type in declare_model:
            with st.expander(f"📐 {constraint_type} constraints"):
                st.markdown(f"💡 *{explanation}*")
                rows = []
                explanation_texts = []
                for activities, metrics in declare_model[constraint_type].items():
                    if isinstance(activities, tuple):
                        activity_str = " → ".join(activities)
                        if constraint_type == "response":
                            example_desc = (
                                f"If **{activities[0]}** occurs in a case, "
                                f"**{activities[1]}** must eventually follow at some point afterwards."
                            )
                        elif constraint_type == "precedence":
                            example_desc = (
                                f"If **{activities[1]}** occurs in a case, "
                                f"**{activities[0]}** must have occurred before."
                            )
                        else:
                            example_desc = (
                                f"For each case, the model checks whether and how often **{activities}** occurs "
                                f"to satisfy existence constraints"
                            )
                    else:
                        activity_str = activities
                        example_desc = f"In all cases, the model checks how often **{activities}** occurs to satisfy the constraint."

                    support = metrics["support"]
                    confidence = metrics["confidence"]
                    confidence_percent = f"{confidence / support:.2%}" if support > 0 else "0%"

                    rows.append({
                        "Constraint": activity_str,
                        "Support": support,
                        "Confidence": f"{confidence} ({confidence_percent})"
                        # if metrics["support"] > 0 else "0%"
                    })

                    explanation_texts.append(
                        f"""
                        🔹 **{activity_str}**  
                        {example_desc}  
                        → The constraint was relevant in **{support}** cases (support).  
                        → It was fulfilled in **{confidence}** of them → Confidence: **{confidence_percent}**
                        """
                    )

                df = pd.DataFrame(rows)
                st.dataframe(df, use_container_width=True)

                st.markdown("### ℹ️ Constraint Explanations with Example")
                for text in explanation_texts:
                    st.markdown(text)

render_declare_model(declare_model)

# Feedback area
feedback_input("Does the DECLARE Model reflect your experience?", "feedback_declare_model")

st.markdown("---")

# Footprint model
st.markdown("### Footprint model of the event log")

# Generate footprint model
fp_log = pm4py.discover_footprints(filtered_df)

file_path = 'footprint_model_filtered.png'
bpmn_model_filtered_image = pm4py.vis.save_vis_footprints(
    fp_log,
    file_path = file_path,
)

# Show footprint model
st.image('footprint_model_filtered.png', caption = f'Filtered footprint model ({int(coverage*100)}% coverage)')

# Show explanation for users
st.info("""
**Legend for Footprint Matrix Symbols (read row → column):**  
Each cell describes the relation from the activity in the **row** to the activity in the **column**.

- `>` : The **row activity** directly precedes the **column activity** (causal relation)  
- `<` : The **column activity** directly precedes the **row activity** (inverse causal relation)  
- `||` : The two activities can occur **in parallel or in any order**  
- `#` : **No direct relation** between the two activities observed
""")

# Feedback area
feedback_input("Does the footprint model reflect your experience?", "feedback_footprint_model")


