import streamlit as st
import time
import google.generativeai as genai
from autogen import AssistantAgent, UserProxyAgent
from langchain_google_genai import ChatGoogleGenerativeAI
import copy
import os

# Configure Gemini API
api_key = "AIzaSyDG-0xIaprzdT70VTf-LnMt62_s-F8SJqA"
genai.configure(api_key=api_key)

# System messages
CREATOR_SYSTEM_MESSAGE = """
You are a Content Creator Agent specializing in Generative AI. Your role is to:
1. Draft clear, concise, and technically accurate content
2. Revise content based on constructive feedback
3. Structure output in markdown format
4. Focus exclusively on content creation (no commentary)
"""

CRITIC_SYSTEM_MESSAGE = """
You are a Content Critic Agent evaluating Generative AI content. Your role is to:
1. Analyze technical accuracy and language clarity
2. Provide specific, constructive feedback
3. Identify both strengths and areas for improvement
4. Maintain professional, objective tone
"""

# Custom wrapper for deepcopy compatibility
class GeminiAgent:
    def __init__(self, model, system_message):
        self.model = model
        self.system_message = system_message
    
    def generate(self, prompt):
        full_prompt = self.system_message + "\n\n" + prompt
        try:
            response = self.model.invoke(full_prompt)
            return response.content
        except Exception as e:
            return f"Error: {str(e)}"
    
    def __deepcopy__(self, memo):
        return GeminiAgent(
            model=ChatGoogleGenerativeAI(model=self.model.model, google_api_key=api_key),
            system_message=self.system_message
        )

# Initialize Gemini models through LangChain
creator_model = GeminiAgent(
    model=ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=api_key),
    system_message=CREATOR_SYSTEM_MESSAGE
)

critic_model = GeminiAgent(
    model=ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=api_key),
    system_message=CRITIC_SYSTEM_MESSAGE
)

# ===== Custom CSS for Professional Look =====
custom_css = """
<style>
body, .stApp {
    background: linear-gradient(120deg, #f8fafc 0%, #e0e7ef 100%);
    color: #222831;
}

[data-testid="stSidebar"] {
    background: #222831;
    color: #f8fafc;
}

.st-emotion-cache-10trblm {
    color: #0077b6;
    font-weight: 800;
    letter-spacing: 1px;
}

.stButton > button {
    background: linear-gradient(90deg, #0077b6 0%, #00b4d8 100%);
    color: white;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    padding: 0.5em 2em;
    margin-top: 1em;
    transition: background 0.3s;
}
.stButton > button:hover {
    background: linear-gradient(90deg, #00b4d8 0%, #0077b6 100%);
}

.st-expanderHeader {
    background: #e0e7ef;
    color: #0077b6;
    font-weight: 600;
    border-radius: 6px;
}

.stAlert {
    border-radius: 8px;
}

.role-header {
    font-size: 1.1em;
    font-weight: 700;
    padding: 10px 0 4px 0;
    color: #0077b6;
}

.creator-box {
    background: #e3f6fd;
    border-left: 6px solid #00b4d8;
    border-radius: 10px;
    padding: 18px;
    margin-bottom: 10px;
}

.critic-box {
    background: #fff4e6;
    border-left: 6px solid #ffb703;
    border-radius: 10px;
    padding: 18px;
    margin-bottom: 10px;
}

.final-box {
    background: #eafbe7;
    border-left: 6px solid #43aa8b;
    border-radius: 12px;
    padding: 22px;
    margin-bottom: 16px;
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# ===== Streamlit UI (Redesigned) =====
st.set_page_config(page_title="Agentic Content Refinement", page_icon="🧑‍💼", layout="wide")

with st.sidebar:
    st.image(
        "https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=400&q=80",
        use_column_width=True,
    )
    st.title("🧑‍💼 Content Refinement")
    st.markdown(
        """
        <div style='font-size: 1.1em;'>
        <b>Professional AI Content Workflow</b><br>
        <span style='color:#0077b6;'>Unique, modern, and plagiarism-free.</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("---")
    st.info("1. Enter your topic.\n2. Choose number of turns.\n3. Click 'Start Simulation'.", icon="📝")
    st.markdown("---")
    st.caption("Powered by Gemini + Autogen")

st.title("Agentic Content Refinement 🧑‍💼")
st.markdown(
    "<div style='font-size:1.15em; margin-bottom:1em;'>A professional, multi-agent system for content creation and critique.\nExperience a unique, iterative AI workflow!</div>",
    unsafe_allow_html=True,
)

# Controls
col1, col2 = st.columns([2, 1])
with col1:
    topic = st.text_input("Content Topic", "Agentic AI")
with col2:
    turns = st.slider("Conversation Turns", 3, 5, 3)
generate_btn = st.button("Start Simulation", use_container_width=True)

if generate_btn:
    # Create AutoGen agents with proper configuration
    creator = AssistantAgent(
        name="Creator",
        system_message=CREATOR_SYSTEM_MESSAGE,
        llm_config={
            "config_list": [
                {
                    "model": "gemini-1.5-flash",
                    "api_key": api_key,
                    "base_url": "https://generativelanguage.googleapis.com/v1beta/models/"
                }
            ],
            "timeout": 120
        },
        human_input_mode="NEVER",
        is_termination_msg=lambda x: x.get("content", "").find("TERMINATE") >= 0,
    )
    
    critic = AssistantAgent(
        name="Critic",
        system_message=CRITIC_SYSTEM_MESSAGE,
        llm_config={
            "config_list": [
                {
                    "model": "gemini-1.5-flash",
                    "api_key": api_key,
                    "base_url": "https://generativelanguage.googleapis.com/v1beta/models/"
                }
            ],
            "timeout": 120
        },
        human_input_mode="NEVER",
        is_termination_msg=lambda x: x.get("content", "").find("TERMINATE") >= 0,
    )
    
    user_proxy = UserProxyAgent(
        name="User_Proxy",
        human_input_mode="NEVER",
        max_consecutive_auto_reply=0,
        code_execution_config=False,
    )
    
    conversation_history = []
    creator_output = ""
    critic_feedback = ""
    reflections = []

    progress = st.progress(0, text="Starting conversation...")
    
    for turn in range(1, turns + 1):
        progress.progress(turn/turns, text=f"Turn {turn} of {turns}")
        if turn % 2 == 1:
            # Content Creator Turn
            with st.container():
                st.markdown(f"<div class='role-header'>📝 Content Creator (Turn {turn})</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='creator-box'>", unsafe_allow_html=True)
                if turn == 1:
                    prompt = f"Draft comprehensive content about {topic} in markdown format covering:\n- Key concepts\n- Technical foundations\n- Real-world applications\n- Future implications"
                else:
                    prompt = f"Revise this content based on the critic's feedback:\n\n{critic_feedback}\n\nCurrent content:\n{creator_output}\n\nProvide improved markdown content:"
                st.markdown("**Prompt:**")
                st.code(prompt, language="markdown")
                creator_output = creator_model.generate(prompt)
                st.markdown("**Generated Content:**")
                st.markdown(creator_output)
                st.markdown("</div>", unsafe_allow_html=True)
                conversation_history.append((f"Creator (Turn {turn})", creator_output))
                if turn > 1:
                    reflection_prompt = f"Summarize in 1-2 sentences how you improved the content based on the critic's feedback."
                    reflection = creator_model.generate(reflection_prompt + "\n\nFeedback received:\n" + critic_feedback + "\n\nRevised content:\n" + creator_output)
                    st.info(f"**Creator's Reflection:** {reflection}")
                    reflections.append((f"Creator Reflection (Turn {turn})", reflection))
        else:
            # Content Critic Turn
            with st.container():
                st.markdown(f"<div class='role-header'>🧐 Content Critic (Turn {turn})</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='critic-box'>", unsafe_allow_html=True)
                prompt = f"Evaluate this content on:\n1. Technical accuracy\n2. Clarity of explanations\n3. Depth of coverage\n4. Improvement suggestions\n\nContent:\n{creator_output}"
                st.markdown("**Prompt:**")
                st.code(prompt, language="markdown")
                critic_feedback = critic_model.generate(prompt)
                st.markdown("**Critical Feedback:**")
                st.write(critic_feedback)
                st.markdown("</div>", unsafe_allow_html=True)
                conversation_history.append((f"Critic (Turn {turn})", critic_feedback))
                if turn > 2:
                    critic_reflection_prompt = f"Did the creator address your previous feedback? Summarize in 1-2 sentences."
                    critic_reflection = critic_model.generate(critic_reflection_prompt + "\n\nPrevious feedback:\n" + conversation_history[-3][1] + "\n\nCurrent content:\n" + creator_output)
                    st.info(f"**Critic's Reflection:** {critic_reflection}")
                    reflections.append((f"Critic Reflection (Turn {turn})", critic_reflection))
        time.sleep(1)

    progress.empty()
    st.divider()
    st.subheader("✅ Final Refined Content")
    st.markdown(f"<div class='final-box'><b>Final Markdown Output:</b><br><br>{creator_output}</div>", unsafe_allow_html=True)
    
    st.divider()
    st.subheader("🗨️ Full Conversation Trace")
    for i, (role, content) in enumerate(conversation_history, 1):
        with st.expander(f"{role}"):
            st.write(content)
    if reflections:
        st.divider()
        st.subheader("🔎 Agent Reflections")
        for i, (role, reflection) in enumerate(reflections, 1):
            with st.expander(f"{role}"):
                st.write(reflection)
else:
    st.info("Enter a topic and start the simulation from the sidebar.")