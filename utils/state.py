import streamlit as st

def init_session_state():
    """Ensure required keys exist in session state."""
    st.session_state.setdefault("feedbacks", {})    # {feedback_key: {"label": str, "text": str}}
    st.session_state.setdefault("viz_images", {"items": []})  # [{"key": str, "title": str, "bytes": b"..."}]
    st.session_state.setdefault("viz_data", {})

def feedback_input(label: str, key: str, height: int = 100, placeholder: str = "Please share your thoughts..."):
    """Render text area for feedback."""
    st.text_area(label=label, key=key, height=height, placeholder=placeholder)

def set_viz_meta(key: str, meta: dict):
    """Store rich metadata for a given visualization key."""
    st.session_state.viz_data[key] = meta or {}

def attach_text_to_visual(
    viz_key: str,
    label: str,
    *,
    kind: str = "feedback",          # e.g. "feedback" | "note" | "legend"
    from_input_key: str | None = None,
    text: str | None = None,
):
    """
    Bind a text block to a visualization (will appear directly under the image in the PDF).
    - Use `from_input_key` to copy text from a Streamlit text_area (user feedback).
    - Or pass `text` for programmatic notes (LLM explanation, legends, etc.).
    Stores under: feedbacks[f"{kind}__{viz_key}"] = {"label","text"}.
    """
    st.session_state.setdefault("feedbacks", {})
    if from_input_key is None and text is None:
        return
    content = (st.session_state.get(from_input_key) if from_input_key else text) or ""
    st.session_state.feedbacks[f"{kind}__{viz_key}"] = {
        "label": label,
        "text": content.strip()
    }