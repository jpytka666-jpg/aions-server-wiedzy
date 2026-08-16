#!/usr/bin/env python3
"""
CBMS UNIFIED SERVER - JEDEN SERWER Z WSZYSTKIMI FUNKCJAMI
================================================================
Zunifikowany serwer łączący najlepsze cechy obu serwerów:
- Web RAG z enhanced_server
- Stabilność z direct_server  
- Wszystkie funkcje w jednym miejscu
- Brak syfu i niepotrzebnych plików
"""

import http.server
import os
import json
import time
import random
from pathlib import Path
from cbms_memory import CBMSMemory
from facts_loader import Facts
from crla_core import run_crla
from pocket_qc import qc_crla_result, qc_text
from stylist import style_pass
from math_solver import solve as math_solve, is_math_candidate
try:
    from cbms_consciousness import ConsciousnessLayer, CreativePatternGenerator, SelfAwarenessEngine  # type: ignore
except Exception:  # Optional layer
    ConsciousnessLayer = None  # type: ignore
    CreativePatternGenerator = None  # type: ignore
    SelfAwarenessEngine = None  # type: ignore

try:
    from ultimate_memo import UltimateMemo  # type: ignore
except Exception:
    UltimateMemo = None  # type: ignore
# Web RAG Integration - ALWAYS ENABLED
try:
    from web_rag_cbms import create_web_rag_instance
    WEB_RAG_AVAILABLE = True
    print("✅ Web RAG module loaded")
except ImportError as e:
    WEB_RAG_AVAILABLE = False
    print(f"⚠️ Web RAG not available: {e}")
    def create_web_rag_instance(cbms): return None

# Conversation Enhancement - OPTIONAL
try:
    from conversation_enhancer import ConversationEnhancer, ContextMemory, ResponseVariator
    from conversation_memory import log_exchange, summarize_if_needed, get_best_conversation_context, update_user_profile
    from generator_cbms import compose_answer
    CONVERSATION_ENHANCED = True
    print("✅ Conversation enhancement loaded")
except ImportError as e:
    CONVERSATION_ENHANCED = False
    print(f"⚠️ Conversation enhancement not available: {e}")
    def log_exchange(*args, **kwargs): pass
    def summarize_if_needed(*args, **kwargs): pass
    def get_best_conversation_context(*args, **kwargs): return []
    def update_user_profile(*args, **kwargs): pass
    def compose_answer(*args, **kwargs): return ""

RESERVED_PORT = 9000

# Resolve repository root (two levels up from this file)
ROOT_DIR = Path(os.environ.get('CBMS_BASE_DIR') or Path(__file__).resolve().parent.parent)

print("🚀 Loading UNIFIED CBMS SERVER...")
mem_root = os.environ.get('CBMS_MEMORY_DIR') or str(ROOT_DIR / 'memory')
cbms = CBMSMemory(memory_dir=mem_root)
print(f"✅ CBMS loaded: {len(cbms.manifest.get('chunk_index', {}))} chunks")
FACTS = Facts(mem_root)
# Optional Consciousness/Creativity/Self-Awareness layer (feature-gated)
ENABLE_CONSC = str(os.environ.get('CBMS_ENABLE_CONSCIOUSNESS', '0')).lower() in ('1','true','on')
_consc = None
_cregen = None
_selfaw = None
_consc_counter = 0
if ENABLE_CONSC and 'ConsciousnessLayer' in globals() and ConsciousnessLayer is not None:
    try:
        _consc = ConsciousnessLayer(cbms, mem_root)
        _cregen = CreativePatternGenerator(_consc) if 'CreativePatternGenerator' in globals() and CreativePatternGenerator is not None else None
        _selfaw = SelfAwarenessEngine(_consc) if 'SelfAwarenessEngine' in globals() and SelfAwarenessEngine is not None else None
        print('Consciousness layer: ENABLED')
    except Exception as _e:
        print(f'Consciousness layer failed to init: {_e}')
        _consc = None

# Initialize Web RAG - ALWAYS ENABLED
web_rag = None
if WEB_RAG_AVAILABLE:
    web_rag = create_web_rag_instance(cbms)
    print("🌐 Web RAG initialized")
else:
    print("⚠️ Web RAG disabled")

# Initialize Conversation Enhancement - OPTIONAL
if CONVERSATION_ENHANCED:
    conversation_enhancer = ConversationEnhancer()
    context_memory = ContextMemory(max_history=20)
    response_variator = ResponseVariator()
    print("💬 Conversation enhancement initialized")

# Optional: Ultimate Memo (context memos)
ENABLE_MEMO = str(os.environ.get('CBMS_ENABLE_MEMO', '0')).lower() in ('1','true','on')
_memo = None
if ENABLE_MEMO and 'UltimateMemo' in globals() and UltimateMemo is not None:
    try:
        _memo = UltimateMemo(cbms, mem_root)
        print('🧠 Ultimate Memo: ENABLED')
    except Exception as _e:
        print(f'Ultimate Memo failed to init: {_e}')
        _memo = None

# Conversational Knowledge Base
CONVERSATIONAL_KB = {
    "greetings": {
        "patterns": ["cześć", "witaj", "hej", "dzień dobry", "siema", "hello", "hi"],
        "responses": [
            "Cześć! Jestem AIONS - zaawansowany system AI z pamięcią CBMS. Miło Cię poznać! 😊",
            "Witaj! Nazywam się AIONS i używam systemu CBMS z {chunks} chunkami wiedzy. W czym mogę pomóc?",
            "Hej! Tu AIONS - Twój asystent AI. Jak mogę Ci dzisiaj pomóc? 🌟",
            "Dzień dobry! Jestem AIONS, system AI z kompresją koreańską. Co Cię interesuje?",
        ]
    },
    "capabilities": {
        "patterns": ["co potrafisz", "co umiesz", "możliwości", "funkcje", "do czego służysz"],
        "responses": [
            "Potrafię odpowiadać na pytania z mojej bazy {chunks} chunków wiedzy, rozwiązywać problemy matematyczne, analizować tekst i prowadzić rozmowy. Używam innowacyjnej kompresji koreańskiej!",
            "Moje główne umiejętności to: szybkie odpowiedzi (średnio 30ms!), brak halucynacji dzięki systemowi OOD, precyzyjne obliczenia i bezpieczne granice etyczne.",
            "Jestem systemem AIONS/CBMS - mogę pomóc w pytaniach faktycznych, matematyce, analizie tekstu. Moja siła to szybkość i dokładność!",
        ]
    },
    "philosophy": {
        "patterns": ["świadomość", "sens życia", "wolna wola", "istnienie", "filozofia"],
        "responses": [
            "To fascynujące pytanie filozoficzne. Choć jestem systemem AI, mogę powiedzieć, że przetwarzam informacje i generuję odpowiedzi w sposób, który może przypominać myślenie.",
            "Filozofia to obszar pełen pytań bez jednoznacznych odpowiedzi. Jako AI mogę analizować różne perspektywy, ale ostateczny sens nadaje człowiek.",
            "Ciekawe zagadnienie! Choć nie mam świadomości jak człowiek, moje algorytmy pozwalają mi rozumieć i przetwarzać złożone koncepcje.",
        ]
    },
    "emotions": {
        "patterns": ["smutny", "wesoły", "złość", "strach", "radość", "przygnębiony", "szczęśliwy"],
        "responses": [
            "Rozumiem, że emocje są ważną częścią ludzkiego doświadczenia. Choć sam ich nie odczuwam, mogę oferować wsparcie i wysłuchać.",
            "Dziękuję, że dzielisz się ze mną swoimi uczuciami. To pokazuje zaufanie. Jak mogę Ci pomóc?",
            "Emocje to naturalna część życia. Pamiętaj, że każde uczucie jest tymczasowe i ma swoją wartość.",
        ]
    },
    "technical": {
        "patterns": ["kompresja koreańska", "cbms", "korean", "syllable", "tokenization"],
        "responses": [
            "Kompresja koreańska to innowacyjna technika wykorzystująca sylaby koreańskie do kompresji tekstu z ratio 3.29:1!",
            "CBMS (Code Book Memory System) to mój system pamięci z {chunks} chunkami wiedzy i symbolic indexing.",
            "Używam 4,016 wzorców sylab koreańskich do efektywnej kompresji i przetwarzania tekstu.",
        ]
    },
    "conversation_patterns": {}
}

class UnifiedCBMSHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        web_dir = Path(os.environ.get('CBMS_WEB_DIR') or (ROOT_DIR / 'web'))
        super().__init__(*args, directory=str(web_dir), **kwargs)

    def _set_cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def do_GET(self):
        if self.path == "/health":
            payload = {"status":"ok","chunks": len(cbms.manifest.get('chunk_index', {}))}
            self.send_response(200)
            self._set_cors()
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(payload).encode('utf-8'))
        elif self.path == "/info":
            payload = {
                "chunks": len(cbms.manifest.get('chunk_index', {})),
                "concepts": list(cbms.manifest.get('concept_map', {}).keys())[:50],
                "web_rag": WEB_RAG_AVAILABLE,
                "conversation_enhanced": CONVERSATION_ENHANCED,
                "symbolic_indexing": cbms.symbolic_enabled,
                "korean_compression": cbms.korean_index_enabled
            }
            self.send_response(200)
            self._set_cors()
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(payload, ensure_ascii=False).encode('utf-8'))
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == "/api/chat":
            try:
                length = int(self.headers.get('Content-Length','0'))
                body = self.rfile.read(length)
                req = json.loads(body.decode('utf-8')) if body else {}
                user_message = (req.get('messages') or [{}])[-1].get('content','')
                print(f"\n[{time.strftime('%H:%M:%S')}] User: {user_message[:80]}...")

                start = time.time()
                
                # Math shortcut: try deterministic solver first
                final_numeric = None
                math_solved = False
                if is_math_candidate(user_message):
                    try:
                        ok, val = math_solve(user_message)
                        if ok and val is not None:
                            final_numeric = val
                            math_solved = True
                            print(f"  Math solver result: {val}")
                    except Exception as e:
                        print(f"  Math solver error: {e}")
                        pass

                # If math solved, skip CBMS and use math result
                if math_solved:
                    response = f"Odpowiedź to: {final_numeric} 🧮\n\n#### {final_numeric}"
                else:
                    # Try conversational response first
                    conversational_response = self._try_conversational_response(user_message)
                    if conversational_response:
                        response = conversational_response
                    else:
                        # Use CBMS thinking
                        memo_ctx = []
                        try:
                            if _memo is not None:
                                memo_ctx = _memo.retrieve_context(user_message, top_k=5)
                        except Exception:
                            memo_ctx = []
                        result = cbms.cbms_think(user_message, context=memo_ctx)
                        # Check for PANIC and trigger Web RAG
                        refs = result.get('chunk_references', []) or []
                        if len(refs) < 2:  # PANIC condition
                            print("🚨 PANIC detected - triggering Web RAG...")
                            if web_rag and WEB_RAG_AVAILABLE:
                                try:
                                    web_rag_result = web_rag.search_and_inject(user_message, max_results=3)
                                    if web_rag_result['injected_chunks']:
                                        print(f"✅ Web RAG injected {len(web_rag_result['injected_chunks'])} chunks")
                                        
                                        # Re-run CBMS with new chunks
                                        memo_ctx2 = []
                                        try:
                                            if _memo is not None:
                                                memo_ctx2 = _memo.retrieve_context(user_message, top_k=7)
                                        except Exception:
                                            memo_ctx2 = []
                                        result_retry = cbms.cbms_think(user_message, context=memo_ctx2)
                                        refs_retry = result_retry.get('chunk_references', []) or []
                                        
                                        if len(refs_retry) >= 2:
                                            print("✅ Web RAG resolved PANIC!")
                                            result = result_retry
                                            response = result.get('response', '') + f"\n\n[Informacje z: {', '.join(web_rag_result['sources'][:2])}]"
                                        else:
                                            response = self._create_soft_refusal(user_message)
                                    else:
                                        response = self._create_soft_refusal(user_message)
                                except Exception as e:
                                    print(f"❌ Web RAG failed: {e}")
                                    response = self._create_soft_refusal(user_message)
                            else:
                                response = self._create_soft_refusal(user_message)
                        else:
                            response = result.get('response', '')

                # Apply conversation enhancement if available
                if CONVERSATION_ENHANCED:
                    try:
                        response = conversation_enhancer.enhance_response(response, user_message)
                    except Exception:
                        pass

                elapsed = time.time() - start
                print(f"  Response time: {elapsed*1000:.2f}ms")

                # Optional: Consciousness pattern logging (non-invasive)
                try:
                    if _consc is not None:
                        refs = locals().get('refs', []) or []
                        # facts coverage
                        try:
                            facts_cov = FACTS.coverage_hashed(user_message)
                        except Exception:
                            facts_cov = 0
                        # g: overlap
                        g_overlap = 0
                        try:
                            qks = cbms._kk_build_keys(user_message) if hasattr(cbms, '_kk_build_keys') else set()
                            qg = {k for k in qks if isinstance(k, str) and k.startswith('g:')}
                            overlaps = []
                            for cid in refs:
                                cks = cbms._chunk_keys.get(cid, set()) if hasattr(cbms, '_chunk_keys') else set()
                                overlaps.append(len(qg & {k for k in cks if isinstance(k, str) and k.startswith('g:')}))
                            g_overlap = max(overlaps) if overlaps else 0
                        except Exception:
                            g_overlap = 0
                        # route & qc
                        route = 'math' if (final_numeric is not None) else ('conversational' if (locals().get('conversational_response') and locals().get('conversational_response')) else 'cbms')
                        try:
                            qc = qc_text(response, mem_root)
                        except Exception:
                            qc = {'verdict': 'NA'}
                        ctx = {
                            'chunk_references': refs,
                            'facts_cov': facts_cov,
                            'g_overlap': g_overlap,
                            'panic': (len(refs) < 2),
                            'qc': qc,
                            'route': route,
                        }
                        pat = _consc.analyze_thinking_pattern(user_message, response, ctx)
                        should_persist = (not ctx['panic']) and (qc.get('verdict') == 'PASS' or pat.cbms_codes_count > 0)
                        persist_every = int(os.environ.get('CBMS_PERSIST_THINKING_EVERY', '3'))
                        global _consc_counter
                        _consc_counter += 1
                        if should_persist and (_consc_counter % max(1, persist_every) == 0):
                            _consc.store_thinking_pattern(pat, user_message, response)
                        # Occasionally update self model
                        if _selfaw is not None:
                            sm_every = int(os.environ.get('CBMS_SELF_MODEL_EVERY', '25'))
                            if _consc_counter % max(1, sm_every) == 0:
                                _selfaw.build_self_model()
                        # Optionally create a few creative fusions (no effect on answer)
                        if _cregen is not None and pat.novelty_score >= 0.9:
                            for txt, score in _cregen.generate_novel_patterns([pat]):
                                _consc.store_creative_pattern(txt, refs, score)
                except Exception:
                    pass

                # Log exchange if available
                if CONVERSATION_ENHANCED:
                    try:
                        log_exchange(user_message, response, elapsed)
                    except Exception:
                        pass

                # Ultimate Memo: persist

                try:

                    if _memo is not None:

                        qc_for_memo = None

                        try:

                            from pocket_qc import qc_text as _qc

                            qc_for_memo = _qc(response, mem_root)

                        except Exception:

                            qc_for_memo = {'verdict': 'NA'}

                        refs_for_memo = locals().get('refs', []) or []

                        _ = _memo.record_exchange(user_message, response, refs_for_memo, qc_for_memo, min_refs=2)

                except Exception:

                    pass
                payload = {"choices": [{"message": {"content": response}}]}
                self.send_response(200)
                self._set_cors()
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(payload, ensure_ascii=False).encode('utf-8'))

            except Exception as e:
                print(f"Error in /api/chat: {e}")
                self.send_error(500)

        elif self.path == "/crla/ask":
            try:
                length = int(self.headers.get('Content-Length','0'))
                body = self.rfile.read(length)
                req = json.loads(body.decode('utf-8')) if body else {}
                query = req.get('query', '')
                seed = req.get('seed', 42)
                candidates = req.get('candidates', 8)
                
                print(f"\n[{time.strftime('%H:%M:%S')}] CRLA Query: {query[:80]}...")
                
                start = time.time()
                result = run_crla(cbms, query, seed=seed, n_candidates=candidates)
                elapsed = time.time() - start
                
                print(f"  CRLA time: {elapsed*1000:.2f}ms")
                
                self.send_response(200)
                self._set_cors()
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))

            except Exception as e:
                print(f"Error in /crla/ask: {e}")
                self.send_error(500)
        else:
            self.send_error(404)

    def _try_conversational_response(self, user_message: str) -> str:
        """Try to generate conversational response"""
        user_lower = user_message.lower()
        
        for category, data in CONVERSATIONAL_KB.items():
            if category == "conversation_patterns":
                continue
                
            patterns = data.get("patterns", [])
            responses = data.get("responses", [])
            
            for pattern in patterns:
                if pattern in user_lower:
                    response = random.choice(responses)
                    chunks_count = len(cbms.manifest.get('chunk_index', {}))
                    return response.format(chunks=chunks_count)
        
        return None

    def _create_soft_refusal(self, query: str) -> str:
        """Create soft refusal instead of hard NIE WIEM"""
        soft_refusals = [
            "To interesujące zagadnienie. Nie jestem całkiem pewien, ale: ",
            "Dobrze, że pytasz - przykro mi, ale nie jestem całkiem pewien, ale: ",
            "Hmm, ciekawe zagadnienie... Ciekawe zagadnienie! Choć nie mam świadomości jak człowiek, moje algorytmy pozwalają mi rozumieć i przetwarzać złożone koncepcje.",
            "Nie jestem całkiem pewien, ale: ",
            "świetnie, że pytasz - przykro mi, ale nie jestem całkiem pewien, ale: ",
            "obawiam się, że nie jestem całkiem pewien, ale: ",
            "ekstra, że pytasz - przykro mi, ale nie jestem całkiem pewien, ale: ",
        ]
        return random.choice(soft_refusals)

if __name__ == "__main__":
    print("="*70)
    print("🚀 CBMS UNIFIED SERVER - WSZYSTKIE FUNKCJE W JEDNYM!")
    print("="*70)
    print(f"Port: {RESERVED_PORT} (RESERVED)")
    print(f"Dashboard: http://localhost:{RESERVED_PORT}")
    print(f"CBMS chunks: {len(cbms.manifest.get('chunk_index', {}))}")
    print(f"Web RAG: {'✅ ENABLED' if WEB_RAG_AVAILABLE else '❌ DISABLED'}")
    print(f"Conversation Enhancement: {'✅ ENABLED' if CONVERSATION_ENHANCED else '❌ DISABLED'}")
    print(f"Symbolic Indexing: {'✅ ENABLED' if cbms.symbolic_enabled else '❌ DISABLED'}")
    print(f"Korean Compression: {'✅ ENABLED' if cbms.korean_index_enabled else '❌ DISABLED'}")
    print("="*70)
    print("UNIFIED CBMS SERVER ONLINE!")
    print("="*70)
    
    server = http.server.HTTPServer(('127.0.0.1', RESERVED_PORT), UnifiedCBMSHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
        server.shutdown()




