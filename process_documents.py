"""
Script to process and index sample documents into the vector store.
Run this script after setting up your environment to prepare the RAG system.
"""

import os
import logging
from rag_engine import RAGEngine
from config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Process all sample documents and add them to the vector store."""
    logger.info("Starting document processing...")
    
    # Validate configuration
    settings = get_settings()
    
    if not settings.validate_llm_config():
        logger.error("Invalid LLM configuration. Please check your .env file.")
        return
    
    if not settings.validate_vector_store_config():
        logger.error("Invalid vector store configuration. Please check your .env file.")
        return
    
    # Initialize RAG engine
    try:
        rag_engine = RAGEngine()
        logger.info("RAG engine initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize RAG engine: {e}")
        return
    
    # List of sample documents to process
    documents = [
        "company_policies.md",
        "product_faqs.md",
        "technical_documentation.md"
    ]
    
    # Process each document
    total_chunks = 0
    processed_count = 0
    
    for doc_name in documents:
        if not os.path.exists(doc_name):
            logger.warning(f"Document not found: {doc_name}")
            continue
        
        try:
            logger.info(f"Processing {doc_name}...")
            chunk_count = rag_engine.process_document(doc_name)
            total_chunks += chunk_count
            processed_count += 1
            logger.info(f"✓ {doc_name}: {chunk_count} chunks created")
        except Exception as e:
            logger.error(f"✗ Error processing {doc_name}: {e}")
    
    # Summary
    logger.info("\n" + "="*50)
    logger.info("Document Processing Summary")
    logger.info("="*50)
    logger.info(f"Documents processed: {processed_count}/{len(documents)}")
    logger.info(f"Total chunks created: {total_chunks}")
    logger.info(f"Vector store: {settings.vector_store}")
    logger.info("="*50)
    
    if processed_count > 0:
        logger.info("\n✓ Document processing completed successfully!")
        logger.info("You can now start the FastAPI server with: uvicorn main:app --reload")
    else:
        logger.error("\n✗ No documents were processed. Please check the errors above.")


if __name__ == "__main__":
    main()
