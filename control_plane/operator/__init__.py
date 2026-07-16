"""AIONS Control Plane — Operator package.

Petla operatora: observe -> diagnose -> act -> verify -> learn.

AIONS siedzi przed poligonem Linux jak czlowiek-admin: obserwuje stan przez
istniejace skille odczytowe, diagnozuje odchylenia wg prostych regul,
naprawia niskoryzykowne przypadki przez istniejace skille akcji (bramka
ryzyka silnika control_plane.skills.gate decyduje o dopuszczeniu kazdego
uruchomienia), weryfikuje efekt ponownym observe i zapisuje kazdy incydent
do dziennika uczenia (runtime/state/operator_incidents.jsonl).

Nowy pakiet — nie modyfikuje istniejacego silnika control_plane/skills/*.
"""
from .loop import observe, diagnose, act, verify, learn, run_cycle, main  # noqa: F401

__all__ = ["observe", "diagnose", "act", "verify", "learn", "run_cycle", "main"]
