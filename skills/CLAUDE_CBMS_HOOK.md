# 🧠 CLAUDE CBMS HOOK - EXTERNAL MEMORY PROTOCOL

## PROBLEM
Anthropic context window = ograniczony RAM
Za dużo tool calls = "Compacting... 41%" = utrata kontekstu

## ROZWIĄZANIE  
CBMS = zewnętrzny mózg (525 chunków)
ChromaDB = pamięć długoterminowa (102+ sesji)

## BOOTSTRAP (każda sesja)
```
1. cbms_get_chunk(KBOOTSTRAP)     → potwierdź połączenie
2. memory_recall(session, query)  → co było ostatnio?
```

## ZASADY PRACY
| ❌ NIE RÓB | ✅ RÓB |
|-----------|--------|
| 10x list_directory | 1x cbms_search |
| Ładuj całe pliki | cbms_get_chunk(ID) |
| Trzymaj w kontekście | Sięgaj gdy potrzeba |
| Odkrywaj od nowa | memory_recall |

## KLUCZOWE NAMED CHUNKS
- `KBOOTSTRAP` - start marker
- `KCBMSPIPE001` - cały pipeline CBMS
- `KGUARD001` - guardrails/safety
- `KPLASTERS001` - plastry PACK-200g
- `KWEBRAG001` - web RAG tryb
- `KCODEBOOK001` - kompresja koreańska
- `KDOC*` - dokumentacja systemu
- `KMAIPA0001` - knowledge base Q&A

## PO WAŻNEJ ROBOCIE
```
memory_store(session_id, "co zrobiłem", ttl_days=365)
conv_dump(summary="krótki opis")
```

## MANTRA
**CBMS = dysk, Context = RAM. Nie ładuj wszystkiego - sięgaj!**
