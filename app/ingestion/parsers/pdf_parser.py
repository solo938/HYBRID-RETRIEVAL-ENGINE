"""PDF parser using PyMuPDF with context manager."""
import fitz
from pathlib import Path
from typing import Dict, Any

def parse_pdf(file_path: str | Path) -> Dict[str, Any]:
    """
    Extract text and metadata from a PDF file.
    
    Args:
        file_path: Path to the PDF file.
        
    Returns:
        dict: {"text": str, "metadata": {"source": str, "pages": int, ...}}
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")
    
    with fitz.open(path) as doc:
        text_parts = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            text_parts.append(page.get_text())
        
        full_text = "\n\n".join(text_parts)
        
        metadata = {
            "source": str(path.absolute()),
            "pages": len(doc),
            "title": doc.metadata.get("title", ""),
            "author": doc.metadata.get("author", ""),
            "creation_date": doc.metadata.get("creationDate", ""),
        }
    
    return {
        "text": full_text,
        "metadata": metadata
    }

# Example usage
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        result = parse_pdf(sys.argv[1])
        print(f"✓ Parsed: {result['metadata']['source']}")
        print(f"  Pages: {result['metadata']['pages']}")
        print(f"  Text length: {len(result['text'])} characters")
        print(f"\nFirst 500 chars:\n{result['text'][:500]}...")
    else:
        print("Usage: python pdf_parser.py <file.pdf>")