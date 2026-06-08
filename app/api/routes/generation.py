"""Generation endpoints: /generate (streaming) and /generate_sync."""
import json
import traceback
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.core.models.security import ACLContext
from app.core.models.filters import RetrievalFilters
from app.generation.rag_pipeline import RAGPipeline
from app.retrieval.hybrid_retriever import HybridRetriever
from app.api.dependencies import get_rag_pipeline, get_retriever

router = APIRouter(prefix="/generate", tags=["generation"])


class GenerateRequest(BaseModel):
    query: str
    top_k: int = 5
    stream: bool = False
    user_id: Optional[str] = None
    groups: Optional[list[str]] = None
    roles: Optional[list[str]] = None
    filters: Optional[RetrievalFilters] = None


class GenerateResponse(BaseModel):
    answer: str
    citations: list[dict]
    grounded: bool
    total_tokens: int


@router.post("/sync", response_model=GenerateResponse)
async def generate_sync(
    request: GenerateRequest,
    pipeline: RAGPipeline = Depends(get_rag_pipeline),
):
    """Generate a grounded answer (non‑streaming)."""
    acl = None
    if request.user_id:
        acl = ACLContext(
            user_id=request.user_id,
            groups=request.groups or [],
            roles=request.roles or [],
        )

    try:
        print("=" * 60)
        print(f"Processing query: {request.query}")
        print(f"Top K: {request.top_k}")
        
        # IMPORTANT: Added 'await' here because answer() is now async
        result = await pipeline.answer(
            query=request.query,
            top_k=request.top_k,
            acl_context=acl,
            filters=request.filters,
        )
        
        print(f"Answer generated: {len(result.answer)} chars")
        print(f"Citations: {len(result.citations)}")
        print("=" * 60)
        
        return GenerateResponse(
            answer=result.answer,
            citations=[c.__dict__ for c in result.citations],
            grounded=result.grounded,
            total_tokens=result.total_tokens,
        )
    except Exception as e:
        print("=" * 60)
        print("ERROR IN /generate/sync:")
        traceback.print_exc()
        print("=" * 60)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def generate_stream(
    request: GenerateRequest,
    pipeline: RAGPipeline = Depends(get_rag_pipeline),
):
    """Stream the generated answer token by token (SSE)."""
    if not request.stream:
        return await generate_sync(request, pipeline)

    acl = None
    if request.user_id:
        acl = ACLContext(
            user_id=request.user_id,
            groups=request.groups or [],
            roles=request.roles or [],
        )

    async def event_stream():
        try:
            print(f"Streaming query: {request.query}")
            
            # 1. Retrieve
            retrieval_result = pipeline.retriever.retrieve(
                query=request.query,
                top_k=request.top_k,
                acl_context=acl,
                filters=request.filters,
            )
            chunks = retrieval_result.results
            print(f"Retrieved {len(chunks)} chunks")

            # 2. Assemble context
            context_window = pipeline.context_assembler.assemble(chunks)
            selected_chunks = context_window.chunks
            print(f"Assembled {len(selected_chunks)} chunks into context")

            # 3. Build citations
            citations, chunks_with_citations = pipeline.citation_builder.build(selected_chunks)
            print(f"Built {len(citations)} citations")

            # 4. Build prompt
            prompt = pipeline.prompt_builder.build(request.query, chunks_with_citations, citations)
            print(f"Prompt length: {len(prompt)} chars")

            # 5. Stream tokens from LLM
            async for token in pipeline.llm.stream_generate(prompt):
                yield f"data: {json.dumps({'token': token})}\n\n"

            # 6. Send citations at the end
            yield f"data: {json.dumps({'citations': [c.__dict__ for c in citations]})}\n\n"
            yield "data: [DONE]\n\n"
            print("Streaming complete")
            
        except Exception as e:
            print("=" * 60)
            print("ERROR IN /generate/stream:")
            traceback.print_exc()
            print("=" * 60)
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/retrieve")
async def retrieve(
    request: GenerateRequest,
    retriever: HybridRetriever = Depends(get_retriever),
):
    """Perform only retrieval (no generation) and return the full result with traces."""
    try:
        result = retriever.retrieve(
            query=request.query,
            top_k=request.top_k,
            acl_context=ACLContext(
                user_id=request.user_id or "",
                groups=request.groups or [],
                roles=request.roles or [],
            ) if request.user_id else None,
            filters=request.filters,
        )
        # Convert to serializable format
        return {
            "results": [c.__dict__ for c in result.results],
            "trace": result.trace.__dict__,
            "retrieval_time_ms": result.retrieval_time_ms,
            "total_results": result.total_results,
            "fusion_method": result.fusion_method.value,
        }
    except Exception as e:
        print("=" * 60)
        print("ERROR IN /retrieve:")
        traceback.print_exc()
        print("=" * 60)
        raise HTTPException(status_code=500, detail=str(e))