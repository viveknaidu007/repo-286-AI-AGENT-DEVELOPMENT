"""
Vector store implementations for FAISS, Pinecone, and Azure AI Search.
Default is FAISS (local, free), with commented code for cloud alternatives.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import os
import pickle
import logging

# FAISS (Default - Local)
import faiss
import numpy as np

# Pinecone (Uncomment to use)
# import pinecone

# Azure AI Search (Uncomment to use)
# from azure.search.documents import SearchClient
# from azure.search.documents.indexes import SearchIndexClient
# from azure.search.documents.models import VectorizedQuery
# from azure.core.credentials import AzureKeyCredential

from sentence_transformers import SentenceTransformer
from config import get_settings

logger = logging.getLogger(__name__)


class BaseVectorStore(ABC):
    """Base class for vector stores."""
    
    @abstractmethod
    def add_documents(
        self, 
        documents: List[Dict[str, Any]]
    ) -> None:
        """Add documents to the vector store."""
        pass
    
    @abstractmethod
    def search(
        self, 
        query: str, 
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Search for similar documents."""
        pass
    
    @abstractmethod
    def delete_all(self) -> None:
        """Delete all documents from the store."""
        pass


class FAISSVectorStore(BaseVectorStore):
    """FAISS vector store implementation (Default - Local, Free)."""
    
    def __init__(self):
        settings = get_settings()
        self.index_path = settings.faiss_index_path
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.dimension = 384  # Dimension for all-MiniLM-L6-v2
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        
        # Load or create index
        self.index = self._load_or_create_index()
        self.documents = self._load_documents()
        
        logger.info(f"Initialized FAISS vector store at {self.index_path}")
    
    def _load_or_create_index(self) -> faiss.Index:
        """Load existing FAISS index or create a new one."""
        index_file = f"{self.index_path}.index"
        
        if os.path.exists(index_file):
            try:
                index = faiss.read_index(index_file)
                logger.info(f"Loaded existing FAISS index with {index.ntotal} vectors")
                return index
            except Exception as e:
                logger.warning(f"Error loading index: {e}. Creating new index.")
        
        # Create new index using L2 distance
        index = faiss.IndexFlatL2(self.dimension)
        logger.info("Created new FAISS index")
        return index
    
    def _load_documents(self) -> List[Dict[str, Any]]:
        """Load document metadata."""
        docs_file = f"{self.index_path}.docs"
        
        if os.path.exists(docs_file):
            try:
                with open(docs_file, 'rb') as f:
                    documents = pickle.load(f)
                logger.info(f"Loaded {len(documents)} document metadata entries")
                return documents
            except Exception as e:
                logger.warning(f"Error loading documents: {e}")
        
        return []
    
    def _save_index(self) -> None:
        """Save FAISS index to disk."""
        try:
            faiss.write_index(self.index, f"{self.index_path}.index")
            logger.info("Saved FAISS index")
        except Exception as e:
            logger.error(f"Error saving index: {e}")
    
    def _save_documents(self) -> None:
        """Save document metadata to disk."""
        try:
            with open(f"{self.index_path}.docs", 'wb') as f:
                pickle.dump(self.documents, f)
            logger.info("Saved document metadata")
        except Exception as e:
            logger.error(f"Error saving documents: {e}")
    
    def add_documents(
        self, 
        documents: List[Dict[str, Any]]
    ) -> None:
        """Add documents to FAISS index."""
        if not documents:
            return
        
        # Extract text content for embedding
        texts = [doc.get('content', '') for doc in documents]
        
        # Generate embeddings
        embeddings = self.embedding_model.encode(texts, convert_to_numpy=True)
        
        # Add to FAISS index
        self.index.add(embeddings.astype('float32'))
        
        # Store document metadata
        self.documents.extend(documents)
        
        # Save to disk
        self._save_index()
        self._save_documents()
        
        logger.info(f"Added {len(documents)} documents to FAISS index")
    
    def search(
        self, 
        query: str, 
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Search for similar documents using FAISS."""
        if self.index.ntotal == 0:
            logger.warning("Index is empty, no results to return")
            return []
        
        # Generate query embedding
        query_embedding = self.embedding_model.encode([query], convert_to_numpy=True)
        
        # Search
        top_k = min(top_k, self.index.ntotal)
        distances, indices = self.index.search(query_embedding.astype('float32'), top_k)
        
        # Retrieve documents
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx < len(self.documents):
                doc = self.documents[idx].copy()
                doc['score'] = float(1 / (1 + distance))  # Convert distance to similarity score
                results.append(doc)
        
        logger.info(f"Found {len(results)} results for query")
        return results
    
    def delete_all(self) -> None:
        """Delete all documents and reset index."""
        self.index = faiss.IndexFlatL2(self.dimension)
        self.documents = []
        self._save_index()
        self._save_documents()
        logger.info("Deleted all documents from FAISS index")


# Uncomment below to use Pinecone
"""
class PineconeVectorStore(BaseVectorStore):
    '''Pinecone vector store implementation.'''
    
    def __init__(self):
        settings = get_settings()
        
        # Initialize Pinecone
        pinecone.init(
            api_key=settings.pinecone_api_key,
            environment=settings.pinecone_environment
        )
        
        self.index_name = settings.pinecone_index_name
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.dimension = 384
        
        # Create index if it doesn't exist
        if self.index_name not in pinecone.list_indexes():
            pinecone.create_index(
                name=self.index_name,
                dimension=self.dimension,
                metric='cosine'
            )
            logger.info(f"Created Pinecone index: {self.index_name}")
        
        self.index = pinecone.Index(self.index_name)
        logger.info(f"Initialized Pinecone vector store: {self.index_name}")
    
    def add_documents(
        self, 
        documents: List[Dict[str, Any]]
    ) -> None:
        '''Add documents to Pinecone index.'''
        if not documents:
            return
        
        # Prepare vectors for upsert
        vectors = []
        for i, doc in enumerate(documents):
            text = doc.get('content', '')
            embedding = self.embedding_model.encode(text).tolist()
            
            vector_id = doc.get('id', f"doc_{i}")
            metadata = {
                'content': text,
                'source': doc.get('source', ''),
                'metadata': doc.get('metadata', {})
            }
            
            vectors.append((vector_id, embedding, metadata))
        
        # Upsert to Pinecone
        self.index.upsert(vectors=vectors)
        logger.info(f"Added {len(documents)} documents to Pinecone")
    
    def search(
        self, 
        query: str, 
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        '''Search for similar documents in Pinecone.'''
        # Generate query embedding
        query_embedding = self.embedding_model.encode(query).tolist()
        
        # Search
        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True
        )
        
        # Format results
        formatted_results = []
        for match in results.matches:
            doc = {
                'content': match.metadata.get('content', ''),
                'source': match.metadata.get('source', ''),
                'score': match.score,
                'metadata': match.metadata.get('metadata', {})
            }
            formatted_results.append(doc)
        
        logger.info(f"Found {len(formatted_results)} results from Pinecone")
        return formatted_results
    
    def delete_all(self) -> None:
        '''Delete all vectors from Pinecone index.'''
        self.index.delete(delete_all=True)
        logger.info("Deleted all documents from Pinecone")
"""


# Uncomment below to use Azure AI Search
"""
class AzureAISearchVectorStore(BaseVectorStore):
    '''Azure AI Search vector store implementation.'''
    
    def __init__(self):
        settings = get_settings()
        
        self.endpoint = settings.azure_search_endpoint
        self.index_name = settings.azure_search_index_name
        self.credential = AzureKeyCredential(settings.azure_search_api_key)
        
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.dimension = 384
        
        # Initialize clients
        self.search_client = SearchClient(
            endpoint=self.endpoint,
            index_name=self.index_name,
            credential=self.credential
        )
        
        self.index_client = SearchIndexClient(
            endpoint=self.endpoint,
            credential=self.credential
        )
        
        # Create index if it doesn't exist
        self._create_index_if_not_exists()
        
        logger.info(f"Initialized Azure AI Search: {self.index_name}")
    
    def _create_index_if_not_exists(self) -> None:
        '''Create search index if it doesn't exist.'''
        from azure.search.documents.indexes.models import (
            SearchIndex,
            SimpleField,
            SearchableField,
            SearchField,
            VectorSearch,
            VectorSearchProfile,
            HnswAlgorithmConfiguration
        )
        
        try:
            # Check if index exists
            self.index_client.get_index(self.index_name)
            logger.info(f"Index {self.index_name} already exists")
        except:
            # Create index
            fields = [
                SimpleField(name="id", type="Edm.String", key=True),
                SearchableField(name="content", type="Edm.String"),
                SearchableField(name="source", type="Edm.String"),
                SearchField(
                    name="embedding",
                    type="Collection(Edm.Single)",
                    searchable=True,
                    vector_search_dimensions=self.dimension,
                    vector_search_profile_name="default-profile"
                )
            ]
            
            vector_search = VectorSearch(
                profiles=[VectorSearchProfile(
                    name="default-profile",
                    algorithm_configuration_name="default-algo"
                )],
                algorithms=[HnswAlgorithmConfiguration(name="default-algo")]
            )
            
            index = SearchIndex(
                name=self.index_name,
                fields=fields,
                vector_search=vector_search
            )
            
            self.index_client.create_index(index)
            logger.info(f"Created index {self.index_name}")
    
    def add_documents(
        self, 
        documents: List[Dict[str, Any]]
    ) -> None:
        '''Add documents to Azure AI Search.'''
        if not documents:
            return
        
        # Prepare documents for upload
        search_docs = []
        for i, doc in enumerate(documents):
            text = doc.get('content', '')
            embedding = self.embedding_model.encode(text).tolist()
            
            search_doc = {
                'id': doc.get('id', f"doc_{i}"),
                'content': text,
                'source': doc.get('source', ''),
                'embedding': embedding
            }
            search_docs.append(search_doc)
        
        # Upload to Azure Search
        self.search_client.upload_documents(documents=search_docs)
        logger.info(f"Added {len(documents)} documents to Azure AI Search")
    
    def search(
        self, 
        query: str, 
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        '''Search for similar documents in Azure AI Search.'''
        # Generate query embedding
        query_embedding = self.embedding_model.encode(query).tolist()
        
        # Create vector query
        vector_query = VectorizedQuery(
            vector=query_embedding,
            k_nearest_neighbors=top_k,
            fields="embedding"
        )
        
        # Search
        results = self.search_client.search(
            search_text=None,
            vector_queries=[vector_query],
            select=["content", "source"]
        )
        
        # Format results
        formatted_results = []
        for result in results:
            doc = {
                'content': result.get('content', ''),
                'source': result.get('source', ''),
                'score': result.get('@search.score', 0)
            }
            formatted_results.append(doc)
        
        logger.info(f"Found {len(formatted_results)} results from Azure AI Search")
        return formatted_results
    
    def delete_all(self) -> None:
        '''Delete all documents from Azure AI Search.'''
        # This requires fetching all document IDs first
        results = self.search_client.search(search_text="*", select=["id"])
        doc_ids = [{"id": result["id"]} for result in results]
        
        if doc_ids:
            self.search_client.delete_documents(documents=doc_ids)
            logger.info(f"Deleted {len(doc_ids)} documents from Azure AI Search")
"""


def get_vector_store() -> BaseVectorStore:
    """Factory function to get the configured vector store."""
    settings = get_settings()
    
    if settings.vector_store == "faiss":
        return FAISSVectorStore()
    # Uncomment below when using Pinecone
    # elif settings.vector_store == "pinecone":
    #     return PineconeVectorStore()
    # Uncomment below when using Azure AI Search
    # elif settings.vector_store == "azure_search":
    #     return AzureAISearchVectorStore()
    else:
        raise ValueError(f"Unsupported vector store: {settings.vector_store}")
