# retrieval/learning_to_rank/lambdamart_ranker.py
"""
LambdaMART Learning-to-Rank for retrieval reranking
Requires: pip install lightgbm scikit-learn
"""
import numpy as np
import lightgbm as lgb
from typing import List, Dict, Tuple, Any
from sklearn.model_selection import train_test_split
from dataclasses import dataclass

@dataclass
class RankingFeature:
    """Single ranking feature"""
    name: str
    value: float

class FeatureExtractor:
    """Extract features for LTR"""
    
    def extract_features(self, query: str, document: Dict) -> List[RankingFeature]:
        """Extract features from query-document pair"""
        features = []
        
        # 1. BM25 score
        features.append(RankingFeature("bm25_score", document.get('bm25_score', 0.0)))
        
        # 2. Vector similarity
        features.append(RankingFeature("vector_sim", document.get('vector_similarity', 0.0)))
        
        # 3. Document length (normalized)
        doc_len = len(document.get('text', '').split())
        features.append(RankingFeature("doc_length", min(doc_len / 1000, 1.0)))
        
        # 4. Query term overlap
        query_terms = set(query.lower().split())
        doc_terms = set(document.get('text', '').lower().split())
        overlap = len(query_terms & doc_terms) / max(len(query_terms), 1)
        features.append(RankingFeature("term_overlap", overlap))
        
        # 5. Position in initial ranking
        features.append(RankingFeature("initial_rank", 1.0 / (document.get('rank', 1) + 1)))
        
        # 6. RRF score
        features.append(RankingFeature("rrf_score", document.get('rrf_score', 0.0)))
        
        # 7. Semantic similarity (if available)
        features.append(RankingFeature("semantic_sim", document.get('semantic_score', 0.0)))
        
        return features

class LambdaMARTranker:
    """LambdaMART Learning-to-Rank model"""
    
    def __init__(self, num_trees: int = 100, learning_rate: float = 0.1):
        self.num_trees = num_trees
        self.learning_rate = learning_rate
        self.model = None
        self.feature_extractor = FeatureExtractor()
    
    def prepare_training_data(self, qrels: List[Dict]) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Prepare training data from qrels (query relevance judgments)
        
        qrels format: [
            {"query_id": "q1", "doc_id": "d1", "relevance": 2, "features": [...]},
            ...
        ]
        """
        X = []  # Features
        y = []  # Relevance scores
        groups = []  # Query groups
        
        current_query_id = None
        query_doc_count = 0
        
        for item in sorted(qrels, key=lambda x: x['query_id']):
            if item['query_id'] != current_query_id:
                if current_query_id is not None:
                    groups.append(query_doc_count)
                current_query_id = item['query_id']
                query_doc_count = 0
            
            # Extract feature values
            feature_values = [f.value for f in item.get('features', [])]
            X.append(feature_values)
            y.append(item['relevance'])
            query_doc_count += 1
        
        groups.append(query_doc_count)
        
        return np.array(X), np.array(y), np.array(groups)
    
    def train(self, qrels: List[Dict], validation_split: float = 0.2):
        """Train LambdaMART model"""
        X, y, groups = self.prepare_training_data(qrels)
        
        # Create ranking dataset
        train_data = lgb.Dataset(
            X, label=y, group=groups,
            params={'objective': 'lambdarank', 'metric': 'ndcg', 'ndcg_eval_at': [5, 10]}
        )
        
        # Train model
        self.model = lgb.train(
            params={
                'objective': 'lambdarank',
                'metric': 'ndcg',
                'ndcg_eval_at': [5, 10],
                'num_leaves': 31,
                'learning_rate': self.learning_rate,
                'num_trees': self.num_trees,
                'verbose': 1
            },
            train_set=train_data
        )
        
        print(f"✅ Trained LambdaMART with {self.num_trees} trees")
        return self.model
    
    def predict(self, features: List[List[float]]) -> List[float]:
        """Predict relevance scores for documents"""
        if self.model is None:
            raise ValueError("Model not trained yet")
        return self.model.predict(features)
    
    def rerank(self, query: str, documents: List[Dict]) -> List[Dict]:
        """Rerank documents using LambdaMART"""
        # Extract features for each document
        all_features = []
        for doc in documents:
            features = self.feature_extractor.extract_features(query, doc)
            feature_values = [f.value for f in features]
            all_features.append(feature_values)
        
        # Predict scores
        scores = self.predict(all_features)
        
        # Sort by predicted score
        for doc, score in zip(documents, scores):
            doc['ltr_score'] = score
        
        reranked = sorted(documents, key=lambda x: x['ltr_score'], reverse=True)
        return reranked
    
    def save(self, path: str):
        """Save model to disk"""
        if self.model:
            self.model.save_model(path)
            print(f"✅ Saved model to {path}")
    
    def load(self, path: str):
        """Load model from disk"""
        self.model = lgb.Booster(model_file=path)
        print(f"✅ Loaded model from {path}")