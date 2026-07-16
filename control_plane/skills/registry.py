"""AIONS Skill Engine — plug-and-play object registry.

Drop a folder into skills_lib/ with a skill.json (+ handler.py for executable
skills) and it is discovered automatically. No core code changes required.
"""
from __future__ import annotations
import importlib.util
import os
from pathlib import Path

from . import schema

REPO = Path(__file__).resolve().parents[2]
SKILLS_DIR = REPO / "skills_lib"


# v1.1 (backlog): minimalna normalizacja tokenow bez zewnetrznych bibliotek
# (Porter/Snowball to overkill dla tego silnika). Cel: "services" ma trafiac
# w tag "service", PL "uslugi" ma trafiac w tag "usluga", a stare zapytania
# ("dysk", "memory") maja dzialac dokladnie tak jak przed zmiana.
#
# Uwaga o regule EN "es": literalne "kazde slowo konczace sie na es -> utnij
# es" nadstemowaloby "services" do "servic", podczas gdy samo "service" (bez
# sufiksu mnogiej liczby, konczy sie na "ce" a nie "es") zostaloby bez zmian
# -- oba zapytania NIE trafilyby w ten sam token. Dlatego "es" jest ucinane
# tylko po literze syczacej (s/x/z/h, tj. koncowki -ses/-xes/-zes/-ches/-shes,
# np. "boxes"->"box", "churches"->"church"), a zwykle "-s" (np. "services"
# ->"service") leci przez ogolna regule "s" (dlugosc > 3). To jest jedyne
# swiadome odejscie od literalnego brzmienia zadania -- bez niego test
# "services" -> tag "service" nie przechodzi.
_EN_SUFFIXES_SIBILANT = ("s", "x", "z", "h")
_PL_SUFFIXES = ("ów", "ami", "ach", "om", "ie", "y", "i", "a", "e")


def _stem_en(word: str) -> str:
    if len(word) > 4 and word.endswith("ies"):
        return word[:-3] + "y"
    if len(word) > 4 and word.endswith("es") and word[-3] in _EN_SUFFIXES_SIBILANT:
        return word[:-2]
    if len(word) > 3 and word.endswith("s"):
        return word[:-1]
    return word


def _stem_pl(word: str) -> str:
    if len(word) <= 4:
        return word
    for suf in _PL_SUFFIXES:
        if word.endswith(suf):
            return word[: -len(suf)]
    return word


def _stem_token(word: str) -> str:
    """Lowercase + prosty EN/PL stemmer. Stosowany identycznie do tokenow
    indeksu (blob/tags) i zapytania -- wazna jest tylko spojnosc, nie
    lingwistyczna poprawnosc."""
    w = word.lower()
    w = _stem_en(w)
    w = _stem_pl(w)
    return w


def _stem_set(tokens) -> set:
    return {_stem_token(t) for t in tokens if t}


class SkillRegistry:
    def __init__(self, skills_dir=SKILLS_DIR):
        self.skills_dir = Path(skills_dir)
        self.objects = {}
        self.handlers = {}
        self.errors = []

    def discover(self):
        self.objects.clear()
        self.handlers.clear()
        self.errors.clear()
        if not self.skills_dir.exists():
            return {"loaded": 0, "errors": ["skills_lib not found"]}
        for d in sorted(self.skills_dir.iterdir()):
            sj = d / "skill.json"
            if not sj.exists():
                continue
            try:
                o = schema.load(str(sj))
                errs = schema.validate(o)
                if errs:
                    self.errors.append(f"{d.name}: {errs}")
                    continue
                self.objects[o.id] = o
                if o.type in schema.EXECUTABLE and o.handler:
                    self._load_handler(o)
            except Exception as e:
                self.errors.append(f"{d.name}: {e}")
        return {"loaded": len(self.objects), "errors": self.errors}

    def _load_handler(self, o):
        mod_name, fn_name = o.handler.split(":")
        mod_path = Path(o.source_dir) / f"{mod_name}.py"
        spec = importlib.util.spec_from_file_location(
            f"skill_{o.id}_{mod_name}".replace(".", "_"), str(mod_path)
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        self.handlers[o.id] = getattr(mod, fn_name)

    def get(self, oid):
        return self.objects.get(oid)

    def handler(self, oid):
        return self.handlers.get(oid)

    def list_ids(self):
        return list(self.objects.keys())

    def search(self, query, top_k=5, types=None):
        """Lexical retrieval over ALL object types (semantic upsert is optional,
        added later against a dedicated Chroma collection). Retriever is
        type-agnostic: it just ranks the best-matching objects.

        v1.1 (backlog): minimalny bezbiblioteczny stemmer (_stem_token) jest
        stosowany IDENTYCZNIE do tokenow query, blob (id+name+description+tags)
        i samych tagow, zeby np. zapytanie "services" trafialo w tag "service"
        albo PL "uslugi" w tag "usluga". Sam scoring (overlap + 0.5*taghit) jest
        bez zmian -- zmienia sie tylko to, co wchodzi do zbiorow tokenow."""
        q = _stem_set(query.lower().replace(",", " ").replace(".", " ").split())
        scored = []
        for o in self.objects.values():
            if types and o.type not in types:
                continue
            blob = _stem_set(o.blob().replace(".", " ").split())
            overlap = len(q & blob)
            taghit = len(q & _stem_set(" ".join(o.tags).lower().split()))
            score = overlap + 0.5 * taghit
            if score > 0:
                scored.append((round(score, 2), o.id, o.type))
        scored.sort(reverse=True)
        return [{"id": i, "type": t, "score": s} for s, i, t in scored[:top_k]]
