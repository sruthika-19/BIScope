import os
import sqlite3
import json
import logging
from urllib.parse import urlparse

# Configure paths relative to the script location
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DB_DIR = os.path.join(BASE_DIR, 'backend', 'database')
DB_PATH = os.path.join(DB_DIR, 'biscope.db')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Authoritative verified BIS LIMS URLs
SOURCE_MAP = {
    "P001": "https://lims.bis.gov.in/home/search_is_number/?is_number__doc_no=14543&is_number__year=2024&page=1",
    "P003": "https://lims.bis.gov.in/home/search_is_number/?is_number__doc_no=2925",
    "P004": "https://lims.bis.gov.in/home/search_is_number/?is_number__doc_no=4246",
    "P005": "https://lims.bis.gov.in/home/search_is_number/?is_number__doc_no=694",
    "P006": "https://lims.bis.gov.in/home/search_is_number/?is_number__doc_no=16240",
    "P008": "https://lims.bis.gov.in/home/search_is_number/?is_number__doc_no=15658&page=1",
    "P009": "https://lims.bis.gov.in/home/search_is_number/?is_number__doc_no=9873&page=1",
    "P011": "https://lims.bis.gov.in/home/search_is_number/?is_number__doc_no=996",
    "P012": "https://lims.bis.gov.in/home/search_is_number/?is_number__doc_no=374",
    "P013": "https://lims.bis.gov.in/home/search_is_number/?is_number__doc_no=2052",
    "P014": "https://lims.bis.gov.in/home/search_is_number/?is_number__doc_no=1180",
    "P015": "https://lims.bis.gov.in/home/search_is_number/?is_number__doc_no=1786",
    "P016": "https://lims.bis.gov.in/home/search_is_number/?is_number__doc_no=269&page=1",
    "P018": "https://lims.bis.gov.in/home/search_is_number/?is_number__doc_no=13252&lab__lab_name__icontains="
}

def initialize_database():
    """Creates the database schema and imports authoritative data directly from JSON."""
    os.makedirs(DB_DIR, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # 1. Create the THREE required tables safely (Existing Schema Preserved)
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
                year TEXT,
                source TEXT
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

        # Safely migrate existing databases to include the 'source' column
        cursor.execute("PRAGMA table_info(standards)")
        columns = [info[1] for info in cursor.fetchall()]
        if "source" not in columns:
            cursor.execute("ALTER TABLE standards ADD COLUMN source TEXT")

        json_path = os.path.join(BASE_DIR, 'backend', 'data', 'detailed_requirements.json')

        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        products_imported = 0
        standards_imported = 0

        # 2. Extract authoritative data with explicit validation
        for product_code, details in data.items():
            try:
                # STRICT MAPPING: Fail explicitly if required fields are missing
                product_name = details["product_name"]
                std_num = details["standard_number"]
                year = str(details["edition_year"])
            except KeyError as e:
                logger.error(f"Validation failed: Missing required field {e} for {product_code}. Skipping record.")
                continue

            source_url = SOURCE_MAP.get(product_code)

            # STRICT URL VALIDATION
            if source_url is not None:
                parsed = urlparse(source_url)
                if parsed.scheme != "https" or parsed.netloc != "lims.bis.gov.in":
                    logger.error(f"Validation failed: Invalid source URL '{source_url}' for {product_code}. Inserting NULL instead.")
                    source_url = None

            # Insert Product
            cursor.execute('''
                INSERT OR IGNORE INTO products (product_code, product_name)
                VALUES (?, ?)
            ''', (product_code, product_name))
            if cursor.rowcount > 0:
                products_imported += 1

            # Retrieve the product ID for mapping
            cursor.execute('SELECT id FROM products WHERE product_code = ?', (product_code,))
            p_row = cursor.fetchone()
            if not p_row:
                continue
            p_id = p_row[0]

            # Check if standard exists to determine whether to INSERT or UPDATE
            cursor.execute('SELECT id, source FROM standards WHERE standard_number = ?', (std_num,))
            s_row = cursor.fetchone()

            if not s_row:
                cursor.execute('''
                    INSERT INTO standards (standard_number, year, source)
                    VALUES (?, ?, ?)
                ''', (std_num, year, source_url))
                s_id = cursor.lastrowid
                standards_imported += 1
            else:
                s_id = s_row[0]
                existing_source = s_row[1]
                # Update source if we have a verified URL and it is not already set correctly
                if source_url and existing_source != source_url:
                    cursor.execute('UPDATE standards SET source = ? WHERE id = ?', (source_url, s_id))

            # Map Product to Standard
            cursor.execute('''
                INSERT OR IGNORE INTO product_standards (product_id, standard_id)
                VALUES (?, ?)
            ''', (p_id, s_id))

        conn.commit()
        logger.info(f"Successfully initialized biscope.db. Inserted {products_imported} new products and {standards_imported} new standards.")

    except FileNotFoundError:
        logger.error(f"Source data file not found at {json_path}. Cannot populate DB.")
    except Exception as e:
        logger.error(f"Error populating database: {str(e)}")
    finally:
        conn.close()

if __name__ == "__main__":
    initialize_database()
