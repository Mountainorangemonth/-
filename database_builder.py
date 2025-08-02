
import os
import sqlite3
import zipfile
import requests
import json
from tqdm import tqdm
from collections import defaultdict

# --- Configuration ---
CFPA_URL = "https://github.com/CFPAOrg/Minecraft-Mod-Language-Package/releases/latest/download/Minecraft-Mod-Language-Package-1.20.zip"
ZIP_PATH = "community_pack.zip"
DB_PATH = "translations.db"

def download_file(url, path):
    """Downloads a file from a URL with a progress bar."""
    print(f"Downloading from {url}...")
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        total_size = int(response.headers.get('content-length', 0))
        with open(path, 'wb') as f, tqdm(total=total_size, unit='iB', unit_scale=True, desc="Downloading Pack") as pbar:
            for data in response.iter_content(chunk_size=1024):
                pbar.update(len(data))
                f.write(data)
        print("Download complete.")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error: Failed to download translation pack - {e}")
        return False

def build_database():
    """Builds the SQLite database from the downloaded translation pack."""
    if os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} already exists. Deleting to rebuild.")
        os.remove(DB_PATH)

    if not os.path.exists(ZIP_PATH):
        if not download_file(CFPA_URL, ZIP_PATH):
            return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS translations (
        source_text TEXT PRIMARY KEY,
        translated_text TEXT NOT NULL
    )
    ''')

    print("Processing language files from zip...")
    lang_files = defaultdict(dict)
    try:
        with zipfile.ZipFile(ZIP_PATH, 'r') as z:
            for filename in tqdm(z.namelist(), desc="Reading lang files"):
                if (filename.endswith('en_us.json') or filename.endswith('zh_cn.json')) and filename.startswith('assets/'):
                    try:
                        with z.open(filename) as f:
                            data = json.load(f)
                            lang_code = 'en_us' if filename.endswith('en_us.json') else 'zh_cn'
                            mod_id = filename.split('/')[1]
                            lang_files[(mod_id, lang_code)].update(data)
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        continue
    except zipfile.BadZipFile:
        print(f"Error: The downloaded file {ZIP_PATH} is not a valid zip file.")
        conn.close()
        return

    print("Building translation pairs and inserting into database...")
    insert_count = 0
    # Group by mod_id
    mod_ids = set(k[0] for k in lang_files.keys())

    for mod_id in tqdm(mod_ids, desc="Building Database"):
        en_data = lang_files.get((mod_id, 'en_us'), {})
        cn_data = lang_files.get((mod_id, 'zh_cn'), {})

        if not en_data or not cn_data:
            continue

        # Find common keys and create translation pairs
        common_keys = en_data.keys() & cn_data.keys()
        for key in common_keys:
            source_text = en_data[key]
            translated_text = cn_data[key]
            # We only care about non-empty strings
            if isinstance(source_text, str) and isinstance(translated_text, str) and source_text and translated_text:
                cursor.execute("INSERT OR IGNORE INTO translations (source_text, translated_text) VALUES (?, ?)", (source_text, translated_text))
    
    conn.commit()
    insert_count = conn.total_changes
    conn.close()

    print(f"Database build complete. Inserted {insert_count} unique translations.")
    print(f"Database saved to: {DB_PATH}")

if __name__ == "__main__":
    build_database()
