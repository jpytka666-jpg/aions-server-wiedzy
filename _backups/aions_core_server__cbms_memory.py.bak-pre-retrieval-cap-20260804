#!/usr/bin/env python3
"""
CBMS Memory System - AI Knowledge Management with Chunking
Implements CBMS-style thinking and memory for AI agents
"""

import json
import os
import sys
import time
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

class CBMSMemory:
    """CBMS-based AI memory system"""
    
    def __init__(self, memory_dir: str = None):
        if memory_dir is None:
            # Fallback to repo-local memory directory if env var not set
            default_root = Path(__file__).resolve().parent.parent
            memory_dir = os.environ.get("CBMS_MEMORY_DIR", str(default_root / "memory"))
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(exist_ok=True)
        
        # Memory structure
        self.chunks_dir = self.memory_dir / "chunks"
        self.chunks_dir.mkdir(exist_ok=True)
        
        self.manifest_file = self.memory_dir / "knowledge_manifest.json"
        self.thinking_log = self.memory_dir / "thinking_log.jsonl"
        
        # Load existing manifest
        self.manifest = self._load_manifest()
        self.chunk_cache = {}
        # Korean-style key index (syllable-like fixed blocks)
        self.korean_index_enabled = True
        self._chunk_keys = {}
        try:
            from korean_keys import build_keys as _kk_build
            self._kk_build_keys = _kk_build
            self._build_korean_chunk_index()
        except Exception:
            self.korean_index_enabled = False

        # Symbolic (Esperanto/CBMS) indexing - ALWAYS ENABLED BY DEFAULT
        self.symbolic_enabled = False
        self._symbolic_idx = None
        try:
            # PERMANENTLY ENABLED - NO OPTIMIZATION AT COST OF FUNCTIONALITY
            use_sym = str(os.environ.get("CBMS_SYMBOLIC", "1")).lower() in ("1", "true", "on")
            cb_path = self.memory_dir / "codebook" / "codebook.json"
            if use_sym and cb_path.exists():
                from codebook_engine import Codebook  # type: ignore
                from cbms_symbolic_index import SymbolicIndex  # type: ignore
                cb = Codebook.load(cb_path)
                idx = SymbolicIndex(self.memory_dir, cb)
                built = idx.build(limit=None)
                if built > 0:
                    self._symbolic_idx = idx
                    self.symbolic_enabled = True
        except Exception:
            # Symbolic layer is strictly optional
            self.symbolic_enabled = False
    
    def _load_manifest(self) -> Dict:
        """Load knowledge manifest"""
        if self.manifest_file.exists():
            with open(self.manifest_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "version": "1.0",
            "created": datetime.now().isoformat(),
            "total_chunks": 0,
            "chunk_index": {},
            "concept_map": {},
            "thinking_sessions": []
        }
    
    def _save_manifest(self):
        """Save knowledge manifest"""
        with open(self.manifest_file, 'w', encoding='utf-8') as f:
            json.dump(self.manifest, f, indent=2, ensure_ascii=False)
    
    def create_knowledge_chunk(self, content: str, concept: str,
                             references: List[str] = None,
                             meta: Dict[str, Any] = None) -> str:
        """Create new knowledge chunk with CBMS ID"""
        
        # Generate CBMS-style ID
        hash_obj = hashlib.sha256(content.encode('utf-8'))
        chunk_id = "K" + hash_obj.hexdigest()[:12].upper()  # K = Knowledge
        
        # Create chunk data
        chunk_data = {
            "id": chunk_id,
            "concept": concept,
            "content": content,
            "created": datetime.now().isoformat(),
            "size": len(content),
            "references": references or [],
            "access_count": 0,
            "last_accessed": None
        }
        # Optional metadata (eo/cbms_codes/hangul_code etc.)
        if meta:
            try:
                for k, v in meta.items():
                    if k not in chunk_data:
                        chunk_data[k] = v
            except Exception:
                pass
        # Auto-assign Hangul address if not provided
        try:
            if "hangul_code" not in chunk_data:
                from hangul_addressing import make_hangul_code  # type: ignore
                chunk_data["hangul_code"] = make_hangul_code(chunk_id)
        except Exception:
            pass
        
        # Save chunk
        chunk_file = self.chunks_dir / f"{chunk_id}.json"
        with open(chunk_file, 'w', encoding='utf-8') as f:
            json.dump(chunk_data, f, indent=2, ensure_ascii=False)

        # Update manifest
        self.manifest["chunk_index"][chunk_id] = {
            "concept": concept,
            "size": len(content),
            "created": chunk_data["created"],
            "file": str(chunk_file)
        }
        
        # Update concept map
        if concept not in self.manifest["concept_map"]:
            self.manifest["concept_map"][concept] = []
        self.manifest["concept_map"][concept].append(chunk_id)
        
        self.manifest["total_chunks"] += 1
        self._save_manifest()

        # Update korean-keys in-memory index for this new chunk
        try:
            if self.korean_index_enabled and hasattr(self, '_kk_build_keys'):
                self._chunk_keys[chunk_id] = self._kk_build_keys(content)
        except Exception:
            # Non-fatal: index stays consistent after next startup rebuild
            pass

        return chunk_id
    
    def retrieve_chunk(self, chunk_id: str) -> Optional[Dict]:
        """Retrieve knowledge chunk by ID"""
        if chunk_id in self.chunk_cache:
            chunk_data = self.chunk_cache[chunk_id]
        else:
            chunk_file = self.chunks_dir / f"{chunk_id}.json"
            if not chunk_file.exists():
                return None
            
            with open(chunk_file, 'r', encoding='utf-8') as f:
                chunk_data = json.load(f)
            
            self.chunk_cache[chunk_id] = chunk_data
        
        # Update access stats (defensive - some old chunks lack access_count)
        chunk_data["access_count"] = chunk_data.get("access_count", 0) + 1
        chunk_data["last_accessed"] = datetime.now().isoformat()
        
        return chunk_data
    
    def find_chunks_by_concept(self, concept: str) -> List[str]:
        """Find all chunks related to a concept"""
        return self.manifest["concept_map"].get(concept, [])
    
    def cbms_think(self, query: str, context: List[str] = None) -> Dict:
        """Process query using CBMS thinking pattern"""
        
        thinking_session = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "context_chunks": context or [],
            "retrieved_chunks": [],
            "reasoning": [],
            "result_chunks": [],
            "processing_time": 0
        }
        
        start_time = time.time()
        
        # Step 1: Identify relevant concepts
        concepts = self._extract_concepts(query)
        thinking_session["reasoning"].append(f"Identified concepts: {concepts}")
        
        # Step 2: Retrieve relevant chunks (korean keys first, then concepts, optional symbols)
        relevant_chunks = []
        # Inject provided context chunk IDs up-front for fast-path recall
        try:
            if context:
                for cid in context:
                    if cid and cid not in relevant_chunks:
                        relevant_chunks.append(cid)
                thinking_session["reasoning"].append(f"Injected context: {len(context)}")
        except Exception:
            pass
        if self.korean_index_enabled:
            q_keys = self._kk_build_keys(query)
            scores = {}
            for cid, keys in self._chunk_keys.items():
                ov = len(q_keys & keys)
                if ov > 0:
                    scores[cid] = ov
            ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            relevant_chunks.extend([cid for cid, _ in ranked[:50]])
            thinking_session["reasoning"].append(f"Korean-keys hits: {len(relevant_chunks)}")
        # Optional symbolic matches via Esperanto/CBMS codes (does not replace KR)
        if self.symbolic_enabled and self._symbolic_idx is not None:
            try:
                sym_ranked = self._symbolic_idx.search(query, top_k=7)
                sym_hits = [cid for cid, _ in sym_ranked]
                for cid in sym_hits:
                    if cid not in relevant_chunks:
                        relevant_chunks.append(cid)
                thinking_session["reasoning"].append(f"Symbolic hits: {len(sym_hits)}")
            except Exception:
                thinking_session["reasoning"].append("Symbolic hits: error")
        for concept in concepts:
            chunk_ids = self.find_chunks_by_concept(concept)
            for cid in chunk_ids:
                if cid not in relevant_chunks:
                    relevant_chunks.append(cid)
        
        thinking_session["retrieved_chunks"] = relevant_chunks
        thinking_session["reasoning"].append(f"Retrieved {len(relevant_chunks)} chunks")

        # --- CRITICAL TERM BOOSTING ---
        # Re-rank chunks if query contains critical terms (all-caps acronyms/names)
        import string
        clean_tokens = [w.strip(string.punctuation) for w in query.split()]
        critical_terms = [w for w in clean_tokens if w.isupper() and len(w) > 1 and w not in ["CZY", "JAK", "KTO", "CO", "TO"]]
        if critical_terms:
            thinking_session["reasoning"].append(f"Applying critical term boost for: {critical_terms}")
            boosted = []
            others = []
            # Check content of top 100 retrieval candidates
            for cid in relevant_chunks[:100]:
                data = self.retrieve_chunk(cid)
                if data and any(term in data.get('content', '') for term in critical_terms):
                    boosted.append(cid)
                else:
                    others.append(cid)
            # Add remaining chunks that weren't checked
            others.extend(relevant_chunks[100:])
            relevant_chunks = boosted + others
            thinking_session["reasoning"].append(f"Boosted {len(boosted)} chunks to top")
            print(f"DEBUG: Boosted {len(boosted)} chunks. Top chunk: {boosted[0] if boosted else 'None'}", file=sys.stderr)
        # -----------------------------
        
        # Step 3: Process and synthesize
        synthesized_knowledge = self._synthesize_chunks(relevant_chunks, query)
        print(f"DEBUG: Synthesis result length: {len(synthesized_knowledge)}", file=sys.stderr)
        print(f"DEBUG: Synthesis result preview: {synthesized_knowledge[:100]}...", file=sys.stderr)

        thinking_session["reasoning"].append("Synthesized knowledge from chunks")
        
        # Step 4: Create new knowledge if needed
        if self._should_create_new_chunk(query, synthesized_knowledge):
            new_chunk_id = self.create_knowledge_chunk(
                synthesized_knowledge, 
                self._primary_concept(concepts),
                relevant_chunks
            )
            thinking_session["result_chunks"].append(new_chunk_id)
            thinking_session["reasoning"].append(f"Created new chunk: {new_chunk_id}")
        
        thinking_session["processing_time"] = time.time() - start_time
        
        # Log thinking session
        self._log_thinking_session(thinking_session)
        
        return {
            "answer": synthesized_knowledge,
            "response": synthesized_knowledge, # Alias for AIONS_ULTIMATE compatibility
            "chunk_references": relevant_chunks,
            "new_chunks": thinking_session["result_chunks"],
            "thinking_trace": thinking_session["reasoning"],
            "latency_ms": round((time.time() - start_time) * 1000.0, 3),
        }
    
    def _extract_concepts(self, text: str) -> List[str]:
        """Extract key concepts from text - ENHANCED for Claude knowledge"""
        # Programming keywords
        programming_keywords = {
            "python": "programming_python", "javascript": "programming_javascript",
            "java": "programming_systems", "database": "programming_databases", 
            "web": "programming_web", "html": "programming_web", "css": "programming_web",
            "sql": "programming_databases", "sorting": "programming_python",
            "function": "programming_python", "array": "programming_javascript"
        }
        
        # AI/ML keywords
        ai_keywords = {
            "AI": "ai_ml_fundamentals", "machine learning": "ai_ml_fundamentals",
            "NLP": "ai_nlp", "neural": "ai_ml_fundamentals", "model": "ai_ml_fundamentals"
        }
        
        # System keywords
        system_keywords = {
            "CBMS": "general", "chunk": "general", "memory": "general",
            "desktop": "desktop_files_analysis"
        }
        
        found_concepts = []
        text_lower = text.lower()
        
        # Check all keyword categories
        for keywords_dict in [programming_keywords, ai_keywords, system_keywords]:
            for keyword, concept in keywords_dict.items():
                if keyword.lower() in text_lower:
                    found_concepts.append(concept)
        
        return list(set(found_concepts)) or ["general"]
    
    def _synthesize_chunks(self, chunk_ids: List[str], query: str) -> str:
        """Synthesize knowledge from multiple chunks"""
        if not chunk_ids:
            return f"No prior knowledge found for: {query}"
        
        # Load chunk contents
        chunk_contents = []
        relevant_knowledge = []
        
        for chunk_id in chunk_ids[:15]:  # Top 15 chunks
            chunk_data = self.retrieve_chunk(chunk_id)
            if chunk_data and chunk_data['content']:
                # Filter out meta prompts and commands
                content = chunk_data['content']
                if not any(phrase in content.upper() for phrase in ['PRZECZYTAJ', 'PODSUMUJ', 'NO PRIOR KNOWLEDGE']):
                    relevant_knowledge.append(content)
                    chunk_contents.append(f"[{chunk_id}] {content}")
        
        if not relevant_knowledge:
            return f"Witaj! Jestem AIONS - Advanced Intelligence Operating System.\n\nSystem oparty na CBMS (Code Book Memory System) z integracją Claude thinking patterns.\nGotowy do pomocy w zadaniach programistycznych, analizie i rozwiązywaniu problemów.\n\nZadaj mi pytanie, a odpowiem błyskawicznie!"
        
        # Create intelligent synthesis
        if query.upper() in ['WITAJ', 'WITAM', 'PRZEDSTAW SIE', 'HELLO', 'HI']:
            return f"Witaj! Jestem AIONS z {len(chunk_ids)} aktywnych modułów wiedzy.\n\nSystem działa na bazie CBMS + Bielik + Claude patterns.\nMam dostęp do wiedzy o programowaniu, AI/ML, systemach i więcej.\n\nW czym mogę pomóc?"
        
        # For other queries, provide relevant synthesis
        synthesis = f"Na podstawie {len(relevant_knowledge)} fragmentów wiedzy:\n\n"
        
        # Combine knowledge intelligently
        if len(relevant_knowledge) == 1:
            synthesis += relevant_knowledge[0]
        else:
            # Summarize key points
            synthesis += "Kluczowe informacje:\n"
            for i, knowledge in enumerate(relevant_knowledge[:3], 1):
                summary = knowledge[:150] + "..." if len(knowledge) > 150 else knowledge
                synthesis += f"{i}. {summary}\n"
        
        synthesis += f"\n\n[Źródło: CBMS, {len(chunk_ids)} chunków pamięci]"
        return synthesis
    
    def _should_create_new_chunk(self, query: str, synthesis: str) -> bool:
        """Determine if new knowledge chunk should be created"""
        # Create new chunk if significant new insight or query is complex
        return len(query) > 50 or "new" in query.lower() or "how" in query.lower()
    
    def _primary_concept(self, concepts: List[str]) -> str:
        """Select primary concept for chunking"""
        return concepts[0] if concepts else "general"
    
    def _log_thinking_session(self, session: Dict):
        """Log thinking session to JSONL"""
        with open(self.thinking_log, 'a', encoding='utf-8') as f:
            f.write(json.dumps(session, ensure_ascii=False) + '\n')

    def _build_korean_chunk_index(self):
        """Build in-memory index of korean-style keys for each chunk.

        If manifest contains stale absolute paths (e.g., from another machine),
        fall back to the local chunks directory and transparently repair entries.
        """
        self._chunk_keys = {}
        updated_manifest = False
        for cid, meta in (self.manifest.get("chunk_index") or {}).items():
            try:
                # Always prefer current memory/chunks path for portability
                preferred = self.chunks_dir / f"{cid}.json"
                p = preferred if preferred.exists() else Path(meta.get("file", ""))
                if not p or not p.exists():
                    # No file available anywhere; skip
                    continue
                # If manifest points elsewhere, repair it
                if str(p) != meta.get("file"):
                    meta["file"] = str(p)
                    updated_manifest = True
                data = json.loads(p.read_text(encoding='utf-8', errors='ignore'))
                content = data.get('content', '') or ''
                self._chunk_keys[cid] = self._kk_build_keys(content)
            except Exception:
                continue
        if updated_manifest:
            # Persist repaired file paths so next startup is clean
            try:
                self._save_manifest()
            except Exception:
                pass
    
    def get_memory_stats(self) -> Dict:
        """Get memory system statistics"""
        return {
            "total_chunks": self.manifest["total_chunks"],
            "concepts": len(self.manifest["concept_map"]),
            "memory_size_mb": sum(
                os.path.getsize(self.chunks_dir / f"{cid}.json") 
                for cid in self.manifest["chunk_index"]
            ) / (1024 * 1024),
            "thinking_sessions": len(open(self.thinking_log, 'r').readlines()) if self.thinking_log.exists() else 0
        }

    def cbms_think_like_claude(self, query: str, context: List[str] = None) -> Dict:
        """Enhanced thinking using Claude reasoning patterns"""
        
        thinking_session = {
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "reasoning_patterns": [],
            "evidence_gathered": [],
            "synthesis_steps": [],
            "final_reasoning": ""
        }
        
        # PHASE 1: Problem Assessment using Claude patterns
        assessment_concepts = ["claude_meta_reasoning", "thinking_methodology_analytical_breakdown"]
        assessment_chunks = []
        for concept in assessment_concepts:
            chunks = self.find_chunks_by_concept(concept)
            assessment_chunks.extend(chunks)
        
        # Apply analytical breakdown
        problem_components = self._extract_concepts(query)
        thinking_session["reasoning_patterns"].append("analytical_breakdown")
        
        # PHASE 2: Evidence Gathering
        evidence_concepts = problem_components + ["thinking_methodology_evidence_based_thinking"]
        relevant_chunks = []
        # Inject provided context chunk IDs up-front for fast-path recall
        try:
            if context:
                for cid in context:
                    if cid and cid not in relevant_chunks:
                        relevant_chunks.append(cid)
                thinking_session["reasoning"].append(f"Injected context: {len(context)}")
        except Exception:
            pass
        
        for concept in evidence_concepts:
            chunk_ids = self.find_chunks_by_concept(concept)
            relevant_chunks.extend(chunk_ids)
            if chunk_ids:
                thinking_session["evidence_gathered"].append(f"Found {len(chunk_ids)} chunks for {concept}")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_chunks = []
        for chunk_id in relevant_chunks:
            if chunk_id not in seen:
                seen.add(chunk_id)
                unique_chunks.append(chunk_id)
        
        # PHASE 3: Multidisciplinary Synthesis
        if unique_chunks:
            synthesis_patterns = self.find_chunks_by_concept("thinking_methodology_multidisciplinary_synthesis")
            thinking_session["reasoning_patterns"].append("multidisciplinary_synthesis")
            
            # Load and synthesize chunk contents
            synthesized_knowledge = self._synthesize_chunks_with_claude_reasoning(unique_chunks, query)
            thinking_session["synthesis_steps"].append("Applied Claude synthesis methodology")
        else:
            # Use iterative refinement for new knowledge creation
            refinement_patterns = self.find_chunks_by_concept("thinking_methodology_iterative_refinement")
            thinking_session["reasoning_patterns"].append("iterative_refinement")
            
            synthesized_knowledge = f"No direct knowledge found for: {query}. Applying iterative refinement to build new understanding."
            
            # Create new knowledge chunk using Claude methodology
            new_chunk_content = f"Analysis of: {query}\n\nApplying Claude thinking patterns for systematic exploration of this topic."
            new_chunk_id = self.create_knowledge_chunk(
                content=new_chunk_content,
                concept="generated_analysis"
            )
            unique_chunks.append(new_chunk_id)
            synthesized_knowledge = new_chunk_content
        
        # PHASE 4: Uncertainty Management and Validation
        uncertainty_patterns = self.find_chunks_by_concept("thinking_methodology_uncertainty_management")
        thinking_session["reasoning_patterns"].append("uncertainty_management")
        thinking_session["final_reasoning"] = "Applied Claude meta-reasoning framework for comprehensive analysis"
        
        # Log the enhanced thinking session
        self._log_thinking_session(thinking_session)
        
        return {
            "answer": synthesized_knowledge,
            "chunk_references": unique_chunks,
            "reasoning_patterns_used": thinking_session["reasoning_patterns"],
            "thinking_trace": thinking_session["reasoning_patterns"],
            "claude_methodology": True
        }
    
    def _synthesize_chunks_with_claude_reasoning(self, chunk_ids: List[str], query: str) -> str:
        """Synthesize chunks using Claude's reasoning methodology"""
        
        if not chunk_ids:
            return "No relevant knowledge chunks found."
        
        # Load chunk contents with Claude contextual reasoning
        chunk_contents = []
        for chunk_id in chunk_ids[:10]:  # Limit to prevent overload
            chunk_file = self.chunks_dir / f"{chunk_id}.json"
            if chunk_file.exists():
                with open(chunk_file, 'r', encoding='utf-8') as f:
                    chunk_data = json.load(f)
                    chunk_contents.append(f"[{chunk_id}] {chunk_data['content']}")
        
        if not chunk_contents:
            return "Knowledge chunks found but could not be loaded."
        
        # Apply Claude synthesis methodology
        synthesis = f"Based on {len(chunk_ids)} knowledge chunks:\n\n"
        synthesis += "\n\n".join(chunk_contents)
        
        # Add meta-reasoning note
        synthesis += f"\n\n[Analysis completed using Claude reasoning patterns: {', '.join(['analytical_breakdown', 'evidence_based_thinking', 'multidisciplinary_synthesis'])}]"
        
        return synthesis

def demo_cbms_memory():
    """Demo CBMS memory system"""
    memory = CBMSMemory()
    
    print("CBMS Memory System Demo")
    print("="*40)
    
    # Create some knowledge
    chunk1 = memory.create_knowledge_chunk(
        "CBMS to system kompresji pamieci AI przez chunking i symboliczne referencje",
        "CBMS",
        []
    )
    print(f"Created chunk: {chunk1}")
    
    # Test thinking
    result = memory.cbms_think("Jak dziala CBMS system?")
    print(f"\nThinking result: {result['answer'][:100]}...")
    
    # Show stats
    stats = memory.get_memory_stats()
    print(f"\nMemory stats: {stats}")

if __name__ == "__main__":
    demo_cbms_memory()

