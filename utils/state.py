import streamlit as st

def init_session_state():
    """Ensure required keys exist in session state."""
    st.session_state.setdefault("feedbacks", {})    # {feedback_key: {"label": str, "text": str}}
    st.session_state.setdefault("viz_images", {"items": []})  # [{"key": str, "title": str, "bytes": b"..."}]
    st.session_state.setdefault("viz_data", {})

def feedback_input(label: str, key: str, height: int = 100, placeholder: str = "Please share your thoughts..."):
    """Render text area for feedback."""
    st.text_area(label=label, key=key, height=height, placeholder=placeholder)

def record_feedback_from_key(key: str, label: str):
    """Copy current text of the text area into a structured store."""
    text = (st.session_state.get(key) or "").strip()
    st.session_state.feedbacks[key] = {"label": label, "text": text}

def set_viz_meta(key: str, meta: dict):
    """Store rich metadata for a given visualization key."""
    st.session_state.viz_data[key] = meta or {}
    st.session_state.setdefault("viz_data", {})