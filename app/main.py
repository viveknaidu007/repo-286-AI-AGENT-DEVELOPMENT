"""
FastAPI application for RAG AI Agent.
Provides REST API endpoints and serves the frontend.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel, Field
from typing import Optional, List
import logging
import os
from contextlib import asynccontextmanager

from app.agent import AIAgent
from app.config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global agent instance
agent: Optional[AIAgent] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    global agent
    
    # Startup
    logger.info("Starting up RAG AI Agent...")
    settings = get_settings()
    
    # Validate configuration
    if not settings.validate_llm_config():
        logger.error("Invalid LLM configuration. Please check your environment variables.")
        raise RuntimeError("Invalid LLM configuration")
    
    if not settings.validate_vector_store_config():
        logger.error("Invalid vector store configuration. Please check your environment variables.")
        raise RuntimeError("Invalid vector store configuration")
    
    # Initialize agent
    agent = AIAgent()
    logger.info("RAG AI Agent initialized successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down RAG AI Agent...")
    if agent:
        agent.cleanup_sessions()


# Create FastAPI app
settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_allowed_origins_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response models
class AskRequest(BaseModel):
    """Request model for /ask endpoint."""
    query: str = Field(..., description="User's question", min_length=1)
    session_id: Optional[str] = Field(None, description="Optional session ID for conversation continuity")


class AskResponse(BaseModel):
    """Response model for /ask endpoint."""
    answer: str = Field(..., description="AI-generated answer")
    sources: List[str] = Field(default_factory=list, description="Source documents used")
    session_id: str = Field(..., description="Session ID for this conversation")
    used_rag: bool = Field(..., description="Whether RAG was used for this query")


class HealthResponse(BaseModel):
    """Response model for /health endpoint."""
    status: str
    version: str
    llm_provider: str
    vector_store: str


# API Endpoints
@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main frontend page."""
    index_path = os.path.join("static", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return HTMLResponse(content="<h1>RAG AI Agent</h1><p>Frontend not found. Please ensure static/index.html exists.</p>")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    Returns the status of the application and configuration.
    """
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        llm_provider=settings.llm_provider,
        vector_store=settings.vector_store
    )


@app.post("/ask", response_model=AskResponse)
async def ask_question(request: AskRequest):
    """
    Main endpoint for asking questions to the AI agent.
    
    The agent will decide whether to:
    - Answer directly using the LLM
    - Retrieve relevant information from documents using RAG
    
    Returns the answer along with source documents if RAG was used.
    """
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        logger.info(f"Processing query: {request.query[:100]}...")
        
        result = agent.process_query(
            query=request.query,
            session_id=request.session_id
        )
        
        return AskResponse(
            answer=result["answer"],
            sources=result.get("sources", []),
            session_id=result["session_id"],
            used_rag=result.get("used_rag", False)
        )
    
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/cleanup-sessions")
async def cleanup_sessions():
    """
    Cleanup expired sessions.
    This endpoint can be called periodically to free up memory.
    """
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        cleaned = agent.cleanup_sessions()
        return {"message": f"Cleaned up {cleaned} expired sessions"}
    except Exception as e:
        logger.error(f"Error cleaning up sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Mount static files (CSS, JS, etc.)
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """Custom 404 handler."""
    return {"error": "Not found", "path": str(request.url)}


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    """Custom 500 handler."""
    logger.error(f"Internal error: {exc}")
    return {"error": "Internal server error", "detail": str(exc)}


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
