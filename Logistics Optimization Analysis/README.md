# Logistics Optimization Analysis with CrewAI

## Objective

This project implements a Crew AI system for analyzing logistics data and developing optimization strategies for logistics industry problems, such as optimizing delivery routes or inventory management.

## Features
- **Two AI Agents:**
  - **Logistics Analyst:** Analyzes logistics operations to find inefficiencies in delivery routes and inventory turnover.
  - **Optimization Strategist:** Designs data-driven strategies to optimize logistics operations and improve performance.
- **Parametrized Tasks:** Input a list of products to focus the analysis and optimization.
- **Streamlit UI:** Simple web interface for entering products and viewing results.

## How It Works
1. **User Input:** Enter a comma-separated list of products in the Streamlit app.
2. **CrewAI Agents:**
   - The Logistics Analyst researches the current state of logistics for the selected products, focusing on route efficiency and inventory turnover trends.
   - The Optimization Strategist creates an optimization strategy based on the analyst's findings.
3. **Results:** The final optimization strategy is displayed in the app.

## Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone <repo-url>
   cd Logistics-Optimization-Analysis
   ```
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Set up environment variables:**
   - Create a `.env` file in the project root with your Google API key:
     ```env
     GOOGLE_API_KEY=your_google_api_key_here
     ```
4. **Run the Streamlit app:**
   ```bash
   streamlit run app.py
   ```

## File Structure
- `app.py` - Main Streamlit application with CrewAI workflow
- `requirements.txt` - Python dependencies
- `.env` - Environment variables (not committed)
- `.gitignore` - Files and folders to ignore in git

## Customization
- You can modify the agent roles, goals, and tasks in `app.py` to suit different logistics problems or industries.

## License
MIT License 