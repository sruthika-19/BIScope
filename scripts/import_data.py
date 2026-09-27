import os
import sqlite3
import json
import logging

# Configure paths relative to the script location
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DB_DIR = os.path.join(BASE_DIR, 'backend', 'database')
DB_PATH = os.path.join(DB_DIR, 'biscope.db')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize_database():
    """Creates the database schema and imports data from existing local sources."""
    os.makedirs(DB_DIR, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Create the THREE required tables safely
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_code TEXT UNIQUE,
            product_name TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS standards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            standard_number TEXT UNIQUE,
            year TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS product_standards (
            product_id INTEGER,
            standard_id INTEGER,
            FOREIGN KEY(product_id) REFERENCES products(id),
            FOREIGN KEY(standard_id) REFERENCES standards(id),
            UNIQUE(product_id, standard_id)
        )
    ''')

    # 2. Extract authoritative data to prevent duplication
    json_path = os.path.join(BASE_DIR, 'backend', 'data', 'detailed_requirements.json')

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 3. Insert records idempotently (IGNORE duplicates on re-runs)
        for product_code, details in data.items():
            product_name = product_code.replace('_', ' ').title()

            # Insert Product
            cursor.execute('''
                INSERT OR IGNORE INTO products (product_code, product_name)
                VALUES (?, ?)
            ''', (product_code, product_name))

            # Retrieve the product ID
            cursor.execute('SELECT id FROM products WHERE product_code = ?', (product_code,))
            p_row = cursor.fetchone()
            if not p_row:
                continue
            p_id = p_row[0]

            # Insert Standard
            standard_info = details.get("standard", "")
            parts = standard_info.split(":")
            std_num = parts[0].strip() if len(parts) > 0 else standard_info
            year = parts[1].strip() if len(parts) > 1 else ""

            cursor.execute('''
                INSERT OR IGNORE INTO standards (standard_number, year)
                VALUES (?, ?)
            ''', (std_num, year))

            # Retrieve the standard ID
            cursor.execute('SELECT id FROM standards WHERE standard_number = ?', (std_num,))
            s_row = cursor.fetchone()
            if not s_row:
                continue
            s_id = s_row[0]

            # Map Product to Standard
            cursor.execute('''
                INSERT OR IGNORE INTO product_standards (product_id, standard_id)
                VALUES (?, ?)
            ''', (p_id, s_id))

        conn.commit()
        logger.info("Successfully initialized biscope.db with products, standards, and mappings.")

    except FileNotFoundError:
        logger.error(f"Source data file not found at {json_path}. Cannot populate DB.")
    except Exception as e:
        logger.error(f"Error populating database: {str(e)}")
    finally:
        conn.close()

if __name__ == "__main__":
    initialize_database()
