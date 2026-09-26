import unittest
from services.terminology import analyze_query

class TestTerminologyAudit(unittest.TestCase):

    def test_all_18_products_detected(self):
        queries = [
            ("Packaged Drinking Water", "P001"),
            ("Sandals and Slippers", "P002"),
            ("Industrial Safety Helmet", "P003"),
            ("LPG Gas Stove", "P004"),
            ("PVC Insulated Cable", "P005"),
            ("RO Water Treatment System", "P006"),
            ("Storage Water Heater", "P007"),
            ("Paver Blocks", "P008"),
            ("Toys", "P009"),
            ("LPG/CNG Valves", "P010"),
            ("Single-Phase Induction Motor", "P011"),
            ("Electric Ceiling Fan", "P012"),
            ("Cattle Feed", "P013"),
            ("Distribution Transformer", "P014"),
            ("Reinforcement Steel Bars", "P015"),
            ("Cement", "P016"),
            ("Solar Water Pump", "P017"),
            ("IT Equipment", "P018")
        ]
        for query, expected_id in queries:
            with self.subTest(query=query):
                res = analyze_query(query)
                self.assertNotEqual(res["status"], "unsupported", f"Failed for {query}")
                self.assertEqual(res["products"][0]["product_id"], expected_id)

    def test_synonyms_and_regional(self):
        self.assertEqual(analyze_query("chappals")["products"][0]["product_id"], "P002")
        self.assertEqual(analyze_query("TMT bars")["products"][0]["product_id"], "P015")

    def test_minor_spelling_mistakes(self):
        res = analyze_query("geiser")
        self.assertEqual(res["products"][0]["product_id"], "P007")

    def test_descriptive_phrases(self):
        res = analyze_query("machine that heats water and stores it")
        self.assertEqual(res["products"][0]["product_id"], "P007")
        self.assertLess(res["products"][0]["heuristic_confidence"], 0.80) 

    def test_abbreviations(self):
        self.assertEqual(analyze_query("RO purifier")["products"][0]["product_id"], "P006")
        self.assertEqual(analyze_query("OPC")["products"][0]["product_id"], "P016")

    def test_plural_forms(self):
        res = analyze_query("helmets")
        self.assertEqual(res["products"][0]["product_id"], "P003")

    def test_generic_terms_ambiguity(self):
        # water heater
        res = analyze_query("water heater")
        self.assertEqual(res["status"], "needs_clarification")
        self.assertIn("storage water heater or an instant water heater", res["clarification"]["question"])
        
        # electric water heater
        res2 = analyze_query("electric water heater")
        self.assertEqual(res2["status"], "needs_clarification")
        self.assertIn("storage water heater or an instant water heater", res2["clarification"]["question"])
        
        # geyser
        res3 = analyze_query("geyser")
        self.assertEqual(res3["status"], "supported")

        # instant water heater
        res4 = analyze_query("instant water heater")
        self.assertEqual(res4["status"], "unsupported") 

        # helmet
        res5 = analyze_query("helmet")
        self.assertEqual(res5["status"], "needs_clarification")
        self.assertIn("industrial/workplace use or motorcycle/road use", res5["clarification"]["question"])
        
        # motor
        res6 = analyze_query("motor")
        self.assertEqual(res6["status"], "needs_clarification")
        self.assertIn("single-phase induction motor or a different type", res6["clarification"]["question"])
        
        # transformer
        res7 = analyze_query("transformer")
        self.assertEqual(res7["status"], "needs_clarification")
        self.assertIn("distribution transformer or another type", res6["clarification"]["question"] if False else res7["clarification"]["question"])
        
        # electronic equipment / IT equipment
        res8 = analyze_query("electronic equipment")
        self.assertEqual(res8["status"], "needs_clarification")
        res9 = analyze_query("IT equipment")
        self.assertEqual(res9["status"], "needs_clarification")

    def test_specific_terms_supported(self):
        res = analyze_query("industrial safety helmet")
        self.assertEqual(res["status"], "supported")
        
        res2 = analyze_query("single-phase induction motor")
        self.assertEqual(res2["status"], "supported")
        
        res3 = analyze_query("distribution transformer")
        self.assertEqual(res3["status"], "supported")

    def test_already_provided_attributes_duplicate_prevention(self):
        res = analyze_query("Storage water heater for my home, 15 litre.")
        self.assertEqual(res["status"], "supported")
        self.assertFalse(res["clarification"]["needed"])
        self.assertIn("storage", res["products"][0]["extracted_attributes"]["storage/instant type"])

    def test_multiple_product_attribute_targeting(self):
        res = analyze_query("LPG gas stove and CNG valve")
        self.assertEqual(res["status"], "multiple_products")
        
        ids = [p["product_id"] for p in res["products"]]
        self.assertIn("P004", ids)
        self.assertIn("P010", ids)
        
        p004_attrs = next(p["extracted_attributes"] for p in res["products"] if p["product_id"] == "P004")
        p010_attrs = next(p["extracted_attributes"] for p in res["products"] if p["product_id"] == "P010")
        self.assertIn("lpg", p004_attrs.get("fuel type", []))
        self.assertIn("cng", p010_attrs.get("gas type", []))
        
        self.assertFalse(res["clarification"]["needed"])

    def test_conflicting_attributes_same_product(self):
        res = analyze_query("LPG CNG valve")
        self.assertEqual(res["status"], "needs_clarification")
        self.assertIn("cng and lpg", res["clarification"]["question"].lower())

    def test_cng_gas_stove_unsupported(self):
        res = analyze_query("CNG gas stove")
        self.assertEqual(res["status"], "unsupported")

    def test_unsupported_queries(self):
        res = analyze_query("smartphone")
        self.assertEqual(res["status"], "unsupported")

    def test_follow_up_query_reanalysis(self):
        initial = analyze_query("helmet")
        self.assertEqual(initial["status"], "needs_clarification")
        
        follow_up = analyze_query("industrial helmet")
        self.assertEqual(follow_up["status"], "supported")
        self.assertFalse(follow_up["clarification"]["needed"])

    def test_heuristic_confidence_relative_scoring(self):
        res_exact = analyze_query("LPG gas stove")
        res_ambig = analyze_query("stove")
        self.assertGreater(res_exact["products"][0]["heuristic_confidence"], res_ambig["products"][0]["heuristic_confidence"])

        res_syn = analyze_query("industrial safety helmet")
        res_kw = analyze_query("helmet")
        self.assertGreater(res_syn["products"][0]["heuristic_confidence"], res_kw["products"][0]["heuristic_confidence"])
        
        res_conflict = analyze_query("LPG CNG valve")
        res_clean = analyze_query("LPG valve")
        self.assertGreater(res_clean["products"][0]["heuristic_confidence"], res_conflict["products"][0]["heuristic_confidence"])
        
    def test_negative_generic_cases(self):
        self.assertEqual(analyze_query("stove")["status"], "needs_clarification")
        self.assertEqual(analyze_query("gas stove")["status"], "needs_clarification")
        self.assertEqual(analyze_query("LPG gas stove")["status"], "supported")
        
        self.assertEqual(analyze_query("cable")["status"], "needs_clarification")
        self.assertEqual(analyze_query("electric cable")["status"], "needs_clarification")
        self.assertEqual(analyze_query("PVC insulated cable")["status"], "supported")
        
        self.assertEqual(analyze_query("water purifier")["status"], "needs_clarification")
        self.assertEqual(analyze_query("RO purifier")["status"], "supported")
        
        self.assertEqual(analyze_query("electric motor")["status"], "needs_clarification")
        self.assertEqual(analyze_query("AC motor")["status"], "needs_clarification")
        self.assertEqual(analyze_query("induction motor")["status"], "needs_clarification")
        
        self.assertEqual(analyze_query("animal feed")["status"], "needs_clarification")
        self.assertEqual(analyze_query("cattle feed")["status"], "supported")
        
        self.assertEqual(analyze_query("power transformer")["status"], "needs_clarification")
        
        self.assertEqual(analyze_query("steel bars")["status"], "needs_clarification")
        self.assertEqual(analyze_query("reinforcement steel bars")["status"], "supported")

    # --- NEW ADVANCED EDGE CASE TESTS ---

    def test_extreme_punctuation(self):
        # Should strip heavy punctuation and still identify the geyser correctly
        res = analyze_query("!!!geyser???!!!")
        self.assertEqual(res["status"], "supported")
        self.assertEqual(res["products"][0]["product_id"], "P007")

    def test_long_noisy_query(self):
        # Should ignore stop phrases and noise, extracting "industrial" for "helmet"
        res = analyze_query("Hello I am looking for a very good quality industrial safety helmet for my construction workers please")
        self.assertEqual(res["status"], "supported")
        self.assertEqual(res["products"][0]["product_id"], "P003")
        self.assertIn("industrial", res["products"][0]["extracted_attributes"]["intended use"])

    def test_contradiction_toys(self):
        # P009 is children's toys. "dog toy" or "pet toy" should contradict the child attribute and fall to unsupported.
        res = analyze_query("dog toy")
        self.assertEqual(res["status"], "unsupported")

    def test_contradiction_cable(self):
        # P005 is PVC Insulated Power/Electric Cable. "hdmi cable" should trigger the data cable contradiction.
        res = analyze_query("hdmi cable")
        self.assertEqual(res["status"], "unsupported")

    def test_typos_expanded(self):
        # Verifying the typo mapping logic properly catches common Indian phonetic spellings
        self.assertEqual(analyze_query("cment")["products"][0]["product_id"], "P016")
        self.assertEqual(analyze_query("slipers")["products"][0]["product_id"], "P002")

if __name__ == '__main__':
    unittest.main()