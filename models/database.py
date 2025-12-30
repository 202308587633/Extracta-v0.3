import sqlite3

class DatabaseModel:
    def __init__(self, db_name="database.db"):
        self.db_name = db_name
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            # Tabela de Histórico (HTML Bruto)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL,
                    html_content TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Nova Tabela de Resultados Extraídos (Dados Minerados)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS extracted_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    author TEXT,
                    search_link TEXT,
                    repo_link TEXT,
                    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def save_scraping(self, url, html_content):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO history (url, html_content) VALUES (?, ?)", (url, html_content))
            conn.commit()

    def save_log(self, message):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO logs (message) VALUES (?)", (message,))
            conn.commit()

    def get_history_list(self):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, url, created_at FROM history ORDER BY created_at DESC")
            return cursor.fetchall()

    def get_history_content(self, history_id):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT html_content FROM history WHERE id = ?", (history_id,))
            result = cursor.fetchone()
            return result[0] if result else ""

    def delete_history(self, history_id):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM history WHERE id = ?", (history_id,))
            conn.commit()
            
    def get_history_item(self, history_id):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT url, html_content FROM history WHERE id = ?", (history_id,))
            return cursor.fetchone()

    def save_extracted_results(self, data_list):
        """Salva a lista de dicionários extraídos no banco"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            for item in data_list:
                cursor.execute("""
                    INSERT INTO extracted_results (title, author, search_link, repo_link)
                    VALUES (?, ?, ?, ?)
                """, (item.get('title'), item.get('author'), item.get('search_link'), item.get('repo_link')))
            conn.commit()

    def get_all_extracted_results(self):
        """Recupera todos os registros minerados para preencher a tabela"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT title, author, search_link, repo_link FROM extracted_results ORDER BY extracted_at DESC")
            rows = cursor.fetchall()
            return [{'title': r[0], 'author': r[1], 'search_link': r[2], 'repo_link': r[3]} for r in rows]
        