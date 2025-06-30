# Importing libraries
import streamlit as st
from openai import AzureOpenAI
from dotenv import load_dotenv
import os
import sys

# Importing automatic script
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.visualize_data import run_visualizations as visualize_data

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
st.set_page_config(page_title="Initial Data Exploration", layout="wide")
st.title("🔍 Initial Data Exploration")
st.markdown("""The Initial Data Exploration mode enables you to get first insights into the uploaded event dataset""")

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

# Initializing chatbot in sidebar (reason: chatbot is scrolling with the visualizations)
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

# Showing header 
st.subheader("📈 Graphics")

# Generating the visualizations to explore the event data
visualize_data(st.session_state["df"], st.session_state["case_id_key"], st.session_state["activity_key"], st.session_state["timestamp_key"], st.session_state["resource_key"])
