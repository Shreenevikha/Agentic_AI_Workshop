from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import Chroma
from vendor_risk_analyzer.config import CHROMA_PERSIST_DIRECTORY, GOOGLE_API_KEY
from typing import Dict, List
import os

class ExternalIntelligenceAgent:
    def __init__(self):
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=GOOGLE_API_KEY
        )
        self.vector_store = Chroma(
            persist_directory=CHROMA_PERSIST_DIRECTORY,
            embedding_function=self.embeddings
        )
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.0-pro",
            google_api_key=GOOGLE_API_KEY,
            temperature=0,
            convert_system_message_to_human=True
        )

    def fetch_regulatory_data(self, vendor_info: Dict, n_results: int = 3) -> Dict:
        """
        Fetch and summarize regulatory data for a vendor using RAG.
        Args:
            vendor_info: Dict with keys like 'vendor_name', 'pan', 'gstin'
            n_results: Number of relevant documents to retrieve
        Returns:
            Dict with summary and sources
        """
        # Compose a query from vendor info
        query_parts = []
        if 'vendor_name' in vendor_info:
            query_parts.append(f"Company: {vendor_info['vendor_name']}")
        if 'pan' in vendor_info:
            query_parts.append(f"PAN: {vendor_info['pan']}")
        if 'gstin' in vendor_info:
            query_parts.append(f"GSTIN: {vendor_info['gstin']}")
        query = ", ".join(query_parts)

        # Retrieve relevant documents from vector store
        results = self.vector_store.similarity_search_with_score(query, k=n_results)
        context = "\n\n".join([
            f"Source {i+1}:\n{doc.page_content}" for i, (doc, score) in enumerate(results)
        ])

        prompt = f"""
        Based on the following regulatory data context, provide a summary of the vendor's status, compliance, and any legal disputes. If information is missing, state so.
        
        Context:
        {context}
        
        Query: {query}
        
        Please provide a concise summary and cite the sources by their number.
        """
        response = self.llm.invoke(prompt)
        return {
            "summary": response.content,
            "sources": [doc.metadata for doc, score in results]
        } 