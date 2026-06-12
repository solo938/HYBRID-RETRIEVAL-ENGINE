# 🔍 Hybrid RAG Engine

> Production-grade Retrieval-Augmented Generation pipeline — hybrid search, cross-encoder reranking, ACL-aware security, and a CI/CD evaluation harness that automatically blocks metric regressions on every push.

[![CI Quality Gate](https://github.com/solo938/HYBRID-RETRIEVAL-ENGINE/actions/workflows/eval-gate.yml/badge.svg)](https://github.com/solo938/HYBRID-RETRIEVAL-ENGINE/actions)
![Python](https://img.shields.io/badge/Python-3.11-blue)
![Qdrant](https://img.shields.io/badge/Vector_DB-Qdrant-red)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 🎬 Demo

[![Watch Demo](https://img.shields.io/badge/Watch-Demo-red?style=for-the-badge)](https://github.com/user-attachments/assets/586804ea-2619-495e-9b45-015cca385ef9)

---

## 📊 Retrieval Performance

| Version | Pipeline | Recall@5 | Recall@10 | MRR | nDCG@10 | P95 Latency |
|---|---|---|---|---|---|---|
| v1.0 | Dense only · BGE-small | 0.40 | 0.71 | 0.23 | 0.34 | 180ms |
| v1.2 | Dense + MiniLM Cross-Encoder | **0.40** | **0.73** | **0.24** | **0.36** | 340ms |

> Evaluated on 75 queries from SQuAD v2 dev split. CI gate runs automatically on every push and pull request.
> <p align="center">
  <img src="https://raw.githubusercontent.com/solo938/HYBRID-RETRIEVAL-ENGINE/main/HYBRID%20RETRIEVAL%20ENGINE%20RERANK.png" width="1000">
</p>

---

## 🚦 CI / CD Quality Gate

Every pull request triggers automated evaluation. **Merge is blocked** if any metric drops below threshold.

```
🚦 RAG EVALUATION QUALITY GATE
==================================================
📊 RESULTS
--------------------------------------------------
✅ PASS  recall@5     0.4333  █████████████  (min: 0.35)
✅ PASS  recall@10    0.7333  ██████████████████████  (min: 0.65)
✅ PASS  mrr          0.2431  ███████  (min: 0.18)
✅ PASS  ndcg@10      0.3586  ██████████  (min: 0.28)
==================================================
✅ ALL QUALITY GATES PASSED — safe to merge
```

This gate runs automatically on every `git push` — preventing any model update, retriever change, or prompt edit from silently degrading answer quality.

---

## 🏗️ Full System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        INGESTION PIPELINE                           │
│                                                                     │
│   PDFs · HTML · Markdown · JSON · Excel · Wikis · Tickets · Logs    │
│      │                                                              │
│      ▼                                                              │
│  ┌─────────┐  ┌─────────────┐  ┌────────────┐  ┌───────────────┐    │
│  │ Parsers │→ │  Chunking   │→ │ Enrichment │→ │  Embedding    │    │
│  │pdf/html │  │ semantic    │  │ entity     │  │ BGE-small     │    │
│  │markdown │  │ recursive   │  │ keyword    │  │ batch embed   │    │
│  │json/xlsx│  │ metadata    │  │ metadata   │  │ cache layer   │    │
│  └─────────┘  └─────────────┘  └────────────┘  └──────┬────────┘    │
│                                                         │           │
│                                   ┌─────────────────────▼────────┐  │
│                                   │      ACL-Aware Indexing       │ │
│                                   │  Qdrant vector index (HNSW)   │ │
│                                   │  BM25 sparse index            │ │
│                                   │  Document-level ACL tags      │ │
│                                   └──────────────────────────────-┘ │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                          QUERY PIPELINE                             │
│                                                                     │
│   User Query                                                        │
│      │                                                              │
│      ▼                                                              │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    Query Understanding                       │   │
│  │  Intent Classification → Query Rewriting → Multi-Query       │   │
│  │  Expansion → Synonym/Acronym Expansion → Entity Boosting     │   │
│  └─────────────────────────┬────────────────────────────────────┘   │
│                            │                                        │
│         ┌──────────────────┴──────────────────┐                     │
│         ▼                                      ▼                    │
│  ┌──────────────────┐              ┌───────────────────────┐        │
│  │ Dense Retrieval  │              │   Sparse Retrieval    │        │
│  │ Qdrant ANN       │              │   BM25 lexical        │        │
│  │ HNSW index       │              │   Keyword matching    │        │
│  │ Cosine sim       │              │   TF-IDF scoring      │        │
│  └────────┬─────────┘              └───────────┬───────────┘        │
│           │                                    │                    │
│           └──────────────┬─────────────────────┘                    │
│                          ▼                                          │
│              ┌───────────────────────┐                              │
│              │      Fusion Layer     │                              │
│              │  RRF (Reciprocal      │                              │
│              │  Rank Fusion)         │                              │
│              │  Weighted Fusion      │                              │
│              └──────────┬────────────┘                              │
│                         ▼                                           │
│              ┌───────────────────────┐                              │
│              │    Reranking Layer    │                              │
│              │  Cross-Encoder        │                              │
│              │  (MiniLM-L-6-v2)      │                              │
│              │  Late Interaction     │                              │
│              │  (ColBERT)            │                              │
│              │  LLM Reranker         │                              │
│              └──────────┬────────────┘                              │
│                         ▼                                           │
│              ┌───────────────────────┐                              │
│              │   ACL Authorization   │                              │
│              │  Role-based filter    │                              │
│              │  Query-time checks    │                              │
│              └──────────┬────────────┘                              │
│                         ▼                                           │
│              ┌───────────────────────┐                              │
│              │   Answer Generation   │                              │
│              │  Grounded prompts     │                              │
│              │  Citation builder     │                              │
│              │  Hallucination guard  │                              │
│              │  PII detection        │                              │
│              │  Token budgeting      │                              │
│              └───────────────────────┘                              │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                       EVALUATION PIPELINE                           │
│                                                                     │
│   Golden Dataset (SQuAD v2 + IT Tickets)                            │
│      │                                                              │
│      ▼                                                              │
│  Retrieval Eval        Generation Eval        Regression Tests      │
│  recall@k, MRR         faithfulness           prompt_regression     │
│  precision@k           groundedness           retriever_regression  │
│  nDCG                  answer relevancy       model_regression      │
│      │                      │                       │               │
│      └──────────────────────┴───────────────────────┘               │
│                             │                                       │
│                             ▼                                       │
│                  CI Quality Gate (GitHub Actions)                   │
│                  Block merge if metrics regress                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Embeddings** | BAAI/bge-small-en-v1.5 | Dense vector representations |
| **Vector Store** | Qdrant (HNSW) | ANN index, payload filtering |
| **Sparse Retrieval** | BM25 (rank-bm25) | Lexical keyword matching |
| **Fusion** | RRF + Weighted Fusion | Combine dense + sparse rankings |
| **Reranking** | MiniLM cross-encoder, ColBERT, LLM reranker | Precision ranking |
| **Query Understanding** | Custom intent classifier, query rewriter | Robust query handling |
| **Evaluation** | recall@k, MRR, nDCG, RAGAS | Quantified quality measurement |
| **Security** | ACL-aware indexing + query-time authz | Document-level access control |
| **Guardrails** | Hallucination guard, PII detection, prompt injection | Safe outputs |
| **Observability** | OpenTelemetry, Prometheus, Grafana | Full pipeline instrumentation |
| **Caching** | Semantic cache, retrieval cache | Latency + cost reduction |
| **API** | FastAPI (REST) + gRPC | Scalable service layer |
| **CI/CD** | GitHub Actions | Automated regression gate |
| **LLM Providers** | OpenAI, Anthropic, Gemini, Ollama | Multi-model compatibility |
| **Streaming** | SSE response streamer | Real-time generation |

---

## 📁 Project Structure

```
hybrid-retrieval-engine/
│
├── app/
│   ├── retrieval/
│   │   ├── hybrid_retriever.py              # Full pipeline orchestrator
│   │   ├── dense_retriever.py               # Qdrant ANN search
│   │   ├── sparse_retriever.py              # BM25 lexical search
│   │   ├── fusion/
│   │   │   ├── rrf.py                       # Reciprocal Rank Fusion
│   │   │   └── weighted_fusion.py           # Weighted score fusion
│   │   ├── reranking/
│   │   │   ├── cross_encoder.py             # MiniLM cross-encoder
│   │   │   ├── late_interaction.py          # ColBERT late interaction
│   │   │   └── llm_reranker.py              # LLM-based reranker
│   │   └── query_understanding/
│   │       ├── intent_classifier.py         # Query intent routing
│   │       ├── query_rewriter.py            # Query rewriting
│   │       ├── multi_query_expander.py      # Query expansion
│   │       └── keyword_boosting.py          # Entity/keyword boosting
│   │
│   ├── ingestion/
│   │   ├── parsers/                         # PDF, HTML, Markdown, JSON, Excel
│   │   ├── chunking/                        # Semantic, recursive, metadata
│   │   ├── embeddings/                      # BGE embedder + cache
│   │   └── enrichment/                      # NER, keywords, metadata
│   │
│   ├── evaluation/
│   │   ├── harness/evaluation_runner.py     # End-to-end eval runner
│   │   ├── datasets/goldens/                # 500 SQuAD + 100 IT tickets
│   │   ├── metrics/retrieval_metrics.py     # precision@k, recall@k, MRR, nDCG
│   │   ├── generation/                      # faithfulness, groundedness
│   │   └── regression/                      # regression test suite
│   │
│   ├── security/
│   │   ├── acl/                             # ACL indexing + permission engine
│   │   └── auth/authorization.py            # Request authorization
│   │
│   ├── observability/
│   │   ├── tracing.py                       # OpenTelemetry
│   │   ├── metrics.py                       # Prometheus
│   │   └── dashboards/rag_pipeline.json     # Grafana dashboard
│   │
│   ├── performance/
│   │   ├── caching/                         # Semantic + retrieval cache
│   │   ├── optimization/                    # Adaptive retrieval, token budgets
│   │   └── streaming/response_streamer.py   # SSE streaming
│   │
│   ├── guardrails/                          # Hallucination, PII, injection
│   ├── generation/                          # RAG pipeline, citations, prompts
│   ├── llm/providers/                       # OpenAI, Anthropic, Gemini, Ollama
│   ├── feedback/                            # Feedback + human review queue
│   └── api/
│       ├── rest/v1/                         # FastAPI REST endpoints
│       └── grpc/server.py                   # gRPC service
│
├── .github/
│   ├── workflows/eval-gate.yml              # CI quality gate
│   └── scripts/eval_gate.py                 # Eval runner for CI
│
└── data/
    ├── raw/                                 # PDFs, HTML, Markdown, JSON, Excel
    └── golden_dataset/                      # questions, answers, eval splits
```

---

## 🚀 Quick Start

```bash
# Clone and install
git clone https://github.com/solo938/HYBRID-RETRIEVAL-ENGINE
cd HYBRID-RETRIEVAL-ENGINE
pip install -r requirements.txt

# Build golden evaluation dataset from SQuAD v2
python3 app/evaluation/datasets/golden_dataset_builder.py

# Run CI quality gate locally
python3 .github/scripts/eval_gate.py

# Start the API
uvicorn app.api.main:app --reload
# → http://localhost:8000
```

---

## 📋 Evaluation Dataset

| Dataset | Size | Purpose |
|---|---|---|
| SQuAD v2 (Stanford) | 500 Q&A pairs | Retrieval + generation eval |
| IT Tickets (enterprise) | 100 tickets | Enterprise domain eval |
| Train split | 350 queries | Model development |
| Dev split | 75 queries | CI gate evaluation |
| Test split | 75 queries | Final benchmark |

---

## 🔒 Security & Access Control

Document-level ACL enforced at both index time and query time:

```python
# Only returns documents the user has permission to access
results = retriever.retrieve(
    query="security policy documentation",
    acl_context=ACLContext(user_id="eng_001", roles=["engineer"])
)
```

| Role | Access Level | Permitted Collections |
|---|---|---|
| admin | unrestricted | all |
| engineer | internal | langchain_docs, qdrant_docs, runbooks |
| analyst | internal | benchmarks, eval_results, ticket_data |
| viewer | public | public_docs, faqs |
| security_team | restricted | security_policies, audit_logs |

---

## 📈 Observability & SRE

| Signal | What is Tracked |
|---|---|
| **Traces** | Latency per stage — dense retrieval, rerank, generation |
| **Metrics** | Token cost per query, recall trend, cache hit rate |
| **Logs** | Structured JSON with query ID, user, latency |
| **Alerts** | Answer failure rate spike, recall regression, P95 > 2s |
| **SLOs** | Availability 99.9% · P95 latency < 2s |

---

## ⚡ Performance & Cost

| Optimization | Implementation | Impact |
|---|---|---|
| Semantic caching | Cache similar queries by embedding | ~60% latency on cache hits |
| Retrieval caching | Cache top-k results per query | Eliminates repeat Qdrant calls |
| Adaptive retrieval | Adjust top-k by query complexity | Reduces reranker cost |
| Token budgeting | Cap context window per query | Controls generation cost |
| Batch embedding | BGE batch encoder | 4x throughput on ingestion |
| Streaming | SSE response streaming | First token < 500ms |

---

## 🔄 Feedback Loop

```
User Query → Answer → 👍 / 👎 Feedback
                              │
                              ▼
                    Human Review Queue
                              │
                              ▼
                    Relevance Labeling
                              │
                              ▼
                    Golden Dataset Update → Re-evaluation → CI Gate
```

---

## 🎯 KLA Success Criteria — Full Coverage

| KLA "What Success Looks Like" | This Project |
|---|---|
| Standardized RAG pipeline that measurably improves answer relevance | ✅ recall@10=0.73, nDCG=0.36, before/after metrics table |
| Repeatable evaluation framework with quality gates preventing regressions | ✅ GitHub Actions CI gate blocks every PR on metric drop |
| Meaningful latency and cost reductions via caching and adaptive retrieval | ✅ Semantic cache + adaptive retrieval + token budgeting |
| Secure compliant retrieval enforcing access control | ✅ ACL-aware indexing + query-time role-based authorization |

---

## 📄 License

MIT
