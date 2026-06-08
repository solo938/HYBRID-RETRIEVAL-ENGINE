# observability/metrics.py - Complete implementation
from prometheus_client import Counter, Histogram, Gauge, Summary
import time
from functools import wraps
from typing import Callable, Any

# Metrics definitions
RETRIEVAL_LATENCY = Histogram(
    'rag_retrieval_latency_seconds',
    'Retrieval latency in seconds',
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0]
)

RERANKING_LATENCY = Histogram(
    'rag_reranking_latency_seconds',
    'Reranking latency in seconds',
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0]
)

QUERY_COUNT = Counter(
    'rag_queries_total',
    'Total number of queries',
    ['status', 'domain']
)

CACHE_HITS = Counter(
    'rag_cache_hits_total',
    'Cache hits',
    ['cache_level']
)

CACHE_MISSES = Counter(
    'rag_cache_misses_total',
    'Cache misses',
    ['cache_level']
)

ACTIVE_QUERIES = Gauge(
    'rag_active_queries',
    'Currently active queries'
)

TOKEN_USAGE = Counter(
    'rag_tokens_total',
    'Total tokens used',
    ['model', 'type']  # type: 'input' or 'output'
)

RECALL_SCORE = Gauge(
    'rag_recall_at_k',
    'Recall@K score',
    ['k']
)

FAITHFULNESS_SCORE = Gauge(
    'rag_faithfulness',
    'Generation faithfulness score'
)

COST_PER_QUERY = Histogram(
    'rag_cost_per_query_dollars',
    'Cost per query in USD',
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5]
)

def track_latency(metric: Histogram):
    """Decorator to track function latency"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start
                metric.observe(duration)
        return wrapper
    return decorator

# Export metrics for Prometheus
def get_metrics_endpoint():
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    return generate_latest(), CONTENT_TYPE_LATEST