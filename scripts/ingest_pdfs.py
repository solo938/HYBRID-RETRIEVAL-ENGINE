"""Ingest all PDFs from data/raw/ into Qdrant and BM25."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.ingestion.document_loader import load_document
from app.ingestion.indexing.vector_indexer import VectorIndexer
from app.ingestion.indexing.bm25_indexer import BM25Indexer

def ingest_pdfs():
    raw_dir = Path("data/raw")
    pdf_files = list(raw_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("No PDF files found in data/raw/")
        return
    
    print(f"Found {len(pdf_files)} PDF files")
    
    all_docs = []
    
    for pdf_path in pdf_files:
        print(f"Processing: {pdf_path.name}")
        docs = load_document(pdf_path, chunk_size=500, chunk_overlap=50)
        print(f"  Created {len(docs)} chunks")
        all_docs.extend(docs)
    
    print(f"\nTotal chunks: {len(all_docs)}")
    
    # Index into Qdrant
    print("\nIndexing into Qdrant...")
    vector_indexer = VectorIndexer()
    vector_indexer.create_collection(force_recreate=True)
    vector_indexer.upsert_documents(all_docs)
    
    # Index into BM25
    print("Indexing into BM25...")
    bm25_indexer = BM25Indexer(cache_path=Path("data/bm25_index.pkl"))
    bm25_indexer.index_documents(all_docs)
    
    print("\n✅ Ingestion complete!")

if __name__ == "__main__":
    ingest_pdfs()