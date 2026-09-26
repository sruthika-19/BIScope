import sqlite3
from pathlib import Path
from typing import Dict, Any

# Dynamically resolve path to the database folder in this specific project
DB_PATH = Path(__file__).resolve().parent.parent / "database" / "biscope.db"

def search_standards(product_id: str, attributes: dict) -> Dict[str, Any]:
    """
    Retrieves product and standard information directly from the SQLite database.
    Preserves all database statuses exactly as they appear.
    """
    if not DB_PATH.exists():
        return {
            "status": "DB_NOT_FOUND",
            "message": f"Database file not found at {DB_PATH}",
            "product_id": product_id,
            "extracted_attributes": attributes,
            "data": None
        }

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # 1. Look up product, ignoring rows with NULL product_code
        cursor.execute(
            "SELECT * FROM products WHERE product_code = ? AND product_code IS NOT NULL",
            (product_id,)
        )
        product_row = cursor.fetchone()

        if not product_row:
            conn.close()
            return {
                "status": "NOT_FOUND",
                "message": f"No verified product found in database for ID: {product_id}",
                "product_id": product_id,
                "extracted_attributes": attributes,
                "data": None
            }

        # 2. Look up mapped standards
        query = """
            SELECT s.* 
            FROM standards s
            JOIN product_standards ps ON s.id = ps.standard_id
            JOIN products p ON ps.product_id = p.id
            WHERE p.product_code = ?
        """
        cursor.execute(query, (product_id,))
        standard_rows = cursor.fetchall()

        if not standard_rows:
            conn.close()
            return {
                "status": "NO_STANDARD_MAPPING",
                "message": f"Product {product_id} exists, but no standard mapping is currently available.",
                "product_id": product_id,
                "extracted_attributes": attributes,
                "data": {
                    "product": dict(product_row),
                    "standards": []
                }
            }

        standards_list = [dict(row) for row in standard_rows]
        conn.close()

        return {
            "status": "DATABASE",
            "message": f"Successfully retrieved database records for {product_id}.",
            "product_id": product_id,
            "extracted_attributes": attributes,
            "data": {
                "product": dict(product_row),
                "standards": standards_list
            }
        }

    except sqlite3.Error as e:
        return {
            "status": "DB_ERROR",
            "message": f"SQLite Database Error: {str(e)}",
            "product_id": product_id,
            "extracted_attributes": attributes,
            "data": None
        }