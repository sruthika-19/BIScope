import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional

# Dynamically resolve path to the database folder
DB_PATH = Path(__file__).resolve().parent.parent / "database" / "biscope.db"

def search_database(query: str) -> List[Dict[str, Any]]:
    """
    Searches the SQLite database for products and their candidate standards.
    Matches against product ID, name, search terms, and normalized terms.
    """
    if not DB_PATH.exists() or not query.strip():
        return []

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Use LIKE for partial matching
        search_pattern = f"%{query.strip()}%"

        # Join products and standards, filtering out NULL product codes
        sql = """
            SELECT 
                p.product_code as product_id,
                p.name as product_name,
                p.normalized_term,
                s.id as standard_id,
                s.standard_number,
                s.title,
                s.edition_year,
                s.status,
                s.qco_info
            FROM products p
            JOIN product_standards ps ON p.id = ps.product_id
            JOIN standards s ON ps.standard_id = s.id
            WHERE p.product_code IS NOT NULL
              AND (
                  p.name LIKE ? OR 
                  p.search_terms LIKE ? OR 
                  p.normalized_term LIKE ? OR 
                  p.product_code LIKE ?
              )
        """
        
        cursor.execute(sql, (search_pattern, search_pattern, search_pattern, search_pattern))
        rows = cursor.fetchall()
        
        results = [dict(row) for row in rows]
        conn.close()
        
        return results

    except sqlite3.Error as e:
        print(f"Database error during search: {e}")
        return []

def get_standard_details(standard_id: int) -> Optional[Dict[str, Any]]:
    """
    Retrieves the complete details for a specific standard ID from the database.
    Returns None if the standard ID does not exist.
    """
    if not DB_PATH.exists():
        return None

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM standards WHERE id = ?", (standard_id,))
        row = cursor.fetchone()
        
        conn.close()

        if row:
            return dict(row)
        return None

    except sqlite3.Error as e:
        print(f"Database error retrieving standard details: {e}")
        return None

def build_standard_explanation(product_id: str, standard_id: int) -> Optional[Dict[str, Any]]:
    """
    Deterministically explains why a standard is associated with a product
    based ONLY on the SQLite product_standards mapping table.
    """
    if not DB_PATH.exists():
        return None

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Check product
        cursor.execute("SELECT * FROM products WHERE product_code = ?", (product_id,))
        product = cursor.fetchone()
        if not product:
            conn.close()
            return None

        # Check standard
        cursor.execute("SELECT * FROM standards WHERE id = ?", (standard_id,))
        standard = cursor.fetchone()
        if not standard:
            conn.close()
            return None

        # Check relationship
        cursor.execute(
            "SELECT * FROM product_standards WHERE product_id = ? AND standard_id = ?", 
            (product['id'], standard['id'])
        )
        link = cursor.fetchone()
        conn.close()

        if link:
            return {
                "product_id": product_id,
                "standard_id": standard_id,
                "standard_number": standard["standard_number"],
                "relationship": "candidate",
                "matches": [
                    f"The standard {standard['standard_number']} is linked to this product in the BIScope candidate-standard dataset."
                ],
                "mismatches": [],
                "unknown": [
                    "Technical applicability requires verification against the official BIS standard."
                ],
                "explanation": f"{standard['standard_number']} is listed as a candidate standard for {product['name']} in the current BIScope dataset. Technical applicability and compliance still require verification."
            }
        else:
            return {
                "product_id": product_id,
                "standard_id": standard_id,
                "standard_number": standard["standard_number"],
                "relationship": "unlinked",
                "matches": [],
                "mismatches": [
                    "No direct mapping exists in the current BIScope database between this product and standard."
                ],
                "unknown": [
                    "Technical applicability requires verification against the official BIS standard."
                ],
                "explanation": f"{standard['standard_number']} is not currently linked as a candidate standard for {product['name']} in the database."
            }

    except sqlite3.Error as e:
        print(f"Database error in build_standard_explanation: {e}")
        return None


def build_alternative_explanation(product_id: str, selected_standard_id: int) -> Optional[Dict[str, Any]]:
    """
    Deterministically retrieves alternative standards mapped to the same product.
    """
    if not DB_PATH.exists():
        return None

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT id, name FROM products WHERE product_code = ?", (product_id,))
        product = cursor.fetchone()
        if not product:
            conn.close()
            return None

        # Find alternatives linked to the same product but excluding the selected standard
        query = """
            SELECT s.id, s.standard_number, s.title
            FROM standards s
            JOIN product_standards ps ON s.id = ps.standard_id
            WHERE ps.product_id = ? AND s.id != ?
        """
        cursor.execute(query, (product['id'], selected_standard_id))
        rows = cursor.fetchall()
        conn.close()

        alternatives = []
        for r in rows:
            alternatives.append({
                "standard_id": r["id"],
                "standard_number": r["standard_number"],
                "title": r["title"],
                "relationship": "alternative_candidate",
                "matches": [
                    f"Standard {r['standard_number']} is also linked to {product['name']} in the database."
                ],
                "mismatches": [],
                "unknown": [
                    "Technical differences and specific applicability between this alternative and the selected standard require manual verification."
                ],
                "explanation": f"{r['standard_number']} is an alternative candidate standard for {product['name']}. Applicability is currently 'To be verified'."
            })

        return {
            "product_id": product_id,
            "selected_standard_id": selected_standard_id,
            "alternatives": alternatives
        }

    except sqlite3.Error as e:
        print(f"Database error in build_alternative_explanation: {e}")
        return None