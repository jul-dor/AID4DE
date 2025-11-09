import streamlit as st

st.set_page_config(page_title="Manual", layout="wide")
st.title("📘 AID4DE Manual")

st.markdown("""
Welcome to **AID4DE (Artificial Intelligence-Assisted Data Validation For Domain Experts)** —  
a Streamlit-based tool for *interactive validation and exploration of event logs* in **Process Mining**.

By combining **Process Mining techniques** with **Generative AI**, AID4DE enables **domain experts** without deep technical expertise to:
- explore event log data interactively,  
- assess its **fitness for purpose**, and  
- generate **data validation reports** in an intuitive, explainable way.

---

## 🎯 Purpose of the Tool

**AID4DE** is designed to:
- Empower domain experts to explore event logs through natural language interaction.
- Provide automated visualizations that uncover patterns, frequencies, and process behaviors.
- Facilitate data quality validation and documentation of findings.
- Build a bridge between domain knowledge and process mining analytics.

The tool operates on event logs that comply with the structural requirements of process mining algorithms.

---

## 🧭 Overview of the Workflow

Below is a step-by-step guide to navigate through the six main pages of the app.

### 1️⃣ **Welcome**
- Upload your **event log** (XES format required).  
- Enter a **natural language question or objective** guiding the analysis.  
- The tool validates your input and prepares the data for exploration.

### 2️⃣ **Initial Data Exploration**
- Generates a **set of predefined visualizations** automatically, including activity, resource, and case distributions.
- Allows you to provide **qualitative feedback** directly below each visualization.
- This stage establishes a **first understanding** of your dataset.

### 3️⃣ **Initial Process Exploration**
- Focuses on **process-centric views** derived from the event log.
- Enables adjustment of parameters such as the **variant coverage threshold** to refine process discovery.
- Supports deeper insight into workflow variability and dominant paths.

### 4️⃣ **Interactive Event Log Exploration**
- Uses AI-based recommendations to propose **additional, targeted visualizations**.
- Helps identify anomalies, inconsistencies, or patterns that affect **data validity**.
- Allows on-demand generation of visuals based on your follow-up questions.

### 5️⃣ **PDF Export**
- Compiles your **visualizations and written feedback** into a structured report.  
- The export includes all generated images and annotations for easy sharing and documentation.  
- You can download the report as a **timestamped PDF** titled *“Data Validation Report”*.

### 6️⃣ **Manual (this page)**
- Provides background information and usage guidance for all features.
- You can return here at any time during the analysis for reference.

---

## 🧩 Key Concepts

- **Event Log:** A structured dataset capturing events, each linked to a case (process instance), activity, timestamp, and resource.  
- **Variant:** A unique sequence of activities representing a particular process path.  
- **Fitness for Purpose:** The degree to which the event log accurately reflects relevant aspects of the underlying business processes and thus supports the analytical objectives defined during the planning phase --- typically formalized as an Analysis Question.

---

## 💬 AI Chat Assistant

Throughout the exploration pages, an integrated **AI assistant**:
- Answers natural language questions about your data and visualizations.
- Provides context-aware explanations based on the metadata of the generated plots.
- Updates its understanding dynamically as new visualizations and feedback are added.

You can use it to ask:
> “Which activities occur most frequently?”  
> “How balanced is the resource workload?”  
> “Are there any process variants that dominate the event log?”

---

## 🧾 Tips for Effective Use

- Always ensure your uploaded event log contains **case ID**, **activity** and **timestamp** attributes.
- Use short, precise questions for best AI responses.
- Provide written feedback under each visualization to enrich the later report.
- You can regenerate the PDF export at any time — it will include all new visuals and feedback.

---

## 📚 Learn More

To learn more about Process Mining or the AID4DE approach:
- [Process Mining Manifesto (IEEE Task Force)](https://www.tfpm.org/manifesto/)
- [PM4Py Python Library Documentation](https://pm4py.fit.fraunhofer.de/)
            
---

**Enjoy exploring and validating your event data with AID4DE! 🚀**
""")
