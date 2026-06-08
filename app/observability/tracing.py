# observability/tracing.py - OpenTelemetry implementation
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
import functools

class TracingSetup:
    """Setup OpenTelemetry tracing for RAG pipeline"""
    
    def __init__(self, service_name: str = "rag-engine", endpoint: str = "http://localhost:4317"):
        self.service_name = service_name
        self.endpoint = endpoint
        
    def setup(self):
        # Set up tracer provider
        provider = TracerProvider()
        
        # Add OTLP exporter
        otlp_exporter = OTLPSpanExporter(endpoint=self.endpoint, insecure=True)
        provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
        
        # Set global tracer
        trace.set_tracer_provider(provider)
        
        # Instrument libraries
        RequestsInstrumentor().instrument()
        HTTPXClientInstrumentor().instrument()
        
        return trace.get_tracer(self.service_name)

def trace_rag_pipeline(func):
    """Decorator to trace RAG pipeline steps"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        tracer = trace.get_tracer(__name__)
        with tracer.start_as_current_span(func.__name__) as span:
            # Add attributes
            span.set_attribute("pipeline.step", func.__name__)
            
            result = func(*args, **kwargs)
            
            # Add result attributes
            if isinstance(result, dict):
                if 'latency_ms' in result:
                    span.set_attribute("latency_ms", result['latency_ms'])
                if 'num_docs' in result:
                    span.set_attribute("retrieved_documents", result['num_docs'])
            
            return result
    return wrapper

# Usage in your code
tracer_setup = TracingSetup()
tracer = tracer_setup.setup()

@trace_rag_pipeline
def hybrid_search(query: str):
    """Your hybrid search implementation"""
    with tracer.start_as_current_span("retrieval") as span:
        span.set_attribute("query", query)
        # ... your retrieval logic