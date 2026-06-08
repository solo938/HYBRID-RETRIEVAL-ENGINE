"""
Ingest all documents from data/raw/ into the RAG system
Supports: PDFs, HTML, Excel, JSON, Markdown
"""
import json
import os
from pathlib import Path
from typing import List, Dict
import sys

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from sentence_transformers import SentenceTransformer
import numpy as np

class DocumentIngestor:
    def __init__(self):
        print("🚀 Initializing Document Ingestor...")
        self.model = SentenceTransformer("BAAI/bge-small-en-v1.5")
        self.documents = []
        self.chunk_id = 0
    
    def ingest_pdfs(self, pdf_dir: str = "data/raw/pdfs"):
        """Ingest PDF files"""
        from pypdf import PdfReader
        pdf_dir = Path(pdf_dir)
        if not pdf_dir.exists():
            print(f"  ⚠️ PDF directory not found: {pdf_dir}")
            return
        
        for pdf_file in pdf_dir.glob("*.pdf"):
            try:
                reader = PdfReader(pdf_file)
                text = ""
                for page in reader.pages[:10]:  # First 10 pages only
                    text += page.extract_text()
                
                if text:
                    self.documents.append({
                        "id": f"pdf_{pdf_file.stem}",
                        "content": text[:2000],  # Limit length
                        "source": str(pdf_file),
                        "type": "pdf",
                        "title": pdf_file.stem
                    })
                    print(f"  ✅ Ingested: {pdf_file.name} ({len(text[:2000])} chars)")
            except Exception as e:
                print(f"  ❌ Failed to ingest {pdf_file.name}: {e}")
    
    def ingest_html(self, html_dir: str = "data/raw/html"):
        """Ingest HTML files"""
        from bs4 import BeautifulSoup
        html_dir = Path(html_dir)
        if not html_dir.exists():
            print(f"  ⚠️ HTML directory not found: {html_dir}")
            return
        
        for html_file in html_dir.glob("*.html"):
            try:
                with open(html_file, 'r', encoding='utf-8') as f:
                    soup = BeautifulSoup(f.read(), 'html.parser')
                    # Remove script and style elements
                    for script in soup(["script", "style"]):
                        script.decompose()
                    text = soup.get_text()
                    # Clean up whitespace
                    lines = (line.strip() for line in text.splitlines())
                    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                    text = ' '.join(chunk for chunk in chunks if chunk)
                
                if text:
                    self.documents.append({
                        "id": f"html_{html_file.stem}",
                        "content": text[:2000],
                        "source": str(html_file),
                        "type": "html",
                        "title": html_file.stem
                    })
                    print(f"  ✅ Ingested: {html_file.name} ({len(text[:2000])} chars)")
            except Exception as e:
                print(f"  ❌ Failed to ingest {html_file.name}: {e}")
    
    def ingest_excel(self, excel_dir: str = "data/raw/excel"):
        """Ingest Excel files"""
        import pandas as pd
        excel_dir = Path(excel_dir)
        if not excel_dir.exists():
            print(f"  ⚠️ Excel directory not found: {excel_dir}")
            return
        
        for excel_file in excel_dir.glob("*.xlsx"):
            try:
                df = pd.read_excel(excel_file)
                text = df.to_string()
                self.documents.append({
                    "id": f"excel_{excel_file.stem}",
                    "content": text[:2000],
                    "source": str(excel_file),
                    "type": "excel",
                    "title": excel_file.stem,
                    "metadata": {col: str(df[col].iloc[0]) if len(df) > 0 else "" for col in df.columns[:5]}
                })
                print(f"  ✅ Ingested: {excel_file.name} ({len(text[:2000])} chars)")
            except Exception as e:
                print(f"  ❌ Failed to ingest {excel_file.name}: {e}")
    
    def ingest_json(self, json_dir: str = "data/raw/json"):
        """Ingest JSON files"""
        json_dir = Path(json_dir)
        if not json_dir.exists():
            print(f"  ⚠️ JSON directory not found: {json_dir}")
            return
        
        for json_file in json_dir.glob("*.json"):
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                
                # Handle list of items
                if isinstance(data, list):
                    for i, item in enumerate(data[:20]):  # First 20 items
                        text = json.dumps(item, indent=2)
                        self.documents.append({
                            "id": f"json_{json_file.stem}_{i}",
                            "content": text[:1500],
                            "source": str(json_file),
                            "type": "json",
                            "title": f"{json_file.stem}_{i}"
                        })
                else:
                    text = json.dumps(data, indent=2)[:2000]
                    self.documents.append({
                        "id": f"json_{json_file.stem}",
                        "content": text,
                        "source": str(json_file),
                        "type": "json",
                        "title": json_file.stem
                    })
                print(f"  ✅ Ingested: {json_file.name}")
            except Exception as e:
                print(f"  ❌ Failed to ingest {json_file.name}: {e}")
    
    def ingest_markdown(self, md_dir: str = "data/raw/markdown"):
        """Ingest Markdown files"""
        md_dir = Path(md_dir)
        if not md_dir.exists():
            print(f"  ⚠️ Markdown directory not found: {md_dir}")
            return
        
        for md_file in md_dir.glob("*.md"):
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    text = f.read()
                
                self.documents.append({
                    "id": f"md_{md_file.stem}",
                    "content": text[:2000],
                    "source": str(md_file),
                    "type": "markdown",
                    "title": md_file.stem
                })
                print(f"  ✅ Ingested: {md_file.name} ({len(text[:2000])} chars)")
            except Exception as e:
                print(f"  ❌ Failed to ingest {md_file.name}: {e}")
    
    def ingest_all(self):
        """Ingest all document types"""
        print("\n📥 Ingesting all documents...\n")
        self.ingest_pdfs()
        self.ingest_html()
        self.ingest_excel()
        self.ingest_json()
        self.ingest_markdown()
        
        print(f"\n✅ Total documents ingested: {len(self.documents)}")
        
        # Generate embeddings
        if self.documents:
            print("\n🔧 Generating embeddings...")
            texts = [d["content"] for d in self.documents]
            embeddings = self.model.encode(texts, normalize_embeddings=True)
            
            # Save to file
            output = {
                "documents": self.documents,
                "embeddings": embeddings.tolist()
            }
            
            with open("data/processed/all_documents_index.json", "w") as f:
                json.dump(output, f, indent=2)
            
            print(f"✅ Saved index with {len(self.documents)} documents")
        
        return self.documents

if __name__ == "__main__":
    ingestor = DocumentIngestor()
    docs = ingestor.ingest_all()
    
    print("\n" + "="*60)
    print("📊 Ingestion Summary")
    print("="*60)
    print(f"Total documents: {len(docs)}")
    
    # Count by type
    types = {}
    for doc in docs:
        t = doc.get("type", "unknown")
        types[t] = types.get(t, 0) + 1
    
    for t, count in types.items():
        print(f"  {t}: {count}")
