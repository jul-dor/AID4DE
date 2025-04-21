# Masterthesis
Goal: Enabling interactive event data exploration for domain experts

Name of the prototype: EDE4DE (Event Data Exploration 4 Domain Experts)


Notes for set-up:
- Pfad zum virtuellen Environment und für die Aktivierung: C:\Users\julia\virtualenvs\pm\Scripts\python.exe

Execute streamlilt app:
- Example with main.py Script: streamlit run main.py

# 🤖 Streamlit prototype to enable interactive event data exploration for domain experts

This project is a prototype to support the event data exploration by domain experts built with [Streamlit](https://streamlit.io). Users can upload an event dataset and an analysis question and then interactively explore the dataset in a targeted manner to assess the representativeness of the event data. 

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/your-repo.git
cd repo
```

### 2. Set Up Virtual Environment (optional but recommended)

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install Requirements

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

This project uses a `.env` file to store sensitive keys (e.g., API keys).  
A template is provided as `.env.template`. To get started:

```bash
cp .env.template .env  # On Windows: copy .env.template .env
```

Then edit `.env` and add your values:

```env
API_KEY=your_real_api_key_here
```

---

## 💬 Usage

Run the Streamlit app locally:

```bash
streamlit run app.py
```

---

## 🛠️ Managing Dependencies

If you install new packages during development, update the `requirements.txt` file:

```bash
pip freeze > requirements.txt
```

> Make sure you are inside your virtual environment when you do this!

---

## ❗ Notes

- Do **not** commit your `.env` file – it's excluded via `.gitignore`.
- A `.env.template` file is provided to help others understand what variables they need to set.
- The chatbot logic can be extended by integrating LLM APIs like OpenAI or Claude.
- Streamlit Cloud and similar services will automatically install packages from `requirements.txt`.