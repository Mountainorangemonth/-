
import sqlite3

class DatabaseManager:
    def __init__(self, db_path='translations.db'):
        self.db_path = db_path
        self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
        self.cursor = self.connection.cursor()
        self._create_table()

    def _create_table(self):
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS translations (
            source_text TEXT PRIMARY KEY,
            translated_text TEXT NOT NULL
        )
        ''')
        self.connection.commit()

    def get_translations(self, texts):
        """Fetches translations for a list of texts from the database."""
        if not texts:
            return {}
        
        # Using a placeholder for each text to avoid SQL injection
        placeholders = ', '.join('?' for _ in texts)
        query = f"SELECT source_text, translated_text FROM translations WHERE source_text IN ({placeholders})"
        
        self.cursor.execute(query, texts)
        results = self.cursor.fetchall()
        return dict(results)

    def add_translation(self, source_text, translated_text):
        """Adds a new translation to the database, implementing the permanent memory."""
        if source_text and translated_text:
            self.cursor.execute("INSERT OR REPLACE INTO translations (source_text, translated_text) VALUES (?, ?)", (source_text, translated_text))
            self.connection.commit()

    def close(self):
        if self.connection:
            self.connection.close()
