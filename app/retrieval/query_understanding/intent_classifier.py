from enum import Enum

class QueryIntent(Enum):
    FACTUAL = "factual"
    KEYWORD = "keyword"
    SEMANTIC = "semantic"
    NAVIGATIONAL = "navigational"

class IntentClassifier:
    def classify(self, query: str) -> QueryIntent:
        q = query.lower()
        if '"' in q or q.startswith("exact:"):
            return QueryIntent.KEYWORD
        if any(phrase in q for phrase in ["how to", "steps", "guide", "tutorial"]):
            return QueryIntent.NAVIGATIONAL
        if len(q.split()) < 4:
            return QueryIntent.KEYWORD
        if any(word in q for word in ["why", "explain", "what is", "define"]):
            return QueryIntent.FACTUAL
        return QueryIntent.SEMANTIC