"""
ACAE — deterministyczny pack repozytorium.

Zamiast cial funkcji pakujemy sygnatury, zeby wprowadzenie modelu w kod kosztowalo
ulamek dzisiejszego kontekstu. Cala wartosc tego modulu siedzi w slowie
"deterministyczny": ten sam commit ma dawac ten sam pack_hash, niezaleznie od
kolejnosci systemu plikow, mtime, katalogu roboczego i systemu operacyjnego.

Warstwy:
    canon    — funkcje kanonizujace (hash, JSON, sciezki, konce linii)
    ports    — protokoly Locator / Reader / Store; cale I/O siedzi za nimi
    symbols  — adapter na SymbolIndex z aions_core.server.ts_symbols
    secrets  — skan sekretow przed wpuszczeniem pliku do packa
    core     — PackRequest -> PackManifest, czysta funkcja, zero I/O
    pack     — zapis artefaktu na dysk
    cli      — python -m acae pack --root .
"""

__version__ = "0.1.0"
