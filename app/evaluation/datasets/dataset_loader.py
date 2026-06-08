"""Load evaluation datasets from JSON/JSONL files."""
import json
from dataclasses import dataclass
from typing import List, Set
from pathlib import Path


@dataclass
class RetrievalSample:
    query: str
    relevant_chunk_ids: Set[str]


class RetrievalDatasetLoader:
    @staticmethod
    def load_jsonl(path: Path) -> List[RetrievalSample]:
        samples = []
        with open(path) as f:
            for line in f:
                data = json.loads(line)
                samples.append(RetrievalSample(
                    query=data["query"],
                    relevant_chunk_ids=set(data["relevant_chunk_ids"]),
                ))
        return samples

    @staticmethod
    def load_json(path: Path) -> List[RetrievalSample]:
        with open(path) as f:
            data = json.load(f)
        return [RetrievalSample(q["query"], set(q["relevant_chunk_ids"])) for q in data]