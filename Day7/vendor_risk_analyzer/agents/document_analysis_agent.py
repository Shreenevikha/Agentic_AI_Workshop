from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI
import PyPDF2
import os
from typing import Dict, List
from vendor_risk_analyzer.config import CHROMA_PERSIST_DIRECTORY, REQUIRED_FIELDS, GOOGLE_API_KEY
import shutil
import time

class DocumentAnalysisAgent:
    def __init__(self):
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=GOOGLE_API_KEY
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.0-pro",  # Updated model name
            google_api_key=GOOGLE_API_KEY,
            temperature=0,
            convert_system_message_to_human=True
        )
        
        # Clear existing ChromaDB directory if it exists
        if os.path.exists(CHROMA_PERSIST_DIRECTORY):
            shutil.rmtree(CHROMA_PERSIST_DIRECTORY)
        
    def extract_text_from_file(self, file_path: str) -> str:
        """Extract text from PDF or text documents."""
        file_extension = os.path.splitext(file_path)[1].lower()
        
        if file_extension == '.pdf':
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text()
        elif file_extension == '.txt':
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")
            
        return text

    def process_document(self, file_path: str) -> Dict:
        """Process a document and extract relevant information."""
        # Extract text from document
        text = self.extract_text_from_file(file_path)
        
        # Create a single prompt for all required fields
        prompt = f"""
        Extract the following information from this document:
        {text}
        
        Please provide the following details in a structured format:
        {', '.join(REQUIRED_FIELDS)}
        
        Format your response as a simple list of key-value pairs.
        """
        
        # Add retry logic for rate limits
        max_retries = 5
        base_delay = 60  # Start with 60 seconds delay
        
        for attempt in range(max_retries):
            try:
                response = self.llm.invoke(prompt)
                break
            except Exception as e:
                if "ResourceExhausted" in str(e) and attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)  # Exponential backoff
                    print(f"Rate limit hit, waiting {delay} seconds... (Attempt {attempt + 1}/{max_retries})")
                    time.sleep(delay)
                    continue
                raise
        
        # Parse the response into a dictionary
        extracted_info = {}
        for line in response.content.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower()
                value = value.strip()
                if key in REQUIRED_FIELDS:
                    extracted_info[key] = value
        
        return extracted_info

    def analyze_documents(self, document_paths: List[str]) -> Dict:
        """Analyze multiple documents and combine results."""
        all_info = {}
        for doc_path in document_paths:
            print(f"Processing document: {doc_path}")
            doc_info = self.process_document(doc_path)
            all_info.update(doc_info)
            # Add delay between documents
            time.sleep(30)  # Wait 30 seconds between documents
        return all_info 