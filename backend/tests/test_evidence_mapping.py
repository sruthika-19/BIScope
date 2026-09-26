from services.evidence_mapping import map_document_to_requirements
from data.detailed_requirements import DETAILED_REQUIREMENTS

p001_reqs = DETAILED_REQUIREMENTS["requirements"]

def print_results(title, results):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)

    for result in results:
        print(
            result["requirement_id"],
            "|",
            result["requirement_description"],
            "|",
            result["status"],
            "| matched:",
            result["matched_terms"],
            "| missing:",
            result["missing_terms"]
        )

doc_1 = """
This is a microbiological test report confirming E. Coli
and Coliform bacteria are absent.
"""

results_1 = map_document_to_requirements(p001_reqs, doc_1)
print_results("TEST 1 - Microbiological Evidence", results_1)

doc_2 = """
Product specification for packaged drinking water.

Microbiological test report attached.

Chemical test report attached.

Packaging specification attached.

Product label attached.
"""

results_2 = map_document_to_requirements(p001_reqs, doc_2)
print_results("TEST 2 - Multiple Evidence Sections", results_2)

doc_3 = ""

results_3 = map_document_to_requirements(p001_reqs, doc_3)
print_results("TEST 3 - Empty Document", results_3)
