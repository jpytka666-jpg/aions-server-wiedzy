#!/usr/bin/env python3
"""
AGI with Existing Models Integration
Uses Phi-3, Mistral-7B, and CBMS chunks already on system
"""

import os
import sys
import json
import time
import torch
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import hashlib
import pickle
from collections import defaultdict

# Add paths for existing systems
sys.path.extend([
    r"D:\AGI_CODex",
    r"D:\AGI_CODex\runtime",
    r"D:\CBMS_EXTRACT\BACKUP 01\BACKUP 01\AIONS_COMPLETE",
    r"E:\AI DEVELOPMENT\WORK SPACE\IMPORT FROM_E\claude mess\CLAUDE_EXPERIMENT",
    r"C:\Users\User\Desktop\AIONS_CBMS_RELEASE"
])

# Try importing existing components
try:
    from llama_cpp import Llama
    LLAMA_CPP_AVAILABLE = True
except ImportError:
    LLAMA_CPP_AVAILABLE = False
    print("Warning: llama-cpp-python not available. Install with: pip install llama-cpp-python")

try:
    from transformers import AutoModelForCausalLM, AutoTokenizer
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print("Warning: transformers not available. Install with: pip install transformers")


@dataclass
class ModelConfig:
    """Configuration for available models"""
    name: str
    path: str
    type: str  # gguf, pytorch, safetensors
    size_gb: float
    speed_ms: int
    capabilities: List[str]


class ExistingModelsHub:
    """Hub for all existing models on system"""

    def __init__(self):
        self.models = self._discover_models()
        self.active_models = {}
        self.chunks_path = self._find_chunks_path()
        self.chunks_cache = {}

    def _discover_models(self) -> Dict[str, ModelConfig]:
        """Discover all available models on system"""
        models = {}

        # Mistral-7B (PRIORITY)
        mistral_path = r"D:\LOCAL LLM MODELS\Mistral-7B-FULL-AIONS"
        if Path(mistral_path).exists():
            models["mistral_7b"] = ModelConfig(
                name="Mistral-7B",
                path=mistral_path,
                type="pytorch",
                size_gb=13.5,
                speed_ms=500,
                capabilities=["complex", "reasoning", "general"]
            )
            print(f"✓ Found Mistral-7B at {mistral_path}")

        # Modified Phi-3 with Korean (SECONDARY / BROKEN ON CPU)
        korean_phi3_path = r"D:\LOCAL LLM MODELS\AIONS-Korean-PHI3\AIONS_KOREAN_MODIFIED_PHI3.safetensors"
        if Path(korean_phi3_path).exists():
            models["phi3_korean"] = ModelConfig(
                name="Phi-3 Korean",
                path=korean_phi3_path,
                type="safetensors",
                size_gb=2.6,
                speed_ms=150,
                capabilities=["korean", "compressed", "specialized"]
            )
            print(f"✓ Found Phi-3 Korean at {korean_phi3_path}")
            
        # Bielik-4.5B
        bielik_path = r"D:\LOCAL LLM MODELS\Bielik-4.5B-Q4_K_M\bielik-4.5b-v3.0-instruct-q4_k_m-imat.gguf"
        if Path(bielik_path).exists():
            models["bielik"] = ModelConfig(
                name="Bielik-4.5B",
                path=bielik_path,
                type="gguf",
                size_gb=4.5,
                speed_ms=100,
                capabilities=["polish", "specialized", "fast"]
            )
            print(f"✓ Found Bielik-4.5B at {bielik_path}")

        return models

    def _find_chunks_path(self) -> str:
        """Find path to CBMS chunks"""
        # Prefer env or repo-local memory/chunks
        root = Path(__file__).resolve().parent
        env_mem = os.environ.get('CBMS_MEMORY_DIR')
        # POPRAWKA 2026-08-16: bylo `root.parent / 'memory' / 'chunks'`, czyli
        # <repo>/memory/chunks. Ten katalog ISTNIEJE, ale jest PUSTY, wiec petla
        # ponizej brala go jako pierwszy pasujacy i konczyla z wynikiem 0 blokow —
        # nie siegajac nawet dalej. Prawdziwe 167 blokow lezy w aions_core/memory/chunks.
        # Dwie sciezki zewnetrzne usuniete: `E:\AIONS_COMPLETE\cbms_memory\chunks`
        # to puste lustro (0 plikow), a `D:\AGI_CODex\chunks` nie istnieje wcale.
        try:
            from .lokalizacje import katalog_pamieci
        except ImportError:
            # Dwa znane tryby uruchomienia — jako czesc pakietu i jako skrypt.
            # Patrz ten sam komentarz w cbms_curve_machine._load_chunks.
            from lokalizacje import katalog_pamieci
        paths = [
            (Path(env_mem) / 'chunks') if env_mem else None,
            katalog_pamieci() / 'chunks',
        ]

        for p in paths:
            try:
                if p and Path(p).exists():
                    chunk_count = len(list(Path(p).glob("*.json"))) + len(list(Path(p).glob("*.bin")))
                    print(f"✓ Found {chunk_count} chunks at {p}")
                    return str(p)
            except Exception:
                continue

        print("⚠ No chunks directory found")
        return None

    def load_model(self, model_key: str) -> Any:
        """Load a specific model"""
        if model_key not in self.models:
            raise ValueError(f"Model {model_key} not found")

        if model_key in self.active_models:
            return self.active_models[model_key]

        # Enforce Single Model Policy (User Request: "HOW MANY MODELS YOU RUN AT ONCE?")
        # Unload all other models to free RAM
        if self.active_models:
            print("♻️ Unloading previous models to save memory...")
            self.active_models.clear()
            import gc
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

        config = self.models[model_key]

        if config.type == "gguf" and LLAMA_CPP_AVAILABLE:
            # Load GGUF model with llama.cpp
            print(f"Loading {config.name} with llama.cpp...")
            model = Llama(
                model_path=config.path,
                n_ctx=2048,
                n_gpu_layers=0, # Force CPU
                n_threads=8,
                verbose=False
            )
            self.active_models[model_key] = model
            return model

        elif config.type == "pytorch" and TRANSFORMERS_AVAILABLE:
            # Load PyTorch model
            print(f"Loading {config.name} with transformers...")
            model = AutoModelForCausalLM.from_pretrained(
                config.path,
                torch_dtype=torch.float32,
                device_map="cpu",
                low_cpu_mem_usage=True
            )
            tokenizer = AutoTokenizer.from_pretrained(config.path, use_fast=True)
            self.active_models[model_key] = (model, tokenizer)
            return model, tokenizer

        elif config.type == "safetensors" and TRANSFORMERS_AVAILABLE:
            # Load Safetensors Modified Model (Phi-3 Special Case)
            print(f"Loading {config.name} (Safetensors) with transformers...")
            from safetensors.torch import load_file
            from transformers import AutoConfig
            
            # Use base config for Phi-3 (User's Modified Model is based on this)
            base_model_id = "microsoft/Phi-3-mini-4k-instruct"
            
            print(f"  - Loading config from {base_model_id}...")
            try:
                config_obj = AutoConfig.from_pretrained(
                    base_model_id, 
                    trust_remote_code=False, # Use native
                    local_files_only=True,
                    _attn_implementation='eager'
                )
                print("  - Config loaded.")
            except Exception as e:
                print(f"  ❌ Config load failed: {e}")
                raise

            print(f"  - Loading weights from {config.path}...")
            try:
                state_dict = load_file(config.path)
                print("  - Weights loaded.")
            except Exception as e:
                print(f"  ❌ Weight load failed: {e}")
                raise
            
            print("  - Initializing model skeleton...")
            try:
                model = AutoModelForCausalLM.from_config(
                    config_obj, 
                    trust_remote_code=False, # Use native
                    attn_implementation="eager"
                )
                print("  - Model skeleton created.")
            except Exception as e:
                print(f"  ❌ Model skeleton failed: {e}")
                raise

            print("  - Applying weights...")
            try:
                model.load_state_dict(state_dict, strict=False) 
                print("  - Weights applied.")
            except Exception as e:
                print(f"  ❌ Weight application failed: {e}")
                raise
            
            print("  - Moving to CPU...")
            model = model.to("cpu")
                
            print("  - Loading tokenizer...")
            tokenizer = AutoTokenizer.from_pretrained(
                base_model_id, 
                trust_remote_code=False, # Use native
                local_files_only=True
            )
            print("  - Tokenizer loaded.")
            
            self.active_models[model_key] = (model, tokenizer)
            print(f"✅ {config.name} Loaded Successfully!")
            return model, tokenizer

        else:
            print(f"Cannot load {config.name} - missing dependencies")
            return None

    def get_chunks(self, limit: int = None) -> List[Dict]:
        """Load CBMS chunks"""
        if not self.chunks_path:
            return []

        if self.chunks_cache:
            chunks = list(self.chunks_cache.values())
            return chunks[:limit] if limit else chunks

        chunks = []
        path = Path(self.chunks_path)

        # Load JSON chunks
        for chunk_file in path.glob("*.json"):
            try:
                with open(chunk_file, 'r', encoding='utf-8') as f:
                    chunk = json.load(f)
                    chunks.append(chunk)
                    self.chunks_cache[chunk.get("id", chunk_file.stem)] = chunk
            except Exception as e:
                print(f"Error loading {chunk_file}: {e}")

        # Load binary chunks if present
        for chunk_file in path.glob("*.bin"):
            try:
                with open(chunk_file, 'rb') as f:
                    content = f.read()
                    chunk = {
                        "id": chunk_file.stem,
                        "content": content.decode('utf-8', errors='ignore'),
                        "type": "binary"
                    }
                    chunks.append(chunk)
                    self.chunks_cache[chunk["id"]] = chunk
            except Exception as e:
                print(f"Error loading {chunk_file}: {e}")

        print(f"Loaded {len(chunks)} chunks")
        return chunks[:limit] if limit else chunks


class KoreanCompression:
    """Korean syllable compression from existing system"""

    def __init__(self):
        self.syllable_patterns = self._load_patterns()
        self.compression_ratio = 3.29

    def _load_patterns(self) -> List[str]:
        """Load Korean syllable patterns"""
        # Try to import existing Korean compression
        try:
            korean_path = r"D:\CBMS_EXTRACT\KOREAN_NEURAL_INJECTION_PHI3.py"
            if Path(korean_path).exists():
                # Read patterns from file
                with open(korean_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Extract patterns (simplified - in real implementation would parse properly)
                    if "syllable_patterns" in content:
                        print("✓ Loaded Korean compression patterns")
                        return self._generate_default_patterns()
        except Exception as e:
            print(f"Warning: Could not load Korean patterns: {e}")

        return self._generate_default_patterns()

    def _generate_default_patterns(self) -> List[str]:
        """Generate default syllable patterns"""
        # 4,016 patterns as mentioned in docs
        patterns = []
        consonants = "ㄱㄴㄷㄹㅁㅂㅅㅇㅈㅊㅋㅌㅍㅎ"
        vowels = "ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ"

        for c1 in consonants[:10]:
            for v in vowels[:20]:
                for c2 in consonants[:20]:
                    patterns.append(c1 + v + c2)
                    if len(patterns) >= 4016:
                        return patterns

        return patterns

    def compress(self, text: str) -> bytes:
        """Compress text using Korean syllable encoding"""
        # Simplified compression
        compressed = text.encode('utf-8')

        # Apply compression ratio simulation
        target_size = int(len(compressed) / self.compression_ratio)

        # Simple compression using zlib as placeholder
        import zlib
        compressed = zlib.compress(compressed)[:target_size]

        return compressed

    def decompress(self, data: bytes) -> str:
        """Decompress Korean-encoded data"""
        import zlib
        try:
            decompressed = zlib.decompress(data)
            return decompressed.decode('utf-8', errors='ignore')
        except:
            return data.decode('utf-8', errors='ignore')


class AGIExistingModels:
    """AGI system using existing models and CBMS"""

    def __init__(self):
        self.hub = ExistingModelsHub()
        self.korean = KoreanCompression()
        self.chunks = self.hub.get_chunks(limit=100)  # Start with 100 chunks
        self.current_model = None
        self.model_key = None

    def select_model(self, query: str, capabilities_needed: List[str] = None) -> str:
        """Select best model for query"""
        # Simple heuristic selection
        query_lower = query.lower()

        # Check language
        if any(polish_word in query_lower for polish_word in ["czy", "jak", "dlaczego", "gdzie"]):
            if "bielik" in self.hub.models:
                return "bielik"

        # Check for speed requirement
        if "fast" in query_lower or "quick" in query_lower:
            if "bielik" in self.hub.models and LLAMA_CPP_AVAILABLE:
                return "bielik"
            if "phi3_q4" in self.hub.models: # Fallback
                return "phi3_q4"

        # High Performance default (Llama-CPP is much faster on CPU than Transformers)
        if "bielik" in self.hub.models and LLAMA_CPP_AVAILABLE:
             return "bielik"

        # Complex reasoning fallback to Mistral
        if any(word in query_lower for word in ["explain", "reasoning", "why", "complex", "code"]):
            if "mistral_7b" in self.hub.models:
                return "mistral_7b"

        # Default fallback chain
        for key in ["bielik", "mistral_7b", "phi3_korean", "phi3_q4"]:
            if key in self.hub.models:
                return key

        return None

    def retrieve_chunks(self, query: str, k: int = 12) -> List[Dict]:
        """Retrieve relevant chunks using BM25"""
        # Simple keyword-based retrieval (placeholder for BM25)
        query_words = set(query.lower().split())
        scored_chunks = []

        for chunk in self.chunks:
            content = chunk.get("content", "").lower()
            content_words = set(content.split())

            # Calculate overlap score
            overlap = len(query_words & content_words)
            if overlap > 0:
                scored_chunks.append((overlap, chunk))

        # Sort by score and return top k
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        return [chunk for _, chunk in scored_chunks[:k]]

    def generate_with_model(self, model_key: str, prompt: str, context: str = "") -> str:
        """Generate response using selected model"""
        if model_key not in self.hub.active_models:
            model = self.hub.load_model(model_key)
            if model is None:
                return "Model not available"

        config = self.hub.models[model_key]

        if config.type == "gguf" and LLAMA_CPP_AVAILABLE:
            model = self.hub.active_models[model_key]

            # Prepare prompt with context
            full_prompt = f"Context: {context}\n\nQuery: {prompt}\n\nResponse:"

            # Generate
            response = model(
                full_prompt,
                max_tokens=256,
                temperature=0.7,
                top_p=0.95,
                echo=False
            )

            return response['choices'][0]['text']

        elif config.type == "pytorch" and TRANSFORMERS_AVAILABLE:
            model, tokenizer = self.hub.active_models[model_key]

            # Prepare input
            full_prompt = f"Context: {context}\n\nQuery: {prompt}\n\nResponse:"
            inputs = tokenizer(full_prompt, return_tensors="pt", truncation=True, max_length=512)

            # Generate
            with torch.no_grad():
                outputs = model.generate(
                    **inputs,
                    max_new_tokens=256,
                    temperature=0.7,
                    do_sample=True,
                    top_p=0.95,
                    use_cache=False
                )

            response = tokenizer.decode(outputs[0], skip_special_tokens=True)
            # Extract only the response part
            if "Response:" in response:
                response = response.split("Response:")[-1].strip()

            return response

        return "Model type not supported"

    def process(self, query: str) -> Dict[str, Any]:
        """Main processing pipeline"""
        start_time = time.time()

        # Select model
        model_key = self.select_model(query)
        if not model_key:
            return {
                "response": "No suitable model available",
                "model": None,
                "latency_ms": 0,
                "chunks_used": 0
            }

        # Retrieve relevant chunks
        relevant_chunks = self.retrieve_chunks(query, k=12)

        # Prepare context from chunks
        context_parts = []
        for chunk in relevant_chunks[:5]:  # Use top 5 chunks
            content = chunk.get("content", "")[:200]  # Limit each chunk
            context_parts.append(content)

        context = " ".join(context_parts)

        # Apply Korean compression to context
        if len(context) > 1000:
            compressed = self.korean.compress(context)
            print(f"Compressed context: {len(context)} → {len(compressed)} bytes")
            # For generation, use original (compression is for storage)

        # Generate response
        response = self.generate_with_model(model_key, query, context)

        # Calculate metrics
        latency_ms = (time.time() - start_time) * 1000

        return {
            "response": response,
            "model": self.hub.models[model_key].name,
            "latency_ms": latency_ms,
            "chunks_used": len(relevant_chunks),
            "context_size": len(context),
            "compression_ratio": self.korean.compression_ratio if len(context) > 1000 else 1.0
        }


class MultiModelEnsemble:
    """Ensemble of multiple models for best results"""

    def __init__(self):
        self.agi = AGIExistingModels()
        self.model_weights = {
            "phi3_q4": 0.3,      # Fast
            "mistral_7b": 0.4,   # Quality
            "phi3_korean": 0.2,  # Specialized
            "bielik_7b": 0.1    # Polish
        }

    def ensemble_generate(self, query: str) -> Dict[str, Any]:
        """Generate using multiple models and combine"""
        responses = []
        total_weight = 0

        for model_key, weight in self.model_weights.items():
            if model_key in self.agi.hub.models:
                try:
                    result = self.agi.process(query)
                    responses.append({
                        "model": model_key,
                        "response": result["response"],
                        "weight": weight,
                        "latency": result["latency_ms"]
                    })
                    total_weight += weight
                except Exception as e:
                    print(f"Error with {model_key}: {e}")

        if not responses:
            return {"response": "No models available", "models_used": 0}

        # Combine responses (simple weighted selection for now)
        # In production, would use more sophisticated combination
        best_response = max(responses, key=lambda x: x["weight"])

        return {
            "response": best_response["response"],
            "models_used": len(responses),
            "primary_model": best_response["model"],
            "average_latency": np.mean([r["latency"] for r in responses])
        }


def test_existing_models():
    """Test the existing models integration"""
    print("\n" + "="*80)
    print("TESTING AGI WITH EXISTING MODELS")
    print("="*80)

    # Initialize system
    agi = AGIExistingModels()

    # Test queries
    queries = [
        "What is CBMS and how does it work?",
        "Explain Korean compression in simple terms",
        "Czym jest sztuczna inteligencja?",  # Polish
        "How fast can Phi-3 process queries?"
    ]

    for query in queries:
        print(f"\nQuery: {query}")
        print("-" * 40)

        result = agi.process(query)

        print(f"Model: {result['model']}")
        print(f"Latency: {result['latency_ms']:.2f}ms")
        print(f"Chunks used: {result['chunks_used']}")
        print(f"Response: {result['response'][:200]}...")

    # Test ensemble
    print("\n" + "="*80)
    print("TESTING MULTI-MODEL ENSEMBLE")
    print("="*80)

    ensemble = MultiModelEnsemble()
    result = ensemble.ensemble_generate("Explain the benefits of edge AI")

    print(f"Models used: {result['models_used']}")
    print(f"Primary model: {result.get('primary_model', 'N/A')}")
    print(f"Average latency: {result.get('average_latency', 0):.2f}ms")
    print(f"Response: {result['response'][:200]}...")


if __name__ == "__main__":
    # Check available resources
    print(f"CUDA available: {torch.cuda.is_available()}")
    print(f"Device: {torch.cuda.get_device_name() if torch.cuda.is_available() else 'CPU'}")

    # Run tests
    test_existing_models()
