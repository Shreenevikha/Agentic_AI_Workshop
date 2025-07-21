## Overview
This project implements a research and summarization agent using LangGraph. The system processes user queries by determining whether they require reasoning from an LLM, web research, or retrieval from a knowledge base. It leverages multiple specialized sub-agents to generate well-structured, informative responses.

## Agent Architecture
- **Router Agent**: Determines the best approach for answering a query (LLM, web research, or retrieval-augmented generation).
- **Web Research Agent**: Handles queries requiring up-to-date information by performing web searches and extracting relevant details.
- **RAG Agent**: Answers queries related to a predefined dataset using retrieval-augmented generation.
- **Summarization Agent**: Synthesizes and structures the final response from gathered information.

## Getting Started
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Place your dataset in the `my_docs/` directory.
3. Run the main application:
   ```bash
   python app.py
   ```

## Requirements
- Python 3.8+
- [LangGraph](https://github.com/langchain-ai/langgraph)
- Other dependencies listed in `requirements.txt`

## Project Structure
- `app.py` – Main application entry point
- `my_docs/` – Directory for datasets (e.g., PDFs)
- `requirements.txt` – Python dependencies

