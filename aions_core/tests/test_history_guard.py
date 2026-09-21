from __future__ import annotations
import json, sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"aions_core"/"server"))
import history_guard

class HistoryGuardTests(unittest.TestCase):
    def test_ledger_valid(self):
        self.assertEqual(history_guard.validate(),[])
    def test_r2_is_known_old_defect(self):
        r=history_guard.classify("R2_opakowanie_syntezy")
        self.assertEqual(r["history_status"],"KNOWN")
        self.assertEqual(r["id"],"CBMS_SYNTH_TEMPLATE")
        self.assertIn("2025-11",r["known_since"])
    def test_pocket_qc_is_not_new(self):
        self.assertEqual(history_guard.classify("Pocket QC")["id"],"POCKET_QC")
    def test_crla_is_not_new(self):
        self.assertEqual(history_guard.classify("CRLA tournament")["id"],"CRLA")
    def test_unknown_never_becomes_new(self):
        r=history_guard.classify("zyxwvu totally unseen mechanism 94821")
        self.assertEqual(r["history_status"],"UNKNOWN_NOT_PROVEN_NEW")
    def test_every_item_has_evidence(self):
        d=history_guard.load_ledger()
        for sec in ("mechanisms","defects","decisions"):
            for item in d[sec]:
                self.assertTrue(item.get("evidence"),item["id"])

class AuditRegressions20260921(unittest.TestCase):
    """
    Testy dopiete do trzech bledow znalezionych w audycie commita 1617f9d.
    Kazdy z nich PRZECHODZIL przed poprawka bledu i MUSI padac po jej cofnieciu.
    """

    POSPOLITE = ["pocket", "system", "memory", "gate", "new", "defect", "error", "qc"]

    def test_pojedyncze_pospolite_slowo_nie_jest_dowodem(self):
        # Przed poprawka: "system" -> KNOWN CBMS (80), "gate" -> KNOWN POCKET_QC (80),
        # "new" -> KNOWN NOVELTY_NEEDS_HISTORY (80). Bramka stemplowala "znane"
        # na wszystkim, co zawieralo pospolite slowo. To odwraca jej sens.
        for slowo in self.POSPOLITE:
            r = history_guard.classify(slowo)
            self.assertEqual(r["history_status"], "UNKNOWN_NOT_PROVEN_NEW",
                             f"{slowo!r} nie moze sam z siebie znaczyc KNOWN, dostal {r.get('id')}")

    def test_jedno_slowo_moze_trafic_tylko_dokladnie_w_identyfikator(self):
        self.assertEqual(history_guard.classify("CRLA")["id"], "CRLA")
        r = history_guard.classify("Warlock")
        self.assertEqual(r["history_status"], "KNOWN")
        self.assertEqual(r["id"], "WARLOCK")
        self.assertIn("RUNTIME_ON_CANONICAL_SERVER_WIEDZY_NOT_VERIFIED", r["status"])

    def test_podkreslnik_i_spacja_daja_ten_sam_werdykt(self):
        # Przed poprawka maszynowy "R2_opakowanie_syntezy" trafial w 100,
        # a ludzki "R2 opakowanie syntezy" wracal jako UNKNOWN. Ta sama rzecz.
        a = history_guard.classify("R2_opakowanie_syntezy")
        b = history_guard.classify("R2 opakowanie syntezy")
        self.assertEqual(a["history_status"], "KNOWN")
        self.assertEqual(b["history_status"], "KNOWN")
        self.assertEqual(a["id"], b["id"])
        self.assertEqual(a["match_score"], b["match_score"])


    def test_qc_text_klasyfikuje_tekst_a_nie_werdykt(self):
        # BLAD W MOIM WLASNYM PIERWSZYM PODEJSCIU: sprawdzalem ZRODLO funkcji
        # przez inspect.getsource i asercja padla na wlasnym komentarzu, ktory
        # cytowal zly kod. Test czytajacy tekst zrodla nie testuje zachowania.
        # Ten test wola funkcje i patrzy na wynik.
        import os, tempfile, pocket_qc
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["CBMS_BASE_DIR"] = tmp          # log idzie do smietnika, nie do repo
            try:
                mem = ROOT / "aions_core" / "memory"
                # Tekst niosacy ZNANY kod bramki. Stary kod klasyfikowal slowo
                # werdyktu ("PASS"/"RETRY"/"FAIL") i zwracal tu UNKNOWN.
                znany = pocket_qc.qc_text("R2_opakowanie_syntezy", mem)
                self.assertEqual(znany["history"]["history_status"], "KNOWN")
                self.assertEqual(znany["history"]["id"], "CBMS_SYNTH_TEMPLATE")
                # Tekst bez zadnego zwiazku z ksiega musi zostac UNKNOWN.
                obcy = pocket_qc.qc_text("zyxwvu totally unseen 94821", mem)
                self.assertEqual(obcy["history"]["history_status"],
                                 "UNKNOWN_NOT_PROVEN_NEW")
            finally:
                os.environ.pop("CBMS_BASE_DIR", None)
        # Samo slowo werdyktu nie jest faktem historycznym.
        for werdykt in ("PASS", "RETRY", "FAIL"):
            self.assertEqual(history_guard.classify(werdykt)["history_status"],
                             "UNKNOWN_NOT_PROVEN_NEW")
    def test_unknown_niesie_slabe_trafienia_zamiast_je_gubic(self):
        r = history_guard.classify("memory")
        self.assertEqual(r["history_status"], "UNKNOWN_NOT_PROVEN_NEW")
        self.assertIn("possible_matches", r)

class SemanticEvidenceAudit20260921(unittest.TestCase):
    def test_every_record_has_semantic_evidence_contract(self):
        d = history_guard.load_ledger()
        for sec in ("mechanisms", "defects", "decisions"):
            for item in d[sec]:
                self.assertTrue(item.get("evidence_checks"), item["id"])

    def test_semantic_validator_bites_when_anchor_is_false(self):
        import tempfile
        d = history_guard.load_ledger()
        victim = next(x for x in d["mechanisms"] if x["id"] == "CBMS")
        victim["evidence_checks"][0]["contains_all"].append("THIS_ANCHOR_MUST_NOT_EXIST_94821")
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "ledger.json"
            p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
            errs = history_guard.validate(p)
        self.assertTrue(any("THIS_ANCHOR_MUST_NOT_EXIST_94821" in e for e in errs), errs)

    def test_warlock_is_known_but_not_claimed_running(self):
        r = history_guard.classify("Warlock")
        self.assertEqual(r["id"], "WARLOCK")
        self.assertIn("RUNTIME_ON_CANONICAL_SERVER_WIEDZY_NOT_VERIFIED", r["status"])

    def test_warlock_rename_corruption_is_known_defect(self):
        r = history_guard.classify("warlock rename corruption")
        self.assertEqual(r["history_status"], "KNOWN")
        self.assertEqual(r["id"], "WARLOCK_RENAME_DOC_CORRUPTION")

class AuditOf4f6496e(unittest.TestCase):
    """
    Dziura znaleziona w audycie commita 4f6496e: kontrakt dowodowy BEZ zadnej
    kotwicy przechodzil walidacje bez bledu, czyli cicho wracal do starego
    zachowania "plik istnieje". Zmierzone przed poprawka: usuniecie
    contains_all i contains_any z CBMS_SYNTH_TEMPLATE dawalo ERRORS=0.
    """

    def _ledger_bez_kotwic(self, tmpdir):
        import json, copy
        d = copy.deepcopy(history_guard.load_ledger())
        for rec in d["defects"]:
            if rec["id"] == "CBMS_SYNTH_TEMPLATE":
                rec["evidence_checks"][0].pop("contains_all", None)
                rec["evidence_checks"][0].pop("contains_any", None)
        p = Path(tmpdir) / "ledger.json"
        p.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
        return p

    def test_kontrakt_bez_kotwic_jest_bledem(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            errs = history_guard.validate(self._ledger_bez_kotwic(tmp))
            self.assertTrue(any("no anchors" in e for e in errs),
                            f"kontrakt bez kotwic musi byc bledem, dostalem: {errs}")

    def test_prawdziwa_ksiega_nadal_czysta(self):
        self.assertEqual(history_guard.validate(), [])


if __name__ == "__main__":
    unittest.main()

