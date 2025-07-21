import os
import pandas as pd
import streamlit as st
import google.generativeai as genai
from autogen.agentchat import (
    AssistantAgent,
    UserProxyAgent,
    GroupChat,
    GroupChatManager,
)
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in environment variables.")

genai.configure(api_key=api_key)

def gemini_call(prompt, model_name="models/gemini-1.5-flash"):
    return genai.GenerativeModel(model_name).generate_content(prompt).text

# ===== Agent Definitions =====
class DataPrepAgent(AssistantAgent):
    def generate_reply(self, messages, sender, config=None):
        df = st.session_state["df"]
        prompt = f"""You are a Data Cleaning Agent.
- Handle missing values
- Fix data types
- Remove duplicates

Dataset head:
{df.head().to_string()}

Summary stats:
{df.describe(include='all').to_string()}

Return Python code for preprocessing and a short explanation."""
        return gemini_call(prompt)

class EDAAgent(AssistantAgent):
    def generate_reply(self, messages, sender, config=None):
        df = st.session_state["df"]
        prompt = f"""You are an EDA Agent.
- Provide summary statistics
- Extract at least 3 insights
- Suggest visualizations

Dataset head:
{df.head().to_string()}"""
        return gemini_call(prompt)

class ReportGeneratorAgent(AssistantAgent):
    def generate_reply(self, messages, sender, config=None):
        insights = st.session_state.get("eda_output", "")
        prompt = f"""You are a Report Generator.
Create a clean EDA report based on insights:

{insights}

Include:
- Overview
- Key Findings
- Visual Suggestions
- Summary conclusion."""
        return gemini_call(prompt)

class CriticAgent(AssistantAgent):
    def generate_reply(self, messages, sender, config=None):
        report = st.session_state.get("report_output", "")
        prompt = f"""You are a Critic Agent.
Review the EDA report:

{report}

Comment on clarity, accuracy, completeness, and suggest improvements."""
        return gemini_call(prompt)

class ExecutorAgent(AssistantAgent):
    def generate_reply(self, messages, sender, config=None):
        code = st.session_state.get("prep_output", "")
        prompt = f"""You are an Executor Agent.
Validate the following data preprocessing code:

{code}

- Is it runnable?
- Suggest corrections if needed."""
        return gemini_call(prompt)

# ===== Admin / Proxy Agent =====
admin_agent = UserProxyAgent(
    name="Admin",
    human_input_mode="NEVER",
    code_execution_config=False  # disables Docker requirement
)

# ===== Custom CSS for Modern Look =====
custom_css = """
<style>
body, .stApp {
    background: linear-gradient(135deg, #232526 0%, #414345 100%);
    color: #f3f3f3;
}

/* Sidebar styling */
[data-testid="stSidebar"] {
    background: #1e2a38;
    color: #f3f3f3;
}

/* Main title */
.st-emotion-cache-10trblm {
    color: #00c6fb;
    font-weight: 700;
    letter-spacing: 1px;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(90deg, #00c6fb 0%, #005bea 100%);
    color: white;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    padding: 0.5em 2em;
    margin-top: 1em;
    transition: background 0.3s;
}
.stButton > button:hover {
    background: linear-gradient(90deg, #005bea 0%, #00c6fb 100%);
}

/* Expander headers */
.st-expanderHeader {
    background: #232526;
    color: #00c6fb;
    font-weight: 600;
    border-radius: 6px;
}

/* Dataframe preview */
.stDataFrame {
    background: #232526;
    color: #f3f3f3;
    border-radius: 8px;
}

/* Info and success boxes */
.stAlert {
    border-radius: 8px;
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# ===== Streamlit UI (Redesigned) =====
st.set_page_config(layout="wide", page_title="Agentic EDA Redesign", page_icon="🦄")

with st.sidebar:
    st.image(
        "https://images.unsplash.com/photo-1465101046530-73398c7f28ca?auto=format&fit=crop&w=400&q=80",
        use_column_width=True,
    )
    st.title("🦄 EDA Multi-Agent")
    st.markdown(
        """
        <div style='font-size: 1.1em;'>
        <b>Welcome!</b> Upload your CSV and let our AI agents do the rest.<br>
        <span style='color:#00c6fb;'>Modern, fast, and unique.</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("---")
    st.info("Step 1: Upload your CSV file.\nStep 2: Click 'Run EDA'.\nStep 3: Explore the results!", icon="📋")
    st.markdown("---")
    st.caption("Powered by Gemini + Autogen")

st.title("Agentic EDA Platform 🦄")
st.markdown(
    "<div style='font-size:1.2em; margin-bottom:1em;'>A modern, multi-agent system for Exploratory Data Analysis.\nUpload your data and get instant, AI-powered insights!</div>",
    unsafe_allow_html=True,
)

uploaded = st.file_uploader("Upload CSV File", type=["csv"])
if uploaded:
    df = pd.read_csv(uploaded)
    st.session_state["df"] = df
    st.subheader("Raw Dataset Preview")
    st.dataframe(df.head(), use_container_width=True, hide_index=True)

    run_eda = st.button("Run EDA 🚀")
    if run_eda:
        with st.spinner("Initializing agents and analyzing data..."):
            agents = [
                admin_agent,
                DataPrepAgent(name="DataPrep"),
                EDAAgent(name="EDA"),
                ReportGeneratorAgent(name="ReportGen"),
                CriticAgent(name="Critic"),
                ExecutorAgent(name="Executor"),
            ]
            chat = GroupChat(agents=agents, messages=[])
            manager = GroupChatManager(groupchat=chat)

        with st.spinner("Running multi-agent system..."):
            # ===== Data Preparation Output =====
            prep = agents[1].generate_reply([], "Admin")
            st.session_state["prep_output"] = prep
            with st.expander("🧹 Data Preparation Output", expanded=True):
                st.markdown("**Python Code:**")
                st.code(prep, language="python")

            # ===== EDA Agent Output =====
            eda_out = agents[2].generate_reply([], "Admin")
            st.session_state["eda_output"] = eda_out
            with st.expander("📊 EDA Insights", expanded=True):
                st.markdown(eda_out)

            # ===== Report Generation =====
            report = agents[3].generate_reply([], "Admin")
            st.session_state["report_output"] = report
            with st.expander("📄 EDA Report", expanded=True):
                st.markdown(report)

            # ===== Critic Feedback =====
            critique = agents[4].generate_reply([], "Admin")
            with st.expander("🧐 Critic Agent Feedback", expanded=False):
                st.markdown(critique)

            # ===== Code Execution Check =====
            exec_feedback = agents[5].generate_reply([], "Admin")
            with st.expander("✅ Executor Agent Validation", expanded=False):
                st.markdown(exec_feedback)

        st.success("✔️ Agentic EDA completed successfully.")
else:
    st.info("Upload a CSV file in the sidebar to begin.")
