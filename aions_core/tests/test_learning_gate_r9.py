import sys, unittest
sys.path.insert(0, r"E:\server wiedzy\aions_core\server")
from cbms_memory import CBMSMemory

def gate(t):
    return CBMSMemory.learning_gate(CBMSMemory.__new__(CBMSMemory), t)

class R9ModelMowiBrak(unittest.TestCase):
    def test_odrzuca_uczciwe_nie_wiem(self):
        for t in [
            "Blok nie zawiera informacji na temat dzialania bramki zapisu learning_gate w CBMS.",
            "Podane bloki nie zawieraja odpowiedzi na to pytanie, opisane sa tylko mechanizmy odmowy.",
            "Brak informacji o Korean keys w dostarczonych fragmentach wiedzy.",
            "The provided blocks do not contain information about the fan controller on Darkstar.",
            "There is no information in the context about Warlock or its runtime.",
        ]:
            ok, why = gate(t)
            self.assertFalse(ok, t); self.assertEqual(why, "R9_model_mowi_brak", t)
    def test_przepuszcza_prawdziwa_odpowiedz_z_cytatem_brak_danych(self):
        t = ("Pipeline CBMS zaczyna sie od przetworzenia zapytania w CBMSMemory.cbms_think(). "
             "Jesli brakuje chunkow (min_hits), glowny guardrail w cbms_direct_server.py natychmiast "
             "zwraca NIE WIEM / BRAK DANYCH CBMS-KR i blokuje dalsze przetwarzanie.")
        ok, why = gate(t)
        self.assertTrue(ok, why)
    def test_szablon_nadal_r2(self):
        ok, why = gate("Na podstawie 15 fragmentów wiedzy:\n\nKluczowe informacje:\n1. cos")
        self.assertFalse(ok); self.assertEqual(why, "R2_opakowanie_syntezy")

class ZapisPoTresci(unittest.TestCase):
    def test_pytanie_nie_ma_glosu(self):
        m = CBMSMemory.__new__(CBMSMemory)
        self.assertTrue(m._should_create_new_chunk("krotkie?", "x" * 40))
        self.assertFalse(m._should_create_new_chunk("bardzo dlugie pytanie " * 5 + "how new", ""))
        self.assertFalse(m._should_create_new_chunk("bardzo dlugie pytanie " * 5, "za krotko"))

if __name__ == "__main__":
    unittest.main()
