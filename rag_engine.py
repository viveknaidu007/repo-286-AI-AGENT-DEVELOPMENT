"""
RAG (Retrieval-Augmented Generation) engine for document processing and retrieval.
Handles document chunking, embedding, and context retrieval for the AI agent.
"""

import os
import re
from typing import List, Dict, Any, Optional
import logging

# For document processing
import markdown
from pypdf import PdfReader

from vector_stores import get_vector_store
from config import get_settings

logger = logging.getLogger(__name__)


class RAGEngine:
    """RAG engine for document processing and retrieval."""
    
    def __init__(self):
        self.settings = get_settings()
        self.vector_store = get_vector_store()
        logger.info("Initialized RAG engine")
    
    def process_document(
        self, 
        file_path: str,
        source_name: Optional[str] = None
    ) -> int:
        """
        Process a document and add it to the vector store.
        
        Args:
            file_path: Path to the document file
            source_name: Optional name for the source (defaults to filename)
        
        Returns:
            Number of chunks created
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Determine source name
        if source_name is None:
            source_name = os.path.basename(file_path)
        
        # Extract text based on file type
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.pdf':
            text = self._extract_from_pdf(file_path)
        elif file_ext in ['.md', '.markdown']:
            text = self._extract_from_markdown(file_path)
        elif file_ext == '.txt':
            text = self._extract_from_text(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")
        
        # Chunk the text
        chunks = self._chunk_text(text)
        
        # Create document objects
        documents = [
            {
                'content': chunk,
                'source': source_name,
                'metadata': {
                    'file_path': file_path,
                    'chunk_index': i,
                    'total_chunks': len(chunks)
                }
            }
            for i, chunk in enumerate(chunks)
        ]
        
        # Add to vector store
        self.vector_store.add_documents(documents)
        
        logger.info(f"Processed {source_name}: {len(chunks)} chunks created")
        return len(chunks)
    
    def _extract_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file."""
        try:
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            logger.error(f"Error extracting from PDF: {e}")
            raise
    
    def _extract_from_markdown(self, file_path: str) -> str:
        """Extract text from Markdown file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                md_content = f.read()
            
            # Convert markdown to plain text (remove formatting)
            # For better results, we keep the markdown as-is
            return md_content
        except Exception as e:
            logger.error(f"Error extracting from Markdown: {e}")
            raise
    
    def _extract_from_text(self, file_path: str) -> str:
        """Extract text from plain text file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error extracting from text file: {e}")
            raise
    
    def _chunk_text(self, text: str) -> List[str]:
        """
        Chunk text into smaller pieces with overlap.
        Uses a simple character-based chunking strategy.
        """
        chunk_size = self.settings.chunk_size
        chunk_overlap = self.settings.chunk_overlap
        
        # Clean up the text
        text = re.sub(r'\n\s*\n', '\n\n', text)  # Remove excessive newlines
        text = text.strip()
        
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # If this is not the last chunk, try to break at a sentence or paragraph
            if end < len(text):
                # Look for paragraph break
                paragraph_break = text.rfind('\n\n', start, end)
                if paragraph_break != -1 and paragraph_break > start:
                    end = paragraph_break
                else:
                    # Look for sentence break
                    sentence_break = max(
                        text.rfind('. ', start, end),
                        text.rfind('! ', start, end),
                        text.rfind('? ', start, end)
                    )
                    if sentence_break != -1 and sentence_break > start:
                        end = sentence_break + 1
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move start position with overlap
            start = end - chunk_overlap if end < len(text) else end
        
        return chunks
    
    def retrieve_context(
        self, 
        query: str, 
        top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant context for a query.
        
        Args:
            query: The user's query
            top_k: Number of chunks to retrieve (defaults to config value)
        
        Returns:
            List of relevant document chunks with metadata
        """
        if top_k is None:
            top_k = self.settings.max_chunks_to_retrieve
        
        results = self.vector_store.search(query, top_k=top_k)
        
        logger.info(f"Retrieved {len(results)} context chunks for query")
        return results
    
    def format_context(self, chunks: List[Dict[str, Any]]) -> str:
        """
        Format retrieved chunks into a context string for the LLM.
        
        Args:
            chunks: List of document chunks
        
        Returns:
            Formatted context string
        """
        if not chunks:
            return ""
        
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            source = chunk.get('source', 'Unknown')
            content = chunk.get('content', '')
            score = chunk.get('score', 0)
            
            context_parts.append(
                f"[Source {i}: {source} (relevance: {score:.2f})]\n{content}\n"
            )
        
        return "\n---\n".join(context_parts)
    
    def get_sources(self, chunks: List[Dict[str, Any]]) -> List[str]:
        """
        Extract unique source names from chunks.
        
        Args:
            chunks: List of document chunks
        
        Returns:
            List of unique source names
        """
        sources = set()
        for chunk in chunks:
            source = chunk.get('source', '')
            if source:
                sources.add(source)
        
        return sorted(list(sources))
    
    def process_all_documents(self, documents_dir: str = ".") -> Dict[str, int]:
        """
        Process all supported documents in a directory.
        
        Args:
            documents_dir: Directory containing documents
        
        Returns:
            Dictionary mapping filenames to chunk counts
        """
        supported_extensions = ['.pdf', '.md', '.markdown', '.txt']
        results = {}
        
        for filename in os.listdir(documents_dir):
            file_path = os.path.join(documents_dir, filename)
            
            if not os.path.isfile(file_path):
                continue
            
            file_ext = os.path.splitext(filename)[1].lower()
            if file_ext not in supported_extensions:
                continue
            
            try:
                chunk_count = self.process_document(file_path, filename)
                results[filename] = chunk_count
            except Exception as e:
                logger.error(f"Error processing {filename}: {e}")
                results[filename] = 0
        
        return results
