"""
FastAPI endpoints for RAG pipeline with monitoring
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncio

from app.rag_pipeline_complete import CompleteRAGPipeline

# Initialize pipeline
pipeline = CompleteRAGPipeline()

# Create FastAPI app
app = FastAPI(
    title="RAG Pipeline API",
    description="Production RAG system with retrieval, reranking, and generation",
    version="2.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class QueryRequest(BaseModel):
    query: str = Field(..., description="User question", min_length=1, max_length=500)
    stream: bool = Field(False, description="Enable streaming response")
    
class CitationResponse(BaseModel):
    id: int
    citation: str
    chunk_id: str
    relevance_score: float

class QueryResponse(BaseModel):
    question: str
    answer: str
    citations: List[CitationResponse]
    latency_ms: Dict[str, float]
    cost_usd: float
    tokens_used: int
    timestamp: str

class MetricsResponse(BaseModel):
    queries_processed: int
    total_latency_ms: float
    total_cost_usd: float
    avg_latency_ms: float
    avg_cost_per_query_usd: float

# API Endpoints
@app.get("/", tags=["Health"])
async def root():
    return {
        "status": "healthy",
        "service": "RAG Pipeline API",
        "version": "2.0.0",
        "documents_indexed": len(pipeline.documents)
    }

@app.post("/query", response_model=QueryResponse, tags=["RAG"])
async def query_endpoint(request: QueryRequest):
    """Execute complete RAG pipeline: retrieval → reranking → generation"""
    try:
        result = pipeline.query(request.query, verbose=False)
        
        return QueryResponse(
            question=result["question"],
            answer=result["answer"],
            citations=[CitationResponse(**c) for c in result["citations"]],
            latency_ms=result["latency_ms"],
            cost_usd=result["cost_usd"],
            tokens_used=result["tokens_used"],
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics", response_model=MetricsResponse, tags=["Monitoring"])
async def get_metrics():
    """Get pipeline performance metrics"""
    metrics = pipeline.get_metrics()
    return MetricsResponse(
        queries_processed=metrics["queries_processed"],
        total_latency_ms=metrics["total_latency_ms"],
        total_cost_usd=metrics["total_cost_usd"],
        avg_latency_ms=metrics.get("avg_latency_ms", 0),
        avg_cost_per_query_usd=metrics.get("avg_cost_per_query_usd", 0)
    )

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# Prometheus metrics endpoint
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, Counter, Histogram

QUERY_COUNT = Counter('rag_queries_total', 'Total number of queries')
QUERY_LATENCY = Histogram('rag_query_latency_seconds', 'Query latency in seconds')

@app.get("/metrics/prometheus", tags=["Monitoring"])
async def prometheus_metrics():
    return generate_latest()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
