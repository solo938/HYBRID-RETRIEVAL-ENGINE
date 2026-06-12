"""
RAG System with Real Documents from data/raw/
"""
import json
import numpy as np
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from sentence_transformers import SentenceTransformer

app = FastAPI(title="RAG System with Real Documents")

class RealDocumentRAG:
    def __init__(self):
        print("🚀 Loading Real Document RAG System...")
        self.model = SentenceTransformer("BAAI/bge-small-en-v1.5")
        self.documents = []
        self.embeddings = []
        self.query_history = []
        self._load_index()
    
    def _load_index(self):
        index_file = Path("data/processed/all_documents_index.json")
        if not index_file.exists():
            print("⚠️ No index found. Run ingest_all_documents.py first!")
            self._create_sample_docs()
            return
        
        with open(index_file, 'r') as f:
            data = json.load(f)
        
        self.documents = data["documents"]
        self.embeddings = np.array(data["embeddings"])
        print(f"✅ Loaded {len(self.documents)} documents from index")
    
    def _create_sample_docs(self):
        """Fallback sample documents"""
        self.documents = [
            {"id": "sample_1", "content": "AWS security best practices include encryption at rest and in transit, IAM roles for access control, and regular security audits.", "type": "sample", "title": "AWS Security"},
            {"id": "sample_2", "content": "Qdrant hybrid search combines dense vector similarity with sparse keyword matching using RRF fusion.", "type": "sample", "title": "Qdrant Hybrid"},
        ]
        texts = [d["content"] for d in self.documents]
        self.embeddings = self.model.encode(texts, normalize_embeddings=True)
    
    def search(self, query: str, limit: int = 5) -> list:
        q_emb = self.model.encode(query, normalize_embeddings=True)
        scores = self.embeddings @ q_emb
        top_idx = np.argsort(scores)[-limit:][::-1]
        
        results = []
        for i in top_idx:
            doc = self.documents[i]
            results.append({
                "id": doc["id"],
                "content": doc["content"][:400],
                "score": float(scores[i]),
                "source": doc.get("source", "unknown"),
                "type": doc.get("type", "unknown"),
                "title": doc.get("title", doc["id"])
            })
        return results
    
    def query(self, question: str) -> dict:
        import time
        start = time.time()
        
        results = self.search(question, limit=3)
        
        if results and results[0]["score"] > 0.3:
            answer = results[0]["content"]
            citation = f"Source: {results[0]['title']} ({results[0]['type']})"
        else:
            answer = "I cannot find relevant information in the ingested documents."
            citation = ""
        
        latency = (time.time() - start) * 1000
        
        record = {
            "question": question,
            "answer": answer[:500],
            "citations": citation,
            "sources": len(results),
            "top_score": results[0]["score"] if results else 0,
            "latency_ms": round(latency, 2),
            "timestamp": time.time()
        }
        self.query_history.insert(0, record)
        if len(self.query_history) > 50:
            self.query_history.pop()
        
        return record

rag = RealDocumentRAG()

# HTML Dashboard (same as before, but updated title)
HTML_DASHBOARD = """
<!DOCTYPE html>
<html>
<head>
    <title>RAG System - Real Documents</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { text-align: center; color: white; margin-bottom: 30px; }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .card { background: white; border-radius: 15px; padding: 20px; margin-bottom: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }
        .query-input { width: 100%; padding: 15px; border: 2px solid #e0e0e0; border-radius: 10px; font-size: 1em; margin-bottom: 15px; }
        .query-btn { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; padding: 12px 30px; border-radius: 25px; cursor: pointer; }
        .result { background: #f8f9fa; border-radius: 10px; padding: 15px; margin-top: 15px; border-left: 4px solid #667eea; }
        .source-badge { display: inline-block; background: #e0e0e0; padding: 2px 8px; border-radius: 12px; font-size: 0.7em; margin-left: 10px; }
        .history-item { border-bottom: 1px solid #e0e0e0; padding: 10px; cursor: pointer; }
        .history-item:hover { background: #f8f9fa; }
        .metric { font-size: 2em; font-weight: bold; }
        .grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 RAG System - Real Documents</h1>
            <p>Searching PDFs, HTML, Excel, JSON, and Markdown files</p>
        </div>
        
        <div class="grid">
            <div class="card"><h3>📄 Documents</h3><div class="metric" id="docCount">0</div></div>
            <div class="card"><h3>⚡ Avg Latency</h3><div class="metric" id="avgLatency">0ms</div></div>
            <div class="card"><h3>📊 Queries</h3><div class="metric" id="queryCount">0</div></div>
            <div class="card"><h3>🎯 Last Score</h3><div class="metric" id="lastScore">0</div></div>
        </div>
        
        <div class="card">
            <h3>🔎 Ask a Question</h3>
            <input type="text" id="queryInput" class="query-input" placeholder="e.g., What are AWS security best practices?">
            <button class="query-btn" onclick="askQuestion()">Ask</button>
            <div id="result"></div>
        </div>
        
        <div class="card">
            <h3>📜 Recent Queries</h3>
            <div id="history"></div>
        </div>
    </div>
    
    <script>
        async function askQuestion() {
            const query = document.getElementById('queryInput').value;
            if (!query) return;
            
            const resultDiv = document.getElementById('result');
            resultDiv.innerHTML = '<div class="result">Searching...</div>';
            
            const response = await fetch('/api/query', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({query: query})
            });
            const data = await response.json();
            
            resultDiv.innerHTML = `
                <div class="result">
                    <strong>�� Answer:</strong>
                    <p>${data.answer}</p>
                    <small>📖 ${data.citations}</small>
                    <div style="margin-top: 10px; color: #666;">⚡ ${data.latency_ms}ms • Score: ${data.top_score.toFixed(3)}</div>
                </div>
            `;
            
            document.getElementById('queryInput').value = '';
            loadStats();
            loadHistory();
        }
        
        async function loadStats() {
            const response = await fetch('/api/stats');
            const stats = await response.json();
            document.getElementById('docCount').innerText = stats.doc_count;
            document.getElementById('avgLatency').innerHTML = stats.avg_latency + 'ms';
            document.getElementById('queryCount').innerText = stats.total_queries;
            document.getElementById('lastScore').innerText = stats.last_score;
        }
        
        async function loadHistory() {
            const response = await fetch('/api/history');
            const history = await response.json();
            const historyDiv = document.getElementById('history');
            if (history.length === 0) {
                historyDiv.innerHTML = '<div style="padding: 20px; text-align: center; color: #999;">No queries yet</div>';
                return;
            }
            historyDiv.innerHTML = history.map(item => `
                <div class="history-item" onclick="document.getElementById('queryInput').value='${item.question}'; askQuestion();">
                    <strong>${item.question.substring(0, 80)}</strong>
                    <div>⚡ ${item.latency_ms}ms • Score: ${item.top_score.toFixed(3)}</div>
                </div>
            `).join('');
        }
        
        loadStats();
        loadHistory();
        setInterval(() => { loadStats(); }, 5000);
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    return HTMLResponse(HTML_DASHBOARD)

@app.get("/api/stats")
async def get_stats():
    latencies = [q["latency_ms"] for q in rag.query_history]
    return {
        "doc_count": len(rag.documents),
        "avg_latency": round(sum(latencies)/len(latencies), 2) if latencies else 0,
        "total_queries": len(rag.query_history),
        "last_score": rag.query_history[0]["top_score"] if rag.query_history else 0
    }

@app.get("/api/history")
async def get_history():
    return rag.query_history

@app.post("/api/query")
async def query_endpoint(request: Request):
    data = await request.json()
    return rag.query(data.get("query", ""))

if __name__ == "__main__":
    import uvicorn
    print("\n🚀 Starting RAG System with REAL DOCUMENTS")
    print("📍 Dashboard: http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
