"""
AI Agent with tool calling, session memory, and RAG capabilities.
Decides whether to answer directly or use document retrieval.
"""

from typing import Dict, Any, List, Optional
import logging
import uuid
from datetime import datetime, timedelta

from app.llm_providers import get_llm_provider
from app.rag_engine import RAGEngine
from app.config import get_settings

logger = logging.getLogger(__name__)


class SessionMemory:
    """Simple in-memory session storage for conversation history."""
    
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.settings = get_settings()
    
    def get_or_create_session(self, session_id: Optional[str] = None) -> str:
        """Get existing session or create a new one."""
        if session_id and session_id in self.sessions:
            # Update last accessed time
            self.sessions[session_id]['last_accessed'] = datetime.now()
            return session_id
        
        # Create new session
        new_session_id = session_id or str(uuid.uuid4())
        self.sessions[new_session_id] = {
            'history': [],
            'created_at': datetime.now(),
            'last_accessed': datetime.now()
        }
        logger.info(f"Created new session: {new_session_id}")
        return new_session_id
    
    def add_message(
        self, 
        session_id: str, 
        role: str, 
        content: str
    ) -> None:
        """Add a message to session history."""
        if session_id not in self.sessions:
            self.get_or_create_session(session_id)
        
        self.sessions[session_id]['history'].append({
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat()
        })
        
        # Keep only recent messages
        max_history = self.settings.max_conversation_history
        if len(self.sessions[session_id]['history']) > max_history * 2:
            self.sessions[session_id]['history'] = \
                self.sessions[session_id]['history'][-max_history * 2:]
    
    def get_history(self, session_id: str) -> List[Dict[str, str]]:
        """Get conversation history for a session."""
        if session_id not in self.sessions:
            return []
        
        return self.sessions[session_id]['history']
    
    def cleanup_old_sessions(self) -> int:
        """Remove sessions that haven't been accessed recently."""
        timeout = timedelta(seconds=self.settings.session_timeout)
        now = datetime.now()
        
        expired_sessions = [
            sid for sid, data in self.sessions.items()
            if now - data['last_accessed'] > timeout
        ]
        
        for sid in expired_sessions:
            del self.sessions[sid]
        
        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
        
        return len(expired_sessions)


class AIAgent:
    """AI Agent with RAG capabilities and tool calling."""
    
    # Define available tools
    TOOLS = [
        {
            "name": "search_documents",
            "description": "Search through company documents to find relevant information. "
                          "Use this when the user asks about company policies, products, "
                          "technical details, or any information that might be in the documents.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to find relevant information"
                    }
                },
                "required": ["query"]
            }
        }
    ]
    
    def __init__(self):
        self.llm_provider = get_llm_provider()
        self.rag_engine = RAGEngine()
        self.session_memory = SessionMemory()
        logger.info("Initialized AI Agent")
    
    def _should_use_rag(self, query: str) -> bool:
        """
        Decide if the query requires RAG or can be answered directly.
        Uses a simple LLM call to make the decision.
        """
        decision_prompt = f"""You are a helpful assistant. Analyze this user query and decide if you need to search through documents to answer it, or if you can answer directly from your general knowledge.

User query: "{query}"

Respond with ONLY one word:
- "SEARCH" if you need to search documents (for company-specific info, policies, products, technical details)
- "DIRECT" if you can answer from general knowledge

Response:"""
        
        try:
            response = self.llm_provider.generate_response(
                prompt=decision_prompt,
                system_message="You are a decision-making assistant. Respond with only SEARCH or DIRECT."
            )
            
            decision = response.strip().upper()
            logger.info(f"Decision for query: {decision}")
            
            return "SEARCH" in decision
        except Exception as e:
            logger.error(f"Error in decision making: {e}")
            # Default to using RAG if unsure
            return True
    
    def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool and return results."""
        if tool_name == "search_documents":
            query = arguments.get("query", "")
            chunks = self.rag_engine.retrieve_context(query)
            context = self.rag_engine.format_context(chunks)
            sources = self.rag_engine.get_sources(chunks)
            
            return {
                "context": context,
                "sources": sources,
                "chunks_found": len(chunks)
            }
        else:
            logger.warning(f"Unknown tool: {tool_name}")
            return {"error": f"Unknown tool: {tool_name}"}
    
    def process_query(
        self, 
        query: str, 
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a user query and generate a response.
        
        Args:
            query: The user's question
            session_id: Optional session ID for conversation continuity
        
        Returns:
            Dictionary containing answer, sources, and session info
        """
        # Get or create session
        session_id = self.session_memory.get_or_create_session(session_id)
        
        # Add user message to history
        self.session_memory.add_message(session_id, "user", query)
        
        # Get conversation history
        history = self.session_memory.get_history(session_id)
        
        # Decide whether to use RAG
        use_rag = self._should_use_rag(query)
        
        sources = []
        answer = ""
        
        try:
            if use_rag:
                logger.info("Using RAG for query")
                
                # Retrieve relevant context
                chunks = self.rag_engine.retrieve_context(query)
                context = self.rag_engine.format_context(chunks)
                sources = self.rag_engine.get_sources(chunks)
                
                if not chunks:
                    # No relevant documents found
                    system_message = """You are a helpful AI assistant. The user asked a question but no relevant documents were found. Politely inform them that you don't have specific information about their query in the available documents, but try to provide general helpful information if possible."""
                    
                    answer = self.llm_provider.generate_response(
                        prompt=query,
                        system_message=system_message,
                        conversation_history=history[-10:]  # Last 5 exchanges
                    )
                else:
                    # Generate answer using retrieved context
                    system_message = """You are a helpful AI assistant. Use the provided context from documents to answer the user's question accurately. If the context doesn't contain enough information, say so. Always cite the sources when providing information."""
                    
                    enhanced_prompt = f"""Context from documents:
{context}

User question: {query}

Please provide a clear, accurate answer based on the context above. Mention which sources you're using."""
                    
                    answer = self.llm_provider.generate_response(
                        prompt=enhanced_prompt,
                        system_message=system_message,
                        conversation_history=history[-10:]
                    )
            else:
                logger.info("Answering directly without RAG")
                
                # Answer directly without RAG
                system_message = """You are a helpful AI assistant. Answer the user's question clearly and concisely using your general knowledge."""
                
                answer = self.llm_provider.generate_response(
                    prompt=query,
                    system_message=system_message,
                    conversation_history=history[-10:]
                )
            
            # Add assistant response to history
            self.session_memory.add_message(session_id, "assistant", answer)
            
            return {
                "answer": answer,
                "sources": sources,
                "session_id": session_id,
                "used_rag": use_rag
            }
        
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            error_message = "I apologize, but I encountered an error while processing your question. Please try again."
            
            return {
                "answer": error_message,
                "sources": [],
                "session_id": session_id,
                "used_rag": False,
                "error": str(e)
            }
    
    def cleanup_sessions(self) -> int:
        """Clean up expired sessions."""
        return self.session_memory.cleanup_old_sessions()
