# Importing libraries
import streamlit as st
import matplotlib.pyplot as plt
import pm4py
import pandas as pd
from collections import Counter
import numpy as np
import seaborn as sns

# Integrating utility functions
from utils.state import init_session_state, feedback_input, record_feedback_from_key, set_viz_meta 
from utils.media import save_matplotlib_figure_to_bytes, register_png_file_path

# Ensure session scaffolding exists
init_session_state()  

# ---------- Helpers ----------
def _save_fig_and_feedback(fig, *, key: str, title: str, fb_key: str, fb_label: str):
    """Save figure and feedback to session state."""
    save_matplotlib_figure_to_bytes(fig, key=key, title=title)
    feedback_input(fb_label, fb_key)
    record_feedback_from_key(fb_key, fb_label)


# ---------- Plots ----------

# Generating absolute activity frequency plot within frequency & distribution analysis
def plot_absolute_activity_frequency(df, activity_key):
    try:
        activity_counts = Counter(df[activity_key])
        sorted_activities = sorted(activity_counts.items(), key=lambda x: x[1], reverse=True)
        max_activities = 20

        if len(sorted_activities) > max_activities:
            top_activities = sorted_activities[:max_activities]
            hidden_activities = sorted_activities[max_activities:]
            st.info(f"Showing top {max_activities} of {len(activity_counts)} activities.")
        else:
            top_activities = sorted_activities
            hidden_activities = []
        
        activities, frequencies = zip(*top_activities)

        fig, ax = plt.subplots(figsize=(10, 5))
        ax.bar(range(len(activities)), frequencies, color="skyblue", edgecolor='black')
        ax.set_xticks(range(len(activities)))
        ax.set_xticklabels(activities, rotation=45, ha="right")
        ax.set_xlabel('Activities')
        ax.set_ylabel('Frequencies')
        title = 'Absolute Activity Frequency Histogram'
        ax.set_title(title)
        st.pyplot(fig)

        if hidden_activities:
            hidden_text = ", ".join([f"{name} ({count})" for name, count in hidden_activities])
            st.caption(f"Not shown in chart: {hidden_text}")

        # --- Metadata ---
        set_viz_meta("absolute_activity_frequency_graph", {
            "type": "bar_chart",
            "title": title,
            "x_axis": "Activities",
            "y_axis": "Frequencies",
            "top_activities": dict(sorted_activities[:5]),
            "total_activities": int(sum(activity_counts.values()))
        })

        _save_fig_and_feedback(
            fig, key="absolute_activity_frequency_graph",
            title=title,
            fb_key="feedback_absolute_activity_frequency",
            fb_label="Does the above visualization reflect your experience?"
        )

    except Exception as e:
        st.warning(f"Could not render activity frequencies: {e}")

# Generating relative activity frequency plot within frequency & distribution analysis
def plot_relative_activity_frequency(df, activity_key):
    try:
        activity_counts = Counter(df[activity_key])
        total_activities = sum(activity_counts.values()) 

        relative_activity_freq = {
            activity: (count / total_activities) * 100
            for activity, count in activity_counts.items()
        }

        sorted_activities = sorted(relative_activity_freq.items(), key=lambda x: x[1], reverse=True)

        max_activities = 20
        if len(sorted_activities) > max_activities:
            top_activities = sorted_activities[:max_activities]
            hidden_activities = sorted_activities[max_activities:]
            st.info(f"Showing top {max_activities} of {len(activity_counts)} activities.")
        else:
            top_activities = sorted_activities
            hidden_activities = []

        activities, percentages = zip(*top_activities)

        fig, ax = plt.subplots(figsize=(10, 5))
        ax.bar(range(len(activities)), percentages, color="lightsalmon", edgecolor='black')
        ax.set_xticks(range(len(activities)))
        ax.set_xticklabels(activities, rotation=45, ha="right")
        ax.set_xlabel('Activities')
        ax.set_ylabel('Relative Frequency (%)')
        title = 'Relative Activity Frequency Histogram'
        ax.set_title(title)
        st.pyplot(fig)

        if hidden_activities:
            hidden_text = ", ".join([f"{name} ({round(percent, 2)}%)" for name, percent in hidden_activities])
            st.caption(f"Not shown in chart: {hidden_text}")

        # --- Metadata ---
        set_viz_meta("relative_activity_frequency_graph", {
            "type": "bar_chart",
            "title": title,
            "x_axis": "Activities",
            "y_axis": "Relative Frequency (%)",
            "top_activities": {activity: round(percent, 2) for activity, percent in sorted_activities[:5]},
            "total_activities": int(total_activities)
        })

        _save_fig_and_feedback(
            fig, key="relative_activity_frequency_graph",
            title=title,
            fb_key="feedback_relative_activity_frequency",
            fb_label="Does the above visualization reflect your experience?"
        )

    except Exception as e:
        st.warning(f"Could not render activity frequencies: {e}")

# Generating absolute case frequency plot within frequency & distribution analysis
def plot_absolute_case_frequency(df, case_id_key, activity_key, timestamp_key):
    try:
        variants = pm4py.get_variants(
            df,
            activity_key=activity_key,
            case_id_key=case_id_key,
            timestamp_key=timestamp_key
        )

        sorted_variants = sorted(variants.items(), key=lambda x: x[1], reverse=True)
        total_count = sum([count for _, count in sorted_variants])

        cumulative_count = 0
        selected_variants = []
        for variant, count in sorted_variants:
            cumulative_count += count
            selected_variants.append((variant, count))
            if cumulative_count / total_count >= 0.8:
                break
        
        full_variant_count = len(selected_variants)
        if full_variant_count > 10:
            selected_variants = selected_variants[:10]
            st.info(f"Showing 10 of {full_variant_count} variants.")
        else:
            st.info(f"Showing all {full_variant_count} variants covering 80% of all cases.")

        x_labels = [f"Variant {i+1}" for i in range(len(selected_variants))]
        y_values = [count for _, count in selected_variants]
        variant_mapping = dict(zip(x_labels, [variant for variant, _ in selected_variants]))

        fig, ax = plt.subplots(figsize=(12, 6))
        ax.bar(x_labels, y_values, color="skyblue", edgecolor='black')
        ax.set_xlabel("Variants (sorted by frequency)")
        ax.set_ylabel("Frequency")
        if full_variant_count > 10:
            title = "Absolute Case Frequency Histogram (showing the most frequent cases in the log)"
        else:
            title = "Absolute Case Frequency Histogram (showing 80% of cases in the log)"
        ax.set_title(title)
        plt.xticks(rotation=45, ha="right")
        st.pyplot(fig)

        st.markdown("### Legend")
        for label, variant in variant_mapping.items():
            st.markdown(f"**{label}**: {', '.join(variant)}")

        # --- Metadata ---
        set_viz_meta("absolute_case_frequency_graph", {
            "type": "bar_chart",
            "title": "Top 80% Frequent Case Variants",
            "x_axis": "Variants",
            "y_axis": "Frequency",
            "top_variants": {label: list(variant) for label, variant in list(variant_mapping.items())[:5]},
            "coverage_share": round(cumulative_count / total_count, 4)
        })

        _save_fig_and_feedback(
            fig, key="absolute_case_frequency_graph",
            title="Absolute Case Frequency Histogram",
            fb_key="feedback_absolute_case_frequency",
            fb_label="Does the above visualization reflect your experience?"
        )

    except Exception as e:
        st.warning(f"Could not render case frequency graph: {e}")

# Generating relative case frequency plot within frequency & distribution analysis
def plot_relative_case_frequency(df, case_id_key, activity_key, timestamp_key):
    try:
        stochastic_language = pm4py.get_stochastic_language(
            df,
            activity_key=activity_key,
            case_id_key=case_id_key,
            timestamp_key=timestamp_key
        )

        sorted_variants = sorted(stochastic_language.items(), key=lambda x: x[1], reverse=True)

        cumulative_prob = 0
        selected_variants = []
        for variant, prob in sorted_variants:
            cumulative_prob += prob
            selected_variants.append((variant, prob))
            if cumulative_prob >= 0.8:
                break
        
        full_variant_count = len(selected_variants)
        if full_variant_count > 10:
            selected_variants = selected_variants[:10]
            cumulative_prob = sum(prob for _, prob in selected_variants)
            st.info(f"Showing top 10 variants covering {round(cumulative_prob * 100, 1)}% of all cases.")
        else:
            st.info(f"Showing top {full_variant_count} variants covering 80% of all cases.")
        
        x_labels = [f"Variant {i+1}" for i in range(len(selected_variants))]
        y_values = [round(prob * 100, 2) for _, prob in selected_variants]  
        variant_mapping = dict(zip(x_labels, [variant for variant, _ in selected_variants]))

        fig, ax = plt.subplots(figsize=(12, 6))
        ax.bar(x_labels, y_values, color="lightsalmon", edgecolor='black')
        ax.set_xlabel("Variants (sorted by probability)")
        ax.set_ylabel("Relative Frequency (%)")
        if full_variant_count > 10:
            title = "Relative Case Frequency Histogram (showing the most frequent cases in the log)"
        else:
            title = "Relative Case Frequency Histogram (showing 80% of cases in the log)"
        ax.set_title(title)    
        plt.xticks(rotation=45, ha="right")
        st.pyplot(fig)

        st.markdown("### Legend")
        for label, variant in variant_mapping.items():
            st.markdown(f"**{label}**: {', '.join(variant)}")

        # --- Metadata ---
        set_viz_meta("relative_case_frequency_graph", {
            "type": "bar_chart",
            "title": "Top 80% Case Variants by Relative Frequency",
            "x_axis": "Variants",
            "y_axis": "Relative Frequency (%)",
            "top_variants": {
                label: {"activities": list(variant), "percentage": y_values[i]}
                for i, (label, variant) in enumerate(list(variant_mapping.items())[:5])
            },
            "coverage_share": round(cumulative_prob, 4)
        })

        _save_fig_and_feedback(
            fig, key="relative_case_frequency_graph",
            title="Relative Case Frequency Histogram",
            fb_key="feedback_relative_case_frequency",
            fb_label="Does the above visualization reflect your experience?"
        )

    except Exception as e:
        st.warning(f"Could not render relative case frequencies: {e}")

# Generating case length distribution plot within frequency & distribution analysis
def plot_case_length_distribution(df, case_id_key, activity_key, timestamp_key):
    try:
        variants = pm4py.get_variants(
            df,
            activity_key= activity_key,
            case_id_key = case_id_key,
            timestamp_key = timestamp_key
        )

        counts_per_case = Counter()

        for variant, count in variants.items():
            length = len(variant)
            counts_per_case[length] += count
        
        total_cases = sum(counts_per_case.values())
        sorted_lengths_counts = sorted(counts_per_case.items(), key = lambda x: x[0])

        max_lengths = 20

        if len(sorted_lengths_counts) > max_lengths:
            st.info(f"Showing top {max_lengths} case lengths of {len(sorted_lengths_counts)} total.")
            shown_lengths_counts = sorted_lengths_counts[:max_lengths]
            shown_case_total = sum([count for _, count in shown_lengths_counts])
            hidden_percentage = round((1 - shown_case_total / total_cases) * 100, 2)
        else:
            shown_lengths_counts = sorted_lengths_counts
            hidden_percentage = 0.0

        sorted_lengths = [length for length, _ in shown_lengths_counts]
        counts = [count for _, count in shown_lengths_counts]

        fig, ax = plt.subplots(figsize=(10,6))
        ax.bar(sorted_lengths, counts, color='skyblue', edgecolor='black')
        ax.set_xlabel("Number activities per case")
        ax.set_ylabel("Number of Cases")
        title = 'Distribution of number of activities per case'
        ax.set_title(title)
        ax.set_xticks(sorted_lengths)
        ax.grid(axis='y', linestyle='--', alpha=0.7)
        fig.tight_layout()
        st.pyplot(fig)

        if hidden_percentage > 0:
            st.caption(f"{hidden_percentage}% of cases with less frequent case lengths are not shown in the plot.")

        # --- Metadata ---
        set_viz_meta("case_length_distribution_graph", {
            "type": "bar_chart",
            "title": "Distribution of Case Lengths",
            "x_axis": "Activities per Case",
            "y_axis": "Number of Cases",
            "lengths_counts": dict(shown_lengths_counts),
            "hidden_share_percent": hidden_percentage
        })

        _save_fig_and_feedback(
            fig, key="case_length_distribution_graph",
            title="Case length distribution",
            fb_key="feedback_case_length_distribution",
            fb_label="Does the above visualization reflect your experience?"
        )

    except Exception as e:
        st.warning(f"Could not render the case length distribution graph: {e}")

# Generating absolute resource frequency plot within resource analysis
def plot_absolute_resource_frequency(df, resource_key):
    try:
        resource_counts = Counter(df[resource_key])
        sorted_resources = sorted(resource_counts.items(), key=lambda x: x[1], reverse=True)

        max_resources = 20
        if len(sorted_resources) > max_resources:
            top_resources = sorted_resources[:max_resources]
            hidden_resources = sorted_resources[max_resources:]
            st.info(f"Showing top {max_resources} of {len(resource_counts)} resources.")
        else:
            top_resources = sorted_resources
            hidden_resources = []

        resources, frequencies = zip(*top_resources)

        fig, ax = plt.subplots(figsize=(10, 5))
        ax.bar(range(len(resources)), frequencies, color="skyblue", edgecolor='black')
        ax.set_xticks(range(len(resources)))
        ax.set_xticklabels(resources, rotation=45, ha="right")
        ax.set_xlabel("Resources")
        ax.set_ylabel("Frequency")
        title = "Absolute Frequency of Resources"
        ax.set_title(title)
        st.pyplot(fig)

        if hidden_resources:
            hidden_text = ", ".join([f"{res} ({count})" for res, count in hidden_resources])
            st.caption(f"Not shown in chart: {hidden_text}")

        # --- Metadata ---
        set_viz_meta("resource_frequency_absolute", {
            "type": "bar_chart",
            "title": title,
            "x_axis": "Resources",
            "y_axis": "Frequency",
            "top_resources": dict(sorted_resources[:5]),
            "total_events": int(sum(resource_counts.values()))
        })

        _save_fig_and_feedback(
            fig, key="resource_frequency_absolute",
            title=title,
            fb_key="feedback_absolute_resource_frequency",
            fb_label="Does the above visualization reflect your experience?"
        )

    except Exception as e:
        st.warning(f"Could not render absolute resource frequencies: {e}")

# Generating relative resource frequency plot within resource analysis
def plot_relative_resource_frequency(df, resource_key):
    try:
        resource_counts = Counter(df[resource_key])
        total_resources = sum(resource_counts.values())
        relative_resource_freq = {
            resource: (count / total_resources) * 100
            for resource, count in resource_counts.items()
        }

        sorted_resources = sorted(relative_resource_freq.items(), key=lambda x: x[1], reverse=True)

        max_resources = 20
        if len(sorted_resources) > max_resources:
            top_resources = sorted_resources[:max_resources]
            hidden_resources = sorted_resources[max_resources:]
            st.info(f"Showing top {max_resources} of {len(resource_counts)} resources.")

        else:
            top_resources = sorted_resources
            hidden_resources = []

        resources, percentages = zip(*top_resources)

        fig, ax = plt.subplots(figsize=(10, 5))
        ax.bar(range(len(resources)), percentages, color="lightsalmon", edgecolor='black')
        ax.set_xticks(range(len(resources)))
        ax.set_xticklabels(resources, rotation=45, ha="right")

        ax.set_xlabel("Resources")
        ax.set_ylabel("Relative Frequency (%)")
        title = "Relative Frequency of Resources"
        ax.set_title(title)
        st.pyplot(fig)

        if hidden_resources:
            hidden_text = ", ".join([f"{res} ({round(freq, 2)}%)" for res, freq in hidden_resources])
            st.caption(f"Not shown in chart: {hidden_text}")

        # --- Metadata ---
        set_viz_meta("relative_resource_frequency", {
            "type": "bar_chart",
            "title": title,
            "x_axis": "Resources",
            "y_axis": "Relative Frequency (%)",
            "top_resources": {r: round(p, 2) for r, p in sorted_resources[:5]},
            "total_events": int(total_resources)
        })

        _save_fig_and_feedback(
            fig, key="relative_resource_frequency",
            title=title,
            fb_key="feedback_relative_resource_frequency",
            fb_label="Does the above visualization reflect your experience?"
        )

    except Exception as e:
        st.warning(f"Could not render relative resource frequencies: {e}")

# Generating events per time plot within temporal analysis
def plot_events_per_time_graph(df, case_id_key, activity_key, timestamp_key):
    try: 
        file_path = 'events_per_time_graph.png'
        pm4py.vis.save_vis_events_per_time_graph(
            df,
            file_path = file_path,
            case_id_key = case_id_key,
            activity_key = activity_key,
            timestamp_key = timestamp_key
        )

        st.image(file_path, caption= 'Events over Time')
        register_png_file_path(file_path, key="events_per_time_graph", title="Events over time")

         # --- Metadata (coarse) ---
        set_viz_meta("events_per_time_graph", {
            "type": "image",
            "title": "Events over time",
            "x_axis": "Time",
            "y_axis": "Number of Events",
            "description": "Aggregated events per time slice (pm4py default)."
        })

        fb_key = "feedback_events_per_time_graph"
        fb_label = "Does the above visualization reflect your experience?"
        feedback_input(fb_label, fb_key)
        record_feedback_from_key(fb_key, fb_label)
    except Exception as e:
        st.warning(f"Could not render events per time graph: {e}")

# Generating event distribution plot within temporal analysis
def plot_event_distribution_graphs(df, case_id_key, activity_key, timestamp_key):
    distr_types = [
    "days_week",    # 0 = Monday, ..., 6 = Sunday
    "days_month",   # 1–31
    "months",       # 1–12
    "years",        # Event years
    "hours",        # 0–23
    "weeks"         # 0–52
    ]
    
    day_name_mapping = {
    0: "Monday",
    1: "Tuesday",
    2: "Wednesday",
    3: "Thursday",
    4: "Friday",
    5: "Saturday",
    6: "Sunday"
    }
    for distr_type in distr_types:
        try:
            file_path = f"event_distribution_{distr_type}.png"
            pm4py.vis.save_vis_events_distribution_graph(
                df,
                file_path = file_path,
                activity_key = activity_key,
                case_id_key = case_id_key,
                timestamp_key = timestamp_key,
                distr_type = distr_type,
            )

            st.image(file_path, caption=f"Events by {distr_type.replace('_',' ').title()}")
            key = f"event_distribution_{distr_type}"
            register_png_file_path(file_path, key=key, title=f"Events by {distr_type.replace('_',' ').title()}")

            # --- Metadata ---
            if distr_type == "days_week":
                series = df[timestamp_key].dt.dayofweek
                counter = Counter(series)
                mapped = {day_name_mapping[k]: v for k, v in counter.items()}
                x_label = "Day of Week"
            elif distr_type == "days_month":
                series = df[timestamp_key].dt.day
                mapped = {int(k): int(v) for k, v in Counter(series).items()}
                x_label = "Day of Month"
            elif distr_type == "months":
                series = df[timestamp_key].dt.month
                mapped = {int(k): int(v) for k, v in Counter(series).items()}
                x_label = "Month"
            elif distr_type == "years":
                series = df[timestamp_key].dt.year
                mapped = {int(k): int(v) for k, v in Counter(series).items()}
                x_label = "Year"
            elif distr_type == "hours":
                series = df[timestamp_key].dt.hour
                mapped = {int(k): int(v) for k, v in Counter(series).items()}
                x_label = "Hour of Day"
            elif distr_type == "weeks":
                # TODO: Search is isocalendar() starts with 0
                mapped = {int(k): int(v) for k, v in Counter(series).items()}
                x_label = "ISO Week"

            set_viz_meta(key, {
                "type": "bar_chart",
                "title": f"Event distribution by {distr_type.replace('_',' ')}",
                "x_axis": x_label,
                "y_axis": "Number of Events",
                "distribution": mapped
            })

            fb_key = f"feedback_event_distribution_{distr_type}"
            fb_label = "Does the above visualization reflect your experience?"
            feedback_input(fb_label, fb_key)
            record_feedback_from_key(fb_key, fb_label)
                
        except Exception as e:
            st.warning(f"Could not render event distribution graph for '{distr_type}': {e}")

# Generating dotted chart plot within temporal analysis
def plot_dotted_chart(df, case_id_key, activity_key, timestamp_key):
    
    variants = pm4py.get_variants(
        df,
        activity_key=activity_key,
        case_id_key=case_id_key,
        timestamp_key=timestamp_key
    )

    sorted_variants = sorted(variants.items(), key=lambda x: x[1], reverse=True)

    total_count = sum([count for _, count in sorted_variants])
    cumulative_count = 0
    selected_variant_names = []

    for variant, count in sorted_variants:
        cumulative_count += count
        selected_variant_names.append(variant)
        if cumulative_count / total_count >= 0.8:
            break

    filtered_df = pm4py.filter_variants(
        df,
        selected_variant_names,
        activity_key = activity_key,
        case_id_key = case_id_key,
        timestamp_key = timestamp_key
    )
    
    file_path = "dotted_chart.png"
    pm4py.vis.save_vis_dotted_chart(
        filtered_df,
        file_path = file_path,
        activity_key = activity_key,
        case_id_key = case_id_key,
        timestamp_key = timestamp_key,
    )

    st.image(file_path, caption="Dotted Chart")
    register_png_file_path(file_path, key="dotted_chart", title="Dotted Chart")

    # --- Metadata (variant coverage and list) ---
    set_viz_meta("dotted_chart", {
        "type": "image",
        "title": "Dotted Chart",
        "selected_variants_count": len(selected_variant_names),
        "coverage_share": round(cumulative_count / total_count, 4)
    })

    fb_key = "feedback_dotted_chart"
    fb_label = "Does the above visualization reflect your experience?"
    feedback_input(fb_label, fb_key)
    record_feedback_from_key(fb_key, fb_label)

# Generating case duration plot within performance analysis
def plot_case_duration_graph(case_id_key, activity_key, timestamp_key):
    try:
        df_fmt = pm4py.format_dataframe(st.session_state.df_raw, case_id = case_id_key, activity_key = activity_key, timestamp_key= timestamp_key)
        file_path = 'case_duration_graph.png'
        pm4py.vis.save_vis_case_duration_graph(
            df_fmt,
            file_path = file_path,
            activity_key = activity_key,
            case_id_key = case_id_key,
            timestamp_key = timestamp_key
        )
        st.image('case_duration_graph.png', caption = 'Case durations within the data')
        
        # --- Metadata (static axes description) ---
        set_viz_meta("case_duration_graph", {
            "type": "image",
            "title": "Case durations",
            "x_axis": "Cases",
            "y_axis": "Duration",
            "description": "Distribution of case durations."
        })

        fb_key = "feedback_case_duration"
        fb_label = "Does the above visualization reflect your experience?"
        feedback_input(fb_label, fb_key)
        record_feedback_from_key(fb_key, fb_label)
    except Exception as e:
        st.warning (f"Could not render the case duration graph: {e}")

# Generating case duration plot within performance analysis
def retrieve_max_min_avg_case_duration(case_id_key, activity_key, timestamp_key):
    
    df_fmt = pm4py.format_dataframe(st.session_state.df_raw, case_id = case_id_key, activity_key = activity_key, timestamp_key= timestamp_key)

    case_durations = pm4py.stats.get_all_case_durations(
        df_fmt,
        activity_key = activity_key,
        case_id_key = case_id_key,
        timestamp_key = timestamp_key
    )

    case_durations = np.array(case_durations, dtype=float)

    case_durations_days = (case_durations / 3600) / 24
    stats = {
        'Minimum Case Length [Day]': round(float(case_durations_days.min()), 2),
        'Maximum Case Length [Day]': round(float(case_durations_days.max()), 2),
        'Average Case Length [Day]': round(float(case_durations_days.mean()), 2),
        'Standard Deviation Case Length [Day]': round(float(case_durations_days.std()), 2),
    }

    # --- Metadata ---
    set_viz_meta("case_duration_facts", {
        "type": "table",
        "title": "Case duration summary (days)",
        "stats": stats
    })

    return pd.DataFrame(list(stats.items()), columns =["Statistic", "Value"])

# Generating task responsibility heatmap within resource analysis
def plot_task_responsbility_overview(df, activity_key, resource_key):
    top_activities = df[activity_key].value_counts().nlargest(20).index
    if df[activity_key].nunique() > 20:
        st.info(f"Showing top 20 of {df[activity_key].nunique()} activities.")

    top_resources = df[resource_key].value_counts().nlargest(20).index
    if df[resource_key].nunique() > 20:
        st.info(f"Showing top 20 of {df[resource_key].nunique()} resources.")
    
    filtered_df = df[df[activity_key].isin(top_activities) & df[resource_key].isin(top_resources)]

    heatmap = pd.crosstab(filtered_df[activity_key], filtered_df[resource_key])
    heatmap_percent = heatmap.div(heatmap.sum(axis=1), axis=0) * 100
    heatmap_percent = heatmap_percent.round(2)

    fig, ax = plt.subplots(figsize=(12, 8))
    sns.heatmap(heatmap_percent, annot=True, fmt=".1f", cmap="YlGnBu",
                linewidths=0.5, cbar_kws={'label': 'Activity share (%)'})
    ax.set_xlabel("Resource")
    ax.set_ylabel("Activity")
    title = "Heatmap: Activity-Resource Distribution (%)"
    ax.set_title(title)
    plt.xticks(rotation=45, ha='right')
    fig.tight_layout()
    st.pyplot(fig)

     # --- Metadata ---
    # Extract a few top cells by percentage to give LLM a compact hint.
    top_cells = (
        heatmap_percent.stack()
        .sort_values(ascending=False)
        .head(10)
        .round(2)
        .to_dict()
    )

    set_viz_meta("task_responsibility_overview", {
        "type": "heatmap",
        "title": title,
        "x_axis": "Resource",
        "y_axis": "Activity",
        "top_cells_percent": {f"{a} | {r}": float(p) for (a, r), p in top_cells.items()},
        "shape": {"activities": int(heatmap_percent.shape[0]), "resources": int(heatmap_percent.shape[1])}
    })

    _save_fig_and_feedback(
        fig, key="task_responsibility_overview",
        title=title,
        fb_key="feedback_task_responsibility_overview",
        fb_label="Does the above visualization reflect your experience?"
    )

# ---------- Public entry point ----------

# Run all the visualizations
def run_visualizations(df, case_id_key, activity_key, timestamp_key, resource_key):
    """Main entry: renders all plots, captures feedback, stores metadata; API-compatible."""
    # --- Summary statistics (metadata only, shown as table in UI) ---
    summary_stats = {}

    # Number of events
    num_events = len(df)
    summary_stats['Total Events'] = num_events
    
    # Number of cases
    unique_case_count = df[case_id_key].nunique()
    summary_stats['Number of cases'] = unique_case_count

    # Number of variants
    variants = pm4py.get_variants(
        df,
        activity_key= activity_key,
        case_id_key = case_id_key,
        timestamp_key = timestamp_key
    )
    summary_stats['Number of Variants'] = len(variants)

    # Time range of the event log
    df[timestamp_key] = pd.to_datetime(df[timestamp_key])
    start_time = df[timestamp_key].min()
    end_time = df[timestamp_key].max()
    formatted_timeframe = f"{start_time.strftime('%d/%m/%Y %H:%M:%S')} - {end_time.strftime('%d/%m/%Y %H:%M:%S')}"
    summary_stats['Time Horizon'] = f"{formatted_timeframe}"

    # Event attributes overview
    event_attributes = pm4py.get_event_attributes(df)
    formatted_event_attributes = ', '.join(event_attributes)
    summary_stats['Event Attributes'] = formatted_event_attributes

    # Case attributes overview
    trace_attributes = pm4py.get_trace_attributes(df)
    if trace_attributes == ["case:concept:name"] or trace_attributes == []:
        summary_stats['Case Attributes'] = '-'
    else:
        formatted_trace_attributes = ', '.join(trace_attributes)
        summary_stats['Case Attributes'] = formatted_trace_attributes

    # Events per Case
    events_per_case = summary_stats['Total Events']/summary_stats['Number of cases']
    summary_stats['Events per Case'] = round(events_per_case, 2)

    # Show summary statistics in streamlit
    summary_df = pd.DataFrame(list(summary_stats.items()), columns=["Statistic", "Value"])
    with st.expander("📊 Summary Statistics"):
        st.dataframe(summary_df, hide_index=True, use_container_width=True)
        fb_key = "feedback_summary_statistics"
        fb_label = "Do the above statistics reflect your experience?"
        feedback_input(fb_label, fb_key)
        record_feedback_from_key(fb_key, fb_label)

    # Adding metadata
    set_viz_meta("summary_statistics", {
        "type": "table",
        "title": "Summary statistics",
        "values": summary_stats
    })

    # --- Frequency & distribution analysis ---
    with st.expander("🔁 Frequency & Distribution Analysis"):
        plot_absolute_activity_frequency(df, activity_key)
        plot_relative_activity_frequency(df, activity_key)
        plot_absolute_case_frequency(df, case_id_key, activity_key, timestamp_key)
        plot_relative_case_frequency(df, case_id_key, activity_key, timestamp_key)
        plot_case_length_distribution(df, case_id_key, activity_key, timestamp_key)

    # --- Temporal analysis ---
    with st.expander("🕒 Temporal Analysis"):
        plot_events_per_time_graph(df, case_id_key, activity_key, timestamp_key)
        plot_event_distribution_graphs(df, case_id_key, activity_key, timestamp_key)
        #plot_dotted_chart(df, case_id_key, activity_key, timestamp_key)
    
    # --- Performance analysis ---
    with st.expander("⚡ Performance Analysis"):
        performance_summary_df = retrieve_max_min_avg_case_duration(case_id_key, activity_key, timestamp_key)
        st.dataframe(performance_summary_df, hide_index = True, use_container_width = True)
        plot_case_duration_graph(case_id_key, activity_key, timestamp_key)

    # --- Resource analysis ---
    with st.expander("👥 Resource analysis"):
        plot_absolute_resource_frequency(df, resource_key)
        plot_relative_resource_frequency(df, resource_key)
        plot_task_responsbility_overview(df, activity_key, resource_key)


    