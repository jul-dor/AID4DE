# Importing libraries
import streamlit as st
import matplotlib.pyplot as plt
import pm4py
import pandas as pd
from collections import Counter
import numpy as np
import seaborn as sns

# Establish feedback session state
if "feedbacks" not in st.session_state:
    st.session_state.feedbacks = {}

# Establish visualization data session state
if "viz_data" not in st.session_state:
    st.session_state.viz_data = {}

viz_summary = {}

# Establish image session state
if "viz_images" not in st.session_state:
    st.session_state["viz_images"] = {}

# Function for feedback area
def feedback_input(label, key):
    st.text_area(
        label=label,
        key=key,
        height=100,
        placeholder="Please share your thoughts..."
    )

# Generating absolute activity frequency plot within frequency & distribution analysis
def plot_absolute_activity_frequency(df, activity_key, viz_summary):
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
        ax.set_title('Absolute Activity Frequency Histogram')
        st.pyplot(fig)

        if hidden_activities:
            hidden_text = ", ".join([f"{name} ({count})" for name, count in hidden_activities])
            st.caption(f"Not shown in chart: {hidden_text}")

        viz_summary["absolute_activity_frequency_graph"] = {
            "type": "bar_chart",
            "title": "Activity Frequency Histogram",
            "x_axis": "Activities",
            "y_axis": "Frequencies",
            "top_activities": dict(sorted_activities[:5])
        }

        feedback_input("Does the above visualization reflect your experience?", "feedback_absolute_activity_frequency")

    except Exception as e:
        st.warning(f"Could not render activity frequencies: {e}")

# Generating relative activity frequency plot within frequency & distribution analysis
def plot_relative_activity_frequency(df, activity_key, viz_summary):
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
        ax.set_title('Relative Activity Frequency Histogram')
        st.pyplot(fig)

        if hidden_activities:
            hidden_text = ", ".join([f"{name} ({round(percent, 2)}%)" for name, percent in hidden_activities])
            st.caption(f"Not shown in chart: {hidden_text}")

        viz_summary["relative_activity_frequency_graph"] = {
            "type": "bar_chart",
            "title": "Relative Activity Frequency Histogram",
            "x_axis": "Activities",
            "y_axis": "Relative Frequency (%)",
            "top_activities": {activity: round(percent, 2) for activity, percent in sorted_activities[:5]}
        }

        feedback_input("Does the above visualization reflect your experience?", "feedback_relative_activity_frequency")

    except Exception as e:
        st.warning(f"Could not render activity frequencies: {e}")

# Generating absolute case frequency plot within frequency & distribution analysis
def plot_absolute_case_frequency(df, case_id_key, activity_key, timestamp_key, viz_summary):
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
            ax.set_title("Absolute Case Frequency Histogram (showing the most frequent cases in the log)")
        else:
            ax.set_title("Absolute Case Frequency Histogram (showing 80% of cases in the log)")
        plt.xticks(rotation=45, ha="right")
        st.pyplot(fig)

        st.markdown("### Legend")
        for label, variant in variant_mapping.items():
            st.markdown(f"**{label}**: {', '.join(variant)}")

        viz_summary["absolute_case_frequency_graph"] = {
            "type": "bar_chart",
            "title": "Top 80% Frequent Case Variants",
            "x_axis": "Variants",
            "y_axis": "Frequency",
            "top_variants": {label: variant for label, variant in list(variant_mapping.items())[:5]}
        }
        feedback_input("Does the above visualization reflect your experience?", "feedback_absolute_case_frequency")
    except Exception as e:
        st.warning(f"Could not render case frequency graph: {e}")

# Generating relative case frequency plot within frequency & distribution analysis
def plot_relative_case_frequency(df, case_id_key, activity_key, timestamp_key, viz_summary):
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
            ax.set_title("Relative Case Frequency Histogram (showing the most frequent cases in the log)")
        else:
            ax.set_title("Relative Case Frequency Histogram (showing 80% of cases in the log)")
        plt.xticks(rotation=45, ha="right")
        st.pyplot(fig)

        st.markdown("### Legend")
        for label, variant in variant_mapping.items():
            st.markdown(f"**{label}**: {', '.join(variant)}")

        viz_summary["relative_case_frequency_graph"] = {
            "type": "bar_chart",
            "title": "Top 80% Case Variants by Relative Frequency",
            "x_axis": "Variants",
            "y_axis": "Relative Frequency (%)",
            "top_variants": {
                label: {
                    "activities": variant,
                    "percentage": y_values[i]
                }
                for i, (label, variant) in enumerate(list(variant_mapping.items())[:5])
            }
        }

        feedback_input("Does the above visualization reflect your experience?", "feedback_relative_case_frequency")

    except Exception as e:
        st.warning(f"Could not render relative case frequencies: {e}")

# Generating case length distribution plot within frequency & distribution analysis
def plot_case_length_distribution(df, case_id_key, activity_key, timestamp_key, viz_summary):
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
            hidden_lengths_counts = sorted_lengths_counts[max_lengths:]
            shown_case_total = sum([count for _, count in shown_lengths_counts])
            hidden_percentage = round((1 - shown_case_total / total_cases) * 100, 2)
        else:
            shown_lengths_counts = sorted_lengths_counts
            hidden_percentage = 0.0

        sorted_lengths = [length for length, _ in shown_lengths_counts]
        counts = [count for _, count in shown_lengths_counts]

        plt.figure(figsize=(10, 6))
        plt.bar(sorted_lengths, counts, color='skyblue', edgecolor='black')
        plt.xlabel("Number activities per case")
        plt.ylabel("Number Cases")
        plt.title("Distribution of number of activities per case")
        plt.xticks(sorted_lengths)
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        st.pyplot(plt)

        if hidden_percentage > 0:
            st.caption(f"{hidden_percentage}% of cases with less frequent case lengths are not shown in the plot.")

        viz_summary["case_length_distribution_graph"] = {
            "type": "bar_chart",
            "title": "Distribution of Case Lengths",
            "x_axis": "Number of Activities per Case",
            "y_axis": "Number of Cases",
            "max_case_length": max(counts),
            "min_case_length": min(counts)
        }
        feedback_input("Does the above visualization reflect your experience?", "feedback_case_length_distribution")
    except Exception as e:
        st.warning(f"Could not render the case length distribution graph: {e}")

    st.session_state.viz_data = viz_summary

# Generating absolute resource frequency plot within resource analysis
def plot_absolute_resource_frequency(df, resource_key, viz_summary):
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
        ax.set_title("Absolute Frequency of Resources")
        st.pyplot(fig)

        if hidden_resources:
            hidden_text = ", ".join([f"{res} ({count})" for res, count in hidden_resources])
            st.caption(f"Not shown in chart: {hidden_text}")

        viz_summary["resource_frequency_absolute"] = {
            "type": "bar_chart",
            "title": "Absolute Frequency of Resources",
            "x_axis": "Resources",
            "y_axis": "Frequency",
            "top_resources": dict(sorted_resources[:5])
        }

        feedback_input("Does the above visualization reflect your experience?", "feedback_absolute_resource_frequency")

    except Exception as e:
        st.warning(f"Could not render absolute resource frequencies: {e}")

# Generating relative resource frequency plot within resource analysis
def plot_relative_resource_frequency(df, resource_key, viz_summary):
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
        ax.set_title("Relative Frequency of Resources")
        st.pyplot(fig)

        if hidden_resources:
            hidden_text = ", ".join([f"{res} ({round(freq, 2)}%)" for res, freq in hidden_resources])
            st.caption(f"Not shown in chart: {hidden_text}")

        viz_summary["relative_resource_frequency"] = {
            "type": "bar_chart",
            "title": "Relative Frequency of Resources",
            "x_axis": "Resources",
            "y_axis": "Relative Frequency (%)",
            "top_resources": {res: round(p, 2) for res, p in sorted_resources[:5]}
        }

        feedback_input("Does the above visualization reflect your experience?", "feedback_relative_resource_frequency")

    except Exception as e:
        st.warning(f"Could not render relative resource frequencies: {e}")

# Generating events per time plot within temporal analysis
def plot_events_per_time_graph(df, case_id_key, activity_key, timestamp_key, viz_summary):
    try: 
        pm4py.vis.save_vis_events_per_time_graph(
            df,
            file_path = 'events_per_time_graph.png',
            case_id_key = case_id_key,
            activity_key = activity_key,
            timestamp_key = timestamp_key
        )

        st.image('events_per_time_graph.png', caption= 'Events over Time')
        viz_summary["events_per_time_graph"] = {
            "type": "image",
            "title": "Events over time",
            "x_axis": "Time",
            "y_axis": "Number of Events",
            "description": "Shows how many events occurred over time."
        }
        feedback_input("Does the above visualization reflect your experience?", "feedback_events_per_time_graph")
    except Exception as e:
        st.warning(f"Could not render events per time graph: {e}")

# Generating event distribution plot within temporal analysis
def plot_event_distribution_graphs(df, case_id_key, activity_key, timestamp_key, viz_summary):
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
            file_path = f"event_distribution_{distr_type}.svg"
            pm4py.vis.save_vis_events_distribution_graph(
                df,
                file_path = file_path,
                activity_key = activity_key,
                case_id_key = case_id_key,
                timestamp_key = timestamp_key,
                distr_type = distr_type,
            )

            st.image(file_path)

            series = None
            if distr_type == "days_week":
                series = df[timestamp_key].dt.dayofweek
                counter = Counter(series)
                mapped = {day_name_mapping[k]: v for k, v in counter.items()}
            elif distr_type == "days_month":
                series = df[timestamp_key].dt.day
                mapped = dict(Counter(series))
            elif distr_type == "months":
                series = df[timestamp_key].dt.month
                mapped = dict(Counter(series))
            elif distr_type == "years":
                series = df[timestamp_key].dt.year
                mapped = dict(Counter(series))
            elif distr_type == "hours":
                series = df[timestamp_key].dt.hour
                mapped = dict(Counter(series))
            elif distr_type == "weeks":
                # TODO: Search is isocalendar() starts with 0
                series = df[timestamp_key].dt.isocalendar().week
                mapped = dict(Counter(series))

            viz_summary[f"event_distribution_{distr_type}"] = {
                "event_distribution_values": mapped,
                "x_axis": distr_type.replace("_", " ").title(),
                "y_axis": "Number of Events",
                "description": f"Distribution of events by {distr_type.replace('_', ' ')}."
            }

            feedback_input(f"Does the above visualization reflect your experience?",
                f"feedback_event_distribution_{distr_type}")
                
        except Exception as e:
            st.warning(f"Could not render event distribution graph for '{distr_type}': {e}")

# Generating dotted chart plot within temporal analysis
def plot_dotted_chart(df, case_id_key, activity_key, timestamp_key, viz_summary):
    
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
    # TODO: Metadaten aus Dotted Chart ziehen
    file_path = f"dotted_chart.svg"
    pm4py.vis.save_vis_dotted_chart(
        filtered_df,
        file_path = file_path,
        activity_key = activity_key,
        case_id_key = case_id_key,
        timestamp_key = timestamp_key,
    )

    st.image(file_path)

# Generating case duration plot within performance analysis
def plot_case_duration_graph(case_id_key, activity_key, timestamp_key, viz_summary):
    try:
        df_raw = pm4py.format_dataframe(st.session_state.df_raw, case_id = case_id_key, activity_key = activity_key, timestamp_key= timestamp_key)
        # TODO: Adjust the x-axis as it is represented on a second level -> Maybe adjust to week level? 
        pm4py.vis.save_vis_case_duration_graph(
            df_raw,
            file_path = 'case_duration_graph.png',
            activity_key = activity_key,
            case_id_key = case_id_key,
            timestamp_key = timestamp_key
        )
        st.image('case_duration_graph.png', caption = 'Case durations within the data')
        # TODO: Extract metadata from the visualization
        viz_summary["case_duration_graph"] = {
            "type": "image",
            "title": "Case durations",
            "x_axis": "Cases",
            "y_axis": "Duration",
            "description": "Distribution of case durations."
        }
        feedback_input("Does the above visualization reflect your experience?", "feedback_case_duration")
    except Exception as e:
        st.warning (f"Could not render the case duration graph: {e}")

# Generating case duration plot within performance analysis
def retrieve_max_min_avg_case_duration(case_id_key, activity_key, timestamp_key, viz_summary):
    
    df_raw = pm4py.format_dataframe(st.session_state.df_raw, case_id = case_id_key, activity_key = activity_key, timestamp_key= timestamp_key)
    performance_summary_stats = {}

    case_durations = pm4py.stats.get_all_case_durations(
        df_raw,
        activity_key = activity_key,
        case_id_key = case_id_key,
        timestamp_key = timestamp_key
    )

    case_durations = np.array(case_durations)

    # TODO: Add case differentiation where the format of the case duration is chosen (e.g., second-level, minute-level etc.)
    case_durations_hours = case_durations/3600
    case_durations_days = case_durations_hours/24

    min_length = case_durations_days.min()
    min_length = np.round(min_length, 2)
    performance_summary_stats['Minimum Case Length [Day]'] = min_length
    max_length = case_durations_days.max()
    max_length = np.round(max_length, 2)
    performance_summary_stats['Maximum Case Length [Day]'] = max_length
    avg_length = case_durations_days.mean()
    avg_length = np.round(avg_length, 2)
    performance_summary_stats['Average Case Length [Day]'] = avg_length
    std_length = case_durations_days.std()
    std_length = np.round(std_length, 2) 
    performance_summary_stats['Standard Deviation Case Length [Day]'] = std_length


    viz_summary["case_duration_facts"] = {
        "minimum case length": min_length,
        "maximum case length": max_length, 
        "average case length": avg_length,
        "standard deviation case length": std_length
    }

    performance_summary_df = pd.DataFrame(list(performance_summary_stats.items()), columns =["Statistic", "Value"])

    return performance_summary_df

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

    plt.figure(figsize=(12, 8))
    sns.heatmap(heatmap_percent, annot=True, fmt=".1f", cmap="YlGnBu", linewidths=0.5, cbar_kws={'label': 'Activity share (%)'})
    plt.xlabel("Resource")
    plt.ylabel("Activity")
    plt.title("Heatmap: Activity-Resource Distribution (%)")
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    st.pyplot(plt)

    feedback_input("Does the above visualization reflect your experience?", "feedback_task_responsibility_overview")

# Run all the visualizations
def run_visualizations(df, case_id_key, activity_key, timestamp_key, resource_key):

    # --- Summary statistics ---
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
        st.dataframe(summary_df, hide_index = True, use_container_width=True)
        feedback_input("Do the above statistics reflect your experience?", "feedback_summary_statistics")


    # --- Frequency & distribution analysis ---
    with st.expander("🔁 Frequency & Distribution Analysis"):
        plot_absolute_activity_frequency(df, activity_key, viz_summary)
        plot_relative_activity_frequency(df, activity_key, viz_summary)
        plot_absolute_case_frequency(df, case_id_key, activity_key, timestamp_key, viz_summary)
        plot_relative_case_frequency(df, case_id_key, activity_key, timestamp_key, viz_summary)
        plot_case_length_distribution(df, case_id_key, activity_key, timestamp_key, viz_summary)

    # --- Temporal analysis ---
    with st.expander("🕒 Temporal Analysis"):
        plot_events_per_time_graph(df, case_id_key, activity_key, timestamp_key, viz_summary)
        plot_event_distribution_graphs(df, case_id_key, activity_key, timestamp_key, viz_summary)
        # plot_dotted_chart(df, case_id_key, activity_key, timestamp_key, viz_summary)
    
    # --- Performance analysis ---
    with st.expander("⚡ Performance Analysis"):
        performance_summary_df = retrieve_max_min_avg_case_duration(case_id_key, activity_key, timestamp_key, viz_summary)
        st.dataframe(performance_summary_df, hide_index = True, use_container_width = True)
        plot_case_duration_graph(case_id_key, activity_key, timestamp_key, viz_summary)

    # --- Resource analysis ---
    with st.expander("👥 Resource analysis"):
        plot_absolute_resource_frequency(df, resource_key, viz_summary)
        plot_relative_resource_frequency(df, resource_key, viz_summary)
        plot_task_responsbility_overview(df, activity_key, resource_key)


    