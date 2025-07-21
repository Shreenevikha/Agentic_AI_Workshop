import streamlit as st
from crewai import Agent, Task, Crew, Process, LLM
from langchain_google_genai import ChatGoogleGenerativeAI
import os
import ast
from dotenv import load_dotenv

# ===== 100% ONNX-FREE SOLUTION =====
# No chromadb, no CodeInterpreterTool, no ONNX runtime

# Load environment variables
load_dotenv()

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
    max-width: 700px;
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
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

st.set_page_config(
    page_title="AI Python Code Debugger Pro",
    page_icon="🛠️",
    layout="wide"
)

# Sidebar for quick info
with st.sidebar:
    st.image(
        "https://images.unsplash.com/photo-1517694712202-14dd9538aa97?auto=format&fit=crop&w=400&q=80",
        use_column_width=True,
    )
    st.title("🛠️ Code Debugger Pro")
    st.markdown(
        """
        <div style='font-size: 1.1em;'>
        <b>AI-Powered Python Code Review</b><br>
        <span style='color:#008891;'>Modern, unique, and professional.</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("---")
    st.markdown("### 📝 How it Works")
    st.markdown("""
    1. **Paste your Python code**
    2. **Click 'Analyze & Fix'**
    3. **AI agents analyze and correct your code**
    4. **Get a clean, fixed version instantly!**
    """)
    st.markdown("---")
    st.caption("Powered by Gemini + CrewAI")

# Main header
st.markdown("""
<div class="section-header">
    <h1>🛠️ Automated Python Code Debugger Pro</h1>
    <p style="font-size: 1.2rem; opacity: 0.9;">AI-Driven Static Analysis & Correction (No ONNX, No Execution)</p>
</div>
""", unsafe_allow_html=True)

# Custom Python Analyzer (No ONNX)
def analyze_python_code(code: str) -> str:
    """Static analysis without executing code."""
    try:
        # 1. Check syntax via AST
        tree = ast.parse(code)
        # 2. Basic checks
        issues = []
        # Check for print statements (not recommended in production)
        if any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'print' 
               for node in ast.walk(tree)):
            issues.append("⚠️ Found `print()` - Use logging in production.")
        # Check for broad exceptions
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler) and node.type is None:
                issues.append("⚠️ Found bare `except:` - Specify exception types.")
        # 3. Return results
        if issues:
            return "Found issues:\n" + "\n".join(issues)
        return "✅ No syntax errors found. Code looks good!"
    except SyntaxError as e:
        return f"❌ Syntax Error: {e.msg} (Line {e.lineno})"

# Initialize LLM (Groq or Gemini)
llm = LLM(
    api_key=os.getenv("GOOGLE_API_KEY"),
    model="gemini/gemini-2.5-flash"  # Must include provider prefix
)

# ===== Agents =====
code_analyzer = Agent(
    role="Python Static Analyzer",
    goal="Find issues in Python code WITHOUT executing it",
    backstory="Expert in static code analysis using AST parsing.",
    llm=llm,
    verbose=True
)

code_corrector = Agent(
    role="Python Code Fixer",
    goal="Fix issues while keeping original functionality",
    backstory="Specializes in clean, PEP 8 compliant fixes.",
    llm=llm,
    verbose=True
)

manager = Agent(
    role="Code Review Manager",
    goal="Ensure smooth analysis & correction",
    backstory="Coordinates the review process.",
    llm=llm,
    verbose=True
)

# ===== Streamlit UI (Redesigned) =====
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown('<div class="section-header"><h3>Paste Your Python Code Below</h3></div>', unsafe_allow_html=True)
code_input = st.text_area("Paste Python code:", height=300)
submit = st.button("Analyze & Fix", use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

if submit:
    if not code_input.strip():
        st.warning("Please enter Python code.")
    else:
        with st.spinner("Analyzing..."):
            # Task 1: Static Analysis
            analysis_task = Task(
                description=f"Analyze this code:\n```python\n{code_input}\n```",
                agent=code_analyzer,
                expected_output="List of static analysis issues."
            )
            # Task 2: Fix Code
            correction_task = Task(
                description="Fix all issues found.",
                agent=code_corrector,
                expected_output="Corrected Python code with explanations.",
                context=[analysis_task]
            )
            # Run CrewAI
            crew = Crew(
                agents=[code_analyzer, code_corrector, manager],
                tasks=[analysis_task, correction_task],
                verbose=True,
                process=Process.sequential
            )
            result = crew.kickoff()
        st.success("✅ Code Analysis & Correction Complete!")
        st.markdown('<div class="result-box">', unsafe_allow_html=True)
        st.subheader("🔧 Fixed Code")
        st.code(result, language="python")
        st.markdown('</div>', unsafe_allow_html=True)