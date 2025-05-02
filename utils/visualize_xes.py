import streamlit as st
import matplotlib.pyplot as plt
import pm4py
import pandas as pd
from collections import Counter

def run_visualizations(df, case_id_key, activity_key, timestamp_key):

    # TODO: Establish hierarchy in the feedbacks session state and include the checkbox input there next to the textual input 
    # if "checkbox_input" not in st.session_state:
    #     st.session_state.checkbox_inputs = {}
    
    if "feedbacks" not in st.session_state:
        st.session_state.feedbacks = {}
    
    # TODO: Why is viz_data red?
    if "viz_data" not in st.session_state:
        st.session_state.viz_data = {}
    viz_summary = {}

    # def checkbox_input(label, value):
    #     st.checkbox(
    #         label=label,
    #         value=False
    #     )

    def feedback_input(label, key):
        st.text_area(
            label=label,
            key=key,
            height=100,
            placeholder="Please share your thoughts..."
        )
    
    # --- Summary statistics ---
    # TODO: Include further relevant summary statistics
    summary_stats = {}

    # TODO: Shift to frequency and distribution analysis
    activity_counts = df[activity_key].value_counts()
    activity_summary_str = ";".join([f"{activity}: {count}" for activity, count in activity_counts.items()])
    summary_stats["Distinct activities and their number"] = activity_summary_str

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
    summary_stats['Time Horizon'] = f"{start_time} - {end_time}"

    # TODO: Shift to discovery
    start_activities = pm4py.get_start_activities(
        df,
        activity_key= activity_key,
        case_id_key = case_id_key,
        timestamp_key = timestamp_key
    )

    sorted_starts = sorted(start_activities.items(), key = lambda x: x[1], reverse = True)

    total_starts = sum(start_activities.values())

    most_frequent_start = max(start_activities, key = start_activities.get)
    probability = start_activities[most_frequent_start] / total_starts
    
    for i, (event, count) in enumerate(sorted_starts[:3], start=1):
        probability = count / total_starts
        summary_stats[f"Typical starting event #{i}"] = f"{event}: {probability:.2%}"

    # TODO: Shift to discovery
    end_activities = pm4py.get_end_activities(
        df,
        activity_key= activity_key,
        case_id_key = case_id_key,
        timestamp_key = timestamp_key
    )   

    sorted_ends = sorted(end_activities.items(), key = lambda x: x[1], reverse = True)

    total_ends = sum(end_activities.values())

    most_frequent_end = max(end_activities, key = end_activities.get)
    probability_end = end_activities[most_frequent_end] / total_ends

    for i, (event,count) in enumerate(sorted_ends[:3], start = 1):
        probability_end = count / total_ends
        summary_stats[f"Typical ending event #{i}"] = f"{event}: {probability_end:.2%}"

    summary_df = pd.DataFrame(list(summary_stats.items()), columns=["Statistic", "Value"])
    with st.expander("📊 Show Summary Statistics"):
        st.dataframe(summary_df, hide_index = True)

    # --- Event Distribution Graphs ---
    
    distr_types = [
    "days_week",    # 0 = Monday, ..., 6 = Sunday
    "days_month",   # 1–31
    "months",       # 1–12
    "years",        # Event-Jahre
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
    with st.expander("Show Event Distribution Visualizations"):
        for distr_type in distr_types:
            try:
                file_path = f"event_distribution_{distr_type}.svg"
                pm4py.vis.save_vis_events_distribution_graph(
                    df,
                    file_path=file_path,
                    activity_key='Activity',
                    case_id_key='Case ID',
                    timestamp_key='Complete Timestamp',
                    distr_type=distr_type,
                )

                st.image(file_path) #caption=f'Event Distribution by {distr_type.replace("_", " ").title()}')

                # Extract metadata
                series = None
                if distr_type == "days_week":
                    series = df['Complete Timestamp'].dt.dayofweek
                    counter = Counter(series)
                    mapped = {day_name_mapping[k]: v for k, v in counter.items()}
                elif distr_type == "days_month":
                    series = df['Complete Timestamp'].dt.day
                    mapped = dict(Counter(series))
                elif distr_type == "months":
                    series = df['Complete Timestamp'].dt.month
                    mapped = dict(Counter(series))
                elif distr_type == "years":
                    series = df['Complete Timestamp'].dt.year
                    mapped = dict(Counter(series))
                elif distr_type == "hours":
                    series = df['Complete Timestamp'].dt.hour
                    mapped = dict(Counter(series))
                elif distr_type == "weeks":
                    series = df['Complete Timestamp'].dt.isocalendar().week
                    mapped = dict(Counter(series))

                viz_summary[f"event_distribution_{distr_type}"] = {
                    "event_distribution_values": mapped,
                    "x_axis": distr_type.replace("_", " ").title(),
                    "y_axis": "Number of Events",
                    "description": f"Distribution of events by {distr_type.replace('_', ' ')}."
                }

                # checkbox_input()

                feedback_input(f"Does the visualization for {distr_type.replace('_', ' ')} reflect your experience?",
                        f"feedback_event_distribution_{distr_type}")
                
            except Exception as e:
                st.warning(f"Could not render event distribution graph for '{distr_type}': {e}")
    
    # --- Events per Time Graph ---
    st.subheader("Events per time graph")

    try: 
        pm4py.vis.save_vis_events_per_time_graph(
            df,
            file_path = 'events_per_time_graph.png',
            activity_key = 'Activity',
            case_id_key = 'Case ID',
            timestamp_key = 'Complete Timestamp'
        )
        st.image('events_per_time_graph.png', caption= 'Events over Time')
        viz_summary["events_per_time_graph"] = {
            "type": "image",
            "title": "Events over time",
            "x_axis": "Time",
            "y_axis": "Number of Events",
            "description": "Shows how many events occurred over time."
        }
        feedback_input("Does the visualization reflect your experience?", "feedback_events_per_time_graph")
    except Exception as e:
        st.warning(f"Could not render events per time graph: {e}")

    # --- Activity Frequency Graph ---
    # TODO: Check logic here
    st.subheader("Activity frequency graph (absolute)")
    try:
        activity_counts = Counter(df['Activity'])
        activities = list(activity_counts.keys())
        frequencies = list(activity_counts.values())
        fig, ax = plt.subplots(figsize = (10,5))
        ax.bar(activities, frequencies, color = "skyblue", edgecolor = 'black')
        ax.set_xlabel('Activities')
        ax.set_ylabel('Frequencies')
        ax.set_title('Activity frequency histogram')
        plt.xticks(rotation=45)
        st.pyplot(fig)
        viz_summary["activity_frequency_graph"] = {
            "type": "bar_chart",
            "title": "Activity frequency histogram",
            "x_axis": "Activities",
            "y_axis": "Frequencies",
            "top_activities": dict(sorted(activity_counts.items(), key=lambda x: x[1], reverse=True)[:5])
        }
        feedback_input("Does the visualization reflect your experience?", "feedback_activity_frequency")
    except Exception as e:
        st.warning(f"Could not render activity frequencies: {e}")  

    # --- Case Frequency Statistic ---
    # TODO: Show only some cases of the population (e.g., the top 20%)
    st.subheader("Case frequency statistic")
    try:
        variants = pm4py.get_variants(
            df,
            activity_key= 'Activity',
            case_id_key = 'Case ID',
            timestamp_key = 'Complete Timestamp'
        )

        min_threshold = 2
        grouped_dict = {}
        other_count = 0

        for variant, count in variants.items():
            if count < min_threshold:
                other_count += count
            else:
                grouped_dict[variant] = count

        if other_count > 0:
            grouped_dict[("Other (count < 2)")] = other_count

        # Sorting for frequency
        sorted_variants = sorted(grouped_dict.items(), key=lambda x: x[1], reverse=True)

        # Prepare x and y axis data
        x_labels = [f"Variant_{i+1}" for i in range(len(sorted_variants))]
        y_values = [count for _, count in sorted_variants]
        variant_mapping = dict(zip(x_labels, [variant for variant, _ in sorted_variants]))

        fig, ax = plt.subplots(figsize=(12, 6))
        ax.bar(x_labels, y_values, color="cornflowerblue")
        ax.set_xlabel("Variants (sorted by frequency)")
        ax.set_ylabel("Frequency")
        ax.set_title("Frequencies of Case Variants")
        plt.xticks(rotation=45, ha="right")

        st.pyplot(fig)

        st.markdown("### Legend")
        for label, variant in variant_mapping.items():
            st.markdown(f"**{label}**: {', '.join(variant)}")
        viz_summary["case_frequency_graph"] = {
            "type": "bar_chart",
            "title": "Frequencies of Case Variants",
            "x_axis": "Variants",
            "y_axis": "Frequency",
            "top_variants": {label: variant for label, variant in list(variant_mapping.items())[:5]}
        }
        feedback_input("Does the visualization reflect your experience?", "feedback_case_frequency")
    except Exception as e:
        st.warning (f"Could not render case frequency graph: {e}")

    # --- Case Duration Graph ---
    # TODO: Adjust the x-axis as it is represented on a second level -> Maybe adjust to week level? 
    st.subheader("Case duration graph")
    try:
        pm4py.vis.save_vis_case_duration_graph(
            df,
            file_path = 'case_duration_graph.png',
            activity_key = 'Activity',
            case_id_key = 'Case ID',
            timestamp_key = 'Complete Timestamp'
        )
        st.image('case_duration_graph.png', caption = 'Case durations within the data')
        viz_summary["case_duration_graph"] = {
            "type": "image",
            "title": "Case durations",
            "x_axis": "Cases",
            "y_axis": "Duration",
            "description": "Distribution of case durations."
        }
        feedback_input("Does the visualization reflect your experience?", "feedback_case_duration")
    except Exception as e:
        st.warning (f"Could not render the case duration graph: {e}")

    # --- Case Length Distribution
    #TODO: 'Dict' object is not callable -> Adjust the code
    st.subheader("Case length distribution")
    try:
        variants = pm4py.get_variants(
            df,
            activity_key= 'Activity',
            case_id_key = 'Case ID',
            timestamp_key = 'Complete Timestamp'
        )

        length_counts = variants(int)
        for variant, count in variants.items():
            length = len(variant)
            length_counts[length] += count

        sorted_lengths = sorted(length_counts.items())
        x_vals = [length for length, _ in sorted_lengths]
        y_vals = [count for _, count in sorted_lengths]

        fig, ax = plt.subplots(figsize=(10, 5))
        ax.bar(x_vals, y_vals, color='skyblue', edgecolor='black')
        ax.set_xlabel('Anzahl Aktivitäten pro Case')
        ax.set_ylabel('Anzahl der vorkommenden Cases')
        ax.set_title('Verteilung der Falllängen im Eventlog')
        plt.xticks(x_vals)
        st.pyplot(fig)
        viz_summary["case_length_distribution_graph"] = {
            "type": "bar_chart",
            "title": "Distribution of Case Lengths",
            "x_axis": "Number of Activities per Case",
            "y_axis": "Number of Cases",
            "max_case_length": max(x_vals),
            "min_case_length": min(x_vals)
        }
        feedback_input("Does the visualization reflect your experience?", "feedback_case_length_distribution")
    except Exception as e:
        st.warning(f"Could not render the case length distribution graph: {e}")

    st.session_state.viz_data = viz_summary
