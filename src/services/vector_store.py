import faiss
import numpy as np
from typing import List, Dict, Any, Optional
import logging
import pickle
from pathlib import Path
import re
from openai import AzureOpenAI

logger = logging.getLogger(__name__)
AZURE_OPENAI_ENDPOINT="https://norch-m2irp375-switzerlandnorth.cognitiveservices.azure.com"
azure_openai_api_key="10d62b9f3c784273bf05bdea0edbd879"

# Azure OpenAI and Search Index Clients
openai_client = AzureOpenAI(
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_key=azure_openai_api_key,
    api_version="2024-06-01"
)
class VectorStore:
    """FAISS vector store for resume and job requirement matching"""
    
    def __init__(self, model_name: str = "text-embedding-3-large", dimension: int = 384):
        self.model_name = model_name
        self.dimension = dimension
        self.embedding_model = model_name
        
        # Initialize FAISS index
        self.index = faiss.IndexFlatIP(dimension)
        
        # Document storage with type tracking
        self.documents = []
        self.metadata = []
        self.document_types = []  # 'resume' or 'job'
        
        # Create storage directory
        self.storage_dir = Path("./faiss_storage")
        self.storage_dir.mkdir(exist_ok=True)
        
        logger.info(f"Initialized VectorStore with {model_name} (dim={dimension})")

    def _preprocess_text(self, text: str) -> str:
        """Clean and normalize text before embedding"""
        text = re.sub(r'(\d{4})(\d{4})', r'\1-\2', text)  # Fix dates (20232024 -> 2023-2024)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def add_resume_chunks(self, chunks: List[str], metadata: Optional[Dict[str, Any]] = None):
        """Add resume chunks to the vector store"""
        if not chunks:
            logger.warning("Empty resume chunks provided")
            return

        try:
            cleaned_chunks = [self._preprocess_text(chunk) for chunk in chunks]
            response = openai_client.embeddings.create(
                input=cleaned_chunks,
                model=self.embedding_model
            )
            embeddings = response.data[0].embedding
            print(embeddings)
            
            if len(embeddings) > 0:
                
                self.documents.extend(cleaned_chunks)
                self.metadata.extend([metadata or {}] * len(cleaned_chunks))
                self.document_types.extend(['resume'] * len(cleaned_chunks))
                logger.info(f"Added {len(cleaned_chunks)} resume chunks")
            else:
                logger.warning("No valid embeddings generated for resume chunks")

        except Exception as e:
            logger.error(f"Error adding resume chunks: {str(e)}")
            raise ValueError("Failed to add resume chunks") from e

    def add_job_requirements(self, requirements: List[str], metadata: Optional[Dict[str, Any]] = None):
        """Add job requirements to the vector store"""
        if not requirements:
            logger.warning("Empty job requirements provided")
            return

        try:
            cleaned_reqs = [self._preprocess_text(req) for req in requirements]
            response = openai_client.embeddings.create(
                input=cleaned_reqs,
                model=self.embedding_model
            )
            embeddings = response.data[0].embedding
            
            if len(embeddings) > 0:
                
                self.documents.extend(cleaned_reqs)
                self.metadata.extend([metadata or {}] * len(cleaned_reqs))
                self.document_types.extend(['job'] * len(cleaned_reqs))
                logger.info(f"Added {len(cleaned_reqs)} job requirements")
            else:
                logger.warning("No valid embeddings generated for job requirements")

        except Exception as e:
            logger.error(f"Error adding job requirements: {str(e)}")
            raise ValueError("Failed to add job requirements") from e

    def find_similar_chunks(self, query: str, n_results: int = 5, doc_type: str = "resume") -> List[Dict[str, Any]]:
        """
        Find similar chunks (keeping your original function name)
        
        Args:
            query: Search query text
            n_results: Number of results to return
            doc_type: Type of documents to search ('resume' or 'job')
            
        Returns:
            List of results with text, metadata, and similarity score
        """
        if not self.documents:
            logger.warning("No documents available for search")
            return []

        try:
            clean_query = self._preprocess_text(query)
            response = openai_client.embeddings.create(
                input=clean_query,
                model=self.embedding_model
            )
            query_embedding = response.data[0].embedding
            
            # Get indices of documents of the requested type
            if doc_type:
                type_indices = [i for i, t in enumerate(self.document_types) if t == doc_type]
                if not type_indices:
                    logger.warning(f"No documents of type '{doc_type}' available")
                    return []
                k = min(n_results, len(type_indices))
            else:
                type_indices = range(len(self.documents))
                k = min(n_results, len(self.documents))
            
            # Search the full index
            distances, indices = self.index.search(
                query_embedding.astype('float32'), 
                len(self.documents)
            )
            
            # Filter results by document type and get top k
            results = []
            for i, distance in zip(indices[0], distances[0]):
                if i in type_indices and 0 <= i < len(self.documents):
                    results.append({
                        'document': self.documents[i],
                        'metadata': self.metadata[i],
                        'distance': float(distance),
                        'type': self.document_types[i]
                    })
                    if len(results) >= k:
                        break
            
            return sorted(results, key=lambda x: x['distance'], reverse=True)

        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            return []

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate cosine similarity between two texts"""
        try:
            clean_text1 = self._preprocess_text(text1)
            clean_text2 = self._preprocess_text(text2)
            response = openai_client.embeddings.create(
                input=clean_text1 + clean_text2,
                model=self.embedding_model
            )
            embeddings = response.data[0].embedding
            
            similarity = np.dot(embeddings[0], embeddings[1]) / (
                np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])
            )
            
            return float(max(0, min(1, similarity)))
            
        except Exception as e:
            logger.error(f"Similarity calculation failed: {str(e)}")
            return 0.0

    def save_index(self, filename: str = "faiss_index"):
        """Save the vector store to disk"""
        try:
            # Save FAISS index
            faiss.write_index(self.index, str(self.storage_dir / f"{filename}.faiss"))
            
            # Save document data
            with open(self.storage_dir / f"{filename}_data.pkl", 'wb') as f:
                pickle.dump({
                    'documents': self.documents,
                    'metadata': self.metadata,
                    'document_types': self.document_types,
                    'config': {
                        'model_name': self.model_name,
                        'dimension': self.dimension
                    }
                }, f)
            
            logger.info(f"Saved index to {self.storage_dir}/{filename}.*")

        except Exception as e:
            logger.error(f"Failed to save index: {str(e)}")
            raise IOError("Failed to save index") from e

    def load_index(self, filename: str = "faiss_index"):
        """Load the vector store from disk"""
        try:
            index_path = self.storage_dir / f"{filename}.faiss"
            data_path = self.storage_dir / f"{filename}_data.pkl"
            
            if not index_path.exists() or not data_path.exists():
                logger.warning("Index files missing, starting fresh")
                return False
                
            self.index = faiss.read_index(str(index_path))
            
            with open(data_path, 'rb') as f:
                data = pickle.load(f)
                self.documents = data.get('documents', [])
                self.metadata = data.get('metadata', [])
                self.document_types = data.get('document_types', [])
                
                # Verify model compatibility
                config = data.get('config', {})
                if config.get('model_name') != self.model_name:
                    logger.warning(f"Loaded model {config.get('model_name')} doesn't match current {self.model_name}")
                if config.get('dimension') != self.dimension:
                    raise ValueError(f"Dimension mismatch: loaded {config.get('dimension')} vs current {self.dimension}")
            
            logger.info(f"Loaded index from {self.storage_dir}/{filename}.*")
            return True

        except Exception as e:
            logger.error(f"Failed to load index: {str(e)}")
            raise IOError("Failed to load index") from e

    def clear_collections(self):
        """Reset the vector store to empty state"""
        self.index = faiss.IndexFlatIP(self.dimension)
        self.documents = []
        self.metadata = []
        self.document_types = []
        logger.info("Cleared all collections")


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize vector store
    vs = VectorStore()
    
    # Example resume chunks (preprocessed from your PDF)
    resume_chunks = [
        "Chayma Barkaoui Looking for new opportunities +21624171267 chaymaabarkaoui@gmail.com",
        "AI Software Developer at E-Tafakna (October 2024-Currently)",
        "Developed multilingual Legal AI agent using LLMs (GPT, Claude) for Tunisian legal scenarios",
        "Built contract recommendation system with Azure AI Search and Tesseract-OCR",
        "Designed contract health check system with risk percentage analysis",
        "Implemented AI-powered clause analyzer for contract compliance",
        "Freelance AI Developer (2023-2024) on Upwork",
        "Created plagiarism detection system using Self-Organizing Maps and transformer models",
        "Built YouTube semantic search engine with SentenceTransformer and Pinecone",
        "Master's Thesis: Fuzzy sentiment analysis for financial forecasting with 22% RMSE improvement"
    ]
    
    # Add resume chunks with metadata
    vs.add_resume_chunks(
        chunks=resume_chunks,
        metadata={
            "candidate": "Chayma Barkaoui",
            "source": "CV_PDF_2024"
        }
    )
    
    # Example job requirements
    job_reqs = [
        "Seeking AI developer with experience in legal tech and LLMs",
        "Must have Azure AI and document processing experience",
        "Experience with contract analysis and risk assessment preferred",
        "Knowledge of multilingual NLP systems is a plus"
    ]
    
    # Add job requirements
    vs.add_job_requirements(
        requirements=job_reqs,
        metadata={
            "job_id": "AI_LEGAL_123",
            "company": "LegalTech Inc"
        }
    )
    
    # Search for similar chunks (original function name)
    print("\nSearching for legal AI experience:")
    results = vs.find_similar_chunks("legal AI experience with Azure", doc_type="resume")
    for i, res in enumerate(results, 1):
        print(f"{i}. Score: {res['distance']:.3f}")
        print(f"   Document: {res['document'][:100]}.")
        print(f"   Type: {res['type']} | Source: {res['metadata'].get('source', '')}")
    
    # Save and reload the index
    vs.save_index()
    vs.clear_collections()
    vs.load_index()