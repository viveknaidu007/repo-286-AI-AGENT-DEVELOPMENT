#!/bin/bash

# Azure App Service startup script
# This script is executed when the container starts on Azure

echo "Starting RAG AI Agent on Azure..."

# Install dependencies if needed
if [ -f requirements.txt ]; then
    echo "Installing Python dependencies..."
    pip install --no-cache-dir -r requirements.txt
fi

# Process documents if vector store is empty
if [ ! -d "vector_store" ]; then
    echo "Processing documents for the first time..."
    python process_documents.py
fi

# Start the FastAPI application
echo "Starting FastAPI server..."
uvicorn main:app --host 0.0.0.0 --port 8000
