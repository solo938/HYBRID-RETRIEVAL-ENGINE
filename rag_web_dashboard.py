"""
Complete RAG System with Web Dashboard - No Docker/Grafana needed
"""
import json
import time
import threading
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import numpy as np
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sentence_transformers import SentenceTransformer, CrossEncoder
from prometheus_client import Counter, Histogram, Gauge, generate_latest
import asyncio

# Initialize FastAPI
app = FastAPI(title="RAG System Dashboard", version="2.0.0")

# Prometheus metrics
QUERY_COUNT = Counter('rag_queries_total', 'Total queries processed')
QUERY_LATENCY = Histogram('rag_query_latency_seconds', 'Query latency', buckets=[0.1, 0.5, 1, 2, 5])
TOKENS_USED = Counter('rag_tokens_total', 'Total tokens used', ['type'])

class RAGSystem:
    def __init__(self):
        print("🚀 Loading RAG System...")
        self.dense_model = SentenceTransformer("BAAI/bge-small-en-v1.5")
        self.reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2", max_length=512)
        self.documents = []
        self.embeddings = []
        self.query_history = []
        self._load_documents()
        print(f"✅ Ready with {len(self.documents)} documents")
    
    def _load_documents(self):
        goldens = Path("app/evaluation/datasets/goldens")
        with open(goldens / "questions.json") as f:
            questions = json.load(f)
        
        for q in questions[:200]:  # Use 200 docs for speed
            if q.get("context"):
                self.documents.append({
                    "id": q["id"],
                    "content": q["context"],
                    "question": q["text"]
                })
        
        texts = [d["content"] for d in self.documents]
        self.embeddings = self.dense_model.encode(texts, normalize_embeddings=True)
    
    def search(self, query: str, limit: int = 10) -> List[Dict]:
        q_emb = self.dense_model.encode(query, normalize_embeddings=True)
        scores = self.embeddings @ q_emb
        top_idx = np.argsort(scores)[-limit:][::-1]
        
        results = []
        for i in top_idx:
            results.append({
                "id": self.documents[i]["id"],
                "content": self.documents[i]["content"][:300] + "...",
                "score": float(scores[i])
            })
        return results
    
    def query(self, question: str) -> Dict:
        start = time.time()
        QUERY_COUNT.inc()
        
        # Search
        results = self.search(question, limit=5)
        
        # Generate answer
        if results:
            answer = f"Based on the context: {results[0]['content'][:150]}..."
            citation = f"[1] {results[0]['id']}"
        else:
            answer = "I cannot answer based on the provided context."
            citation = ""
        
        latency = (time.time() - start) * 1000
        QUERY_LATENCY.observe(latency / 1000)
        
        query_record = {
            "question": question,
            "answer": answer,
            "citations": citation,
            "sources": len(results),
            "latency_ms": latency,
            "timestamp": datetime.now().isoformat()
        }
        self.query_history.insert(0, query_record)
        if len(self.query_history) > 50:
            self.query_history.pop()
        
        return query_record
    
    def get_stats(self):
        if not self.query_history:
            return {"queries": 0, "avg_latency": 0}
        
        latencies = [q["latency_ms"] for q in self.query_history]
        return {
            "total_queries": len(self.query_history),
            "avg_latency_ms": sum(latencies) / len(latencies),
            "p95_latency_ms": sorted(latencies)[int(len(latencies) * 0.95)],
            "queries_last_hour": len([q for q in self.query_history 
                                      if datetime.fromisoformat(q["timestamp"]) > 
                                      datetime.now().replace(hour=datetime.now().hour-1)])
        }

# Initialize RAG system
rag = RAGSystem()

# HTML Dashboard
HTML_DASHBOARD = """
<!DOCTYPE html>
<html>
<head>
    <title>RAG System Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; }
        .container { max-width: 1400px; margin: 0 auto; }
        .header { text-align: center; color: white; margin-bottom: 30px; }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .header p { font-size: 1.1em; opacity: 0.9; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 20px; }
        .card { background: white; border-radius: 15px; padding: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }
        .card h3 { color: #667eea; margin-bottom: 15px; font-size: 1.2em; }
        .metric { font-size: 2em; font-weight: bold; color: #333; margin: 10px 0; }
        .query-box { background: white; border-radius: 15px; padding: 20px; margin-bottom: 20px; }
        .query-input { width: 100%; padding: 15px; border: 2px solid #e0e0e0; border-radius: 10px; font-size: 1em; margin-bottom: 10px; }
        .query-btn { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; padding: 12px 30px; border-radius: 25px; cursor: pointer; font-size: 1em; }
        .query-btn:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0,0,0,0.2); }
        .result { background: #f8f9fa; border-radius: 10px; padding: 15px; margin-top: 15px; }
        .history-item { border-bottom: 1px solid #e0e0e0; padding: 10px; cursor: pointer; }
        .history-item:hover { background: #f0f0f0; }
        .timestamp { color: #666; font-size: 0.8em; margin-top: 10px; }
        .loading { display: inline-block; width: 20px; height: 20px; border: 3px solid #f3f3f3; border-top: 3px solid #667eea; border-radius: 50%; animation: spin 1s linear infinite; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 RAG System Dashboard</h1>
            <p>Retrieval-Augmented Generation with Real-time Monitoring</p>
        </div>
        
        <div class="grid">
            <div class="card">
                <h3>📊 Total Queries</h3>
                <div class="metric" id="totalQueries">0</div>
            </div>
            <div class="card">
                <h3>⚡ Avg Latency</h3>
                <div class="metric" id="avgLatency">0ms</div>
            </div>
            <div class="card">
                <h3>📈 P95 Latency</h3>
                <div class="metric" id="p95Latency">0ms</div>
            </div>
            <div class="card">
                <h3>�� Queries (Last Hour)</h3>
                <div class="metric" id="queriesLastHour">0</div>
            </div>
        </div>
        
        <div class="query-box">
            <h3>🔎 Ask a Question</h3>
            <input type="text" id="queryInput" class="query-input" placeholder="e.g., In what country is Normandy located?" onkeypress="if(event.key==='Enter') askQuestion()">
            <button class="query-btn" onclick="askQuestion()">Ask Question</button>
            <div id="queryResult"></div>
        </div>
        
        <div class="card">
            <h3>📜 Recent Queries</h3>
            <div id="historyList"></div>
        </div>
    </div>
    
    <script>
        async function loadStats() {
            const response = await fetch('/api/stats');
            const stats = await response.json();
            document.getElementById('totalQueries').innerText = stats.total_queries;
            document.getElementById('avgLatency').innerText = Math.round(stats.avg_latency_ms) + 'ms';
            document.getElementById('p95Latency').innerText = Math.round(stats.p95_latency_ms) + 'ms';
            document.getElementById('queriesLastHour').innerText = stats.queries_last_hour;
        }
        
        async function loadHistory() {
            const response = await fetch('/api/history');
            const history = await response.json();
            const historyDiv = document.getElementById('historyList');
            historyDiv.innerHTML = history.map(item => `
                <div class="history-item" onclick="showResult('${item.question}')">
                    <strong>${item.question.substring(0, 100)}</strong>
                    <div class="timestamp">${new Date(item.timestamp).toLocaleString()} • ${Math.round(item.latency_ms)}ms</div>
                </div>
            `).join('');
        }
        
        async function askQuestion() {
            const query = document.getElementById('queryInput').value;
            if (!query) return;
            
            const resultDiv = document.getElementById('queryResult');
            resultDiv.innerHTML = '<div class="loading"></div> Loading...';
            
            try {
                const response = await fetch('/api/query', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ query: query })
                });
                const data = await response.json();
                
                resultDiv.innerHTML = `
                    <div class="result">
                        <strong>💡 Answer:</strong>
                        <p>${data.answer}</p>
                        ${data.citations ? `<small>📖 Source: ${data.citations}</small>` : ''}
                        <div class="timestamp">⚡ ${Math.round(data.latency_ms)}ms • ${data.sources} sources • ${new Date(data.timestamp).toLocaleTimeString()}</div>
                    </div>
                `;
                
                document.getElementById('queryInput').value = '';
                loadStats();
                loadHistory();
            } catch (error) {
                resultDiv.innerHTML = `<div class="result" style="color: red;">Error: ${error.message}</div>`;
            }
        }
        
        function showResult(question) {
            document.getElementById('queryInput').value = question;
            askQuestion();
        }
        
        // Auto-refresh every 5 seconds
        setInterval(() => { loadStats(); loadHistory(); }, 5000);
        loadStats();
        loadHistory();
    </script>
</body>
</html>
"""

# API Endpoints
@app.get("/", response_class=HTMLResponse)
async def dashboard():
    return HTMLResponse(HTML_DASHBOARD)

@app.get("/api/stats")
async def get_stats():
    return rag.get_stats()

@app.get("/api/history")
async def get_history():
    return rag.query_history

@app.post("/api/query")
async def query_endpoint(request: Request):
    data = await request.json()
    result = rag.query(data.get("query", ""))
    return result

@app.get("/metrics/prometheus")
async def metrics():
    return Response(content=generate_latest(), media_type="text/plain")

if __name__ == "__main__":
    import uvicorn
    from fastapi.responses import Response
    
    print("\n" + "="*60)
    print("🚀 RAG SYSTEM WITH WEB DASHBOARD")
    print("="*60)
    print("📍 Dashboard: http://localhost:8000")
    print("📊 API Docs: http://localhost:8000/docs")
    print("📈 Metrics: http://localhost:8000/metrics/prometheus")
    print("="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
