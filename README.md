# RAG AI Agent - Intelligent Document Assistant

A production-ready **Retrieval-Augmented Generation (RAG)** system built with FastAPI, featuring an AI agent that intelligently decides whether to answer questions directly or retrieve information from documents. Supports multiple LLM providers and vector storage options.

![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## 🌟 Features

- **Intelligent AI Agent**: Automatically decides whether to use RAG or answer directly
- **Multiple LLM Providers**: Google Gemini (default), OpenAI, Azure OpenAI
- **Flexible Vector Storage**: FAISS (local), Pinecone, Azure AI Search
- **Session-Based Memory**: Maintains conversation context across multiple queries
- **Tool Calling**: Extensible tool system for document search
- **Modern Frontend**: Beautiful, responsive UI with dark mode and glassmorphism
- **Production Ready**: Comprehensive error handling, logging, and monitoring
- **Azure Deployment**: Full Azure integration with deployment scripts

## 📋 Table of Contents

- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Switching Providers](#switching-providers)
- [API Documentation](#api-documentation)
- [Azure Deployment](#azure-deployment)
- [Design Decisions](#design-decisions)
- [Limitations](#limitations)
- [Future Improvements](#future-improvements)

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                            │
│                  (HTML/CSS/JavaScript)                      │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/REST
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                        │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │   Routing    │  │  AI Agent    │  │  Session Memory │  │
│  │   /ask       │──│  - Decision  │──│  - History      │  │
│  │   /health    │  │  - Tools     │  │  - Cleanup      │  │
│  └──────────────┘  └──────┬───────┘  └─────────────────┘  │
└─────────────────────────────┼────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
┌──────────────────────────┐    ┌──────────────────────────┐
│    LLM Provider Layer    │    │    RAG Engine            │
│  ┌────────────────────┐  │    │  ┌────────────────────┐ │
│  │ Google Gemini (✓)  │  │    │  │ Document Processor │ │
│  │ OpenAI             │  │    │  │ - PDF, MD, TXT     │ │
│  │ Azure OpenAI       │  │    │  │ - Chunking         │ │
│  └────────────────────┘  │    │  └─────────┬──────────┘ │
└──────────────────────────┘    │            │            │
                                │            ▼            │
                                │  ┌────────────────────┐ │
                                │  │ Embedding Model    │ │
                                │  │ (SentenceTransform)│ │
                                │  └─────────┬──────────┘ │
                                │            │            │
                                │            ▼            │
                                │  ┌────────────────────┐ │
                                │  │ Vector Store       │ │
                                │  │ - FAISS (✓)        │ │
                                │  │ - Pinecone         │ │
                                │  │ - Azure AI Search  │ │
                                │  └────────────────────┘ │
                                └──────────────────────────┘
```

### How It Works

1. **User Query**: User submits a question through the frontend
2. **Decision Making**: AI agent analyzes the query to determine if RAG is needed
3. **RAG Pipeline** (if needed):
   - Query is embedded using SentenceTransformer
   - Vector store retrieves top-k similar document chunks
   - Retrieved context is formatted and added to the prompt
4. **LLM Generation**: LLM generates response (with or without context)
5. **Response**: Answer is returned with source citations (if RAG was used)

## 🛠️ Tech Stack

### Backend
- **Framework**: FastAPI 0.109.0
- **LLM Orchestration**: LangChain 0.1.4
- **Default LLM**: Google Gemini (free tier)
- **Default Vector Store**: FAISS (local, free)
- **Embeddings**: SentenceTransformers (all-MiniLM-L6-v2)
- **Document Processing**: PyPDF, Markdown

### Frontend
- **HTML5**: Semantic markup
- **CSS3**: Modern styling with CSS variables, gradients, glassmorphism
- **Vanilla JavaScript**: No frameworks, pure ES6+
- **Fonts**: Google Fonts (Inter)

### Infrastructure
- **Server**: Uvicorn (ASGI)
- **Deployment**: Azure App Service
- **Monitoring**: Azure Application Insights (optional)

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- Google AI API key (free at [Google AI Studio](https://makersuite.google.com/app/apikey))
- Git

### Installation

1. **Clone the repository**

```bash
git clone <repository-url>
cd repo-286-AI-AGENT-DEVELOPMENT
```

2. **Create virtual environment**

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Configure environment**

```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your Google API key
# LLM_PROVIDER=google
# GOOGLE_API_KEY=your_google_api_key_here
```

5. **Process sample documents**

```bash
python process_documents.py
```

This will process the three sample documents:
- `company_policies.md`
- `product_faqs.md`
- `technical_documentation.md`

6. **Start the server**

```bash
uvicorn main:app --reload
```

7. **Open your browser**

Navigate to: `http://localhost:8000`

## ⚙️ Configuration

### Environment Variables

All configuration is done through environment variables. See `.env.example` for all available options.

#### LLM Provider Settings

```env
# Options: google, openai, azure_openai
LLM_PROVIDER=google

# Google Gemini (Default)
GOOGLE_API_KEY=your_key_here

# OpenAI (Uncomment to use)
# OPENAI_API_KEY=your_key_here
# OPENAI_MODEL=gpt-4

# Azure OpenAI (Uncomment to use)
# AZURE_OPENAI_API_KEY=your_key_here
# AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
# AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
```

#### Vector Store Settings

```env
# Options: faiss, pinecone, azure_search
VECTOR_STORE=faiss

# FAISS (Default - Local)
FAISS_INDEX_PATH=./vector_store/faiss_index

# Pinecone (Uncomment to use)
# PINECONE_API_KEY=your_key_here
# PINECONE_ENVIRONMENT=us-west1-gcp
# PINECONE_INDEX_NAME=rag-documents

# Azure AI Search (Uncomment to use)
# AZURE_SEARCH_ENDPOINT=https://your-search.search.windows.net
# AZURE_SEARCH_API_KEY=your_key_here
# AZURE_SEARCH_INDEX_NAME=rag-documents
```

#### Application Settings

```env
DEBUG=True
LOG_LEVEL=INFO
HOST=0.0.0.0
PORT=8000
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
MAX_CHUNKS_TO_RETRIEVE=5
SESSION_TIMEOUT=3600
```

## 🔄 Switching Providers

### Switching LLM Providers

#### To OpenAI:

1. **Install OpenAI package** (uncomment in `requirements.txt`):
```txt
openai==1.10.0
langchain-openai==0.0.5
```

2. **Uncomment OpenAI code** in `llm_providers.py`:
```python
# Uncomment the OpenAIProvider class
```

3. **Update `.env`**:
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=your_openai_key
```

4. **Reinstall dependencies**:
```bash
pip install -r requirements.txt
```

#### To Azure OpenAI:

1. **Install Azure OpenAI package** (uncomment in `requirements.txt`):
```txt
langchain-openai==0.0.5
```

2. **Uncomment Azure OpenAI code** in `llm_providers.py`:
```python
# Uncomment the AzureOpenAIProvider class
```

3. **Update `.env`**:
```env
LLM_PROVIDER=azure_openai
AZURE_OPENAI_API_KEY=your_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
```

### Switching Vector Stores

#### To Pinecone:

1. **Install Pinecone** (uncomment in `requirements.txt`):
```txt
pinecone-client==3.0.2
```

2. **Uncomment Pinecone code** in `vector_stores.py`:
```python
# Uncomment the PineconeVectorStore class
```

3. **Update `.env`**:
```env
VECTOR_STORE=pinecone
PINECONE_API_KEY=your_key
PINECONE_ENVIRONMENT=us-west1-gcp
```

4. **Reprocess documents**:
```bash
python process_documents.py
```

#### To Azure AI Search:

1. **Install Azure Search** (uncomment in `requirements.txt`):
```txt
azure-search-documents==11.4.0
azure-identity==1.15.0
```

2. **Uncomment Azure Search code** in `vector_stores.py`:
```python
# Uncomment the AzureAISearchVectorStore class
```

3. **Update `.env`**:
```env
VECTOR_STORE=azure_search
AZURE_SEARCH_ENDPOINT=https://your-search.search.windows.net
AZURE_SEARCH_API_KEY=your_key
```

## 📚 API Documentation

### Endpoints

#### `GET /`
Returns the frontend HTML page.

#### `GET /health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "llm_provider": "google",
  "vector_store": "faiss"
}
```

#### `POST /ask`
Main endpoint for asking questions.

**Request:**
```json
{
  "query": "What is the work from home policy?",
  "session_id": "optional-session-id"
}
```

**Response:**
```json
{
  "answer": "According to our company policy...",
  "sources": ["company_policies.md"],
  "session_id": "abc123...",
  "used_rag": true
}
```

#### `POST /cleanup-sessions`
Cleanup expired sessions (for maintenance).

**Response:**
```json
{
  "message": "Cleaned up 5 expired sessions"
}
```

### Interactive API Docs

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## ☁️ Azure Deployment

See [SETUP_AZURE.md](SETUP_AZURE.md) for comprehensive Azure deployment instructions.

### Quick Deploy

```bash
# 1. Create resources
az group create --name rg-rag-agent --location eastus

# 2. Deploy app
az webapp up \
  --name rag-agent-app \
  --resource-group rg-rag-agent \
  --runtime "PYTHON:3.11" \
  --sku B1

# 3. Configure environment variables
az webapp config appsettings set \
  --name rag-agent-app \
  --resource-group rg-rag-agent \
  --settings @.env.production
```

## 🎯 Design Decisions

### Why Google Gemini as Default?

- **Free tier**: No credit card required for development
- **Good performance**: Competitive with GPT-3.5 for most tasks
- **Easy switching**: Architecture allows seamless provider changes

### Why FAISS as Default Vector Store?

- **No external dependencies**: Works locally without API keys
- **Fast**: Excellent performance for small to medium datasets
- **Free**: No costs for development or production
- **Easy migration**: Can switch to cloud solutions later

### Why Simple Frontend?

- **No build step**: Pure HTML/CSS/JS for simplicity
- **Fast loading**: No heavy frameworks
- **Easy customization**: Straightforward to modify
- **Modern design**: Uses latest CSS features for premium look

### Session-Based Memory

- **Stateless API**: No database required
- **In-memory storage**: Fast access to conversation history
- **Auto-cleanup**: Expired sessions are automatically removed
- **Scalable**: Can be replaced with Redis for production

## ⚠️ Limitations

### Current Limitations

1. **In-Memory Sessions**: Sessions are lost on server restart
   - **Solution**: Use Redis or database for persistence

2. **Single-Server**: No built-in load balancing
   - **Solution**: Deploy behind Azure Load Balancer or use multiple instances

3. **Document Processing**: Must be done manually after deployment
   - **Solution**: Add document upload endpoint or automated processing

4. **No Authentication**: API is publicly accessible
   - **Solution**: Add Azure AD or API key authentication

5. **Limited File Types**: Only PDF, Markdown, and TXT supported
   - **Solution**: Add support for DOCX, HTML, etc.

6. **Embedding Model**: Fixed to all-MiniLM-L6-v2
   - **Solution**: Make embedding model configurable

### Performance Considerations

- **FAISS**: Good for <1M documents, consider Pinecone/Azure Search for larger datasets
- **Gemini**: Has rate limits on free tier, use paid tier or switch to Azure OpenAI for production
- **Chunking**: Fixed size chunking may split sentences, consider semantic chunking

## 🚀 Future Improvements

### Short Term

- [ ] Add document upload endpoint
- [ ] Implement user authentication
- [ ] Add Redis for session persistence
- [ ] Support more document formats (DOCX, HTML)
- [ ] Add conversation export functionality
- [ ] Implement rate limiting

### Medium Term

- [ ] Multi-language support
- [ ] Advanced chunking strategies (semantic, recursive)
- [ ] Document metadata filtering
- [ ] Conversation analytics dashboard
- [ ] A/B testing for different LLMs
- [ ] Streaming responses

### Long Term

- [ ] Multi-modal support (images, audio)
- [ ] Fine-tuned embedding models
- [ ] Automated document updates
- [ ] Knowledge graph integration
- [ ] Advanced agent capabilities (web search, calculations)
- [ ] Enterprise features (SSO, audit logs, compliance)

## 📝 License

This project is licensed under the MIT License.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📧 Support

For issues and questions:
- Create an issue in the repository
- Check existing documentation
- Review Azure deployment guide

## 🙏 Acknowledgments

- FastAPI for the excellent web framework
- LangChain for LLM orchestration
- Google for Gemini API
- Sentence Transformers for embeddings
- FAISS for vector search

---

**Built with ❤️ for the AI Engineer Assignment**
