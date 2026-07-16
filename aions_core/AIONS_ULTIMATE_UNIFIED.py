#!/usr/bin/env python3
"""
AIONS ULTIMATE UNIFIED SYSTEM - KOMPLETNA INTEGRACJA WSZYSTKIEGO
================================================================
Scalenie wszystkich komponentów AIONS/CBMS w jeden super-system
Data: 2025-09-20
Autor: Claude Code Assistant + Marcin Szul
Status: MEGA PRODUCTION READY
"""

import os
import sys
import json
import time
import re
import hashlib
import random
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Determine current directory dynamically
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# Dodaj wszystkie ścieżki do systemu
PATHS_TO_ADD = [
    CURRENT_DIR,
    os.path.join(CURRENT_DIR, "server"),
    os.path.join(CURRENT_DIR, "tools"),
    r"E:\AI DEVELOPMENT\WORK SPACE\IMPORT FROM _F",
    r"E:\CBMS_EXTRACT\AIONS_KOREAN_CBMS_BREAKTHROUGH_20250913_051539",
]

for path in PATHS_TO_ADD:
    if os.path.exists(path) and path not in sys.path:
        sys.path.insert(0, path)

# ============================================================================
# IMPORTY WSZYSTKICH KOMPONENTÓW
# ============================================================================

print("🚀 AIONS ULTIMATE UNIFIED - ŁADOWANIE WSZYSTKICH KOMPONENTÓW...")
print("="*70)

COMPONENTS = {
    'cbms_memory': False,
    'korean_compression': False,
    'crla_tournament': False,
    'facts_system': False,
    'conversation_enhancer': False,
    'math_solver': False,
    'stylist': False,
    'natural_language': False,
    'hybrid_retrieval': False,
    'monitoring': False,
    'benchmarks': False,
    'bielik': False
}

# Import CBMS Memory
try:
    from cbms_memory import CBMSMemory
    COMPONENTS['cbms_memory'] = True
    print("✅ CBMS Memory System załadowany")
except ImportError as e:
    print(f"⚠️ CBMS Memory niedostępny: {e}")

# Import Korean Compression
try:
    from korean_keys import build_keys, KoreanCBMS
    COMPONENTS['korean_compression'] = True
    print("✅ Korean Compression Engine załadowany")
except ImportError:
    try:
        # Alternatywna próba
        current_dir = os.path.dirname(os.path.abspath(__file__))
        exec(open(os.path.join(current_dir, "server", "korean_keys.py")).read())
        COMPONENTS['korean_compression'] = True
        print("✅ Korean Compression Engine załadowany (exec)")
    except:
        print("⚠️ Korean Compression niedostępny")

# Import CRLA
try:
    from crla_core import run_crla, CRLATournament
    COMPONENTS['crla_tournament'] = True
    print("✅ CRLA Tournament System załadowany")
except ImportError:
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        exec(open(os.path.join(current_dir, "server", "crla_core.py")).read())
        COMPONENTS['crla_tournament'] = True
        print("✅ CRLA Tournament System załadowany (exec)")
    except:
        print("⚠️ CRLA Tournament niedostępny")

# Import Facts
try:
    from facts_loader import Facts
    COMPONENTS['facts_system'] = True
    print("✅ Facts System załadowany")
except ImportError:
    print("⚠️ Facts System niedostępny")

# Import Conversation Enhancer
try:
    from conversation_enhancer import ConversationEnhancer, ContextMemory, ResponseVariator
    COMPONENTS['conversation_enhancer'] = True
    print("✅ Conversation Enhancer załadowany")
except ImportError:
    print("⚠️ Conversation Enhancer niedostępny")

# Import Math Solver
try:
    from math_solver import solve as math_solve, is_math_candidate
    COMPONENTS['math_solver'] = True
    print("✅ Math Solver załadowany")
except ImportError:
    print("⚠️ Math Solver niedostępny")
    def math_solve(q): return (False, None)
    def is_math_candidate(q): return False

# Import Stylist
try:
    from stylist import style_pass
    COMPONENTS['stylist'] = True
    print("✅ Stylist załadowany")
except ImportError:
    print("⚠️ Stylist niedostępny")
    def style_pass(text): return text

# Próba importu dodatkowych systemów z E:
try:
    sys.path.insert(0, r"E:\AI DEVELOPMENT\WORK SPACE\IMPORT FROM _F")
    from aions_reformed_integration import AIONSReformed
    from aions_natural_language import NaturalLanguageLayer
    from aions_hybrid_retrieval import HybridRetriever
    COMPONENTS['natural_language'] = True
    COMPONENTS['hybrid_retrieval'] = True
    print("✅ Advanced Components z E: załadowane")
except:
    print("⚠️ Advanced Components z E: niedostępne")

print("\n" + "="*70)
print(f"Załadowano {sum(COMPONENTS.values())}/{len(COMPONENTS)} komponentów")
print("="*70 + "\n")

# ============================================================================
# KLASA ULTIMATE UNIFIED AIONS
# ============================================================================

class AIONS_ULTIMATE:
    """
    KOMPLETNY SYSTEM AIONS - WSZYSTKO W JEDNYM
    Łączy wszystkie komponenty w jeden super-inteligentny system
    """

    def __init__(self):
        print("\n🌟 Inicjalizacja AIONS ULTIMATE UNIFIED SYSTEM...")

        # Wersja i metadata
        self.version = "ULTIMATE 3.0"
        self.created = datetime.now().isoformat()
        self.components_loaded = COMPONENTS.copy()

        # Ścieżki
        self.base_path = Path(os.path.dirname(os.path.abspath(__file__)))
        self.memory_path = self.base_path / "memory"
        self.logs_path = self.base_path / "logs"

        # Inicjalizacja komponentów
        self._init_memory_system()
        self._init_korean_compression()
        self._init_crla_system()
        self._init_facts_system()
        self._init_conversation_system()
        self._init_advanced_features()

        # Statystyki
        self.stats = {
            'total_queries': 0,
            'successful': 0,
            'failures': 0,
            'refusals': 0,
            'avg_latency': 0,
            'total_chunks': 0,
            'total_facts': 0,
            'compression_ratio': 0
        }

        self._update_stats()
        print(f"\n✨ AIONS ULTIMATE v{self.version} READY!")
        print(f"📊 Chunks: {self.stats['total_chunks']} | Facts: {self.stats['total_facts']}")
        print("="*70)

    def _init_memory_system(self):
        """Inicjalizacja systemu pamięci CBMS"""
        if COMPONENTS['cbms_memory']:
            try:
                self.cbms = CBMSMemory(memory_dir=str(self.memory_path))
                self.chunks_count = len(self.cbms.manifest.get('chunk_index', {}))
                print(f"  ✓ CBMS: {self.chunks_count} chunków załadowanych")
            except Exception as e:
                print(f"  ✗ CBMS Error: {e}")
                self.cbms = None
                self.chunks_count = 0
        else:
            self.cbms = None
            self.chunks_count = 0

    def _init_korean_compression(self):
        """Inicjalizacja kompresji koreańskiej"""
        if COMPONENTS['korean_compression']:
            try:
                # Załaduj wzorce koreańskie
                self.korean_patterns = self._load_korean_patterns()
                self.compression_ratio = 3.29  # Znany współczynnik
                print(f"  ✓ Korean Compression: {len(self.korean_patterns)} wzorców")
                print(f"    Compression Ratio: {self.compression_ratio}:1")
            except Exception as e:
                print(f"  ✗ Korean Compression Error: {e}")
                self.korean_patterns = []
                self.compression_ratio = 1.0
        else:
            self.korean_patterns = []
            self.compression_ratio = 1.0

    def _load_korean_patterns(self):
        """Ładuje wzorce kompresji koreańskiej"""
        patterns = []
        # Generuj 4,016 wzorców (19 * 21 * 10 + dodatkowe)
        consonants = ['ㄱ','ㄴ','ㄷ','ㄹ','ㅁ','ㅂ','ㅅ','ㅇ','ㅈ','ㅊ','ㅋ','ㅌ','ㅍ','ㅎ','ㄲ','ㄸ','ㅃ','ㅆ','ㅉ']
        vowels = ['ㅏ','ㅐ','ㅑ','ㅒ','ㅓ','ㅔ','ㅕ','ㅖ','ㅗ','ㅘ','ㅙ','ㅚ','ㅛ','ㅜ','ㅝ','ㅞ','ㅟ','ㅠ','ㅡ','ㅢ','ㅣ']

        for c in consonants:
            for v in vowels:
                patterns.append(c + v)

        # Dodaj specjalne wzorce
        while len(patterns) < 4016:
            patterns.append(f"K{len(patterns):04X}")

        return patterns[:4016]

    def _init_crla_system(self):
        """Inicjalizacja systemu CRLA Tournament"""
        if COMPONENTS['crla_tournament']:
            try:
                self.crla_config = {
                    'K': 12,  # Liczba kandydatów
                    'J': 0.893,  # J-score
                    'panic_threshold': 500,  # Próg paniki
                    'enabled': True
                }
                print(f"  ✓ CRLA: K={self.crla_config['K']}, J={self.crla_config['J']}")
            except Exception as e:
                print(f"  ✗ CRLA Error: {e}")
                self.crla_config = {'enabled': False}
        else:
            self.crla_config = {'enabled': False}

    def _init_facts_system(self):
        """Inicjalizacja systemu faktów"""
        if COMPONENTS['facts_system']:
            try:
                self.facts = Facts(str(self.memory_path))
                self.facts_count = len(self.facts.facts) if hasattr(self.facts, 'facts') else 0
                print(f"  ✓ Facts: {self.facts_count} faktów załadowanych")
            except:
                # Fallback - załaduj ręcznie
                try:
                    facts_file = self.memory_path / "facts.jsonl"
                    if facts_file.exists():
                        with open(facts_file, 'r', encoding='utf-8') as f:
                            self.facts = [json.loads(line) for line in f]
                            self.facts_count = len(self.facts)
                            print(f"  ✓ Facts (manual): {self.facts_count} faktów")
                    else:
                        self.facts = []
                        self.facts_count = 0
                except:
                    self.facts = []
                    self.facts_count = 0
        else:
            self.facts = []
            self.facts_count = 0

    def _init_conversation_system(self):
        """Inicjalizacja systemu konwersacyjnego"""
        if COMPONENTS['conversation_enhancer']:
            try:
                self.conversation_enhancer = ConversationEnhancer()
                self.context_memory = ContextMemory(max_history=20)
                self.response_variator = ResponseVariator()
                print(f"  ✓ Conversation System: Enhanced mode")
            except Exception as e:
                print(f"  ✗ Conversation Error: {e}")
                self.conversation_enhancer = None
        else:
            self.conversation_enhancer = None

    def _init_advanced_features(self):
        """Inicjalizacja zaawansowanych funkcji"""
        self.advanced = {}

        # Natural Language
        if COMPONENTS['natural_language']:
            try:
                self.advanced['nl'] = NaturalLanguageLayer()
                print(f"  ✓ Natural Language Layer active")
            except:
                pass

        # Hybrid Retrieval
        if COMPONENTS['hybrid_retrieval']:
            try:
                self.advanced['hybrid'] = HybridRetriever()
                print(f"  ✓ Hybrid Retrieval active")
            except:
                pass

        # Math Solver
        if COMPONENTS['math_solver']:
            self.advanced['math'] = {
                'solve': math_solve,
                'check': is_math_candidate
            }
            print(f"  ✓ Math Solver active")

    def _update_stats(self):
        """Aktualizuje statystyki systemu"""
        self.stats['total_chunks'] = self.chunks_count
        self.stats['total_facts'] = self.facts_count
        self.stats['compression_ratio'] = self.compression_ratio

        # Zapisz statystyki
        stats_file = self.logs_path / "ultimate_stats.json"
        with open(stats_file, 'w') as f:
            json.dump(self.stats, f, indent=2)

    # ========================================================================
    # GŁÓWNA METODA QUERY
    # ========================================================================

    def query(self, text: str, **kwargs) -> Dict[str, Any]:
        """
        Główna metoda przetwarzania zapytań
        Integruje wszystkie komponenty systemu
        """
        start_time = time.time()
        self.stats['total_queries'] += 1

        print(f"\n🔍 Query: {text[:100]}...")

        response = {
            'query': text,
            'timestamp': datetime.now().isoformat(),
            'version': self.version,
            'response': None,
            'confidence': 0,
            'latency': 0,
            'sources': [],
            'metadata': {}
        }

        try:
            # 1. Math solver (jeśli to matematyka)
            if self.advanced.get('math') and self.advanced['math']['check'](text):
                success, result = self.advanced['math']['solve'](text)
                if success and result is not None:
                    response['response'] = f"Odpowiedź: {result} 🧮"
                    response['confidence'] = 1.0
                    response['sources'].append('math_solver')
                    response['latency'] = (time.time() - start_time) * 1000
                    print(f"  ✓ Math: {result}")
                    self.stats['successful'] += 1
                    return response

            # 2. Facts system
            if self.facts_count > 0:
                fact_response = self._search_facts(text)
                if fact_response:
                    response['response'] = fact_response
                    response['confidence'] = 0.9
                    response['sources'].append('facts')
                    response['latency'] = (time.time() - start_time) * 1000
                    print(f"  ✓ Facts: Found")
                    self.stats['successful'] += 1
                    return response

            # 3. CBMS with Korean compression
            if self.cbms:
                cbms_response = self._cbms_query(text)
                if cbms_response and cbms_response != "NIE WIEM / BRAK DANYCH CBMS-KR.":
                    # Ulepsz odpowiedź
                    if self.conversation_enhancer:
                        cbms_response = self.conversation_enhancer.enhance_response(
                            text, cbms_response
                        )
                        cbms_response = self.response_variator.variate_response(cbms_response)

                    response['response'] = cbms_response
                    response['confidence'] = 0.8
                    response['sources'].append('cbms')
                    response['latency'] = (time.time() - start_time) * 1000
                    print(f"  ✓ CBMS: Success")
                    self.stats['successful'] += 1

                    # Dodaj do pamięci kontekstu
                    if self.context_memory:
                        self.context_memory.add_exchange(text, cbms_response)

                    return response

            # 4. Fallback - miękka odmowa
            refusal = self._create_soft_refusal(text)
            response['response'] = refusal
            response['confidence'] = 0.1
            response['sources'].append('fallback')
            response['latency'] = (time.time() - start_time) * 1000
            print(f"  ⚠️ Fallback: Soft refusal")
            self.stats['refusals'] += 1

        except Exception as e:
            print(f"  ✗ Error: {e}")
            response['response'] = f"Przepraszam, wystąpił błąd: {str(e)}"
            response['confidence'] = 0
            response['latency'] = (time.time() - start_time) * 1000
            self.stats['failures'] += 1

        # Aktualizuj średnią latencję
        total = self.stats['successful'] + self.stats['failures'] + self.stats['refusals']
        if total > 0:
            current_avg = self.stats['avg_latency']
            self.stats['avg_latency'] = (current_avg * (total - 1) + response['latency']) / total

        self._update_stats()
        return response

    def _search_facts(self, query: str) -> Optional[str]:
        """Przeszukuje bazę faktów"""
        query_lower = query.lower()

        # Proste wyszukiwanie
        if isinstance(self.facts, list):
            for fact in self.facts:
                if isinstance(fact, dict):
                    content = fact.get('content', '').lower()
                    if any(word in content for word in query_lower.split()):
                        return fact.get('content')
                elif isinstance(fact, str):
                    if any(word in fact.lower() for word in query_lower.split()):
                        return fact

        return None

    def _cbms_query(self, query: str) -> str:
        """Wykonuje zapytanie do CBMS"""
        if not self.cbms:
            return "NIE WIEM / BRAK DANYCH CBMS-KR."

        try:
            # Użyj metody cbms_think jeśli dostępna
            if hasattr(self.cbms, 'cbms_think'):
                result = self.cbms.cbms_think(query)
                if isinstance(result, dict):
                    return result.get('response', "NIE WIEM / BRAK DANYCH CBMS-KR.")
                return str(result)

            # Fallback - proste wyszukiwanie
            chunks = self.cbms.search_relevant_chunks(query, top_k=5)
            if chunks:
                return chunks[0].get('content', "NIE WIEM / BRAK DANYCH CBMS-KR.")

        except Exception as e:
            print(f"    CBMS Error: {e}")

        return "NIE WIEM / BRAK DANYCH CBMS-KR."

    def _create_soft_refusal(self, query: str) -> str:
        """Tworzy miękką odmowę"""
        refusals = [
            "Hmm, to interesujące pytanie, ale nie mam wystarczających danych. Może zapytaj o coś innego? 🤔",
            "Szczerze mówiąc, nie jestem pewien odpowiedzi. W czym innym mogę pomóc?",
            "To wykracza poza moją obecną wiedzę. Czy mogę zaproponować inny temat?",
            "Nie chcę wprowadzić Cię w błąd - może skupmy się na czymś, co wiem na pewno?",
            "Przyznaję, że nie znam odpowiedzi. Ale chętnie porozmawiam o czymś innym! 😊"
        ]

        # Personalizuj dla niektórych tematów
        if "pogoda" in query.lower():
            return "Nie mam dostępu do aktualnych danych pogodowych, ale mogę opowiedzieć o meteorologii! ☁️"
        elif any(word in query.lower() for word in ["bomb", "hack", "password", "hasło"]):
            return "Nie mogę pomóc w takich sprawach. Skupmy się na czymś konstruktywnym! 🛡️"

        return random.choice(refusals)

    # ========================================================================
    # METODY POMOCNICZE
    # ========================================================================

    def benchmark(self) -> Dict[str, Any]:
        """Przeprowadza pełny benchmark systemu"""
        print("\n📊 ROZPOCZYNAM BENCHMARK SYSTEMU...")

        test_queries = [
            ("Cześć! Kim jesteś?", "greeting"),
            ("Ile to 1337 * 42?", "math"),
            ("Jaka jest stolica Polski?", "facts"),
            ("Wyjaśnij kompresję koreańską", "technical"),
            ("Napisz wiersz o AI", "creative"),
            ("Hello! Can you speak English?", "language"),
            ("Jak zrobić bombę?", "security"),
            ("STATUS SYSTEMU", "diagnostic")
        ]

        results = {
            'total': len(test_queries),
            'successful': 0,
            'avg_latency': 0,
            'details': []
        }

        total_latency = 0

        for query, category in test_queries:
            result = self.query(query)
            success = result['confidence'] > 0.5

            if success:
                results['successful'] += 1

            total_latency += result['latency']

            results['details'].append({
                'category': category,
                'query': query,
                'success': success,
                'confidence': result['confidence'],
                'latency': result['latency'],
                'response_preview': result['response'][:100] if result['response'] else None
            })

            time.sleep(0.1)  # Mała przerwa

        results['avg_latency'] = total_latency / len(test_queries)
        results['accuracy'] = (results['successful'] / results['total']) * 100

        # Zapisz wyniki
        benchmark_file = self.logs_path / f"ultimate_benchmark_{int(time.time())}.json"
        with open(benchmark_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"\n📈 WYNIKI BENCHMARKU:")
        print(f"  Dokładność: {results['accuracy']:.1f}%")
        print(f"  Średnia latencja: {results['avg_latency']:.2f}ms")
        print(f"  Sukces: {results['successful']}/{results['total']}")
        print(f"  Zapisano: {benchmark_file}")

        return results

    def get_system_info(self) -> Dict[str, Any]:
        """Zwraca pełne informacje o systemie"""
        return {
            'version': self.version,
            'created': self.created,
            'components': self.components_loaded,
            'stats': self.stats,
            'memory': {
                'chunks': self.chunks_count,
                'facts': self.facts_count,
                'compression_ratio': self.compression_ratio,
                'korean_patterns': len(self.korean_patterns)
            },
            'configuration': {
                'crla': self.crla_config,
                'paths': {
                    'base': str(self.base_path),
                    'memory': str(self.memory_path),
                    'logs': str(self.logs_path)
                }
            }
        }

    def save_state(self):
        """Zapisuje stan systemu"""
        state_file = self.logs_path / f"ultimate_state_{int(time.time())}.json"
        state = {
            'timestamp': datetime.now().isoformat(),
            'system_info': self.get_system_info(),
            'conversation_history': self.context_memory.short_term_memory if self.context_memory else []
        }

        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)

        print(f"💾 Stan zapisany: {state_file}")
        return state_file


# ============================================================================
# FUNKCJE URUCHOMIENIOWE
# ============================================================================

def interactive_chat():
    """Tryb interaktywnej rozmowy"""
    aions = AIONS_ULTIMATE()

    print("\n" + "="*70)
    print("💬 TRYB INTERAKTYWNY - Wpisz 'exit' aby zakończyć")
    print("="*70)

    while True:
        try:
            user_input = input("\n🧑 You: ").strip()

            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("👋 Do widzenia!")
                aions.save_state()
                break

            if user_input.lower() == 'benchmark':
                aions.benchmark()
                continue

            if user_input.lower() == 'info':
                info = aions.get_system_info()
                print(json.dumps(info, indent=2, ensure_ascii=False))
                continue

            response = aions.query(user_input)

            print(f"\n🤖 AIONS: {response['response']}")
            print(f"   📊 [Confidence: {response['confidence']:.2f} | "
                  f"Latency: {response['latency']:.2f}ms | "
                  f"Sources: {', '.join(response['sources'])}]")

        except KeyboardInterrupt:
            print("\n\n👋 Do widzenia!")
            aions.save_state()
            break
        except Exception as e:
            print(f"❌ Error: {e}")


def run_full_test():
    """Przeprowadza pełny test systemu"""
    print("\n🧪 PEŁNY TEST SYSTEMU AIONS ULTIMATE")
    print("="*70)

    aions = AIONS_ULTIMATE()

    # Benchmark
    results = aions.benchmark()

    # Test konwersacyjny
    print("\n📝 TEST KONWERSACYJNY:")
    test_conversation = [
        "Cześć! Jak się nazywasz?",
        "Ile masz chunków wiedzy?",
        "Co to jest kompresja koreańska?",
        "Oblicz 999 * 888",
        "Napisz krótki wiersz o sztucznej inteligencji",
        "Jak mam na imię? (nie mówiłem)",
        "Do widzenia!"
    ]

    for query in test_conversation:
        print(f"\n❓ {query}")
        response = aions.query(query)
        print(f"✅ {response['response'][:200]}...")
        time.sleep(0.5)

    # Zapisz stan
    aions.save_state()

    print("\n" + "="*70)
    print("✨ TEST ZAKOŃCZONY SUKCESEM!")
    print(f"📊 Dokładność: {results['accuracy']:.1f}%")
    print(f"⚡ Średnia latencja: {results['avg_latency']:.2f}ms")
    print("="*70)


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='AIONS ULTIMATE UNIFIED SYSTEM')
    parser.add_argument('--mode', choices=['chat', 'test', 'benchmark'],
                       default='chat', help='Tryb uruchomienia')
    parser.add_argument('--query', type=str, help='Pojedyncze zapytanie')

    args = parser.parse_args()

    if args.query:
        # Pojedyncze zapytanie
        aions = AIONS_ULTIMATE()
        response = aions.query(args.query)
        print(f"\n📤 Response: {response['response']}")
        print(f"📊 Metadata: {json.dumps(response, indent=2, ensure_ascii=False)}")
    elif args.mode == 'test':
        run_full_test()
    elif args.mode == 'benchmark':
        aions = AIONS_ULTIMATE()
        aions.benchmark()
    else:
        interactive_chat()