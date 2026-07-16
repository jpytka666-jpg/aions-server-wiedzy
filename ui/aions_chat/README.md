# AIONS Chat

Lokalne okienko czatu do rozmowy z systemem AIONS. Zero zewnetrznej infrastruktury,
zero platnych licencji, zero Node/Electron. Tylko Python (biblioteka standardowa) + HTML.

## Jak uruchomic

Dwuklik na `Run.bat`.

To wszystko. Skrypt:
1. Uruchamia lokalny serwer HTTP (`server.py`) na `127.0.0.1:8770` (widoczny tylko na tym komputerze).
2. Otwiera interfejs czatu -- w oknie `pywebview`, jesli ta biblioteka jest
   zainstalowana w venv (`E:\server wiedzy\venv`), a jesli nie -- w domyslnej
   przegladarce pod adresem `http://127.0.0.1:8770`.

Zeby zatrzymac serwer: zamknij okno konsoli albo wcisnij `Ctrl+C`.

## Co potrafi

Napisz w oknie czatu np.:
- "co mam do zrobienia" / "lista" -- pokazuje otwarte sprawy (papiery.list)
- "co pilne" / "termin" -- sprawy z terminem w najblizszych 7 dniach
- "dodaj kupic znaczki do 20 lipca" / "zapamietaj ..." -- zapisuje nowa sprawe
- "zrobione" / "odhacz" -- poinformuje, ze trzeba podac id sprawy
- dowolne inne polecenie (np. "otworz kalkulator", "ktora godzina") -- AIONS
  szuka pasujacego bloku-umiejetnosci (skilla) w rejestrze (`skills_lib`, ~61 blokow)
  i albo go wykonuje (niskie ryzyko), albo pyta o potwierdzenie (srednie/wysokie ryzyko),
  albo mowi, ze jeszcze nie ma takiego bloku.

## Bezpieczenstwo

Akcje ryzykowne (usuwanie plikow, zabijanie procesow, blokowanie ekranu,
czyszczenie TEMP, zamykanie aplikacji) **nigdy nie wykonuja sie automatycznie**.
AIONS Chat zapyta: "To akcja ryzykowna (X). Napisz 'potwierdzam' zeby wykonac."
Dopiero po wpisaniu `potwierdzam` akcja zostanie wykonana.

## Pliki

- `server.py` -- serwer HTTP (`http.server`, zero zaleznosci), integracja z
  `control_plane.skills` (SkillRegistry, executor, papiery, build_context).
- `index.html` -- interfejs czatu (vanilla JS, wszystko inline, offline-first).
- `Run.bat` -- uruchamia `server.py` przez venv AIONS.
- `README.md` -- ten plik.

## Wymagania

- Python z `E:\server wiedzy\venv\Scripts\python.exe` (juz istnieje w systemie AIONS).
- Dostep do `E:\server wiedzy\control_plane` i `E:\server wiedzy\skills_lib`
  (nic tam nie jest modyfikowane -- tylko odczyt/import).
- Brak wymaganych pakietow zewnetrznych. Jesli w venv jest `pywebview`, zostanie
  uzyty do okna natywnego; jesli nie ma -- dziala w przegladarce.
