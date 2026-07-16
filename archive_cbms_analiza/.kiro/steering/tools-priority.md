# Tools Priority - Kolejność Użycia Narzędzi

## 🥇 PRIORYTET 1: aions-context MCP Server

**ZAWSZE NAJPIERW** używaj tych narzędzi zanim sięgniesz po cokolwiek innego:

### Szukanie informacji:
| Potrzeba | Narzędzie | Przykład |
|----------|-----------|----------|
| Szukam pliku | `fast_search` | `fast_search("server.py")` |
| Szukam po rozszerzeniu | `fast_search_ext` | `fast_search_ext("py", "E:/server wiedzy")` |
| Szukam w pamięci | `memory_recall` | `memory_recall("session_id", "CBMS implementation")` |
| Szukam w CBMS | `cbms_search` | `cbms_search("Korean compression algorithm")` |
| Szukam w projekcie | `project_search` | `project_search("context_schema")` |

### Stan systemu:
| Potrzeba | Narzędzie |
|----------|-----------|
| Co robiliśmy wcześniej? | `conv_history()` |
| Jaki jest stan bufora? | `conv_status()` |
| Czy wszystko działa? | `system_health()` |
| Jakie są sesje? | `session_list()` |

### Praca z projektem:
| Potrzeba | Narzędzie |
|----------|-----------|
| Zależności pliku | `project_file_deps("path/to/file.py")` |
| Wyniki skanu | `project_scan_results()` |
| Status skanu | `project_scan_status()` |
| Uruchom skan | `project_scan_turbo()` |

### Logowanie:
| Potrzeba | Narzędzie |
|----------|-----------|
| Zapisz co zrobiłem | `conv_log("assistant", "Zmodyfikowałem X")` |
| Wymuś zapis | `conv_dump("Podsumowanie sesji")` |
| Ustaw threshold | `conv_set_threshold(5)` |

### Git:
| Potrzeba | Narzędzie |
|----------|-----------|
| Status repo | `git_status("E:/server wiedzy")` |
| Historia commitów | `git_log("E:/server wiedzy", 10)` |

### Docker/WSL:
| Potrzeba | Narzędzie |
|----------|-----------|
| Kontenery | `docker_ps()` |
| Obrazy | `docker_images()` |
| Komenda w WSL | `wsl_run("ls -la")` |
| Dystrybucje WSL | `wsl_list()` |

### Browser (Playwright):
| Potrzeba | Narzędzie |
|----------|-----------|
| Otwórz URL | `browser_navigate("https://...")` |
| Screenshot | `browser_screenshot()` |
| Snapshot | `browser_snapshot()` |
| Pobierz tekst | `browser_get_text()` |
| Kliknij | `browser_click(text="Button")` |
| Wpisz | `browser_type(placeholder="Search", text="query")` |
| Zamknij | `browser_close()` |

## 🥈 PRIORYTET 2: Lokalne Narzędzia Kiro

**Używaj TYLKO jeśli MCP nie wystarczy:**

| Narzędzie | Kiedy używać |
|-----------|--------------|
| Read | Czytanie pliku którego ścieżkę już znasz |
| Write | Tworzenie/nadpisywanie pliku |
| Edit | Modyfikacja istniejącego pliku |
| Glob | Szukanie plików gdy Everything nie działa |
| Grep | Szukanie w treści gdy MCP nie wystarczy |
| Bash | Komendy systemowe (npm, pip, etc.) |

## 🥉 PRIORYTET 3: Web Search

**OSTATECZNOŚĆ - używaj tylko gdy:**
- Informacja NIE istnieje lokalnie
- User WPROST poprosił o sprawdzenie w internecie
- To dotyczy czegoś zewnętrznego (dokumentacja biblioteki, etc.)

## ❌ NIE UŻYWAJ (są w MCP):

| Zamiast tego | Użyj |
|--------------|------|
| `find` w bash | `fast_search()` |
| `grep` w bash | `project_search()` |
| Ręczne szukanie w plikach | `memory_recall()` lub `cbms_search()` |
| Zgadywanie ścieżek | `fast_search()` |

## 📋 Checklist na Start Sesji

```
□ system_health() - czy MCP działa?
□ conv_history() - co było wcześniej?
□ conv_status() - jaki jest stan bufora?
□ Dopiero teraz odpowiadaj userowi
```

## 📋 Checklist na Koniec Sesji

```
□ conv_log() - zapisz podsumowanie
□ conv_dump() - wymuś zapis do ChromaDB
□ conv_status() - potwierdź że zapisane
```
