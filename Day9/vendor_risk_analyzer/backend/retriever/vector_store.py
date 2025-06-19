"""
Vector Store Setup
Initializes and manages the vector database for RAG.
"""

import faiss
import numpy as np
from typing import List, Dict, Any
import pickle
import os

class VectorStore:
    def __init__(self, dimension=1536):  # OpenAI embedding dimension
        self.dimension = dimension
        self.index = faiss.IndexFlatL2(dimension)
        self.documents = []
        self.metadata = []
        
    def add_documents(self, texts: List[str], embeddings: List[List[float]], metadata: List[Dict] = None):
        """Add documents to the vector store."""
        if metadata is None:
            metadata = [{"source": f"doc_{i}"} for i in range(len(texts))]
            
        # Convert embeddings to numpy array
        embeddings_array = np.array(embeddings).astype('float32')
        
        # Add to FAISS index
        self.index.add(embeddings_array)
        
        # Store documents and metadata
        self.documents.extend(texts)
        self.metadata.extend(metadata)
        
    def search(self, query_embedding: List[float], k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents."""
        query_array = np.array([query_embedding]).astype('float32')
        distances, indices = self.index.search(query_array, k)
        
        results = []
        for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
            if idx < len(self.documents):
                results.append({
                    "document": self.documents[idx],
                    "metadata": self.metadata[idx],
                    "distance": float(distance)
                })
        
        return results
    
    def save(self, filepath: str):
        """Save the vector store to disk."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, f"{filepath}_index.faiss")
        
        # Save documents and metadata
        with open(f"{filepath}_data.pkl", "wb") as f:
            pickle.dump({
                "documents": self.documents,
                "metadata": self.metadata
            }, f)
    
    def load(self, filepath: str):
        """Load the vector store from disk."""
        # Load FAISS index
        self.index = faiss.read_index(f"{filepath}_index.faiss")
        
        # Load documents and metadata
        with open(f"{filepath}_data.pkl", "rb") as f:
            data = pickle.load(f)
            self.documents = data["documents"]
            self.metadata = data["metadata"]

def initialize_vector_store():
    """Initialize the vector store (FAISS)."""
    return VectorStore() 