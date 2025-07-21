import os
import streamlit as st
from dotenv import load_dotenv
from PIL import Image
import tempfile
import json
import google.generativeai as genai
from autogen.agentchat import UserProxyAgent, AssistantAgent, GroupChat, GroupChatManager

# Load API Key
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("models/gemini-1.5-flash")

# ===== Custom CSS for Professional Look =====
custom_css = """
<style>
body, .stApp {
    background: linear-gradient(120deg, #f6f7fb 0%, #e3eafc 100%);
    color: #1a2636;
}
[data-testid="stSidebar"] {
    background: #0f3057;
    color: #f6f7fb;
}
.st-emotion-cache-10trblm {
    color: #008891;
    font-weight: 800;
    letter-spacing: 1px;
}
.stButton > button {
    background: linear-gradient(90deg, #008891 0%, #00587a 100%);
    color: white;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    padding: 0.5em 2em;
    margin-top: 1em;
    transition: background 0.3s;
}
.stButton > button:hover {
    background: linear-gradient(90deg, #00587a 0%, #008891 100%);
}
.card {
    background: #f6f7fb;
    border-radius: 18px;
    box-shadow: 0 2px 12px rgba(44, 62, 80, 0.07);
    padding: 2.5rem 2.5rem 1.5rem 2.5rem;
    min-width: 350px;
    max-width: 600px;
    width: 100%;
    margin: 0 auto 1.5rem auto;
}
.result-box {
    background: #eafbe7;
    border-left: 6px solid #43aa8b;
    border-radius: 12px;
    padding: 22px;
    margin-bottom: 16px;
}
.section-header {
    background: linear-gradient(90deg, #008891 0%, #00587a 100%);
    color: white;
    padding: 1rem;
    border-radius: 10px;
    margin: 1rem 0;
    text-align: center;
}
.agent-log {
    background: #f1f1f1;
    color: #1a2636;
    border-radius: 10px;
    padding: 12px 18px;
    margin-bottom: 10px;
    font-size: 1.02em;
}
.user-log {
    background: #e0f7fa;
    color: #1a2636;
    border-radius: 10px;
    padding: 12px 18px;
    margin-bottom: 10px;
    font-size: 1.02em;
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

st.set_page_config(page_title="Bill Management Agent Pro", layout="wide", page_icon="🧾")

with st.sidebar:
    st.image(
        "https://images.unsplash.com/photo-1515378791036-0648a3ef77b2?auto=format&fit=crop&w=400&q=80",
        use_column_width=True,
    )
    st.title("🧾 Bill Management Pro")
    st.markdown(
        """
        <div style='font-size: 1.1em;'>
        <b>AI-Powered Bill Analysis</b><br>
        <span style='color:#008891;'>Modern, unique, and professional.</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("---")
    st.markdown("### 📝 How it Works")
    st.markdown("""
    1. **Upload your bill image**
    2. **AI extracts and categorizes expenses**
    3. **Get a summary and agent chat log**
    """)
    st.markdown("---")
    st.caption("Powered by Gemini + Autogen")

st.markdown("""
<div class="section-header">
    <h1>🧾 AI Bill Management Agent Pro</h1>
    <p style="font-size: 1.2rem; opacity: 0.9;">Automated Expense Categorization & Analysis</p>
</div>
""", unsafe_allow_html=True)

# --- Upload File Card ---
st.markdown('<div class="card">', unsafe_allow_html=True)
uploaded_file = st.file_uploader("📤 Upload your bill", type=["jpg", "jpeg", "png"])
st.markdown('</div>', unsafe_allow_html=True)

chat_log = []

# --- Gemini Vision to extract expense categories ---
def process_bill_with_gemini(image_file):
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(image_file.read())
        tmp_path = tmp.name
    image = Image.open(tmp_path)
    response = model.generate_content([
        "Extract all expenses from this bill image. Group them into categories: Groceries, Dining, Utilities, Shopping, Entertainment, Others. Return as JSON format like {category: [{item, cost}]}",
        image
    ])
    try:
        text = response.text.strip()
        json_start = text.find("{")
        json_end = text.rfind("}") + 1
        data = json.loads(text[json_start:json_end])
        return data, response.text
    except Exception as e:
        return None, response.text

# --- Gemini Summary ---
def summarize_expenses_with_gemini(expenses):
    prompt = (
        f"Given the following categorized expenses: {expenses}, "
        "summarize the total expenditure, show each category total, and mention which category has the highest cost and why it could be unusual."
    )
    response = model.generate_content(prompt)
    return response.text.strip()

# --- AutoGen Agents (no Docker, Gemini only) ---
user_proxy = UserProxyAgent(
    name="UserProxy",
    human_input_mode="NEVER",
    code_execution_config={"use_docker": False},
    llm_config=False
)

bill_processing_agent = AssistantAgent(
    name="BillProcessingAgent",
    llm_config=False,
    system_message="You categorize expenses from a bill into standard categories."
)

summary_agent = AssistantAgent(
    name="ExpenseSummarizationAgent",
    llm_config=False,
    system_message="You analyze categorized expenses and summarize trends."
)

group_chat = GroupChat(agents=[user_proxy, bill_processing_agent, summary_agent])
manager = GroupChatManager(groupchat=group_chat)

# --- Main Execution Flow ---
if uploaded_file:
    st.success("✅ File uploaded. Processing...")
    with st.spinner("🔍 Extracting expenses..."):
        categorized_data, raw_response = process_bill_with_gemini(uploaded_file)
    if not categorized_data:
        st.error("❌ Failed to extract expenses.")
        st.text(raw_response)
    else:
        user_proxy.send("Bill uploaded", manager)
        chat_log.append(("UserProxy → chat_manager", "Bill uploaded"))
        user_proxy.send(f"Categorized expenses: {categorized_data}", bill_processing_agent)
        chat_log.append(("UserProxy → BillProcessingAgent", json.dumps(categorized_data, indent=2)))
        bp_response = "Categorization complete. Expenses sorted into available categories."
        chat_log.append(("BillProcessingAgent", bp_response))
        user_proxy.send("Summarize this data", summary_agent)
        chat_log.append(("UserProxy → ExpenseSummarizationAgent", "Summarize this data"))
        with st.spinner("📊 Generating spending summary..."):
            summary = summarize_expenses_with_gemini(categorized_data)
        chat_log.append(("ExpenseSummarizationAgent", summary))
        st.markdown("## 📂 Categorized Expenses")
        for category, items in categorized_data.items():
            if items:
                st.markdown(f"### 🗂️ {category}")
                for i in items:
                    st.markdown(f"- **{i['item']}**: ₹{i['cost']}")
        st.markdown("---")
        st.markdown("## 📋 Spending Summary")
        st.markdown(f"<div class='result-box'>{summary}</div>", unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("## 💬 Agent Chat Logs")
        for sender, message in chat_log:
            style = "user-log" if "UserProxy" in sender else "agent-log"
            st.markdown(f"<div class='{style}'><strong>{sender}</strong><br>{message}</div>", unsafe_allow_html=True)
