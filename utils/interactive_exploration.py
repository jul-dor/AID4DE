# utils/interactive_exploration.py
from __future__ import annotations

import re
from typing import List, Dict, Any
import os

import streamlit as st
import pandas as pd
from openai import AzureOpenAI

from utils.state import (
    init_session_state,
    set_viz_meta,
    feedback_input,
    attach_text_to_visual,
)
from utils.media import register_matplotlib_figure


init_session_state()  # ensure session keys exist


# -------- small helpers --------

def _slugify(text: str, prefix: str = "ix") -> str:
    """Create a stable, short slug usable as key for viz + export."""
    base = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower()).strip("-")
    if not base:
        base = "plot"
    return f"{prefix}_{base[:40]}"

def _get_code_cache() -> dict:
    """Keep a per-suggestion cache of generated plot code to avoid repeated LLM calls."""
    st.session_state.setdefault("ix_plot_code", {})
    return st.session_state["ix_plot_code"]

def _get_azure_model_name() -> str:
    """Return the Azure OpenAI model name from environment variables."""
    model = os.getenv("AZURE_OPENAI_MODEL")
    if not model:
        raise RuntimeError("AZURE_OPENAI_MODEL is not set in environment variables.")
    return model

def get_interactive_client() -> AzureOpenAI:
    """Reuse a single client instance from session state."""
    if "azure_client" not in st.session_state:
        import os
        from dotenv import load_dotenv

        load_dotenv()
        st.session_state.azure_client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        )
    return st.session_state.azure_client


# -------- Proposing suggestions for the visualizations --------

def suggest_visualizations(question: str, excluded_labels: List[str]) -> List[str]:
    """
    Ask the LLM for 5–10 *simple* visualization ideas that help validate event logs.
    """
    client = get_interactive_client()

    excluded_str = ", ".join(excluded_labels) if excluded_labels else "none"

    system_prompt = f"""
You are a data assistant specialized in event log analysis and process mining.

Given an analysis question, propose between 4 and 6 **simple, interpretable** visualization ideas
that help a domain expert assess whether the event log is valid for its intended purpose.

Strong preferences:
- Prefer very easy-to-read plots such as: bar charts (top-N categories), histograms, boxplots,
  line charts over time, simple heatmaps.
- You may include a few visualizations that highlight **outliers** (e.g. long-running cases,
  unusually frequent activities, rare variants), but keep the charts conceptually simple.
- Avoid high-complexity visualizations like: large correlation matrices over many attributes,
  parallel coordinates plots, Sankey diagrams, cluster dendrograms, multi-layer composite charts, or resource handover analysis.

Avoid proposing visualization types that are already covered on other pages, especially:
{excluded_str}.

Return:
- a simple bullet list using "- " or "• "
- each line: one concise visualization idea, starting with a short title,
  followed by a short explanation.
Do NOT return code, markdown headings, or prose paragraphs.
    """.strip()

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"My analysis question is: {question}"},
    ]

    resp = client.chat.completions.create(
        model=_get_azure_model_name(),
        messages=messages,
        temperature=0.6,
    )
    raw = resp.choices[0].message.content or ""

    suggestions: List[str] = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        # remove bullets / numbering
        line = re.sub(r"^[-•\d\.\)]\s*", "", line)
        if line:
            suggestions.append(line)

    # limit to 10 max
    return suggestions[:10]


# -------- Code generation for the visualizations --------

def _build_code_generation_prompt(
    suggestion: str,
    case_id_key: str,
    activity_key: str,
    timestamp_key: str,
    resource_key: str | None,
) -> str:
    """
    System prompt for the code-generating call.
    We force a contract: function build_plot(df) -> (fig, meta_dict)
    """
    return f"""
You are a Python expert for event logs used for process-mining.

The application will give you a pandas DataFrame named `df` with at least these columns:

- df['{case_id_key}']  : case identifiers
- df['{activity_key}'] : activity names
- df['{timestamp_key}']: event timestamps (datetime-like)
- df['{resource_key}'] : resource / performer (may be None or missing)

TASK:
Write **pure Python code** (no markdown, no backticks) that defines a function:

    def build_plot(df):
        # df is the event log dataframe
        # create exactly ONE matplotlib figure
        # return (fig, meta)

`meta` must be a dict with at least:
- "title": short human readable title
- "type": one of ["bar_chart","line_chart","histogram","heatmap"]
- "description": 2–3 sentences what the visualization shows
- "x_axis": label of the x-axis (or "" for tables)
- "y_axis": label of the y-axis (or "" for tables)

Design rules (very important):
- If you create boxplots by group (e.g. case duration by variant),
      do NOT call .boxplot() on a groupby object (this is invalid in pandas).
      Instead, either:
        * use seaborn.boxplot(x="group", y="value", data=df_prepared), OR
        * build a list of 1D arrays per group and pass it to matplotlib:
              grouped = [...]
              ax.boxplot(grouped, labels=[...])
- Never write code like df.groupby("x")["y"].boxplot().
- If you work with categorical variables (e.g. activities, resources), show only the
  top 10–15 categories sorted by frequency and, if helpful, aggregate the rest into \"Other\".
- For diagrams show at maximum 15 categories on any axis.
- Always rotate x-axis tick labels by 45° and right-align them if there are many categories.
- Prefer simple bar charts, histograms, boxplots, line charts, and small heatmaps.
- Avoid overly busy visualizations with too many categories or unreadable labels.
- Focus on data quality / outlier aspects (unusual durations, rare activities, skewed distributions).

Use only standard Python plus pandas, numpy, matplotlib.pyplot, and optionally seaborn.
Import what you need inside the code you produce.

The visualization idea to implement is:
\"\"\"{suggestion}\"\"\".

Focus on something that helps assessing **data quality / validity** of the event log.

Important:
- Do NOT show or save the figure (no plt.show, no df.to_csv, etc.).
- Just build the figure and return it.
- Use clear axis labels and a meaningful title in meta["title"] matching the figure.
- Do NOT reference Streamlit in this code.
    """.strip()


def generate_plot_code_for_suggestion(
    suggestion: str,
    *,
    case_id_key: str,
    activity_key: str,
    timestamp_key: str,
    resource_key: str | None,
) -> str:
    """Ask the LLM to produce Python code implementing build_plot(df)."""
    client = get_interactive_client()
    system_prompt = "You write safe, self-contained Python functions for data visualization."
    user_prompt = _build_code_generation_prompt(
        suggestion, case_id_key, activity_key, timestamp_key, resource_key or ""
    )

    resp = client.chat.completions.create(
        model=_get_azure_model_name(),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.4,
    )

    code = resp.choices[0].message.content or ""

    # strip ```python ... ``` if present
    code = re.sub(r"^```python\s*", "", code.strip(), flags=re.IGNORECASE)
    code = re.sub(r"^```", "", code.strip())
    code = re.sub(r"```$", "", code.strip())
    return code.strip()


# -------- Execute the generated code and register --------

def run_generated_visualization(
    suggestion: str,
    df: pd.DataFrame,
    *,
    case_id_key: str,
    activity_key: str,
    timestamp_key: str,
    resource_key: str | None,
) -> None:
    """
    For one suggestion:
    - ask LLM for code (only once per suggestion; then cache)
    - exec code, expecting build_plot(df) -> (fig, meta)
    - show the figure in Streamlit
    - store image in viz_images for PDF
    - store meta in viz_data
    - attach feedback under the plot
    """
    code_cache = _get_code_cache()
    code = code_cache.get(suggestion)

    if code is None:
        code = generate_plot_code_for_suggestion(
            suggestion,
            case_id_key=case_id_key,
            activity_key=activity_key,
            timestamp_key=timestamp_key,
            resource_key=resource_key,
        )
    code_cache[suggestion] = code

    # sandbox for exec
    local_env: Dict[str, Any] = {}
    try:
        exec(code, {}, local_env)
    except Exception as e:
        st.error(f"Failed to compile generated code for '{suggestion}': {e}")
        with st.expander("Show generated code"):
            st.code(code, language="python")
        return

    build_fn = local_env.get("build_plot")
    if not callable(build_fn):
        st.error("Generated code did not define a callable build_plot(df) function.")
        with st.expander("Show generated code"):
            st.code(code, language="python")
        return

    try:
        fig, meta = build_fn(df.copy())
    except Exception as e:
        st.error(f"Error while executing build_plot(df): {e}")
        with st.expander("Show generated code"):
            st.code(code, language="python")
        return

    if meta is None or not isinstance(meta, dict):
        meta = {}

    title = meta.get("title") or suggestion
    key = meta.get("key") or _slugify(title)

    # --- show in UI ---
    import matplotlib.pyplot as plt
    st.pyplot(fig)

    # --- register image bytes for PDF ---
    register_matplotlib_figure(fig, key=key, title=title)

    # --- store metadata for later LLM context ---
    meta_out = dict(meta)  # shallow copy
    meta_out.setdefault("suggestion_text", suggestion)
    meta_out.setdefault("origin", "interactive_event_log_exploration")
    set_viz_meta(key, meta_out)

    # --- feedback directly under the figure ---
    fb_key = f"feedback__{key}"
    fb_label = "Feedback"
    feedback_input(fb_label, fb_key)
    attach_text_to_visual(key, fb_label, kind="feedback", from_input_key=fb_key)

    # small clean-up
    plt.close(fig)
