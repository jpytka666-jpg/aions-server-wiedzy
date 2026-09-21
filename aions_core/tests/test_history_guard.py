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
if __name__=="__main__":
    unittest.main()
