# Importing libraries
from __future__ import annotations
import streamlit as st
import pandas as pd
import pm4py

# Integrating utility functions
from utils.state import init_session_state, attach_text_to_visual, set_viz_meta
from utils.media import register_png_file_path, register_dataframe_as_image

init_session_state()

@st.cache_data(show_spinner=False)
def filter_variants_for_coverage(
    df: pd.DataFrame,
    coverage_threshold: float,
    *,
    case_id_key: str,
    activity_key: str,
    timestamp_key: str,
) -> pd.DataFrame:
    variants_count = pm4py.get_variants(df, activity_key=activity_key, case_id_key=case_id_key, timestamp_key=timestamp_key)
    sorted_variants = sorted(variants_count.items(), key=lambda x: x[1], reverse=True)
    total_cases = sum(count for _, count in sorted_variants)

    selected_variants, cumulative = set(), 0
    for variant, count in sorted_variants:
        cumulative += count; selected_variants.add(variant)
        if total_cases and (cumulative / total_cases) >= coverage_threshold:
            break

    case_variants = df.groupby(case_id_key)[activity_key].apply(tuple)
    selected_case_ids = case_variants[case_variants.isin(selected_variants)].index
    filtered_df = df[df[case_id_key].isin(selected_case_ids)].copy()

    set_viz_meta("proc_variant_filter", {
        "type": "filter",
        "title": "Variant coverage filter",
        "coverage_threshold": float(coverage_threshold),
        "selected_variants_count": int(len(selected_variants)),
        "total_cases": int(total_cases),
        "retained_cases": int(filtered_df[case_id_key].nunique()),
    })
    return filtered_df

def discover_bpmn_and_register(
    df: pd.DataFrame,
    *,
    case_id_key: str,
    activity_key: str,
    timestamp_key: str,
    coverage_threshold: float,
) -> str:
    bpmn = pm4py.discover_bpmn_inductive(df)
    path = "bpmn_model_filtered.png"
    pm4py.vis.save_vis_bpmn(bpmn, file_path=path)

    title = f"Filtered process model ({int(coverage_threshold*100)}% coverage)"
    register_png_file_path(path, key="proc_bpmn_filtered", title=title)

    set_viz_meta("proc_bpmn_filtered", {
        "type": "image", "title": title, "algorithm": "inductive BPMN",
        "coverage_threshold": float(coverage_threshold),
    })
    return path

def build_process_stats(
    df: pd.DataFrame,
    *,
    case_id_key: str,
    activity_key: str,
    timestamp_key: str,
) -> pd.DataFrame:
    starts = pm4py.get_start_activities(df, activity_key=activity_key, case_id_key=case_id_key, timestamp_key=timestamp_key)
    ends   = pm4py.get_end_activities(df,   activity_key=activity_key, case_id_key=case_id_key,   timestamp_key=timestamp_key)

    rows = []
    if starts:
        total = sum(starts.values())
        for i, (ev, cnt) in enumerate(sorted(starts.items(), key=lambda x: x[1], reverse=True)[:3], start=1):
            p = (cnt / total) if total else 0.0
            rows.append([f"Typical starting event #{i}", f"{ev}: {p:.2%}"])
    if ends:
        total = sum(ends.values())
        for i, (ev, cnt) in enumerate(sorted(ends.items(), key=lambda x: x[1], reverse=True)[:3], start=1):
            p = (cnt / total) if total else 0.0
            rows.append([f"Typical ending event #{i}", f"{ev}: {p:.2%}"])

    set_viz_meta("proc_stats_summary", {
        "type": "table",
        "title": "Process-centric headline stats",
        "top_start_activities": dict(sorted(starts.items(), key=lambda x: x[1], reverse=True)[:5]) if starts else {},
        "top_end_activities":   dict(sorted(ends.items(),   key=lambda x: x[1], reverse=True)[:5]) if ends else {},
    })
    return pd.DataFrame(rows, columns=["Statistic", "Value"])

RELEVANT_CONSTRAINTS = {
    "existence":  "How often an activity must occur in a case (at least/at most once, etc.).",
    "response":   "If one activity occurs, another must eventually follow in the same case.",
    "precedence": "An activity can occur only if another occurred earlier in the case.",
}

def render_declare_model(df: pd.DataFrame) -> None:
    """
    Discover DECLARE constraints, show only the RELEVANT_CONSTRAINTS in the UI,
    and register a single combined table for the PDF export (proc_declare_summary)
    with a legend containing concise explanations. No feedback handling here.
    """
    declare_model = pm4py.discover_declare(df)

    meta_counts = {k: (len(v) if isinstance(v, dict) else 0) for k, v in declare_model.items()}
    set_viz_meta(
        "proc_declare_model",
        {
            "type": "model",
            "title": "DECLARE constraints (selected)",
            "counts_by_type": {k: meta_counts.get(k, 0) for k in RELEVANT_CONSTRAINTS.keys()},
        },
    )

    export_rows = []    # rows for the combined export table
    legend_lines = []   # legend text lines for the export

    # UI rendering per relevant type + collect export material
    for ctype, explanation in RELEVANT_CONSTRAINTS.items():
        if ctype not in declare_model or not declare_model[ctype]:
            continue

        with st.expander(f"📐 {ctype} constraints"):
            st.markdown(f"💡 *{explanation}*")

            rows_ui, texts_ui = [], []
            for acts, metrics in declare_model[ctype].items():
                # Format activities & example text
                if isinstance(acts, tuple):
                    activity_str = " → ".join(acts)
                    if ctype == "response":
                        example_desc = f"If **{acts[0]}** occurs, **{acts[1]}** must eventually follow in the same case."
                    elif ctype == "precedence":
                        example_desc = f"If **{acts[1]}** occurs, **{acts[0]}** must have occurred earlier."
                    else:  # existence (tuple is rare but handled)
                        example_desc = f"Check how often **{acts}** occurs per case to satisfy existence constraints."
                else:
                    activity_str = acts
                    example_desc = (
                        f"Check how often **{acts}** occurs per case." if ctype == "existence" else f"Constraint on **{acts}**."
                    )

                sup = metrics.get("support", 0)
                conf = metrics.get("confidence", 0)
                pct = f"{(conf / sup):.2%}" if sup else "0%"

                # UI table row
                rows_ui.append({"Constraint": activity_str, "Support": sup, "Confidence": f"{conf} ({pct})"})

                # UI explanation
                texts_ui.append(
                    f"🔹 **{activity_str}**  \n"
                    f"{example_desc}  \n"
                    f"→ Support: **{sup}**  \n"
                    f"→ Confidence: **{conf}** ({pct})"
                )

                # Export rows (only relevant types)
                export_rows.append(
                    {"Type": ctype.title(), "Constraint": activity_str, "Support": sup, "Confidence": f"{conf} ({pct})"}
                )

                # Legend line for export
                legend_lines.append(
                    f"• [{ctype}] {activity_str} — {example_desc} (Support: {sup}, Confidence: {conf} → {pct})"
                )

            if rows_ui:
                st.dataframe(pd.DataFrame(rows_ui), use_container_width=True)
                st.markdown("### ℹ️ Constraint Explanations")
                for t in texts_ui:
                    st.markdown(t)

    # Export registration (single summary item + legend for explanations)
    if export_rows:
        df_export = pd.DataFrame(export_rows, columns=["Type", "Constraint", "Support", "Confidence"])
        register_dataframe_as_image(df_export, key="proc_declare_summary", title="DECLARE constraints (selected)")

        if legend_lines:
            attach_text_to_visual(
                "proc_declare_summary",
                label="Constraint Explanations",
                kind="legend",
                text="\n".join(legend_lines),
            )

def discover_footprints_and_register(df: pd.DataFrame, *, coverage_threshold: float) -> None:
    fp = pm4py.discover_footprints(df)
    path = "footprint_model_filtered.png"
    pm4py.vis.save_vis_footprints(fp, file_path=path)

    title = f"Filtered footprint model ({int(coverage_threshold*100)}% coverage)"
    register_png_file_path(path, key="proc_footprints_filtered", title=title)

    set_viz_meta("proc_footprints_filtered", {
        "type": "image", "title": title,
        "legend": {">": "row precedes column", "<": "column precedes row", "||": "parallel", "#": "no relation"}
    })

    st.image(path, caption=title, use_container_width=True)
