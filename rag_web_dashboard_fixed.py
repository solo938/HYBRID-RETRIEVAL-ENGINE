"""
Complete RAG System with Web Dashboard - No Docker/Grafana needed
"""
import json
import time
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from sentence_transformers import SentenceTransformer, CrossEncoder

# Initialize FastAPI
app = FastAPI(title="RAG System Dashboard", version="2.0.0")

class RAGSystem:
    def __init__(self):
        print("🚀 Loading RAG System...")
        print("  Loading BGE-small model...")
        self.dense_model = SentenceTransformer("BAAI/bge-small-en-v1.5")
        print("  Loading MiniLM reranker...")
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
        
        # Search
        results = self.search(question, limit=5)
        
        # Generate answer with citations
        if results:
            # Take first sentence from most relevant document
            first_sentence = results[0]['content'].split('.')[0]
            answer = f"{first_sentence}."
            citation = f"Source: {results[0]['id']}"
        else:
            answer = "I cannot answer based on the provided context."
            citation = ""
        
        latency = (time.time() - start) * 1000
        
        query_record = {
            "question": question,
            "answer": answer,
            "citations": citation,
            "sources": len(results),
            "latency_ms": round(latency, 2),
            "timestamp": datetime.now().isoformat()
        }
        self.query_history.insert(0, query_record)
        if len(self.query_history) > 50:
            self.query_history.pop()
        
        return query_record
    
    def get_stats(self):
        if not self.query_history:
            return {"total_queries": 0, "avg_latency_ms": 0, "p95_latency_ms": 0, "queries_last_hour": 0}
        
        latencies = [q["latency_ms"] for q in self.query_history]
        one_hour_ago = datetime.now().timestamp() - 3600
        recent = len([q for q in self.query_history 
                     if datetime.fromisoformat(q["timestamp"]).timestamp() > one_hour_ago])
        
        return {
            "total_queries": len(self.query_history),
            "avg_latency_ms": round(sum(latencies) / len(latencies), 2),
            "p95_latency_ms": round(sorted(latencies)[int(len(latencies) * 0.95)], 2),
            "queries_last_hour": recent
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
        .container { max-width: 1200px; margin: 0 auto; }
        .header { text-align: center; color: white; margin-bottom: 30px; }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .header p { font-size: 1.1em; opacity: 0.9; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 20px; }
        .card { background: white; border-radius: 15px; padding: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }
        .card h3 { color: #667eea; margin-bottom: 10px; font-size: 0.9em; text-transform: uppercase; letter-spacing: 1px; }
        .metric { font-size: 2em; font-weight: bold; color: #333; }
        .metric-unit { font-size: 0.5em; color: #666; }
        .query-box { background: white; border-radius: 15px; padding: 25px; margin-bottom: 20px; }
        .query-box h3 { color: #667eea; margin-bottom: 15px; }
        .query-input { width: 100%; padding: 15px; border: 2px solid #e0e0e0; border-radius: 10px; font-size: 1em; margin-bottom: 15px; font-family: inherit; }
        .query-input:focus { outline: none; border-color: #667eea; }
        .query-btn { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; padding: 12px 30px; border-radius: 25px; cursor: pointer; font-size: 1em; font-weight: bold; }
        .query-btn:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0,0,0,0.2); }
        .result { background: #f8f9fa; border-radius: 10px; padding: 20px; margin-top: 20px; border-left: 4px solid #667eea; }
        .result strong { color: #667eea; }
        .history-item { border-bottom: 1px solid #e0e0e0; padding: 12px; cursor: pointer; transition: background 0.2s; }
        .history-item:hover { background: #f8f9fa; }
        .history-question { font-weight: 500; margin-bottom: 5px; }
        .history-meta { color: #666; font-size: 0.8em; }
        .timestamp { color: #999; font-size: 0.8em; margin-top: 10px; }
        .loading { display: inline-block; width: 20px; height: 20px; border: 3px solid #f3f3f3; border-top: 3px solid #667eea; border-radius: 50%; animation: spin 1s linear infinite; vertical-align: middle; margin-right: 10px; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .badge { display: inline-block; background: #e0e0e0; padding: 2px 8px; border-radius: 12px; font-size: 0.7em; margin-left: 10px; }
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
                <div class="metric" id="avgLatency">0<span class="metric-unit">ms</span></div>
            </div>
            <div class="card">
                <h3>📈 P95 Latency</h3>
                <div class="metric" id="p95Latency">0<span class="metric-unit">ms</span></div>
            </div>
            <div class="card">
                <h3>🕐 Last Hour</h3>
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
            <div id="historyList" style="max-height: 400px; overflow-y: auto;"></div>
        </div>
    </div>
    
    <script>
        async function loadStats() {
            try {
                const response = await fetch('/api/stats');
                const stats = await response.json();
                document.getElementById('totalQueries').innerText = stats.total_queries;
                document.getElementById('avgLatency').innerHTML = Math.round(stats.avg_latency_ms) + '<span class="metric-unit">ms</span>';
                document.getElementById('p95Latency').innerHTML = Math.round(stats.p95_latency_ms) + '<span class="metric-unit">ms</span>';
                document.getElementById('queriesLastHour').innerText = stats.queries_last_hour;
            } catch(e) { console.error(e); }
        }
        
        async function loadHistory() {
            try {
                const response = await fetch('/api/history');
                const history = await response.json();
                const historyDiv = document.getElementById('historyList');
                if (history.length === 0) {
                    historyDiv.innerHTML = '<div style="padding: 20px; text-align: center; color: #999;">No queries yet. Ask a question above!</div>';
                    return;
                }
                historyDiv.innerHTML = history.map(item => `
                    <div class="history-item" onclick="showResult('${item.question.replace(/'/g, "\\'")}')">
                        <div class="history-question">${item.question.substring(0, 100)}${item.question.length > 100 ? '...' : ''}</div>
                        <div class="history-meta">⚡ ${item.latency_ms}ms • ${item.sources} sources • ${new Date(item.timestamp).toLocaleTimeString()}</div>
                    </div>
                `).join('');
            } catch(e) { console.error(e); }
        }
        
        async function askQuestion() {
            const query = document.getElementById('queryInput').value.trim();
            if (!query) return;
            
            const resultDiv = document.getElementById('queryResult');
            resultDiv.innerHTML = '<div class="result"><span class="loading"></span> Searching and generating answer...</div>';
            
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
                        <p style="margin-top: 10px; line-height: 1.5;">${data.answer}</p>
                        ${data.citations ? `<div style="margin-top: 10px; color: #666; font-size: 0.9em;">📖 ${data.citations}</div>` : ''}
                        <div class="timestamp">⚡ ${data.latency_ms}ms • ${data.sources} sources • ${new Date(data.timestamp).toLocaleTimeString()}</div>
                    </div>
                `;
                
                document.getElementById('queryInput').value = '';
                await loadStats();
                await loadHistory();
            } catch (error) {
                resultDiv.innerHTML = `<div class="result" style="border-left-color: #e74c3c;"><strong style="color: #e74c3c;">Error:</strong> ${error.message}</div>`;
            }
        }
        
        function showResult(question) {
            document.getElementById('queryInput').value = question;
            askQuestion();
        }
        
        // Initial load and auto-refresh
        loadStats();
        loadHistory();
        setInterval(() => { loadStats(); loadHistory(); }, 10000);
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

@app.get("/health")
async def health():
    return {"status": "healthy", "documents": len(rag.documents)}

if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "="*60)
    print("🚀 RAG SYSTEM WITH WEB DASHBOARD")
    print("="*60)
    print("📍 Dashboard: http://localhost:8000")
    print("📊 API Docs: http://localhost:8000/docs")
    print("💚 Health Check: http://localhost:8000/health")
    print("="*60)
    print("\n⚠️  First run will download models (~200MB)")
    print("   This takes 1-2 minutes...\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
