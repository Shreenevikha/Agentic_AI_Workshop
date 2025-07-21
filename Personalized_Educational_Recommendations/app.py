import os
import json
import datetime
import pandas as pd
from typing import List, Dict, Any
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from crewai import Agent, Task, Crew
import google.generativeai as genai
import requests
import re
import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

SERPER_API_KEY = os.getenv("SERPER_API_KEY")

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# Initialize Gemini LLM for CrewAI
gemini_llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    google_api_key=GEMINI_API_KEY,
    temperature=0.7
)

# Helper Functions
def search_learning_materials(topic: str) -> Dict[str, Any]:
    """Search for learning materials on a given topic."""
    try:
        url = "https://google.serper.dev/search"
        headers = {"X-API-KEY": SERPER_API_KEY}
        
        # Search for videos
        video_query = f"{topic} tutorial video"
        video_results = requests.post(url, json={"q": video_query}, headers=headers).json()
        
        # Search for articles
        article_query = f"{topic} guide article"
        article_results = requests.post(url, json={"q": article_query}, headers=headers).json()
        
        # Search for exercises
        exercise_query = f"{topic} practice exercises"
        exercise_results = requests.post(url, json={"q": exercise_query}, headers=headers).json()
        
        videos = []
        articles = []
        exercises = []
        
        # Extract videos
        for v in video_results.get("organic", [])[:3]:
            videos.append(f"{v['title']}: {v['link']}")
        
        # Extract articles
        for a in article_results.get("organic", [])[:3]:
            articles.append(f"{a['title']}: {a['link']}")
            
        # Extract exercises
        for e in exercise_results.get("organic", [])[:3]:
            exercises.append(f"{e['title']}: {e['link']}")
        
        return {
            "topic": topic,
            "videos": videos,
            "articles": articles,
            "exercises": exercises
        }
    except Exception as e:
        return {
            "topic": topic,
            "videos": [f"Error searching videos: {str(e)}"],
            "articles": [f"Error searching articles: {str(e)}"],
            "exercises": [f"Error searching exercises: {str(e)}"]
        }

def generate_quiz_questions(topic: str) -> List[Dict[str, Any]]:
    """Generate quiz questions on a given topic."""
    try:
        prompt = f"""Create 3 multiple-choice questions about {topic}. Format each question as follows:

Question: [Your question here]
A) [Option A]
B) [Option B]
C) [Option C]
D) [Option D]
Answer: [Correct option letter]

Make sure the questions are clear and educational."""
        
        response = model.generate_content(prompt).text
        questions = []
        
        # Parse the response
        question_blocks = response.split("Question:")
        for block in question_blocks[1:]:  # Skip first empty element
            lines = [line.strip() for line in block.strip().split("\n") if line.strip()]
            if len(lines) >= 6:
                question = lines[0]
                options = []
                answer_line = ""
                
                for line in lines[1:]:
                    if line.startswith(('A)', 'B)', 'C)', 'D)')):
                        options.append(line[3:].strip())
                    elif line.startswith("Answer:"):
                        answer_line = line.split(":")[-1].strip()
                
                if len(options) == 4 and answer_line:
                    # Convert answer letter to actual answer text
                    answer_index = ord(answer_line.upper()) - ord('A')
                    if 0 <= answer_index < 4:
                        questions.append({
                            "question": question,
                            "options": options,
                            "answer": options[answer_index]
                        })
        
        return questions[:3]
    except Exception as e:
        return [{"question": f"Error generating quiz: {str(e)}", "options": ["Error", "Error", "Error", "Error"], "answer": "Error"}]

def suggest_projects(topic: str, level: str) -> List[Dict[str, Any]]:
    """Generate project ideas based on topic and expertise level."""
    try:
        prompt = f"""Suggest 3 practical project ideas for someone at a {level} level learning about {topic}.
For each project, provide:
- A clear title
- A detailed description explaining what the project involves
- Why it's suitable for {level} level

Format each project as:
Project: [Title]
Description: [Detailed description]
"""
        
        response = model.generate_content(prompt).text
        projects = []
        
        # Parse the response
        project_blocks = response.split("Project:")
        for block in project_blocks[1:]:  # Skip first empty element
            lines = [line.strip() for line in block.strip().split("\n") if line.strip()]
            
            title = lines[0] if lines else "Untitled Project"
            description = ""
            
            for line in lines[1:]:
                if line.startswith("Description:"):
                    description = line.split(":", 1)[1].strip()
                    break
            
            if description:
                projects.append({
                    "title": title,
                    "description": description,
                    "level": level
                })
        
        return projects[:3]
    except Exception as e:
        return [{"title": f"Error generating projects: {str(e)}", "description": "Unable to generate project suggestions", "level": level}]

# Agents without tools - they will use the functions directly
learning_agent = Agent(
    role="Learning Material Curator",
    goal="Find the best learning resources for a given topic using web search",
    backstory="""You are an expert researcher with years of experience in educational content curation. 
    You excel at finding diverse learning materials including videos, articles, and practical exercises.
    You have access to web search capabilities to find current and relevant learning materials.""",
    llm=gemini_llm,
    verbose=True
)

quiz_agent = Agent(
    role="Quiz Master",
    goal="Create effective assessment quizzes for learning topics",
    backstory="""You are specialized in educational assessment and test creation. 
    You create engaging multiple-choice questions that test understanding and promote learning.
    You can generate high-quality quiz questions on any topic.""",
    llm=gemini_llm,
    verbose=True
)

project_agent = Agent(
    role="Project Mentor",
    goal="Suggest practical projects matching skill levels",
    backstory="""You are experienced in curriculum development and project-based learning. 
    You design hands-on projects that reinforce learning and build practical skills.
    You can suggest projects appropriate for different skill levels.""",
    llm=gemini_llm,
    verbose=True
)

# Tasks with detailed descriptions
def create_learning_task(topic: str):
    return Task(
        description=f"""Search for comprehensive learning materials about '{topic}'. 
        Find videos, articles, and exercises that would help someone learn this topic effectively.
        
        Use web search to find:
        1. Educational videos and tutorials
        2. Articles and guides
        3. Practice exercises and examples
        
        Return the results in a structured format with titles and links.""",
        agent=learning_agent,
        expected_output=f"""A comprehensive list of learning materials for {topic} including:
        - Videos: List of educational videos with titles and links
        - Articles: List of articles and guides with titles and links  
        - Exercises: List of practice exercises with titles and links"""
    )

def create_quiz_task(topic: str):
    return Task(
        description=f"""Create a quiz about '{topic}' with 3 multiple-choice questions. 
        Make sure the questions are educational and test important concepts.
        
        Each question should have:
        - A clear question
        - 4 multiple choice options (A, B, C, D)
        - The correct answer indicated
        
        Focus on testing understanding rather than memorization.""",
        agent=quiz_agent,
        expected_output=f"""A set of 3 quality multiple-choice questions about {topic}, each with:
        - Question text
        - 4 answer options
        - Correct answer identified"""
    )

def create_project_task(topic: str, level: str):
    return Task(
        description=f"""Suggest 3 practical project ideas about '{topic}' suitable for {level} level learners. 
        Each project should have a clear title and detailed description.
        
        Consider the {level} skill level when designing projects:
        - Beginner: Simple, guided projects with clear steps
        - Intermediate: Projects requiring some independent thinking
        - Advanced: Complex projects requiring expertise and creativity
        
        Each project should be practical and help reinforce learning.""",
        agent=project_agent,
        expected_output=f"""3 practical project ideas for {level} level learners about {topic}, each with:
        - Project title
        - Detailed description
        - Why it's suitable for {level} level"""
    )

# Execution function
def generate_learning_path(topic: str, level: str):
    """Generate a complete learning path for the given topic and level."""
    
    try:
        # Directly call helper functions
        learning_materials = search_learning_materials(topic)
        quiz_questions = generate_quiz_questions(topic)
        project_ideas = suggest_projects(topic, level)

        return {
            "learning_materials": learning_materials,
            "quiz_questions": quiz_questions,
            "project_ideas": project_ideas
        }
    except Exception as e:
        st.error(f"❌ Error generating content: {str(e)}")
        return {
            "learning_materials": {},
            "quiz_questions": [],
            "project_ideas": []
        }

def run_quiz(quiz_questions, user_name="User"):
    st.subheader("📝 Interactive Quiz")
    if "quiz_score" not in st.session_state:
        st.session_state.quiz_score = 0
    if "quiz_answers" not in st.session_state or len(st.session_state.quiz_answers) != len(quiz_questions):
        st.session_state.quiz_answers = [None] * len(quiz_questions)
    if "quiz_submitted" not in st.session_state:
        st.session_state.quiz_submitted = False

    for i, q in enumerate(quiz_questions):
        st.markdown(f"**Q{i+1}: {q['question']}**")
        st.session_state.quiz_answers[i] = st.radio(
            f"Choose your answer for Q{i+1}:",
            q["options"],
            key=f"quiz_{i}"
        )
        st.markdown("---")

    if st.button("Submit Quiz"):
        st.session_state.quiz_submitted = True
        score = 0
        results = []
        for i, q in enumerate(quiz_questions):
            user_ans = st.session_state.quiz_answers[i]
            correct = user_ans == q["answer"]
            results.append({
                "Question": q["question"],
                "Your Answer": user_ans,
                "Correct Answer": q["answer"],
                "Result": "Correct" if correct else "Incorrect",
                "Points": 1 if correct else 0
            })
            if correct:
                score += 1
        st.session_state.quiz_score = score
        st.session_state.quiz_results = results

        # Save to local JSON file
        quiz_record = {
            "user": user_name,
            "timestamp": datetime.datetime.now().isoformat(),
            "score": score,
            "total": len(quiz_questions),
            "results": results
        }
        try:
            with open("quiz_results.json", "a") as f:
                f.write(json.dumps(quiz_record) + "\n")
        except Exception as e:
            st.warning(f"Could not save quiz results: {e}")

    if st.session_state.quiz_submitted:
        st.success(f"Your Score: {st.session_state.quiz_score} / {len(quiz_questions)}")
        st.markdown("---")
        st.markdown("### 📝 Question-wise Feedback")
        for i, q in enumerate(st.session_state.quiz_results):
            if q["Result"] == "Correct":
                st.markdown(f"<div style='color:green;'><b>Q{i+1}:</b> ✅ Correct! (+1 point)<br> <b>Your Answer:</b> {q['Your Answer']}<br> <b>Correct Answer:</b> {q['Correct Answer']}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='color:#b94a48;'><b>Q{i+1}:</b> ❌ Incorrect (0 points)<br> <b>Your Answer:</b> {q['Your Answer']}<br> <b>Correct Answer:</b> {q['Correct Answer']}</div>", unsafe_allow_html=True)
            st.markdown("---")
        df = pd.DataFrame(st.session_state.quiz_results)
        st.dataframe(df, use_container_width=True)
        # Download as CSV
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Quiz Results as CSV",
            data=csv,
            file_name="quiz_results.csv",
            mime="text/csv"
        )

# Streamlit UI
def main():
    st.set_page_config(page_title="Personalized Learning Assistant Pro", page_icon="🎓", layout="wide")

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
    .st-expanderHeader {
        background: #e3eafc;
        color: #4361ee;
        font-weight: 600;
        border-radius: 6px;
    }
    .stAlert {
        border-radius: 8px;
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

    with st.sidebar:
        st.image(
            "https://images.unsplash.com/photo-1464983953574-0892a716854b?auto=format&fit=crop&w=400&q=80",
            use_column_width=True,
        )
        st.title("🎓 Learning Path Pro")
        st.markdown(
            """
            <div style='font-size: 1.1em;'>
            <b>Personalized AI Learning, Quiz & Projects</b><br>
            <span style='color:#4361ee;'>Modern, unique, and professional.</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("---")
        st.info("1. Enter your topic and level.\n2. Click 'Generate Learning Path'.\n3. Explore your personalized plan!", icon="📝")
        st.markdown("---")
        st.caption("Powered by Gemini + CrewAI")

    st.title("Personalized Learning Assistant Pro 🎓")
    st.markdown(
        "<div style='font-size:1.15em; margin-bottom:1em;'>A professional, multi-agent system for learning, quizzes, and project ideas.\nGet your personalized path instantly!</div>",
        unsafe_allow_html=True,
    )

    # Check for API keys
    if not GEMINI_API_KEY:
        st.error("⚠️ Please set your GEMINI_API_KEY in the environment variables.")
        st.stop()
    if not SERPER_API_KEY:
        st.error("⚠️ Please set your SERPER_API_KEY in the environment variables.")
        st.stop()

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        topic = st.text_input("Learning Topic", placeholder="e.g., Machine Learning, Python, Data Science")
    with col2:
        level = st.selectbox("Skill Level", ["Beginner", "Intermediate", "Advanced"])
    # Prompt for user name before quiz
    user_name = st.text_input("Your Name (for quiz record)", value="User")
    st.markdown("</div>", unsafe_allow_html=True)

    generate_btn = st.button("Generate Learning Path 🚀", use_container_width=True)

    if generate_btn:
        if not topic.strip():
            st.error("Please enter a topic to learn about.")
            return
        with st.spinner("🔍 Creating your personalized learning path..."):
            result = generate_learning_path(topic, level)
            if result:
                st.success("✅ Learning path generated successfully!")
                st.markdown("---")
                tab1, tab2, tab3 = st.tabs(["📚 Learning Materials", "📝 Quiz", "🚀 Project Ideas"])
                with tab1:
                    st.subheader("📚 Learning Materials")
                    learning_materials = result.get("learning_materials", {})
                    if learning_materials.get("videos"):
                        st.markdown("### 🎥 Videos")
                        for video in learning_materials["videos"]:
                            st.write(f"• {video}")
                    if learning_materials.get("articles"):
                        st.markdown("### 📄 Articles")
                        for article in learning_materials["articles"]:
                            st.write(f"• {article}")
                    if learning_materials.get("exercises"):
                        st.markdown("### 💪 Exercises")
                        for exercise in learning_materials["exercises"]:
                            st.write(f"• {exercise}")
                with tab2:
                    quiz_questions = result.get("quiz_questions", [])
                    if quiz_questions:
                        run_quiz(quiz_questions, user_name)
                    else:
                        st.write("No quiz questions generated.")
                with tab3:
                    st.subheader("🚀 Project Ideas")
                    project_ideas = result.get("project_ideas", [])
                    if project_ideas:
                        for i, project in enumerate(project_ideas, 1):
                            st.markdown(f"### Project {i}: {project['title']}")
                            st.write(f"**Description:** {project['description']}")
                            st.write(f"**Level:** {project['level']}")
                            st.markdown("---")
                    else:
                        st.write("No project ideas generated.")
                if result.get("raw_result"):
                    with st.expander("🔍 View Raw AI Output"):
                        st.text(str(result["raw_result"]))
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666;'>
            <p>🤖 Powered by Google Gemini AI | 🔍 Web Search via Serper API</p>
            <p>💡 This tool generates learning materials, quizzes, and project ideas for any topic</p>
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()