"""Complete RAG pipeline: retrieval → context assembly → citation → prompt → generation."""
from typing import Optional
from app.retrieval.hybrid_retriever import HybridRetriever
from app.core.models.security import ACLContext
from app.core.models.filters import RetrievalFilters
from app.generation.context.context_assembler import ContextAssembler
from app.generation.citations.citation_builder import CitationBuilder
from app.generation.prompts.grounded_prompt_builder import GroundedPromptBuilder
from app.generation.models.response import GroundedAnswer
from app.llm.base import BaseLLMProvider


class RAGPipeline:
    """
    End‑to‑end RAG pipeline:
    1. Retrieve chunks (with ACL and metadata filters)
    2. Assemble context window (deduplicate, token budget)
    3. Build citations
    4. Build grounded prompt
    5. Generate answer with LLM
    """

    def __init__(
        self,
        retriever: HybridRetriever,
        llm: BaseLLMProvider,
        context_assembler: Optional[ContextAssembler] = None,
        citation_builder: Optional[CitationBuilder] = None,
        prompt_builder: Optional[GroundedPromptBuilder] = None,
        max_context_tokens: int = 6000,
    ):
        self.retriever = retriever
        self.llm = llm
        self.context_assembler = context_assembler or ContextAssembler(max_tokens=max_context_tokens)
        self.citation_builder = citation_builder or CitationBuilder()
        self.prompt_builder = prompt_builder or GroundedPromptBuilder()

    async def answer(
        self,
        query: str,
        top_k: int = 5,
        acl_context: Optional[ACLContext] = None,
        filters: Optional[RetrievalFilters] = None,
    ) -> GroundedAnswer:
        """
        Run the full RAG pipeline asynchronously.
        """
        print("\n=== RAG Pipeline Debug ===")
        print(f"1. Query: {query}")
        print(f"2. Top K: {top_k}")
        
        # 1. Retrieve
        print("3. Running retrieval...")
        retrieval_result = self.retriever.retrieve(
            query=query,
            top_k=top_k,
            acl_context=acl_context,
            filters=filters,
        )
        chunks = retrieval_result.results
        print(f"4. Retrieved {len(chunks)} chunks")

        # 2. Assemble context
        print("5. Assembling context...")
        context_window = self.context_assembler.assemble(chunks)
        selected_chunks = context_window.chunks
        print(f"   Assembled {len(selected_chunks)} chunks, total tokens: {context_window.total_tokens}")

        # 3. Build citations
        print("6. Building citations...")
        citations, chunks_with_citations = self.citation_builder.build(selected_chunks)
        print(f"   Built {len(citations)} citations")

        # 4. Build prompt
        print("7. Building prompt...")
        prompt = self.prompt_builder.build(query, chunks_with_citations, citations)
        print(f"   Prompt length: {len(prompt)} characters")

        # 5. Generate answer (async)
        print("8. Generating answer from LLM...")
        answer_text = await self.llm.generate(prompt)
        print(f"   Answer length: {len(answer_text)} characters")
        print("=== RAG Pipeline Complete ===\n")

        # 6. Return grounded answer
        return GroundedAnswer(
            answer=answer_text,
            citations=citations,
            grounded=True,
            total_tokens=context_window.total_tokens,
        )