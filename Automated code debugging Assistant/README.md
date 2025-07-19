# 🔍 Python Code Debugging Assistant

An intelligent Python code analysis and correction system built with **CrewAI** and **Streamlit**. This application uses multiple AI agents to analyze Python code for errors and automatically provide corrected versions.

## 🚀 Features

- **Multi-Agent System**: Three specialized AI agents working together
  - **Code Analyzer**: Identifies syntax and logical errors
  - **Code Corrector**: Fixes identified issues
  - **Manager**: Coordinates the analysis and correction process

- **Static Code Analysis**: Uses AST (Abstract Syntax Tree) parsing for safe code analysis without execution
- **Modern UI**: Clean Streamlit interface for easy interaction
- **Sequential Processing**: Structured workflow ensuring reliable results
- **No ONNX Dependencies**: Lightweight solution without heavy runtime dependencies

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Code Analyzer │───▶│  Code Corrector │───▶│     Manager     │
│                 │    │                 │    │                 │
│ • AST Parsing   │    │ • Fix Issues    │    │ • Coordination  │
│ • Error Detect  │    │ • PEP 8 Compl.  │    │ • Workflow Mgmt │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📋 Prerequisites

- Python 3.8 or higher
- Google API Key (for Gemini model)
- Internet connection for API calls

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd Automated-code-debugging-Assistant
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up API Key**
   
   **Option 1: Environment Variable**
   ```bash
   # Windows
   set GOOGLE_API_KEY=your_api_key_here
   
   # macOS/Linux
   export GOOGLE_API_KEY=your_api_key_here
   ```
   
   **Option 2: Direct in code (not recommended for production)**
   ```python
   os.environ["GOOGLE_API_KEY"] = "your_api_key_here"
   ```

## 🚀 Usage

1. **Start the application**
   ```bash
   streamlit run app.py
   ```

2. **Open your browser**
   Navigate to `http://localhost:8501`

3. **Paste your Python code**
   Enter the code you want to analyze in the text area

4. **Click "Analyze & Fix"**
   The system will process your code and provide corrections

## 📝 Example Usage

### Input Code (with errors):
```python
def fibonacci_iterative(n):
    if n < 0:
        return []
    elif n == 1:
        return [0]
    elif n == 2:
        return [0, 1]
    fib_sequence = [0, 1]
    for i in range(2, n):
    next_fib = fib_sequence[-1] + fib_sequence[-2]
    fib_sequence.append(next_fib)
    return fib_sequence
```

### Expected Output:
The system will identify and fix:
- Indentation errors
- Logic issues
- Code style improvements

## 🔧 Key Components

### Agents

1. **Code Analyzer Agent**
   - Role: Python Static Analyzer
   - Goal: Find issues in Python code WITHOUT executing it
   - Tools: AST parsing, syntax checking

2. **Code Corrector Agent**
   - Role: Python Code Fixer
   - Goal: Fix issues while keeping original functionality
   - Tools: Code transformation, PEP 8 compliance

3. **Manager Agent**
   - Role: Code Review Manager
   - Goal: Ensure smooth analysis & correction
   - Tools: Process coordination

### Tasks

1. **Analysis Task**
   - Agent: Code Analyzer
   - Purpose: Identify errors in the code
   - Output: List of static analysis issues

2. **Correction Task**
   - Agent: Code Corrector
   - Purpose: Fix identified errors
   - Output: Corrected Python code with explanations

## 🛡️ Security Features

- **No Code Execution**: Uses static analysis only
- **API Key Protection**: Environment variable support
- **Safe Parsing**: AST-based analysis prevents malicious code execution

## 📦 Dependencies

- `streamlit`: Web interface
- `crewai`: Multi-agent framework
- `langchain`: LLM integration
- `langchain-google-genai`: Google Gemini integration
- `pydantic`: Data validation
- `typing-extensions`: Type hints support

## 🔍 Error Detection Capabilities

The system can identify:
- ✅ Syntax errors
- ✅ Indentation issues
- ✅ Missing imports
- ✅ Unused variables
- ✅ Code style violations
- ✅ Potential logic errors
- ✅ Print statements (warns about production use)
- ✅ Bare except clauses

## 🎯 Use Cases

- **Code Review**: Automated initial code review
- **Learning**: Understanding common Python errors
- **Refactoring**: Improving code quality
- **Debugging**: Identifying potential issues before execution
- **Education**: Teaching Python best practices

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Important Notes

- **API Costs**: Using Google Gemini API incurs costs based on usage
- **Rate Limits**: Be aware of API rate limits
- **Privacy**: Code is sent to Google's servers for processing
- **No Execution**: This tool analyzes code statically and does not execute it

## 🆘 Troubleshooting

### Common Issues

1. **API Key Error**
   - Ensure your Google API key is valid
   - Check environment variable setup

2. **Import Errors**
   - Verify all dependencies are installed
   - Check Python version compatibility

3. **Streamlit Issues**
   - Ensure port 8501 is available
   - Check firewall settings

### Getting Help

- Check the [Issues](../../issues) page
- Review the code comments for implementation details
- Ensure your Python environment is properly set up

## 🔮 Future Enhancements

- [ ] Support for multiple programming languages
- [ ] Integration with version control systems
- [ ] Batch processing capabilities
- [ ] Custom rule configuration
- [ ] Performance optimization
- [ ] Offline analysis capabilities

---

**Built with ❤️ using CrewAI and Streamlit** 