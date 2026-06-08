import json
import random
from pathlib import Path
from typing import List, Dict, Any
import os

class GoldenDatasetBuilder:
    """Build production golden dataset for RAG evaluation - No HuggingFace dependency"""
    
    def __init__(self, output_dir: str = "app/evaluation/datasets/goldens"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def build_from_squad(self, num_samples: int = 500, squad_path: str = "data/raw/json/squad_v2_sample.json"):
        """Build from local SQuAD v2 JSON file"""
        print(f"📥 Loading SQuAD v2 from {squad_path} ({num_samples} samples)...")
        
        if not os.path.exists(squad_path):
            print(f"❌ SQuAD file not found at {squad_path}")
            print("Downloading SQuAD v2...")
            import requests
            url = "https://rajpurkar.github.io/SQuAD-explorer/dataset/dev-v2.0.json"
            response = requests.get(url)
            with open(squad_path, 'w') as f:
                f.write(response.text)
            print(f"✅ Downloaded SQuAD v2 to {squad_path}")
        
        with open(squad_path, 'r') as f:
            squad_data = json.load(f)
        
        questions = []
        answers = []
        relevant_docs = []
        
        sample_count = 0
        for article in squad_data['data']:
            for paragraph in article['paragraphs']:
                context = paragraph['context']
                
                for qa in paragraph['qas']:
                    if sample_count >= num_samples:
                        break
                    
                    qid = f"squad_{qa['id']}"
                    
                    # Get answer text
                    answer_text = ""
                    is_impossible = len(qa['answers']) == 0
                    if not is_impossible:
                        answer_text = qa['answers'][0]['text']
                    
                    questions.append({
                        "id": qid,
                        "text": qa['question'],
                        "domain": "general_knowledge",
                        "difficulty": "medium",
                        "context": context[:500]  # Store first 500 chars for reference
                    })
                    
                    answers.append({
                        "id": qid,
                        "text": answer_text,
                        "is_impossible": is_impossible,
                        "answer_start": qa['answers'][0]['answer_start'] if qa['answers'] else -1
                    })
                    
                    # Create chunk mappings (simulate multiple chunks per document)
                    chunk_ids = [f"chunk_{qid}_{i}" for i in range(random.randint(1, 3))]
                    relevant_docs.append({
                        "query_id": qid,
                        "document_ids": [f"doc_{article.get('title', 'unknown')}"],
                        "chunk_ids": chunk_ids,
                        "context_preview": context[:200]
                    })
                    
                    sample_count += 1
                
                if sample_count >= num_samples:
                    break
            if sample_count >= num_samples:
                break
        
        self._save_questions(questions)
        self._save_answers(answers)
        self._save_relevant_docs(relevant_docs)
        
        print(f"✅ Built golden dataset with {len(questions)} samples from SQuAD")
        return questions, answers, relevant_docs
    
    def build_from_it_tickets(self, tickets_file: str):
        """Build from IT tickets for enterprise domain"""
        print(f"📥 Loading IT tickets from {tickets_file}...")
        
        if not os.path.exists(tickets_file):
            print(f"⚠️ {tickets_file} not found, creating mock tickets")
            tickets = self._create_mock_tickets()
        else:
            with open(tickets_file, 'r') as f:
                tickets = json.load(f)
        
        questions = []
        answers = []
        relevant_docs = []
        
        for ticket in tickets[:100]:
            qid = ticket.get('ticket_id', ticket.get('id', f"it_{len(questions)}"))
            questions.append({
                "id": qid,
                "text": ticket.get('title', 'No title'),
                "domain": "enterprise_it",
                "difficulty": "easy",
                "metadata": {
                    "priority": ticket.get('priority', 'P3'),
                    "category": ticket.get('category', 'general'),
                    "status": ticket.get('status', 'open')
                }
            })
            
            answers.append({
                "id": qid,
                "text": ticket.get('description', 'No description provided'),
                "is_impossible": False
            })
            
            relevant_docs.append({
                "query_id": qid,
                "document_ids": [f"ticket_{qid}"],
                "chunk_ids": [f"chunk_{qid}_0", f"chunk_{qid}_1"]
            })
        
        self._save_questions(questions, suffix="_it")
        self._save_answers(answers, suffix="_it")
        self._save_relevant_docs(relevant_docs, suffix="_it")
        
        print(f"✅ Built IT ticket dataset with {len(questions)} samples")
    
    def _create_mock_tickets(self):
        """Create mock IT tickets if file doesn't exist"""
        tickets = []
        priorities = ['P1', 'P2', 'P3', 'P4']
        categories = ['network', 'security', 'database', 'application', 'hardware', 'access']
        statuses = ['open', 'in_progress', 'resolved', 'closed']
        teams = ['infra', 'security', 'data', 'apps', 'support']
        
        for i in range(100):
            category = random.choice(categories)
            tickets.append({
                "ticket_id": f"INC{str(i).zfill(6)}",
                "id": f"TICKET_{i}",
                "title": f"[{category.upper()}] Issue with {category} component affecting production",
                "description": f"Detailed description of the {category} issue: Users are unable to access the service. Investigation ongoing. Root cause appears to be related to recent deployment.",
                "priority": random.choice(priorities),
                "category": category,
                "status": random.choice(statuses),
                "assigned_team": random.choice(teams),
                "created_at": f"2025-06-{str(random.randint(1, 30)).zfill(2)}T10:00:00"
            })
        return tickets
    
    def _save_questions(self, questions: List[Dict], suffix: str = ""):
        output_file = self.output_dir / f"questions{suffix}.json"
        with open(output_file, 'w') as f:
            json.dump(questions, f, indent=2)
        print(f"  📄 Saved {len(questions)} questions to {output_file}")
    
    def _save_answers(self, answers: List[Dict], suffix: str = ""):
        output_file = self.output_dir / f"answers{suffix}.json"
        with open(output_file, 'w') as f:
            json.dump(answers, f, indent=2)
        print(f"  📄 Saved {len(answers)} answers to {output_file}")
    
    def _save_relevant_docs(self, relevant_docs: List[Dict], suffix: str = ""):
        output_file = self.output_dir / f"relevant_docs{suffix}.json"
        with open(output_file, 'w') as f:
            json.dump(relevant_docs, f, indent=2)
        print(f"  📄 Saved {len(relevant_docs)} relevance mappings to {output_file}")
    
    def create_evaluation_splits(self):
        """Create train/dev/test splits for evaluation"""
        questions_file = self.output_dir / "questions.json"
        if not questions_file.exists():
            print("⚠️ questions.json not found, skipping splits")
            return
        
        with open(questions_file, 'r') as f:
            questions = json.load(f)
        
        # Create splits: 70% train, 15% dev, 15% test
        n = len(questions)
        train_end = int(n * 0.7)
        dev_end = int(n * 0.85)
        
        splits = {
            "train": questions[:train_end],
            "dev": questions[train_end:dev_end],
            "test": questions[dev_end:]
        }
        
        # Save splits in eval_splits directory
        splits_dir = self.output_dir / "eval_splits"
        splits_dir.mkdir(parents=True, exist_ok=True)
        
        for split_name, split_data in splits.items():
            output_file = splits_dir / f"retrieval_eval_{split_name}.json"
            with open(output_file, 'w') as f:
                json.dump(split_data, f, indent=2)
            print(f"  📄 Saved {len(split_data)} samples to {output_file}")
        
        print(f"✅ Created splits: train={len(splits['train'])}, dev={len(splits['dev'])}, test={len(splits['test'])}")
        
        # Also create generation eval set (subset for generation testing)
        generation_eval = []
        for item in questions[:min(50, len(questions))]:
            generation_eval.append({
                "query_id": item['id'],
                "query": item['text'],
                "domain": item.get('domain', 'general'),
                "expected_answer": "Sample answer - will be populated from answers.json"
            })
        
        gen_file = splits_dir / "generation_eval.json"
        with open(gen_file, 'w') as f:
            json.dump(generation_eval, f, indent=2)
        print(f"  📄 Saved {len(generation_eval)} generation eval samples to {gen_file}")

if __name__ == "__main__":
    builder = GoldenDatasetBuilder()
    builder.build_from_squad(num_samples=500)
    builder.build_from_it_tickets("data/raw/json/it_tickets.json")
    builder.create_evaluation_splits()
