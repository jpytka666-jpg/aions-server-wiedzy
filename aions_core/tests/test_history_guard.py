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
        self.assertEqual(history_guard.classify("Warlock")["history_status"],
                         "UNKNOWN_NOT_PROVEN_NEW")

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

if __name__=="__main__":
    unittest.main()


