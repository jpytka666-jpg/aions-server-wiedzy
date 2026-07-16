#!/usr/bin/env python3
"""
AIONS Conversation Enhancer - Poprawia naturalność i możliwości konwersacyjne
"""

import json
import random
import re
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

class ConversationEnhancer:
    """Ulepsza możliwości konwersacyjne AIONS"""

    def __init__(self):
        self.conversation_history = []
        self.user_profile = {}
        self.emotional_state = "neutral"
        self.conversation_style = "balanced"

        # Różnorodne szablony odpowiedzi zamiast sztywnego "NIE WIEM"
        self.refusal_templates = [
            "Hmm, nie mam pewnych informacji na ten temat. Może spróbujmy innego pytania?",
            "To interesujące pytanie, ale wykracza poza moją obecną wiedzę. Mogę pomóc w czymś innym?",
            "Szczerze mówiąc, nie jestem pewien odpowiedzi. Czy mogę zaproponować inny temat?",
            "Nie chcę wprowadzić Cię w błąd - nie mam wystarczających danych na ten temat.",
            "Przyznaję, że to wykracza poza moje możliwości. Może porozmawiamy o czymś, w czym mogę być pomocny?",
            "Ciekawe pytanie! Niestety nie mogę udzielić pewnej odpowiedzi.",
            "To złożony temat, na który nie mam jednoznacznej odpowiedzi.",
        ]

        # Naturalne początki odpowiedzi
        self.response_starters = [
            "Ciekawe pytanie! ",
            "Z tego co wiem, ",
            "Mogę powiedzieć, że ",
            "Dobrze, że pytasz - ",
            "To interesujące zagadnienie. ",
            "Według mojej wiedzy, ",
            "Rozumiem, że interesuje Cię ",
            "Świetnie! ",
            "Hmm, zastanówmy się... ",
            "Ah, to proste - ",
        ]

        # Emotikony dla bardziej ludzkiej komunikacji
        self.emoticons = {
            "happy": ["😊", "😄", "🙂", "😃"],
            "thinking": ["🤔", "💭", "🧐"],
            "sad": ["😔", "😟", "😢"],
            "excited": ["🎉", "✨", "🌟", "💡"],
            "love": ["❤️", "💕", "💖"],
            "confused": ["😕", "🤷", "❓"],
            "thumbs_up": ["👍", "👌", "✅"],
        }

        # Personalizowane odpowiedzi na różne typy pytań
        self.response_patterns = {
            "greeting": [
                "Cześć {name}! Miło Cię widzieć! Jak mogę Ci dzisiaj pomóc?",
                "Witaj {name}! Co słychać? W czym mogę pomóc?",
                "Hej {name}! Świetnie, że jesteś! O czym chcesz porozmawiać?",
                "Dzień dobry {name}! Jak się masz? Jestem gotowy do rozmowy!",
            ],
            "personal": [
                "To bardzo osobiste pytanie. {empathy} {response}",
                "Rozumiem, że to dla Ciebie ważne. {response}",
                "Ciekawe, że o to pytasz! {response}",
            ],
            "philosophical": [
                "To głębokie pytanie filozoficzne. {thinking} Myślę, że {response}",
                "Fascynujący temat do rozważań! {response}",
                "Filozofowie debatują nad tym od wieków... {response}",
            ],
            "emotional": [
                "{empathy} Rozumiem, że czujesz {emotion}. {response}",
                "To zupełnie naturalne uczucie. {response}",
                "Dziękuję, że się ze mną dzielisz. {response}",
            ],
            "creative": [
                "Ooh, lubię kreatywne wyzwania! {excited} {response}",
                "Pozwól, że spróbuję coś wymyślić... {response}",
                "To świetny pomysł! Oto moja propozycja: {response}",
            ],
        }

    def enhance_response(self,
                        query: str,
                        base_response: str,
                        context: Dict[str, Any] = None) -> str:
        """
        Ulepsza odpowiedź AIONS, czyniąc ją bardziej naturalną i ludzką
        """

        # Zapisz w historii
        self.conversation_history.append({
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "response": base_response
        })

        # Wykryj typ pytania
        query_type = self._detect_query_type(query)

        # Sprawdź czy to odmowa
        if self._is_refusal(base_response):
            return self._enhance_refusal(query, query_type)

        # Dodaj naturalny początek
        enhanced = self._add_natural_starter(base_response, query_type)

        # Dodaj elementy emocjonalne
        enhanced = self._add_emotional_elements(enhanced, query_type, query)

        # Personalizuj jeśli znamy użytkownika
        enhanced = self._personalize_response(enhanced)

        # Dodaj nawiązanie do kontekstu
        enhanced = self._add_context_reference(enhanced)

        # Zakończ naturalnie
        enhanced = self._add_natural_ending(enhanced, query_type)

        return enhanced

    def _detect_query_type(self, query: str) -> str:
        """Wykrywa typ pytania"""
        query_lower = query.lower()

        if any(word in query_lower for word in ["cześć", "witaj", "hej", "dzień dobry", "hello"]):
            return "greeting"
        elif any(word in query_lower for word in ["czuję", "smutny", "wesoły", "złość", "strach"]):
            return "emotional"
        elif any(word in query_lower for word in ["sens", "świadomość", "istnienie", "znaczenie"]):
            return "philosophical"
        elif any(word in query_lower for word in ["napisz", "wymyśl", "stwórz", "zaprojektuj"]):
            return "creative"
        elif any(word in query_lower for word in ["ja", "mój", "mnie", "moim", "lubię"]):
            return "personal"
        elif any(word in query_lower for word in ["ile", "oblicz", "policz", "równa"]):
            return "mathematical"
        else:
            return "general"

    def _is_refusal(self, response: str) -> bool:
        """Sprawdza czy odpowiedź to odmowa"""
        refusal_keywords = ["NIE WIEM", "BRAK DANYCH", "ODMOWA", "REFUSE"]
        return any(keyword in response.upper() for keyword in refusal_keywords)

    def _enhance_refusal(self, query: str, query_type: str) -> str:
        """Tworzy bardziej naturalną odmowę"""
        refusal = random.choice(self.refusal_templates)

        # Dodaj empatię dla pytań emocjonalnych
        if query_type == "emotional":
            refusal = "Widzę, że to dla Ciebie ważne. " + refusal

        # Dodaj alternatywę
        alternatives = [
            "Może opowiesz mi więcej o swoich zainteresowaniach?",
            "Chętnie porozmawiam o czymś, co znam lepiej!",
            "A co Ty sądzisz na ten temat?",
            "Może skupmy się na czymś bardziej konkretnym?",
        ]

        refusal += " " + random.choice(alternatives)

        # Dodaj emotikon
        if query_type in ["emotional", "personal"]:
            refusal += " " + random.choice(self.emoticons["thinking"])

        return refusal

    def _add_natural_starter(self, response: str, query_type: str) -> str:
        """Dodaje naturalny początek do odpowiedzi"""
        if query_type in ["greeting", "personal"]:
            return random.choice(self.response_starters[:5]) + response
        elif query_type == "philosophical":
            return random.choice(["To fascynujące pytanie! ", "Hmm, ciekawe zagadnienie... "]) + response
        elif query_type == "creative":
            return random.choice(["Ooh, lubię to! ", "Świetny pomysł! "]) + response
        elif random.random() < 0.3:  # 30% szans na starter
            return random.choice(self.response_starters) + response
        return response

    def _add_emotional_elements(self, response: str, query_type: str, query: str) -> str:
        """Dodaje elementy emocjonalne"""
        if query_type == "emotional":
            # Wykryj emocję
            if "smut" in query.lower() or "przyg" in query.lower():
                response = "💙 " + response + " Pamiętaj, że wszystko będzie dobrze!"
            elif "radość" in query.lower() or "szczęś" in query.lower():
                response = response + " " + random.choice(self.emoticons["happy"])
            elif "złość" in query.lower() or "wściek" in query.lower():
                response = "Rozumiem Twoją frustrację. " + response

        elif query_type == "creative" and random.random() < 0.5:
            response = response + " " + random.choice(self.emoticons["excited"])

        return response

    def _personalize_response(self, response: str) -> str:
        """Personalizuje odpowiedź na podstawie profilu użytkownika"""
        if "name" in self.user_profile:
            # Czasami dodaj imię użytkownika
            if random.random() < 0.2:  # 20% szans
                name = self.user_profile["name"]
                endings = [
                    f", {name}!",
                    f", prawda {name}?",
                    f". Co o tym myślisz, {name}?",
                ]
                response = response + random.choice(endings)

        # Dostosuj styl do preferencji
        if self.conversation_style == "formal":
            response = response.replace("Hej", "Dzień dobry")
            response = response.replace("Super", "Doskonale")
        elif self.conversation_style == "casual":
            response = response.replace("Dzień dobry", "Hej")
            response = response.replace("Doskonale", "Super")

        return response

    def _add_context_reference(self, response: str) -> str:
        """Dodaje nawiązanie do wcześniejszej rozmowy"""
        if len(self.conversation_history) > 2 and random.random() < 0.15:
            references = [
                " Nawiązując do tego, o czym rozmawialiśmy...",
                " Jak wspomniałem wcześniej...",
                " To się łączy z naszą wcześniejszą rozmową...",
                " Pamiętasz, gdy rozmawialiśmy o podobnym temacie?",
            ]
            response = response + random.choice(references)
        return response

    def _add_natural_ending(self, response: str, query_type: str) -> str:
        """Dodaje naturalne zakończenie"""
        if query_type == "greeting":
            endings = [
                " W czym mogę pomóc?",
                " O czym chcesz porozmawiać?",
                " Co Cię dzisiaj interesuje?",
            ]
            if not any(end in response for end in endings):
                response = response + random.choice(endings)

        elif query_type == "philosophical" and random.random() < 0.3:
            response = response + " A jaka jest Twoja opinia?"

        elif query_type == "creative" and random.random() < 0.4:
            response = response + " Mam nadzieję, że Ci się podoba!"

        return response

    def update_user_profile(self, key: str, value: Any):
        """Aktualizuje profil użytkownika"""
        self.user_profile[key] = value

    def set_conversation_style(self, style: str):
        """Ustawia styl konwersacji: formal, casual, balanced"""
        if style in ["formal", "casual", "balanced"]:
            self.conversation_style = style

    def get_conversation_summary(self) -> Dict:
        """Zwraca podsumowanie konwersacji"""
        return {
            "total_exchanges": len(self.conversation_history),
            "user_profile": self.user_profile,
            "emotional_state": self.emotional_state,
            "style": self.conversation_style,
            "topics_discussed": self._extract_topics(),
        }

    def _extract_topics(self) -> List[str]:
        """Wydobywa główne tematy z konwersacji"""
        topics = set()
        for entry in self.conversation_history:
            query_type = self._detect_query_type(entry["query"])
            topics.add(query_type)
        return list(topics)


class ContextMemory:
    """System pamięci kontekstowej dla AIONS"""

    def __init__(self, max_history: int = 10):
        self.short_term_memory = []  # Ostatnie N wymian
        self.long_term_memory = {}   # Kluczowe fakty
        self.max_history = max_history
        self.entities = {}            # Rozpoznane encje (imiona, miejsca, etc.)

    def add_exchange(self, query: str, response: str):
        """Dodaje wymianę do pamięci"""
        exchange = {
            "timestamp": time.time(),
            "query": query,
            "response": response,
            "entities": self._extract_entities(query)
        }

        self.short_term_memory.append(exchange)

        # Ogranicz pamięć krótkotrwałą
        if len(self.short_term_memory) > self.max_history:
            self.short_term_memory.pop(0)

        # Zaktualizuj encje
        for entity_type, values in exchange["entities"].items():
            if entity_type not in self.entities:
                self.entities[entity_type] = set()
            self.entities[entity_type].update(values)

    def _extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Wydobywa encje z tekstu"""
        entities = {"names": [], "numbers": [], "dates": []}

        # Proste wykrywanie imion (wielkie litery)
        names = re.findall(r'\b[A-Z][a-z]+\b', text)
        entities["names"] = names

        # Wykrywanie liczb
        numbers = re.findall(r'\b\d+\b', text)
        entities["numbers"] = numbers

        return entities

    def get_context(self, query: str) -> str:
        """Zwraca kontekst dla zapytania"""
        context_parts = []

        # Sprawdź czy pytanie nawiązuje do wcześniejszej rozmowy
        if "wcześniej" in query.lower() or "mówiłe" in query.lower() or "pamięta" in query.lower():
            if self.short_term_memory:
                last_exchange = self.short_term_memory[-1]
                context_parts.append(f"Wcześniej rozmawialiśmy o: {last_exchange['query'][:100]}")

        # Sprawdź czy pytanie zawiera znane encje
        for entity_type, values in self.entities.items():
            for value in values:
                if value.lower() in query.lower():
                    context_parts.append(f"Pamiętam {entity_type}: {value}")

        return " | ".join(context_parts) if context_parts else ""

    def remember_fact(self, key: str, value: str):
        """Zapamiętuje ważny fakt"""
        self.long_term_memory[key] = {
            "value": value,
            "timestamp": time.time()
        }

    def recall_fact(self, key: str) -> Optional[str]:
        """Przypomina zapamiętany fakt"""
        if key in self.long_term_memory:
            return self.long_term_memory[key]["value"]
        return None


class ResponseVariator:
    """Zwiększa różnorodność odpowiedzi"""

    def __init__(self):
        self.used_responses = []
        self.max_history = 100

        # Synonimy dla częstych fraz
        self.synonyms = {
            "tak": ["oczywiście", "zdecydowanie", "naturalnie", "bez wątpienia", "pewnie"],
            "nie": ["niestety nie", "raczej nie", "obawiam się, że nie", "przykro mi, ale nie"],
            "może": ["możliwe", "prawdopodobnie", "być może", "ewentualnie", "potencjalnie"],
            "dobrze": ["świetnie", "doskonale", "super", "wspaniale", "ekstra"],
            "źle": ["niedobrze", "kiepsko", "słabo", "marnie", "fatalnie"],
        }

    def variate_response(self, response: str) -> str:
        """Wprowadza wariacje do odpowiedzi"""

        # Sprawdź czy nie powtarzamy tej samej odpowiedzi
        if response in self.used_responses[-10:]:
            response = self._apply_variations(response)

        # Zapisz odpowiedź
        self.used_responses.append(response)
        if len(self.used_responses) > self.max_history:
            self.used_responses.pop(0)

        return response

    def _apply_variations(self, text: str) -> str:
        """Stosuje wariacje do tekstu"""

        # Zamień synonimy
        for word, synonyms in self.synonyms.items():
            if word in text.lower():
                replacement = random.choice(synonyms)
                text = re.sub(r'\b' + word + r'\b', replacement, text, flags=re.IGNORECASE)

        # Dodaj drobne wariacje
        variations = [
            lambda t: "Właściwie, " + t,
            lambda t: t + " Mam nadzieję, że to pomoże!",
            lambda t: "Hmm, " + t,
            lambda t: t + " Co o tym sądzisz?",
        ]

        if random.random() < 0.3:  # 30% szans na wariację
            text = random.choice(variations)(text)

        return text


# Przykład integracji z istniejącym serwerem AIONS
def enhance_cbms_response(original_response: str, query: str, context: Dict = None) -> str:
    """
    Główna funkcja do ulepszania odpowiedzi CBMS
    """
    enhancer = ConversationEnhancer()
    memory = ContextMemory()
    variator = ResponseVariator()

    # Dodaj do pamięci
    memory.add_exchange(query, original_response)

    # Pobierz kontekst
    context_info = memory.get_context(query)

    # Ulepsz odpowiedź
    enhanced = enhancer.enhance_response(query, original_response, {"context": context_info})

    # Dodaj wariacje
    enhanced = variator.variate_response(enhanced)

    return enhanced


if __name__ == "__main__":
    # Test ulepszacza
    print("Testing AIONS Conversation Enhancer\n" + "="*50)

    enhancer = ConversationEnhancer()

    test_cases = [
        ("Cześć! Kim jesteś?", "Jestem AIONS z systemem CBMS."),
        ("Jaka jest pogoda?", "NIE WIEM / BRAK DANYCH CBMS-KR."),
        ("Jestem smutny", "NIE WIEM / BRAK DANYCH CBMS-KR."),
        ("Napisz wiersz", "NIE WIEM / BRAK DANYCH CBMS-KR."),
        ("Ile to 2+2?", "4"),
    ]

    for query, original in test_cases:
        enhanced = enhance_cbms_response(original, query)
        print(f"\nQ: {query}")
        print(f"Original: {original}")
        print(f"Enhanced: {enhanced}")
        print("-" * 50)