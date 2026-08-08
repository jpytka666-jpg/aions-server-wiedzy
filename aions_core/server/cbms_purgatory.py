"""
cbms_purgatory.py -- czysciec (purgatory) dla systemu pamieci CBMS.

PROBLEM
    Nowe chunki, ktore trafiaja prosto do chunks/, nie maja zadnej weryfikacji.
    Miary, ktore wygladaja na sygnal wartosci -- trafienie w wyszukiwaniu (outline),
    stopien wejsciowy (indegree) -- sa tanie i oszukiwalne. Dowod z zywego store:
    chunki "crla_pattern" (czysta telemetria, ~60 znakow) maja 80-89 przychodzacych
    referencji i sa najwyzej w grafie. Chunk K66F9335B44B9 to zapisana przez system
    preambula wlasnej odpowiedzi ("Na podstawie 15 fragmentow wiedzy:"), a ma 62
    referencje przychodzace. access_count nie dziala w ogole -- 0 albo brak w 100%
    chunkow na dysku.

ROZWIAZANIE: trzystopniowy cykl zycia
    purgatory -> (promocja) chunks/  |  (parking) chunks_quarantine/

    Zaden nowy chunk nie trafia prosto do chunks/. Najpierw laduje w
    memory/chunks_purgatory/, gdzie zbiera sygnal przez okres karencji. Po karencji
    zapada wyrok na podstawie DRILLI, nie trafien w outline i nie indegree.

ZASADA WARTOSCI -- to jest sedno tego narzedzia
    Wartoscia NIE jest trafienie w wyszukiwaniu ani liczba referencji.
    Wartoscia jest DRILL -- czy ktos faktycznie siegnal po pelna tresc chunka.

        outline hit (pojawienie sie w szkielecie wynikow)  -> tanie, nie liczy sie
        drill (pobranie pelnej tresci)                     -> ktos tego potrzebowal, +1

    Telemetria bedzie sie wiecznie pojawiac w outline (bo pasuje do fraz zapytan)
    i nigdy nie zostanie zdrillowana (bo nikt nie chce przeczytac "wynik 0.956,
    latencja 0.719 ms"). Taki chunk umiera sam, bez recznej kuracji.

REGULY WYROKU (progi konfigurowalne przez CLI, ponizej wartosci domyslne)
    karencja             14 dni ORAZ min. 3 sesje (sesja = odrebny dzien, w ktorym
                          COKOLWIEK zapisano do rejestru DLA TEGO id -- admit, drill
                          lub outline-hit; patrz DECYZJE w README ponizej)
    drills >= prog        -> PROMOCJA do chunks/          (prog domyslnie 2)
    drills == 0            -> PARKING do chunks_quarantine/ (po uplywie karencji)
    0 < drills < prog       -> jednorazowe przedluzenie karencji o kolejne 14 dni,
                             potem PARKING jesli prog nadal nie osiagniety
    provenance == cloud      -> prog promocji podniesiony do drills >= 3
    provenance == human/verified -> promocja natychmiastowa, bez karencji

BEZPIECZENSTWO (twarde wymagania)
    - Zaden plik chunka nigdy nie jest kasowany (brak os.remove na chunkach).
      Wyrok negatywny = PRZENIESIENIE (os.replace, czyli rename) do
      chunks_quarantine/, nigdy usuniecie.
    - --judge bez --apply niczego nie zapisuje na dysk (czysty podglad, zero
      wywolan zapisu -- nawet do samego rejestru).
    - Przed kazdym --apply rejestr jest kopiowany z timestampem do
      <katalog rejestru>/purgatory_ledger_backups/.
    - Zapis rejestru jest atomowy: .tmp -> walidacja ponownym odczytem -> os.replace.
    - Ruch pliku nigdy nie nadpisuje istniejacego celu -- kolizja id przerywa
      TYLKO ten jeden ruch (reszta wyrokow w tym samym --apply przechodzi dalej).
    - To jest samodzielny leaf: stdlib only, nic nie importuje z AIONS, nie rusza
      cbms_memory.py, crla_core.py ani niczego w server/. Rejestr NIGDY nie ląduje
      w %TEMP% (Windows go czysci bez pytania).

CLI
    python cbms_purgatory.py --config
    python cbms_purgatory.py --admit nowy_chunk.json --provenance local
    python cbms_purgatory.py --admit - --provenance cloud        (json ze stdin)
    python cbms_purgatory.py --record-drill K0123ABC
    python cbms_purgatory.py --record-outline K0123ABC K0456DEF
    python cbms_purgatory.py --status
    python cbms_purgatory.py --judge                              (dry-run, domyslnie)
    python cbms_purgatory.py --judge --apply                      (wykonuje ruchy)

REJESTR
    memory/purgatory_ledger.json -- jedyne miejsce z metadanymi cyklu zycia.
    Chunk json sam w sobie NIGDY nie jest modyfikowany przez to narzedzie (kopiowany
    bajt-w-bajt przy --admit, potem tylko przenoszony jako calosc przy wyroku).
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from datetime import datetime, timezone

BASE = r"E:\server wiedzy\aions_core\memory"
DEF_CHUNKS = os.path.join(BASE, "chunks")
DEF_QUAR = os.path.join(BASE, "chunks_quarantine")
DEF_PURGATORY = os.path.join(BASE, "chunks_purgatory")
DEF_LEDGER = os.path.join(BASE, "purgatory_ledger.json")

PROVENANCE_VALUES = ("local", "cloud", "human", "verified")
IMMEDIATE_PROVENANCE = {"human", "verified"}

DEFAULT_GRACE_DAYS = 14
DEFAULT_MIN_SESSIONS = 3
DEFAULT_EXTEND_DAYS = 14
DEFAULT_PROMOTE_DRILLS = 2
DEFAULT_CLOUD_PROMOTE_DRILLS = 3

V_WAIT = "WAIT"
V_EXTEND = "EXTEND"
V_PROMOTE = "PROMOTE"
V_PARK = "PARK"
V_DECIDED = "DECIDED"

ST_PURGATORY = "purgatory"
ST_ACTIVE = "active"
ST_QUARANTINE = "quarantine"
ST_PROMOTED = "promoted"
ST_PARKED = "parked"


# ------------------------------------------------------------------------ czas

def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime) -> str:
    return dt.isoformat(timespec="seconds")


def parse_dt(value: str) -> datetime:
    """Parsuje ISO8601. Naiwne znaczniki (bez strefy) traktowane jako UTC."""
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def day_str(dt: datetime) -> str:
    return dt.date().isoformat()


def resolve_when(as_of: str | None) -> tuple[datetime | None, str | None]:
    """--as-of pozwala ocenic wyrok 'jakby to bylo X' bez zmiany progow. Tylko do
    podgladu w --status/--judge -- nigdy nie jest zapisywane jako prawdziwy czas."""
    if not as_of:
        return now_utc(), None
    try:
        return parse_dt(as_of), None
    except ValueError as exc:
        return None, f"BLAD: nie mozna sparsowac --as-of '{as_of}': {exc}"


# ---------------------------------------------------------------------- config

class Config:
    """Progi wyroku. Wszystkie nadpisywalne z CLI."""

    def __init__(self, grace_days=DEFAULT_GRACE_DAYS, min_sessions=DEFAULT_MIN_SESSIONS,
                 extend_days=DEFAULT_EXTEND_DAYS, promote_drills=DEFAULT_PROMOTE_DRILLS,
                 cloud_promote_drills=DEFAULT_CLOUD_PROMOTE_DRILLS):
        self.grace_days = grace_days
        self.min_sessions = min_sessions
        self.extend_days = extend_days
        self.promote_drills = promote_drills
        self.cloud_promote_drills = cloud_promote_drills
        self.immediate_provenance = set(IMMEDIATE_PROVENANCE)

    @classmethod
    def from_args(cls, a) -> "Config":
        return cls(a.grace_days, a.min_sessions, a.extend_days,
                    a.promote_drills, a.cloud_promote_drills)

    def as_dict(self) -> dict:
        return {
            "grace_days": self.grace_days,
            "min_sessions": self.min_sessions,
            "extend_days": self.extend_days,
            "promote_drills": self.promote_drills,
            "cloud_promote_drills": self.cloud_promote_drills,
            "immediate_provenance": sorted(self.immediate_provenance),
        }


# --------------------------------------------------------------------- rejestr

def backups_dir_for(ledger_path: str) -> str:
    return os.path.join(os.path.dirname(os.path.abspath(ledger_path)) or ".",
                         "purgatory_ledger_backups")


def default_ledger() -> dict:
    return {"_meta": {"version": 1, "created_at": iso(now_utc()), "updated_at": None},
            "entries": {}}


def load_ledger(path: str) -> dict:
    if not os.path.isfile(path):
        return default_ledger()
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"BLAD: rejestr {path} jest uszkodzony: {exc}")
    if not isinstance(data, dict) or "entries" not in data:
        raise SystemExit(f"BLAD: rejestr {path} ma nieoczekiwany ksztalt")
    return data


def save_ledger(path: str, data: dict) -> None:
    """Zapis atomowy: .tmp -> walidacja odczytem -> os.replace. Uzywane po kazdej
    mutacji rejestru (admit, record-drill, record-outline, judge --apply)."""
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    data.setdefault("_meta", {})["updated_at"] = iso(now_utc())
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
    with open(tmp, encoding="utf-8") as fh:
        json.load(fh)  # walidacja: musi sie dac odczytac zanim podmienimy oryginal
    os.replace(tmp, path)


def backup_ledger(path: str) -> str | None:
    """Kopia rejestru z timestampem przed jakimkolwiek --apply. Nie rusza oryginalu.
    Zwraca None, jesli rejestr jeszcze nie istnial (nic do skopiowania)."""
    if not os.path.isfile(path):
        return None
    backups_dir = backups_dir_for(path)
    os.makedirs(backups_dir, exist_ok=True)
    ts = now_utc().strftime("%Y%m%dT%H%M%SZ")
    dst = os.path.join(backups_dir, f"purgatory_ledger_{ts}.json")
    shutil.copy2(path, dst)
    return dst


def get_entry(ledger: dict, cid: str) -> dict | None:
    return ledger["entries"].get(cid)


def touch_session(entry: dict, when: datetime) -> None:
    d = day_str(when)
    days = entry.setdefault("session_dates", [])
    if d not in days:
        days.append(d)
        days.sort()


def new_entry(cid: str, status: str, when: datetime) -> dict:
    return {
        "id": cid,
        "status": status,               # purgatory | active | quarantine | promoted | parked
        "admitted_at": None,
        "provenance": None,
        "drills": 0,
        "outline_hits": 0,
        "session_dates": [],
        "grace_period_days": DEFAULT_GRACE_DAYS,
        "grace_extended": False,
        "decided_at": None,
        "verdict_reason": None,
        "first_seen": iso(when),
        "last_updated": iso(when),
    }


# ---------------------------------------------------------------------- chunki

def locate_chunk(cid: str, purgatory_dir: str, chunks_dir: str, quarantine_dir: str):
    """Szuka pliku chunka po id. Kolejnosc: purgatory -> active -> quarantine.
    Zwraca (sciezka, status) albo (None, None), jesli nigdzie nie ma takiego pliku."""
    for path, status in ((os.path.join(purgatory_dir, cid + ".json"), ST_PURGATORY),
                          (os.path.join(chunks_dir, cid + ".json"), ST_ACTIVE),
                          (os.path.join(quarantine_dir, cid + ".json"), ST_QUARANTINE)):
        if os.path.isfile(path):
            return path, status
    return None, None


def read_chunk(path: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def safe_move(src: str, dst: str) -> None:
    """Przenosi plik (os.replace = rename na tym samym wolumenie, NIGDY os.remove).
    Odmawia nadpisania istniejacego celu -- kolizja id nie moze skasowac wiedzy."""
    if os.path.exists(dst):
        raise FileExistsError(f"cel juz istnieje, nie nadpisuje: {dst}")
    os.makedirs(os.path.dirname(os.path.abspath(dst)) or ".", exist_ok=True)
    os.replace(src, dst)


# ----------------------------------------------------------------------- wyrok

def judge_entry(entry: dict, cfg: Config, when: datetime) -> tuple[str, str]:
    """Czysta funkcja: (wyrok, uzasadnienie). Nie modyfikuje entry, nie dotyka dysku."""
    if entry["status"] != ST_PURGATORY:
        return V_DECIDED, f"juz rozstrzygniete: {entry['status']} ({entry.get('decided_at')})"

    prov = entry.get("provenance")
    if prov in cfg.immediate_provenance:
        return V_PROMOTE, f"provenance={prov}: promocja natychmiastowa, bez karencji"

    if not entry.get("admitted_at"):
        return V_WAIT, "brak admitted_at -- nie mozna ocenic karencji"

    admitted = parse_dt(entry["admitted_at"])
    age_days = (when - admitted).days
    sessions = len(entry.get("session_dates") or [])
    grace = entry.get("grace_period_days", cfg.grace_days)
    drills = entry.get("drills", 0)
    promote_at = cfg.cloud_promote_drills if prov == "cloud" else cfg.promote_drills

    if not (age_days >= grace and sessions >= cfg.min_sessions):
        return V_WAIT, f"karencja trwa: wiek {age_days}/{grace}d, sesje {sessions}/{cfg.min_sessions}"

    if drills >= promote_at:
        return V_PROMOTE, f"drills={drills} >= prog {promote_at} (provenance={prov})"

    if drills == 0:
        return V_PARK, "0 drilli po uplywie karencji"

    if not entry.get("grace_extended"):
        return V_EXTEND, (f"drills={drills} < prog {promote_at}: jednorazowe "
                           f"przedluzenie karencji o {cfg.extend_days}d")

    return V_PARK, f"drills={drills} < prog {promote_at} po wykorzystanym przedluzeniu"


# --------------------------------------------------------------------- komendy

def cmd_config(cfg: Config, a) -> int:
    payload = {
        "progi": cfg.as_dict(),
        "sciezki": {
            "chunks": a.chunks,
            "chunks_quarantine": a.quarantine,
            "chunks_purgatory": a.purgatory,
            "ledger": a.ledger,
            "ledger_backups": backups_dir_for(a.ledger),
        },
    }
    if a.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print("== CZYSCIEC: PROGI WYROKU ==")
        for k, v in payload["progi"].items():
            print(f"  {k:24s} {v}")
        print()
        print("== SCIEZKI ==")
        for k, v in payload["sciezki"].items():
            print(f"  {k:24s} {v}")
    return 0


def cmd_admit(a) -> int:
    if not a.provenance:
        print("BLAD: --admit wymaga --provenance {local,cloud,human,verified}", file=sys.stderr)
        return 1

    src_is_stdin = a.admit == "-"
    if src_is_stdin:
        raw = sys.stdin.read()
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            print(f"BLAD: stdin nie jest poprawnym JSON: {exc}", file=sys.stderr)
            return 1
        src_path = None
    else:
        if not os.path.isfile(a.admit):
            print(f"BLAD: plik nie istnieje: {a.admit}", file=sys.stderr)
            return 1
        try:
            data = read_chunk(a.admit)
        except (OSError, json.JSONDecodeError) as exc:
            print(f"BLAD: nie mozna odczytac {a.admit}: {exc}", file=sys.stderr)
            return 1
        src_path = a.admit

    if not isinstance(data, dict):
        print("BLAD: korzen chunka musi byc obiektem JSON", file=sys.stderr)
        return 1

    stem = os.path.splitext(os.path.basename(src_path))[0] if src_path else None
    cid = str(data.get("id") or stem or f"KPURG{now_utc().strftime('%Y%m%d%H%M%S')}")

    active_path = os.path.join(a.chunks, cid + ".json")
    if os.path.isfile(active_path):
        print(f"BLAD: id {cid} juz istnieje w chunks/ (aktywny) -- odmawiam admitu, "
              f"promocja pozniej i tak by kolidowala", file=sys.stderr)
        return 1

    ledger = load_ledger(a.ledger)
    existing = get_entry(ledger, cid)
    if existing and existing["status"] == ST_PURGATORY:
        print(f"BLAD: id {cid} jest juz w czysccu od {existing.get('admitted_at')} "
              f"-- ponowny --admit zresetowalby karencje. Uzyj --status.", file=sys.stderr)
        return 1

    quarantine_path = os.path.join(a.quarantine, cid + ".json")
    if os.path.isfile(quarantine_path):
        print(f"UWAGA: id {cid} istnieje tez w chunks_quarantine/ -- kontynuuje admit, "
              f"ale ewentualny PARK tego kandydata pozniej wykryje kolizje i nie nadpisze.")

    os.makedirs(a.purgatory, exist_ok=True)
    dst_path = os.path.join(a.purgatory, cid + ".json")
    if os.path.isfile(dst_path):
        print(f"BLAD: {dst_path} juz istnieje na dysku (poza rejestrem) -- nie nadpisuje.",
              file=sys.stderr)
        return 1

    if src_path:
        shutil.copy2(src_path, dst_path)   # kopia bajt-w-bajt, chunk NIE jest modyfikowany
    else:
        with open(dst_path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)

    when = now_utc()
    entry = new_entry(cid, ST_PURGATORY, when)
    entry["admitted_at"] = iso(when)
    entry["provenance"] = a.provenance
    entry["grace_period_days"] = a.grace_days
    touch_session(entry, when)
    ledger["entries"][cid] = entry
    save_ledger(a.ledger, ledger)

    print(f"OK: przyjeto {cid} do czysca (provenance={a.provenance})")
    print(f"  plik:    {dst_path}")
    print(f"  zrodlo:  {src_path or '(stdin)'}")
    print(f"  rejestr: {a.ledger}")
    return 0


def cmd_record_drill(a) -> int:
    cid = a.record_drill
    path, status = locate_chunk(cid, a.purgatory, a.chunks, a.quarantine)
    if not path:
        print(f"BLAD: {cid} nie znaleziony ani w czysccu, ani w chunks/, ani w "
              f"chunks_quarantine/", file=sys.stderr)
        return 1

    ledger = load_ledger(a.ledger)
    when = now_utc()
    entry = get_entry(ledger, cid)
    if entry is None:
        entry = new_entry(cid, status, when)
        ledger["entries"][cid] = entry

    before = entry["drills"]
    entry["drills"] = before + 1
    entry["last_updated"] = iso(when)
    touch_session(entry, when)
    save_ledger(a.ledger, ledger)

    print(f"OK: {cid} drills {before} -> {entry['drills']}  (status={entry['status']})")
    return 0


def cmd_record_outline(a) -> int:
    ledger = load_ledger(a.ledger)
    when = now_utc()
    ok, missing = [], []
    for cid in a.record_outline:
        path, status = locate_chunk(cid, a.purgatory, a.chunks, a.quarantine)
        if not path:
            missing.append(cid)
            continue
        entry = get_entry(ledger, cid)
        if entry is None:
            entry = new_entry(cid, status, when)
            ledger["entries"][cid] = entry
        entry["outline_hits"] += 1
        entry["last_updated"] = iso(when)
        touch_session(entry, when)
        ok.append((cid, entry["outline_hits"]))

    if ok:
        save_ledger(a.ledger, ledger)
    for cid, n in ok:
        print(f"OK: {cid} outline_hits -> {n}")
    for cid in missing:
        print(f"POMINIETO: {cid} nie znaleziony w zadnym tierze", file=sys.stderr)
    return 0 if not missing else 1


def _status_rows(ledger: dict, cfg: Config, when: datetime) -> list[dict]:
    rows = []
    for cid, entry in ledger["entries"].items():
        if entry["status"] not in (ST_PURGATORY, ST_PROMOTED, ST_PARKED):
            continue
        if entry["status"] == ST_PURGATORY:
            verdict, reason = judge_entry(entry, cfg, when)
        else:
            verdict, reason = "-", (entry.get("verdict_reason") or "")
        admitted = parse_dt(entry["admitted_at"]) if entry.get("admitted_at") else None
        age = (when - admitted).days if admitted else None
        rows.append({
            "id": cid, "age_days": age, "provenance": entry.get("provenance") or "-",
            "drills": entry["drills"], "outline_hits": entry["outline_hits"],
            "status": entry["status"], "verdict": verdict, "reason": reason,
        })
    rows.sort(key=lambda r: (r["status"] != ST_PURGATORY, -(r["age_days"] or 0), r["id"]))
    return rows


def cmd_status(a, cfg: Config) -> int:
    when, err = resolve_when(a.as_of)
    if err:
        print(err, file=sys.stderr)
        return 1

    ledger = load_ledger(a.ledger)
    rows = _status_rows(ledger, cfg, when)
    other = sum(1 for e in ledger["entries"].values()
                if e["status"] in (ST_ACTIVE, ST_QUARANTINE))

    if a.json:
        print(json.dumps({"as_of": iso(when), "rows": rows,
                          "tracked_active_or_quarantine_only": other},
                         ensure_ascii=False, indent=2))
        return 0

    print(f"== CZYSCIEC: STATUS ({len(rows)} kandydatow, stan na {iso(when)}) ==")
    if not rows:
        print("  (rejestr pusty)")
    else:
        w = max(len(r["id"]) for r in rows)
        print(f"  {'id':<{w}}  {'wiek(d)':>7}  {'provenance':<10}  {'drills':>6}  "
              f"{'outline':>7}  {'status':<9}  wyrok-teraz")
        for r in rows:
            age = "-" if r["age_days"] is None else str(r["age_days"])
            print(f"  {r['id']:<{w}}  {age:>7}  {r['provenance']:<10}  {r['drills']:>6}  "
                  f"{r['outline_hits']:>7}  {r['status']:<9}  {r['verdict']} -- {r['reason']}")
    if other:
        print(f"\n  (+ {other} chunkow aktywnych/zaparkowanych ze zbieranym sygnalem "
              f"drilli/outline, poza zakresem wyroku -- nigdy nie przechodza przez --judge)")
    return 0


def cmd_judge(a, cfg: Config) -> int:
    when, err = resolve_when(a.as_of)
    if err:
        print(err, file=sys.stderr)
        return 1

    ledger = load_ledger(a.ledger)
    pending = [(cid, e) for cid, e in ledger["entries"].items() if e["status"] == ST_PURGATORY]
    verdicts = sorted(
        ((cid, entry, *judge_entry(entry, cfg, when)) for cid, entry in pending),
        key=lambda t: t[0])

    mode = "APPLY" if a.apply else "DRY-RUN"
    print(f"== CZYSCIEC: JUDGE [{mode}] ({len(verdicts)} kandydatow w czysccu, stan na {iso(when)}) ==")
    if not verdicts:
        print("  (brak kandydatow w czysccu)")

    counts: dict[str, int] = {}
    for cid, entry, verdict, reason in verdicts:
        counts[verdict] = counts.get(verdict, 0) + 1
        print(f"  {cid:<16} {verdict:<8} {reason}")
    if counts:
        print("  ----")
        for v, n in counts.items():
            print(f"  {v}: {n}")

    if not a.apply:
        print("\n  (dry-run -- dysk NIE zostal dotkniety; uzyj --judge --apply, zeby wykonac ruchy)")
        return 0

    if not verdicts:
        return 0

    backup_path = backup_ledger(a.ledger)
    print(f"\n  kopia rejestru przed apply: {backup_path}")

    applied, skipped = 0, 0
    for cid, entry, verdict, reason in verdicts:
        src = os.path.join(a.purgatory, cid + ".json")
        if verdict == V_PROMOTE:
            dst = os.path.join(a.chunks, cid + ".json")
            try:
                safe_move(src, dst)
            except (FileExistsError, OSError) as exc:
                print(f"  POMINIETO {cid}: {exc}", file=sys.stderr)
                skipped += 1
                continue
            entry["status"], entry["decided_at"], entry["verdict_reason"] = ST_PROMOTED, iso(when), reason
            applied += 1
        elif verdict == V_PARK:
            dst = os.path.join(a.quarantine, cid + ".json")
            try:
                safe_move(src, dst)
            except (FileExistsError, OSError) as exc:
                print(f"  POMINIETO {cid}: {exc}", file=sys.stderr)
                skipped += 1
                continue
            entry["status"], entry["decided_at"], entry["verdict_reason"] = ST_PARKED, iso(when), reason
            applied += 1
        elif verdict == V_EXTEND:
            entry["grace_period_days"] = entry.get("grace_period_days", cfg.grace_days) + cfg.extend_days
            entry["grace_extended"] = True
            applied += 1
        # V_WAIT / V_DECIDED: nic do zrobienia na dysku ani w rejestrze
        entry["last_updated"] = iso(now_utc())

    save_ledger(a.ledger, ledger)
    print(f"\n  zastosowano: {applied}, pominieto (kolizje id): {skipped}")
    return 0


# ------------------------------------------------------------------------ CLI

def build_argparser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Czysciec (purgatory) dla pamieci CBMS -- cykl zycia chunka przed chunks/")
    ap.add_argument("--chunks", default=DEF_CHUNKS)
    ap.add_argument("--quarantine", default=DEF_QUAR)
    ap.add_argument("--purgatory", default=DEF_PURGATORY)
    ap.add_argument("--ledger", default=DEF_LEDGER)

    ap.add_argument("--admit", metavar="PLIK_JSON_LUB_-")
    ap.add_argument("--provenance", choices=PROVENANCE_VALUES)
    ap.add_argument("--record-drill", metavar="ID")
    ap.add_argument("--record-outline", nargs="+", metavar="ID")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--judge", action="store_true")
    ap.add_argument("--apply", action="store_true",
                    help="wykonaj ruchy z --judge (domyslnie tylko podglad, dysk nietkniety)")
    ap.add_argument("--config", action="store_true")

    ap.add_argument("--grace-days", type=int, default=DEFAULT_GRACE_DAYS)
    ap.add_argument("--min-sessions", type=int, default=DEFAULT_MIN_SESSIONS)
    ap.add_argument("--extend-days", type=int, default=DEFAULT_EXTEND_DAYS)
    ap.add_argument("--promote-drills", type=int, default=DEFAULT_PROMOTE_DRILLS)
    ap.add_argument("--cloud-promote-drills", type=int, default=DEFAULT_CLOUD_PROMOTE_DRILLS)
    ap.add_argument("--as-of", metavar="ISO_TIMESTAMP",
                    help="udawaj, ze 'teraz' to ten czas -- tylko podglad w --status/--judge, "
                         "nigdy nie jest zapisywane jako prawdziwy timestamp")

    ap.add_argument("--json", action="store_true")
    return ap


def main(argv=None) -> int:
    a = build_argparser().parse_args(argv)
    cfg = Config.from_args(a)

    if a.apply and not a.judge:
        print("UWAGA: --apply bez --judge nie ma zadnego efektu", file=sys.stderr)

    if a.admit is not None:
        return cmd_admit(a)
    if a.record_drill:
        return cmd_record_drill(a)
    if a.record_outline:
        return cmd_record_outline(a)
    if a.judge:
        return cmd_judge(a, cfg)
    if a.config:
        return cmd_config(cfg, a)
    # domyslnie: status (bezpieczne, tylko odczyt -- tak jak w cbms_outline.py/doctor.py)
    return cmd_status(a, cfg)


if __name__ == "__main__":
    sys.exit(main())
