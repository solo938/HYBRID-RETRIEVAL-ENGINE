# observability/logging.py - Structured logging
import json
import logging
from datetime import datetime
from typing import Dict, Any
from pythonjsonlogger import jsonlogger

class StructuredLogger:
    """Structured JSON logger for RAG pipeline"""
    
    def __init__(self, name: str = "rag_pipeline"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # JSON formatter
        formatter = jsonlogger.JsonFormatter(
            '%(asctime)s %(name)s %(levelname)s %(message)s',
            rename_fields={'asctime': 'timestamp'}
        )
        
        # Console handler
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    def log_query(self, query_id: str, query: str, domain: str, latency_ms: float):
        """Log query execution"""
        self.logger.info(json.dumps({
            "event": "query_execution",
            "query_id": query_id,
            "query": query,
            "domain": domain,
            "latency_ms": latency_ms,
            "timestamp": datetime.utcnow().isoformat()
        }))
    
    def log_retrieval(self, query_id: str, num_docs: int, scores: list):
        """Log retrieval results"""
        self.logger.info(json.dumps({
            "event": "retrieval_results",
            "query_id": query_id,
            "num_documents": num_docs,
            "top_scores": scores[:5],
            "timestamp": datetime.utcnow().isoformat()
        }))
    
    def log_error(self, query_id: str, error: str, stack_trace: str = None):
        """Log errors"""
        self.logger.error(json.dumps({
            "event": "error",
            "query_id": query_id,
            "error": error,
            "stack_trace": stack_trace,
            "timestamp": datetime.utcnow().isoformat()
        }))
    
    def log_generation(self, query_id: str, model: str, tokens: int, cost: float):
        """Log LLM generation"""
        self.logger.info(json.dumps({
            "event": "llm_generation",
            "query_id": query_id,
            "model": model,
            "tokens_used": tokens,
            "cost_usd": cost,
            "timestamp": datetime.utcnow().isoformat()
        }))

# Global logger instance
rag_logger = StructuredLogger()