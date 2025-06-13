
import os
import pymupdf as fitz  # The doc whisperer
import chromadb  # Our memory vault
from chromadb.utils import embedding_functions
import google.generativeai as genai  # Fancy AI buddy
from typing import List, Dict, Tuple
from dotenv import load_dotenv  # For your secret potion stash
from tqdm import tqdm  # Because watching bars move is satisfying

# Load your precious API key without announcing it to the world
load_dotenv()

class RAGSystem:
    def __init__(self, model_name: str = "gemini-1.5-flash"):
        # Initialize Gemini—Google’s brainchild
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        self.model = genai.GenerativeModel(model_name)

        # Say hello to ChromaDB—your memory palace
        self.client = chromadb.Client()
        self.collection = self.client.create_collection(
            name="research_papers",
            embedding_function=embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )
        )

        # To keep track of all that PDF chaos
        self.documents_metadata = {}

    def process_document(self, file_path: str) -> List[Dict]:
        """Tear apart a PDF, politely, and extract knowledge chunks."""
        doc = fitz.open(file_path)
        chunks = []

        for page_num in tqdm(range(len(doc)), desc=f"Processing {os.path.basename(file_path)}"):
            page = doc[page_num]
            text = page.get_text()

            # Grab potential headers—those shouty bold texts
            headers = self._extract_headers(page)

            # Slice and dice into snackable text chunks
            chunk_size = 1000
            overlap = 200

            for i in range(0, len(text), chunk_size - overlap):
                chunk = text[i:i + chunk_size]
                if not chunk.strip():
                    continue  # Skip the empty air

                relevant_header = self._find_relevant_header(chunk, headers)

                chunks.append({
                    "text": chunk,
                    "metadata": {
                        "paper_title": os.path.basename(file_path),
                        "page_number": page_num + 1,
                        "section_title": relevant_header
                    }
                })

        return chunks

    def _extract_headers(self, page) -> List[str]:
        """Detects loud, proud headers on the page."""
        headers = []
        blocks = page.get_text("dict")["blocks"]

        for block in blocks:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        if span["size"] > 12 and span["flags"] & 16:
                            headers.append(span["text"])  # Big and bold? Must be important.

        return headers

    def _find_relevant_header(self, chunk: str, headers: List[str]) -> str:
        """Connect a chunk with its bossy title."""
        if not headers:
            return "Introduction"  # Everyone loves an intro

        return headers[-1]  # The last shouty line before this calm paragraph

    def add_documents(self, directory: str):
        """Recruit all the PDFs and train them to obey."""
        for filename in os.listdir(directory):
            if filename.endswith(".pdf"):
                file_path = os.path.join(directory, filename)
                chunks = self.process_document(file_path)

                self.collection.add(
                    documents=[chunk["text"] for chunk in chunks],
                    metadatas=[chunk["metadata"] for chunk in chunks],
                    ids=[f"{filename}_{i}" for i in range(len(chunks))]
                )

    def query(self, question: str, n_results: int = 3) -> Tuple[str, List[Dict]]:
        """Ask your wise AI guru a question—it might even answer."""
        results = self.collection.query(
            query_texts=[question],
            n_results=n_results
        )

        context = "\n\n".join([
            f"From {meta['paper_title']} (Page {meta['page_number']}, {meta['section_title']}):\n{text}"
            for text, meta in zip(results["documents"][0], results["metadatas"][0])
        ])

        prompt = f"""Based on the following context from research papers, please answer the question.
        If the answer cannot be found in the context, say so (no guessing, AI!).
        
        Context:
        {context}
        
        Question: {question}
        
        Please provide a detailed answer and cite the sources using the paper titles, page numbers, and section titles provided."""

        response = self.model.generate_content(prompt)

        return response.text, results["metadatas"][0]

def main():
    # Power on the RAG Machine
    rag = RAGSystem()

    print("🧠 Processing documents... Hold onto your hats!")
    rag.add_documents("Pdf_files")

    print("\n✨ RAG System Ready! Type 'quit' when your curiosity runs dry.")
    while True:
        question = input("\n❓ Ask your  question: ")
        if question.lower() == 'quit':
            print("👋 Exiting. May your PDFs be ever structured!")
            break

        answer, sources = rag.query(question)
        print("\n🧾 Answer:\n", answer)
        print("\n📚 Sources:")
        for source in sources:
            print(f"- {source['paper_title']} (Page {source['page_number']}, {source['section_title']})")

if __name__ == "__main__":
    main()
