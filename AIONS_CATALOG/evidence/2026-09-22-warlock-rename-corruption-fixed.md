# Warlock rename documentation corruption: naprawione i zabezpieczone

DATA: 2026-09-22
AUTOR: Claude Opus 5 / Cowork, na zlecenie Marcina

## Czym byl defekt

Commit 2cd32c4 w polip-agi puscil masowa podmiane Sheriff na Warlock po
katalogu docs. Podmiana weszla takze w zdania, ktore te zmiane OPISYWALY,
zostawiajac miedzy innymi "Warlock replaces the earlier name Warlock" oraz
"migracja Warlock -> Warlock".

## Gdzie defekt faktycznie siedzial

NIE na main. Galaz main jest starsza niz rename i byla czysta. Zepsute linie
byly na czterech galeziach niosacych commit 2cd32c4, z ktorych najnowsza i
zyjaca jest integration/2026-09-16-salvage.

## Naprawa

Dwanascie linii w pieciu plikach. Kazda przywrocona z tekstu SPRZED rename,
z commita rodzica 3d6afc48b2338a0ddc0e7f6b80d275df5527ecad. Nic nie bylo
wymyslane. Metoda: wypisac kazda linie rodzica zawierajaca Sheriff, zbudowac
z niej postac, jaka dalaby slepa podmiana, i przywrocic oryginal wszedzie,
gdzie ta postac dzis wystepuje.

Diff: dwanascie linii w gore, dwanascie w dol, kazda roznica to jedno slowo.

## Zabezpieczenie

crates/darkstar-core/tests/rename_consistency.rs skanuje docs i wywala sie na
zdaniach mowiacych, ze X zastapil X. Jedzie na istniejacym cargo test.

Powiedziane wprost w samym tescie: lapie dziesiec z dwunastu linii. Dwie
pozostale to podmienione slowo w zdaniu, ktore o zmianie nazwy nie mowi, i z
samego tekstu wykryc sie tego nie da.

Pierwsza, ogolna wersja reguly dawala osiem falszywych alarmow na tym repo,
miedzy innymi na fn bind_addresses(primary: SocketAddr) -> Vec<SocketAddr>.
Zastapiona jawna lista sformulowan.

## Landing i weryfikacja

Galaz fix/warlock-rename-doc-corruption, commit 40cd782.
Scalona przez PR numer 11 do integration/2026-09-16-salvage jako 68ea352.

Po scaleniu, zmierzone na stanie polaczonym:
- szukanie samoodnoszacych fraz na salvage zwraca ZERO trafien
- cargo test -p darkstar-core --test rename_consistency: 3 passed
- test mutacyjny przed scaleniem: schowanie naprawy dokumentacji daje dokladnie
  dziesiec naruszen i test pada

## Ograniczenie tego wpisu, powiedziane wprost

Walidator tego repo nie siega do polip-agi. Nie moze sam sprawdzic tamtych
commitow. Autorytatywnym dowodem sa SHA 40cd782 i 68ea352 w polip-agi, nie ten
plik. Ten plik zapisuje, co zmierzono i czym.

Pozostale trzy galezie z commitem 2cd32c4 nadal niosa stare, zepsute linie.
Naprawiona jest zyjaca linia pracy, nie historia.
