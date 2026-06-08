# Overview
# Qdrant Tutorial Repository

### Basic Tutorials
*Get up and running with Qdrant in minutes.*

| Tutorial | Objective | Stack | Time | Level |
| :--- | :--- | :--- | :--- | :--- |
| [Qdrant Local Quickstart](/documentation/quickstart/index.md) | Basic CRUD operations and local deployment. | <span class="pill">Any</span> | 10m | <span class="text-green">Beginner</span> |
| [Qdrant Cloud Quickstart](/documentation/cloud-quickstart/index.md) | Basic CRUD operations on Qdrant Cloud. | <span class="pill">Any</span> | 10m | <span class="text-green">Beginner</span> |
| [Semantic Search 101](/documentation/tutorials-basics/search-beginners/index.md) | Build a search engine for science fiction books. | <span class="pill">Any</span> | 10m | <span class="text-green">Beginner</span> |
| [Hybrid Search](/documentation/tutorials-basics/cloud-inference-hybrid-search/index.md) | Get started with hybrid search. | <span class="pill">Any</span> | 30m | <span class="text-green">Beginner</span> |
| [Hybrid Search with Reranking](/documentation/tutorials-basics/reranking-hybrid-search/index.md) | Rerank hybrid search results for improved accuracy. | <span class="pill">Any</span> | 40m | <span class="text-yellow">Intermediate</span> |

---

### Search Engineering Tutorials
*Master vector search modalities, reranking, and retrieval quality.*

| Tutorial | Objective | Stack | Time | Level |
| :--- | :--- | :--- | :--- | :--- |
| [Relevance Feedback](/documentation/tutorials-search-engineering/using-relevance-feedback/index.md) | Relevance Feedback Retrieval in Qdrant | <span class="pill">Python</span> | 30m | <span class="text-yellow">Intermediate</span> |
| [Collaborative Filtering](/documentation/tutorials-search-engineering/collaborative-filtering/index.md) | Collaborative filtering using sparse embeddings. | <span class="pill">Python</span> | 45m | <span class="text-yellow">Intermediate</span> |
| [Multivector Document Retrieval](/documentation/tutorials-search-engineering/pdf-retrieval-at-scale/index.md) | PDF RAG using ColPali and embedding pooling. | <span class="pill">Python</span> | 30m | <span class="text-yellow">Intermediate</span> |
| [Measuring ANN Recall](/documentation/tutorials-search-engineering/ann-recall/index.md) | Measure ANN recall with the Web UI and tune HNSW parameters. | <span class="pill">Web UI</span> | 15m | <span class="text-green">Beginner</span> |
| [Multivectors and Late Interaction](/documentation/tutorials-search-engineering/using-multivector-representations/index.md) | Effective use of multivector representations. | <span class="pill">Python</span> | 30m | <span class="text-yellow">Intermediate</span> |
| [Multi-Representation Search](/documentation/tutorials-search-engineering/multi-representation-search/index.md) | Fuse title, summary, chunk, and tag vectors with named vectors and the Query API. | <span class="pill">Python</span> | 45m | <span class="text-yellow">Intermediate</span> |
| [Static Embeddings](/documentation/tutorials-search-engineering/static-embeddings/index.md) | Evaluate the utility of static embeddings. | <span class="pill">Python</span> | 20m | <span class="text-yellow">Intermediate</span> |
| [Branch-Aware Search](/documentation/tutorials-search-engineering/branch-aware-search/index.md) | Scope search to a branch's live view in a versioned corpus, inherited from its ancestors. | <span class="pill">Python</span> | 25m | <span class="text-yellow">Intermediate</span> |

---

### Operations & Scale
*Production-grade management, monitoring, and high-volume optimization.*

| Tutorial | Objective | Stack | Time | Level |
| :--- | :--- | :--- | :--- | :--- |
| [Snapshots](/documentation/tutorials-operations/create-snapshot/index.md) | Create and restore collection snapshots. | <span class="pill">Python</span> | 20m | <span class="text-green">Beginner</span> |
| [Data Migration](/documentation/tutorials-operations/migration/index.md) | Move embeddings to Qdrant. | <span class="pill">CLI</span> | 30m | <span class="text-yellow">Intermediate</span> |
| [Embedding Model Migration](/documentation/tutorials-operations/embedding-model-migration/index.md) | Use your new model with zero downtime. | <span class="pill">Any</span> | 40m | <span class="text-yellow">Intermediate</span> |
| [Time-Based Sharding](/documentation/tutorials-operations/time-based-sharding/index.md) | Efficiently manage time-series data with user-defined sharding. | <span class="pill">Any</span> | 1h | <span class="text-yellow">Intermediate</span> |
| [Large-Scale Search](/documentation/tutorials-operations/large-scale-search/index.md) | Cost-efficient search for LAION-400M datasets. | <span class="pill">Any</span> | 48h | <span class="text-red">Advanced</span> |
| [Secure a Self-Hosted Instance](/documentation/tutorials-operations/secure-qdrant/index.md) | Enable TLS, API keys, and JWT access control. | <span class="pill">Any</span> | 45m | <span class="text-yellow">Intermediate</span> |
| [Qdrant Cloud Prometheus Monitoring](/documentation/ops-monitoring/managed-cloud-prometheus/index.md) | Observability with Prometheus and Grafana. | <span class="pill">Prometheus</span> | 30m | <span class="text-yellow">Intermediate</span> |
| [Self-Hosted Prometheus Monitoring](/documentation/ops-monitoring/hybrid-cloud-prometheus/index.md) | Observability for hybrid/private cloud setups. | <span class="pill">Prometheus</span> | 30m | <span class="text-yellow">Intermediate</span> |

---

### Develop & Implement
*Core tools and APIs for building with Qdrant.*

| Tutorial | Objective | Stack | Time | Level |
| :--- | :--- | :--- | :--- | :--- |
| [Build a Semantic Search API](/documentation/tutorials-develop/neural-search/index.md) | Deploy a search service for company descriptions. | <span class="pill">FastAPI</span> | 30m | <span class="text-green">Beginner</span> |
| [Build a Hybrid Search API](/documentation/tutorials-develop/hybrid-search-fastembed/index.md) | Combine dense and sparse search. | <span class="pill">FastAPI</span> | 20m | <span class="text-green">Beginner</span> |
| [Bulk Operations](/documentation/tutorials-develop/bulk-upload/index.md) | High-scale ingestion approaches. | <span class="pill">Python</span> | 20m | <span class="text-yellow">Intermediate</span> |
| [Async API](/documentation/tutorials-develop/async-api/index.md) | Use Asynchronous programming for efficiency. | <span class="pill">Python</span> | 25m | <span class="text-yellow">Intermediate</span> |
| [Semantic Search for Code](/documentation/tutorials-develop/code-search/index.md) | Navigate codebases using vector similarity. | <span class="pill">Python</span> | 45m | <span class="text-yellow">Intermediate</span> |

---

### Migrate to Qdrant
*Move your vectors from other databases and keep them in sync.*

| Tutorial | Objective | Stack | Time | Level |
| :--- | :--- | :--- | :--- | :--- |
| [Migration Tool Overview](/documentation/migrate-to-qdrant/index.md) | Migrate vectors from any supported source. | <span class="pill">CLI</span> | Varies | <span class="text-yellow">Intermediate</span> |
| [From Pinecone](/documentation/migrate-to-qdrant/from-pinecone/index.md) | Migrate from Pinecone serverless indexes. | <span class="pill">CLI</span> | 15m | <span class="text-yellow">Intermediate</span> |
| [From Weaviate](/documentation/migrate-to-qdrant/from-weaviate/index.md) | Migrate from Weaviate (pre-create collection). | <span class="pill">CLI</span> | 20m | <span class="text-yellow">Intermediate</span> |
| [From Milvus](/documentation/migrate-to-qdrant/from-milvus/index.md) | Migrate from Milvus/Zilliz with partitions. | <span class="pill">CLI</span> | 15m | <span class="text-yellow">Intermediate</span> |
| [From Elasticsearch](/documentation/migrate-to-qdrant/from-elasticsearch/index.md) | Migrate dense vectors from Elasticsearch. | <span class="pill">CLI</span> | 15m | <span class="text-yellow">Intermediate</span> |
| [From pgvector](/documentation/migrate-to-qdrant/from-pgvector/index.md) | Migrate from PostgreSQL pgvector tables. | <span class="pill">CLI</span> | 15m | <span class="text-yellow">Intermediate</span> |
| [Migration Verification](/documentation/migration-guidance/index.md) | Verify data integrity and search quality. | <span class="pill">Python</span> | 1h+ | <span class="text-yellow">Intermediate</span> |
| [Keeping Postgres in Sync](/documentation/data-synchronization/index.md) | Keep Postgres and Qdrant in sync. | <span class="pill">Python</span> | 30m | <span class="text-yellow">Intermediate</span> |


<!-- KEEP BELOW FOR REFERENCE -->
<!-- 

# Qdrant Tutorial Repository

### Basic Tutorials
*Get up and running with Qdrant in minutes.*

| Tutorial | Objective | Stack | Time | Level |
| :--- | :--- | :--- | :--- | :--- |
| [Qdrant Quickstart](/documentation/quickstart/index.md) | Basic CRUD operations and local deployment. | <span class="pill">Python</span> | 10m | <span class="text-green">Beginner</span> |
| [Semantic Search 101](/documentation/tutorials-basics/search-beginners/index.md) | Build a search engine for science fiction books. | <span class="pill">Python</span> | 5m | <span class="text-green">Beginner</span> |
| [5-Minute RAG with DeepSeek](/documentation/tutorials-basics/rag-deepseek/index.md) | Build a RAG pipeline with DeepSeek enrichment. | <span class="pill">Python</span> | 5m | <span class="text-green">Beginner</span> |

---

### Search Engineering
*Master vector search modalities, reranking, and retrieval quality.*

| Tutorial | Objective | Stack | Time | Level |
| :--- | :--- | :--- | :--- | :--- |
| [Hybrid Search with FastEmbed](/documentation/tutorials-develop/hybrid-search-fastembed/index.md) | Combine dense and sparse search for startups. | <span class="pill">FastAPI</span> | 20m | <span class="text-green">Beginner</span> |
| [Semantic Search Basics](/documentation/tutorials-develop/neural-search/index.md) | Deploy a search service for company descriptions. | <span class="pill">FastAPI</span> | 30m | <span class="text-green">Beginner</span> |
| [Collaborative Filtering](/documentation/tutorials-search-engineering/collaborative-filtering/index.md) | Collaborative filtering using sparse embeddings. | <span class="pill">Python</span> | 45m | <span class="text-yellow">Intermediate</span> |
| [Multivector Document Retrieval](/documentation/tutorials-search-engineering/pdf-retrieval-at-scale/index.md) | PDF RAG using ColPali and embedding pooling. | <span class="pill">Python</span> | 30m | <span class="text-yellow">Intermediate</span> |
| [Measuring ANN Recall](/documentation/tutorials-search-engineering/ann-recall/index.md) | Measure ANN recall with the Web UI and tune HNSW parameters. | <span class="pill">Web UI</span> | 15m | <span class="text-green">Beginner</span> |
| [Reranking for Better Search](/documentation/search-precision/reranking-semantic-search/index.md) | Use multivector representations for better ranking. | <span class="pill">Python</span> | 30m | <span class="text-yellow">Intermediate</span> |
| [Hybrid Search with Reranking](/documentation/tutorials-search-engineering/reranking-hybrid-search/index.md) | Implement late interaction and sparse reranking. | <span class="pill">Python</span> | 40m | <span class="text-yellow">Intermediate</span> |
| [Semantic Search for Code](/documentation/tutorials-search-engineering/code-search/index.md) | Navigate codebases using vector similarity. | <span class="pill">Python</span> | 45m | <span class="text-yellow">Intermediate</span> |
| [Multi-Representation Search](/documentation/tutorials-search-engineering/multi-representation-search/index.md) | Fuse title, summary, chunk, and tag vectors with named vectors and the Query API. | <span class="pill">Python</span> | 45m | <span class="text-yellow">Intermediate</span> |
| [Static Embeddings](/documentation/tutorials-search-engineering/static-embeddings/index.md) | Evaluate the renaissance of static embeddings. | <span class="pill">Python</span> | 20m | <span class="text-yellow">Intermediate</span> |
| [Branch-Aware Search](/documentation/tutorials-search-engineering/branch-aware-search/index.md) | Scope search to a branch's live view in a versioned corpus, inherited from its ancestors. | <span class="pill">Python</span> | 25m | <span class="text-yellow">Intermediate</span> |

---

### RAG & AI Agents
*Build intelligent agents and complex LLM-driven applications.*

| Tutorial | Objective | Stack | Time | Level |
| :--- | :--- | :--- | :--- | :--- |
| [Multimodal & Multilingual RAG](/documentation/multimodal-search/index.md) | Search across image and text modalities. | <span class="pill">LlamaIndex</span> | 15m | <span class="text-green">Beginner</span> |
| [Agentic RAG with CrewAI](/documentation/agentic-rag-crewai-zoom/index.md) | Step-by-step multi-agent RAG system. | <span class="pill">CrewAI</span> | 45m | <span class="text-green">Beginner</span> |
| [Agentic RAG with LangGraph](/documentation/agentic-rag-langgraph/index.md) | Build AI agents to answer library documentation. | <span class="pill">LangGraph</span> | 45m | <span class="text-yellow">Intermediate</span> |
| [Discord RAG Bot](/documentation/agentic-rag-camelai-discord/index.md) | Develop a functional bot with CAMEL-AI. | <span class="pill">OpenAI</span> | 45m | <span class="text-yellow">Intermediate</span> |
| [LLM-Powered Filter Automation](/documentation/search-precision/automate-filtering-with-llms/index.md) | Use LLM structured output for dynamic filters. | <span class="pill">Python</span> | 30m | <span class="text-yellow">Intermediate</span> |

---

### Operations & Scale
*Production-grade management, monitoring, and high-volume optimization.*

| Tutorial | Objective | Stack | Time | Level |
| :--- | :--- | :--- | :--- | :--- |
| [Snapshots](/documentation/tutorials-operations/create-snapshot/index.md) | Create and restore collection snapshots. | <span class="pill">Python</span> | 20m | <span class="text-green">Beginner</span> |
| [Cloud Inference Hybrid Search](/documentation/tutorials-and-examples/cloud-inference-hybrid-search/index.md) | Hybrid search using Qdrant's built-in inference. | <span class="pill">Any</span> | 20m | <span class="text-green">Beginner</span> |
| [Data Migration](/documentation/tutorials-operations/migration/index.md) | Move dense and sparse embeddings to Qdrant. | <span class="pill">CLI</span> | 30m | <span class="text-yellow">Intermediate</span> |
| [Qdrant Cloud Prometheus Monitoring](/documentation/ops-monitoring/managed-cloud-prometheus/index.md) | Observability with Prometheus and Grafana. | <span class="pill">Prometheus</span> | 30m | <span class="text-yellow">Intermediate</span> |
| [Self-Hosted Prometheus Monitoring](/documentation/ops-monitoring/hybrid-cloud-prometheus/index.md) | Observability for hybrid/private cloud setups. | <span class="pill">Prometheus</span> | 30m | <span class="text-yellow">Intermediate</span> |
| [Large-Scale Search](/documentation/tutorials-operations/large-scale-search/index.md) | Cost-efficient search for LAION-400M datasets. | <span class="pill">None</span> | 2 days | <span class="text-red">Advanced</span> |

---

### Develop & Implement
*Core tools and APIs for building with Qdrant.*

| Tutorial | Objective | Stack | Time | Level |
| :--- | :--- | :--- | :--- | :--- |
| [Bulk Operations](/documentation/tutorials-develop/bulk-upload/index.md) | High-scale ingestion tricks for power users. | <span class="pill">Python</span> | 20m | <span class="text-yellow">Intermediate</span> |
| [Async API](/documentation/tutorials-develop/async-api/index.md) | Use Asynchronous programming for efficiency. | <span class="pill">Python</span> | 25m | <span class="text-yellow">Intermediate</span> |

---

### Ecosystem & Integrations
*Connect Qdrant to cloud providers, data streams, and ETL tools.*

| Tutorial | Objective | Stack | Time | Level |
| :--- | :--- | :--- | :--- | :--- |
| [S3 Ingestion with LangChain](/documentation/data-ingestion-beginners/index.md) | Stream data from AWS S3 to vector store. | <span class="pill">LangChain</span> | 30m | <span class="text-green">Beginner</span> |
| [Hugging Face Dataset Ingestion](/documentation/tutorials-ecosystem/huggingface-datasets/index.md) | Load and search public ML datasets. | <span class="pill">Python</span> | 15m | <span class="text-green">Beginner</span> |
| [Databricks Ingestion](/documentation/send-data/databricks/index.md) | Vectorize datasets using FastEmbed on Databricks. | <span class="pill">Databricks</span> | 30m | <span class="text-yellow">Intermediate</span> |
| [Querying with Airflow](/documentation/send-data/qdrant-airflow-astronomer/index.md) | Orchestrate data engineering workflows. | <span class="pill">Airflow</span> | 45m | <span class="text-yellow">Intermediate</span> |
| [n8n Workflow Automation](/documentation/qdrant-n8n/index.md) | Combine Qdrant with low-code n8n workflows. | <span class="pill">n8n</span> | 45m | <span class="text-yellow">Intermediate</span> |
| [Kafka Streaming into Qdrant](/documentation/send-data/data-streaming-kafka-qdrant/index.md) | Setup Qdrant Sink Connector for real-time data. | <span class="pill">Kafka</span> | 60m | <span class="text-red">Advanced</span> |

-->