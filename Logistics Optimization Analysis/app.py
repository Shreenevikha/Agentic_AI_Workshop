import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# ===== Custom CSS for Professional Look =====
custom_css = """
<style>
body, .stApp {
    background: linear-gradient(120deg, #f6f7fb 0%, #e3eafc 100%);
    color: #222831;
}
[data-testid="stSidebar"] {
    background: #1b263b;
    color: #f6f7fb;
}
.st-emotion-cache-10trblm {
    color: #4361ee;
    font-weight: 800;
    letter-spacing: 1px;
}
.stButton > button {
    background: linear-gradient(90deg, #4361ee 0%, #48cae4 100%);
    color: white;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    padding: 0.5em 2em;
    margin-top: 1em;
    transition: background 0.3s;
}
.stButton > button:hover {
    background: linear-gradient(90deg, #48cae4 0%, #4361ee 100%);
}
.card {
    background: #f6f7fb;
    border-radius: 18px;
    box-shadow: 0 2px 12px rgba(44, 62, 80, 0.07);
    padding: 2.5rem 2.5rem 1.5rem 2.5rem;
    min-width: 350px;
    max-width: 480px;
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
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# Set page configuration
st.set_page_config(page_title="Logistics Optimizer Pro", layout="wide", page_icon="🚚")

with st.sidebar:
    st.image(
        "https://images.unsplash.com/photo-1515168833906-d2a3b82b302b?auto=format&fit=crop&w=400&q=80",
        use_column_width=True,
    )
    st.title("🚚 Logistics Optimizer Pro")
    st.markdown(
        """
        <div style='font-size: 1.1em;'>
        <b>AI-Powered Logistics Analysis</b><br>
        <span style='color:#4361ee;'>Modern, unique, and professional.</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("---")
    st.info("1. Enter product names.\n2. Click 'Optimize Logistics'.\n3. View your strategy!", icon="📝")
    st.markdown("---")
    st.caption("Powered by Gemini + LangChain")

st.title("Logistics Optimization Pro 🚚")
st.markdown(
    "<div style='font-size:1.15em; margin-bottom:1em;'>A professional, multi-agent system for logistics analysis and optimization.<br>Get actionable strategies instantly!</div>",
    unsafe_allow_html=True,
)

# Input form in a card
st.markdown("<div class='card'>", unsafe_allow_html=True)
with st.form("logistics_form"):
    product_input = st.text_input("Enter product names separated by commas", "TV, Laptops, Headphones")
    submitted = st.form_submit_button("Optimize Logistics")
st.markdown("</div>", unsafe_allow_html=True)

# Initialize Gemini LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    temperature=0.3,
    google_api_key=GOOGLE_API_KEY
)

def logistics_analysis(products):
    prompt = f"""
You are a Logistics Analyst. Analyze logistics data for the following products: {products}.
Focus on delivery routes and inventory turnover trends. Identify current inefficiencies and potential improvement areas in logistics operations.
Provide a concise summary.
"""
    return llm.invoke(prompt).content

def optimization_strategy(analysis_summary):
    prompt = f"""
You are an Optimization Strategist. Based on the following logistics analysis, develop an optimization strategy to reduce delivery time and improve inventory management. List detailed action points to improve logistics efficiency.

Logistics Analysis:
{analysis_summary}
"""
    return llm.invoke(prompt).content

if submitted:
    with st.spinner("Running Gemini agents..."):
        products = [p.strip() for p in product_input.split(",") if p.strip()]
        analysis = logistics_analysis(products)
        strategy = optimization_strategy(analysis)
        result = f"<b>Logistics Analysis:</b><br>{analysis}<br><br><b>Optimization Strategy:</b><br>{strategy}"
    st.success("✅ Optimization Complete!")
    st.subheader("🔍 Final Optimization Strategy")
    st.markdown(f"<div class='result-box'>{result}</div>", unsafe_allow_html=True)
