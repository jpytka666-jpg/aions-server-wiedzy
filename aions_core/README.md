# AIONS/CBMS Release (Local, Offline)

## Szybki start
- Windows: uruchom `run_server.bat` (lub `run_server.ps1` w PowerShell).
- Serwer startuje na `http://127.0.0.1:9000`.
- API:
  - `GET /health` – status, liczba chunków
  - `GET /info` – informacje (koncepty)
  - `POST /api/chat` – CBMS-only odpowiedź z odmową OOD
  - `POST /crla/ask` – turniej CRLA (json: `{ "query":"…", "seed":123, "candidates":8 }`)

## Skład paczki
- `server/` – kod serwera (CBMS, CRLA, stylist, korean-keys, loader faktów)
- `memory/` – manifest, chunki, fakty i indeks
- `tools/` – crawler www, builder faktów, benchmark
- `logs/` – wyniki benchmarku, CRLA runs (jeżeli są)
- `web/` – prosta strona statyczna (dla handlera)

## Odmowa poza domeną (OOD)
- Stały komunikat: `NIE WIEM / BRAK DANYCH CBMS-KR.`
- Kryteria: trafienia kluczy (korean-keys), coverage faktów (hashed), min_hits

## Stylizacja
- `stylist.py` – pasywny filtr językowy, bez prawa zmiany treści. Gdy ryzyko naruszenia faktów – styl NIE jest stosowany.

## Crawler (opcjonalnie)
- Przykład (PowerShell):
  `py .\tools\web_crawler_import.py --seeds=https://en.wikipedia.org/wiki/Beam_search --allow=en.wikipedia.org --max-pages=50 --max-mb=10`
- Nowe fakty zapisują się do `memory/facts.jsonl` i aktualizują indeks.

## Benchmark
- `py .\tools\bench_runner.py` – zapisuje wyniki do `logs/` (latencje p50/p95).

## Uwaga
- Paczka jest samodzielna (CBMS_MEMORY_DIR i CBMS_WEB_DIR ustawiane przez skrypty).
- Brak internetu nie przeszkadza – fakty i chunki są lokalne.
