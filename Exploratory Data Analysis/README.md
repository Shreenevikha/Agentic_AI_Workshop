# Streamlining Exploratory Data Analysis (EDA) with a Multi-Agent System using Autogen

## Overview
This project simplifies and automates the Exploratory Data Analysis (EDA) process using a multi-agent system built with [Autogen](https://github.com/microsoft/autogen) and [Google Gemini](https://ai.google.dev/). Each agent specializes in a specific EDA task, ensuring modularity, efficiency, and high-quality results.

## Key Features
- **Data Preparation Agent:** Cleans and preprocesses data.
- **EDA Agent:** Performs statistical summarization, generates insights, and suggests visualizations.
- **Report Generator Agent:** Produces a structured EDA report with clear findings.
- **Critic Agent:** Reviews outputs for clarity, accuracy, and completeness.
- **Executor Agent:** Validates code and ensures result accuracy.
- **Admin Agent:** Oversees workflow and coordinates agents.

Agents communicate and collaborate to iteratively refine the analysis, ensuring a smooth workflow and reproducible results.

## Final Output
- Overview of the data
- Key insights and findings
- Detailed visualizations (suggested)
- Summary and conclusions, incorporating Critic Agent feedback

## Setup Instructions
1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd Exploratory-Data-Analysis
   ```
2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
3. **Set up environment variables**
   - Create a `.env` file in the project root:
     ```env
     GEMINI_API_KEY=your_gemini_api_key_here
     ```
4. **Run the application**
   ```bash
   streamlit run app.py
   ```

## Usage
- Upload a CSV file via the Streamlit interface.
- Click "Run Agentic EDA" to start the multi-agent analysis.
- Review outputs for data preparation, EDA insights, report, critic feedback, and code validation.

## Requirements
- Python 3.8+
- See `requirements.txt` for full dependencies.

## Project Structure
- `app.py` — Main Streamlit app and agent definitions
- `requirements.txt` — Python dependencies
- `.env` — Environment variables (not tracked in git)

## License
MIT License

## Acknowledgments
- [Microsoft Autogen](https://github.com/microsoft/autogen)
- [Google Gemini](https://ai.google.dev/)
- [Streamlit](https://streamlit.io/)

---

*This project automates and organizes EDA tasks, ensuring efficiency, reproducibility, and high-quality results in collaborative data science settings.* 