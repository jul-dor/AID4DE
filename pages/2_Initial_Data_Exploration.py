# Importing libraries
import streamlit as st
from openai import AzureOpenAI
from dotenv import load_dotenv
import os
import sys
import json
from collections.abc import Mapping, Sequence

# Allow importing from project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Ensure session keys always exist
from utils.state import init_session_state
init_session_state()

# Import the visualizer
from utils.visualize_data import run_visualizations as visualize_data

# Enable connection to LLM
load_dotenv()

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
)

# -------- Helpers to compress viz_data --------
def _truncate_scalar(x, max_len=200):
    """Shorten long strings/numbers for safety."""
    if isinstance(x, str) and len(x) > max_len:
        return x[:max_len] + "…"
    return x

def _truncate_list(lst, max_items=20):
    """Keep only first N items; signal truncation."""
    if len(lst) <= max_items:
        return lst
    return lst[:max_items] + [f"...(+{len(lst)-max_items} more)"]

def _truncate_mapping(dct: Mapping, max_items=20):
    """Keep only first N key/value pairs; stable order."""
    items = list(dct.items())
    if len(items) <= max_items:
        return dct
    kept = dict(items[:max_items])
    kept["__note__"] = f"...(+{len(items)-max_items} more keys)"
    return kept

def _shrink(obj, max_items_per_section=20, max_string_len=200):
    """
    Recursively shrink structures (dict/list) to be token-friendly.
    Keeps numbers small, trims long strings, limits collection sizes.
    """
    # Scalars
    if obj is None or isinstance(obj, (int, float, bool)):
        return obj
    if isinstance(obj, str):
        return _truncate_scalar(obj, max_len=max_string_len)

    # Lists / tuples
    if isinstance(obj, Sequence) and not isinstance(obj, (str, bytes, bytearray)):
        shrunk = [_shrink(x, max_items_per_section, max_string_len) for x in list(obj)]
        return _truncate_list(shrunk, max_items=max_items_per_section)

    # Dict / mapping
    if isinstance(obj, Mapping):
        # Keep a predictable order for stability
        items = []
        for k in sorted(obj.keys(), key=lambda x: str(x)):
            items.append((k, _shrink(obj[k], max_items_per_section, max_string_len)))
        shrunk = _truncate_mapping(dict(items), max_items=max_items_per_section)
        return shrunk

    # Fallback to string repr (truncated)
    return _truncate_scalar(str(obj), max_len=max_string_len)

def build_viz_context(max_items_per_section=20, max_string_len=200, pretty=False):
    """
    Build a compact JSON context from st.session_state.viz_data.
    Always returns a JSON string (possibly empty object).
    """
    viz_data = st.session_state.get("viz_data", {})
    compact = _shrink(viz_data, max_items_per_section, max_string_len)
    return json.dumps(
        {"viz_meta": compact},
        ensure_ascii=False,
        separators=None if pretty else (",", ":")
    )

# Function for sending API requests to the LLM
def api_request(messages: list) -> str:
    """
    Always prepend a system message with compact visualization metadata.
    Keeps responses short, uses user's language, and encourages clarifying Qs.
    """
    viz_json = build_viz_context(
        max_items_per_section=20,   # tweak if you need more/less detail
        max_string_len=200,         # prevent huge strings
        pretty=False                # compact JSON to save tokens
    )

    system_prompt = (
        "You are a process-mining data assistant.\n"
        "Use ONLY the JSON context below to answer. If the user asks for something "
        "not covered by the context, say so briefly.\n"
        "Always reply in the user's language. Be concise. If clarification would help, ask a short question first.\n\n"
        f"JSON_CONTEXT:\n{viz_json}"
    )

    # Prepend system message
    final_messages = [{"role": "system", "content": system_prompt}]
    final_messages.extend(messages)

    completion = client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_MODEL"),
        messages=final_messages
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
