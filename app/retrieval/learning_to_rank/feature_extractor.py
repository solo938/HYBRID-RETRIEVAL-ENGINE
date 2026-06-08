# retrieval/learning_to_rank/feature_extractor.py
from typing import List, Dict, Any
import numpy as np

class ComprehensiveFeatureExtractor:
    """Extract comprehensive features for LTR"""
    
    def extract_all_features(self, query: str, document: Dict, context: Dict = None) -> np.ndarray:
        """Extract all available features"""
        features = []
        
        # Sparse retrieval features
        features.append(document.get('bm25_score', 0.0))
        features.append(document.get('tfidf_score', 0.0))
        
        # Dense retrieval features
        features.append(document.get('dense_score', 0.0))
        features.append(document.get('cosine_sim', 0.0))
        
        # Fusion features
        features.append(document.get('rrf_score', 0.0))
        features.append(document.get('weighted_fusion_score', 0.0))
        
        # Document features
        text = document.get('text', '')
        features.append(len(text.split()))  # Length
        features.append(len(set(text.lower().split())))  # Unique terms
        features.append(text.count('\n'))  # Newlines (structure)
        
        # Query-document interaction
        query_terms = set(query.lower().split())
        doc_terms = set(text.lower().split())
        features.append(len(query_terms & doc_terms) / max(len(query_terms), 1))
        
        # Position features
        features.append(1.0 / (document.get('initial_rank', 1) + 1))
        features.append(document.get('position', 0))
        
        # Metadata features (if available)
        metadata = document.get('metadata', {})
        features.append(metadata.get('page_rank', 0.0))
        features.append(metadata.get('freshness_score', 0.0))
        features.append(metadata.get('authority_score', 0.0))
        
        # Context features
        if context:
            features.append(context.get('query_length', 0))
            features.append(context.get('domain', 0))
        
        return np.array(features)