import json
import re
import os
from pathlib import Path
from collections import defaultdict
from typing import List, Tuple, Dict, Any, Optional

class SmartGuardrail:
    """
    AIONS Smart Guardrail System (CBMS-KR + FACTS DB).
    
    Enforces 'No Hallucination' policy by verifying query keywords against
    the deterministic CBMS knowledge index AND the facts database.
    
    Refusal Policy:
    - If no relevant knowledge chunks are found in EITHER index -> REFUSE ANSWER.
    - If relevant checks found -> Return them as evidence context.
    
    Data Sources:
    1. CBMS_INDEX_KOREAN (Legacy Index: kr_postings.bin)
    2. FACTS DB (Primary Knowledge: facts.jsonl)
    """
    
    def __init__(self, index_dir: str = "cbms_index"):
        self.root = Path(__file__).parent
        self.index_path = self.root / index_dir
        
        # Legacy Source
        self.postings_path = self.index_path / "kr_postings.bin"
        self.meta_path = self.index_path / "kr_meta.json"
        
        # Primary Source (Facts DB)
        # Assuming we copy it or reference it directly. 
        # Using absolute path for E: drive to ensure "No Skip" access.
        self.facts_path = Path("E:/AJAJAJ/AIONS_COMPLETE/cbms_memory/facts.jsonl")
        
        self.REFUSAL_MESSAGE = "NIE WIEM / BRAK DANYCH CBMS-KR."
        self.TOKEN_PATTERN = re.compile(r"[A-Za-z0-9]{3,}")
        self.TOPK = 12
        self.MAX_PREFIX_CHARS = 2500 # Increased for dual context
        
        # Combined Knowledge Base
        self.postings = defaultdict(list) # Token -> List[DocIdx]
        self.doc_texts = []
        self.doc_ids = []
        self.doc_token_sets = []
        
        self._load_combined_index()
        
    def _tokenize(self, text: str) -> List[str]:
        return [tok.lower() for tok in self.TOKEN_PATTERN.findall(text)]

    def _load_combined_index(self):
        """Load and merge both knowledge sources."""
        print("🔄 Guardrail: Loading Knowledge Bases...")
        
        # 1. Load Legacy Index (CBMS-KR)
        legacy_count = 0
        if self.postings_path.exists() and self.meta_path.exists():
            try:
                # Load Postings
                raw_postings = {}
                try:
                    postings_bytes = self.postings_path.read_bytes()
                    raw_postings = json.loads(postings_bytes.decode("utf-8"))
                except Exception as e:
                    print(f"⚠️ Legacy Index Decode Error: {e}")

                # Load Metadata (Docs)
                meta_blob = json.loads(self.meta_path.read_text(encoding="utf-8"))
                legacy_docs = meta_blob.get("docs", [])
                
                for doc in legacy_docs:
                    doc_idx = len(self.doc_texts)
                    text = doc.get("text", "")
                    self.doc_texts.append(text)
                    self.doc_ids.append(doc.get("doc_id", f"LEGACY_{doc_idx}"))
                    
                    tokens = set(self._tokenize(text))
                    self.doc_token_sets.append(tokens)
                    
                    # Add to postings (if not already there from raw_postings, 
                    # but raw_postings points to OLD indices. We must re-index or map.)
                    # Re-indexing is safer for merging.
                    for tok in tokens:
                        self.postings[tok].append(doc_idx)
                        
                    legacy_count += 1
                
                print(f"   + Loaded {legacy_count} legacy docs.")
            except Exception as e:
                print(f"❌ Legacy Load Failed: {e}")
        else:
            print("⚠️ Legacy Index not found found (skipping)")

        # 2. Load Facts DB (Primary)
        facts_count = 0
        if self.facts_path.exists():
            try:
                with open(self.facts_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if not line.strip(): continue
                        try:
                            # {"id": "...", "text": "...", "keys": [...]}
                            record = json.loads(line)
                            doc_idx = len(self.doc_texts)
                            
                            text = record.get("text", "")
                            identifier = record.get("id", f"FACT_{doc_idx}")
                            keys = record.get("keys", []) # Pre-computed keys (grams/hashes)
                            
                            self.doc_texts.append(text)
                            self.doc_ids.append(identifier)
                            
                            # Use keys provided in JSONL as tokens for indexing 
                            # AND tokenize text for natural language search
                            nl_tokens = set(self._tokenize(text))
                            provided_tokens = set(keys)
                            all_tokens = nl_tokens.union(provided_tokens)
                            
                            self.doc_token_sets.append(all_tokens)
                            
                            for tok in all_tokens:
                                self.postings[tok].append(doc_idx)
                                
                            facts_count += 1
                        except json.JSONDecodeError:
                            continue
                            
                print(f"   + Loaded {facts_count} facts from DB.")
            except Exception as e:
                print(f"❌ Facts DB Load Failed: {e}")
        else:
            print(f"⚠️ Facts DB not found at {self.facts_path}")

        print(f"✅ Guardrail Ready: {len(self.doc_texts)} total documents.")

    def retrieve(self, query: str) -> List[Tuple[float, int, int]]:
        """
        Retrieve relevant documents using token overlap.
        """
        tokens = self._tokenize(query)
        if not tokens:
            return []
            
        scores = defaultdict(float)
        query_token_set = set(tokens)
        
        for tok in tokens:
            # Look up token in postings
            matches = self.postings.get(tok, [])
            for doc_idx in matches:
                scores[doc_idx] += 1.0

        candidates = []
        for doc_idx, base_score in scores.items():
            # Verification step: Token Overlap Count
            # We want strict grounding.
            
            # Allow even single keyword match if it's a specific key (like "python")
            # But general text might need more overlap.
            
            doc_tokens = self.doc_token_sets[doc_idx]
            overlap = len(query_token_set & doc_tokens)
            
            # Simple scoring: Base Score (frequency) + Overlap Bonus
            total = base_score + (overlap * 0.5)
            
            if total > 0.5: # Min threshold
                candidates.append((total, doc_idx, overlap))
            
        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates[:self.TOPK]

    def check(self, query: str) -> Dict[str, Any]:
        """
        Check the query against the knowledge base.
        """
        hits = self.retrieve(query)
        
        # Strictness: If ZERO hits, refuse.
        if not hits:
            return {
                "allowed": False,
                "reason": self.REFUSAL_MESSAGE,
                "evidence": None
            }
            
        # Compose evidence string
        snippets = []
        used = 0
        evidence_ids = []
        
        for score, doc_idx, _ in hits:
            text = self.doc_texts[doc_idx]
            if not text:
                continue
                
            needed = self.MAX_PREFIX_CHARS - used
            if needed <= 0:
                break
                
            # Truncate if long chunk
            # But try to keep whole sentences if possible (not implemented here for speed)
            snippet = text[:1000] # Cap individual chunk size too
            
            snippets.append(f"[{self.doc_ids[doc_idx]}] (Score: {score:.1f}) {snippet}")
            evidence_ids.append(self.doc_ids[doc_idx])
            used += len(snippet)
            
        evidence_str = "\n\n".join(snippets)
        
        return {
            "allowed": True,
            "evidence": evidence_str,
            "evidence_ids": evidence_ids
        }
