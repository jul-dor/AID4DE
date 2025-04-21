import streamlit as st
from datetime import datetime
import io
from openai import AzureOpenAI
from dotenv import load_dotenv
import os

load_dotenv()

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
)

def api_request(messages: list) -> str:
    completion = client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_MODEL"),
        messages=messages
        # [
        #     {
        #         "role": "system",
        #         "content": "Assistant that helps users with their questions. Be brief in your answers and always return the answer in the language of the question. If asking a clarifying question to the user would help, ask the question."},
        #     {
        #          "role": "user",
        #          "content": user_prompt
        #     }   
        # ],
    )
    return completion.choices[0].message.content

st.set_page_config(page_title="Data Exploration", layout="wide")
st.title("🔍 Data Exploration")

if "df" not in st.session_state or "question_data" not in st.session_state:
    st.error("Please upload data and provide a question on the main page.")
    st.stop()

# Initialize messages in the session state
if "messages" not in st.session_state:
     st.session_state.messages = []

# Header
col1, col2 = st.columns([1, 2])
col1.markdown(f"📁 **{st.session_state.uploaded_file_name}**")
col2.markdown(f"❓ **Question:** {st.session_state.question_data}")

st.markdown("---")

# Suggestions
with st.expander("💡 Show Suggestions"):
    st.write("💬 Here is a list of potential questions to ask about the uploaded event data based on the question raised :-)")
    st.markdown("""
    Suggestion overview:
    - Suggestion 1 
    - Suggestion 2 
    - Suggestion 3
    """)
#TODO: Establish connection to LLM and question    

st.markdown("---")

# Chat + Plots
col_left, col_right = st.columns([1, 1])
with col_left:
    st.subheader("🧠 Chatbot")

    # Display messages
    for message in st.session_state["messages"]:
         with st.chat_message(message["role"]):
              st.markdown(message["content"])
    
    scroll_anchor = st.empty()

    if user_prompt := st.chat_input("Your question:"):
        st.session_state.messages.append({"role": "user", "content": user_prompt})

        with st.chat_message("user"):
            st.markdown(user_prompt)
        
        with st.chat_message("assistant"):
            chatbot_msg =st.empty()
            full_response = api_request([
                {"role": msg["role"], "content": msg["content"]}
                for msg in st.session_state["messages"]
            ])
            chatbot_msg.markdown(full_response)

        st.session_state.messages.append({"role": "assistant", "content": full_response})

        scroll_anchor.markdown("⬇️")
            # stream = client.chat.completions.create(
            #     model = os.getenv("MODEL"),
            #     messages = [
            #          {"role": msg["role"], "content": msg["content"]}
            #          for msg in st.session_state["messages"]   
            #     ],
            #     stream = True,
            # )

            # for chunk in stream:
            #      token = chunk.choices[0].delta.content
            #      if token is not None:
            #           full_response = full_response + token
            #           chatbot_msg.markdown(full_response)
            
            # chatbot_msg.markdown(full_response)
        
with col_right:
    st.subheader("📈 Graphics")
    st.write("🔧 Plots to be shown here including functionality for annotation!")
    # TODO: Dynamische Grafiken auf Basis des Datensatzes

st.markdown("---")
if st.button("⬇️ Export chat + plots as PDF"):
        buffer = io.BytesIO()
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{now}.pdf"
        st.success(f"PDF '{filename}' was generated!")
        # TODO: PDF-Generierung mit Chatverlauf + Plots einfügen

