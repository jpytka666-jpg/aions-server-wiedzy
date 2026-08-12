"""
Podzial 169 plikow packa na partie do opisania przez agentow (M8).

Dlaczego po BAJTACH, a nie po sztukach: agent czyta CALA tresc kazdego pliku, wiec
koszt partii zalezy od jej rozmiaru, nie od liczby pozycji. Pierwszy przebieg dzielil
po 28 plikow na partie i agent, ktoremu trafily sie duze pliki, pod koniec serii
streszczal zamiast opisywac — mediana wyszla 59 slow przy zamowionych 100-160,
a ostatni wpis w jednej partii byl notatka agenta do siebie zamiast opisem.

Podzial jest deterministyczny: LPT (najwieksze najpierw, kazdy do najlzejszej partii),
remisy rozstrzygane sciezka. Ten sam manifest zawsze daje te same partie.

Zrodlo prawdy o zakresie to `_out/manifest.json` — ten sam zbior 169 plikow,
ktory wchodzi do packa. Zadnego wlasnego skanowania dysku, zeby zakres sie nie rozjechal.
"""
import json
import pathlib

ACAE = pathlib.Path("acae")
PARTII = 12


def main():
    manifest = json.loads((ACAE / "_out" / "manifest.json").read_text(encoding="utf-8"))
    pliki = [(int(f["bytes"]), str(f["path"])) for f in manifest["files"]]

    # LPT: najwieksze najpierw, remis po sciezce -> ten sam wynik przy kazdym uruchomieniu
    pliki.sort(key=lambda p: (-p[0], p[1]))

    partie = [[] for _ in range(PARTII)]
    wagi = [0] * PARTII
    for bajtow, sciezka in pliki:
        i = min(range(PARTII), key=lambda k: (wagi[k], k))
        partie[i].append(sciezka)
        wagi[i] += bajtow

    outdir = ACAE / "_desc"
    outdir.mkdir(parents=True, exist_ok=True)
    for i, partia in enumerate(partie):
        # w partii sortujemy po sciezce — agent czyta sasiadujace pliki obok siebie
        tresc = "\n".join(sorted(partia)) + "\n"
        (outdir / f"batch_{i}.txt").write_text(tresc, encoding="utf-8", newline="\n")

    print(f"plikow w manifescie : {len(pliki)}")
    print(f"partii              : {PARTII}")
    print(f"rozdzielono         : {sum(len(p) for p in partie)}")
    print()
    for i, partia in enumerate(partie):
        print(f"  batch_{i:<2} {len(partia):>3} plikow  {wagi[i]:>7} bajtow")
    print()
    print(f"najlzejsza partia   : {min(wagi)} bajtow")
    print(f"najciezsza partia   : {max(wagi)} bajtow")
    print(f"rozrzut             : {max(wagi) - min(wagi)} bajtow")


if __name__ == "__main__":
    main()
