# Importing libraries
import streamlit as st
from datetime import datetime
import io
from openai import AzureOpenAI
from dotenv import load_dotenv
import os
import sys

# Importing automatic script
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.visualize_xes import run_visualizations as visualize_xes

# Enable connection to LLM
load_dotenv()

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
)

# Function for sending API requests to the LLM
def api_request(messages: list) -> str:
    if "viz_data" in st.session_state:
        viz_context = f"Visualisation summary data: {st.session_state.viz_data}"
        messages.insert(0, {"role": "system", "content": f"You are a data assistant. Use only this context to answer: {viz_context}. Be brief in your answers and always return the answer in the language of the question. If asking a clarifying question to the user would help, ask the question."})
    
    completion = client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_MODEL"),
        messages=messages
    )
    return completion.choices[0].message.content

# Setting up the streamlit page
st.set_page_config(page_title="Data Exploration", layout="wide")
st.title("🔍 Data Exploration")
st.markdown("""The Data Exploration mode enables you to get first insights into the uploaded event dataset""")

# Sending error message if no event dataset and analysis question are uploaded
if "df" not in st.session_state or "question_data" not in st.session_state:
    st.error("Please upload data and provide a question on the main page.")
    st.stop()

# Initialize messages in the session state
if "messages" not in st.session_state:
     st.session_state.messages = []

# Showing the name of the uploaded event dataset and the uploaded analysis question
col1, col2 = st.columns([1, 2])
col1.markdown(f"📁 **{st.session_state.uploaded_file_name}**")
col2.markdown(f"❓ **Question:** {st.session_state.question_data}")

st.markdown("---")

# Suggestions
# TODO: Shift to interactive event data exploration page + establish connection to LLM and analysis question
with st.expander("💡 Show Suggestions"):
    st.write("💬 Here is a list of potential questions to ask about the uploaded event data based on the question raised :-)")
    st.markdown("""
    Suggestion overview:
    - Suggestion 1 
    - Suggestion 2 
    - Suggestion 3
    """)

st.markdown("---")

# Option 1: Chatbot in sidebar (chatbot is scrolling with the visualizations)
with st.sidebar:
    st.subheader("🧠 Chatbot")
    for message in st.session_state["messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if user_prompt := st.chat_input("Your question:"):
        st.session_state.messages.append({"role": "user", "content": user_prompt})

        with st.chat_message("user"):
            st.markdown(user_prompt)
        
        with st.chat_message("assistant"):
            chatbot_msg = st.empty()
            full_response = api_request([
                {"role": msg["role"], "content": msg["content"]}
                for msg in st.session_state["messages"]
            ])
            chatbot_msg.markdown(full_response)

        st.session_state.messages.append({"role": "assistant", "content": full_response})

# Option 2: Split-interface between chatbot and graphics (chatbot does not scroll with the visualizations)
# col_left, col_right = st.columns([1, 1])

# with col_left:
#     st.subheader("🧠 Chatbot")

#     # Display messages
#     for message in st.session_state["messages"]:
#         with st.chat_message(message["role"]):
#             st.markdown(message["content"])
        
#     if user_prompt := st.chat_input("Your question:"):
#         st.session_state.messages.append({"role": "user", "content": user_prompt})

#         with st.chat_message("user"):
#             st.markdown(user_prompt)
            
#         with st.chat_message("assistant"):
#             chatbot_msg =st.empty()
#             full_response = api_request([
#                 {"role": msg["role"], "content": msg["content"]}
#                 for msg in st.session_state["messages"]
#             ])
#             chatbot_msg.markdown(full_response)

#         st.session_state.messages.append({"role": "assistant", "content": full_response})
#with col_right:
st.subheader("📈 Graphics")
st.markdown('<div class = "right-column">', unsafe_allow_html = True)
if st.session_state.uploaded_file_type == '.csv':
    case_id_key = 'Case ID'
    activity_key = 'Activity'
    timestamp_key = 'Complete Timestamp'
else:
    case_id_key = 'case:concept:name'
    activity_key = 'concept:name'
    timestamp_key = 'time:timestamp'
visualize_xes(st.session_state["df"], case_id_key, activity_key, timestamp_key)
    
# TODO: Shift to pdf-export page
st.markdown("---")
if st.button("⬇️ Export chat + plots as PDF"):
        buffer = io.BytesIO()
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{now}.pdf"
        st.success(f"PDF '{filename}' was generated!")
        # TODO: PDF-Generierung mit Chatverlauf + Plots einfügen

