import sqlite3

class DatabaseModel:
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
            
    def save_scraping(self, url, html_content, doc_type='buscador'):
        """Salva o HTML bruto no histórico com distinção de tipo"""
        with sqlite3.connect(self.db_name, check_same_thread=False) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO history (url, html_content, type) VALUES (?, ?, ?)", 
                (url, html_content, doc_type)
            )
            conn.commit()

    def save_extracted_results(self, data_list):
        with sqlite3.connect(self.db_name, check_same_thread=False) as conn:
            cursor = conn.cursor()
            for item in data_list:
                cursor.execute("""
                    INSERT INTO extracted_results (title, author, ppb_link, lap_link)
                    VALUES (?, ?, ?, ?)
                """, (item.get('title'), item.get('author'), item.get('ppb_link'), item.get('lap_link')))
            conn.commit()

    def get_all_extracted_results(self):
        with sqlite3.connect(self.db_name, check_same_thread=False) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT title, author, ppb_link, lap_link FROM extracted_results ORDER BY extracted_at DESC")
            return [{'title': r[0], 'author': r[1], 'ppb_link': r[2], 'lap_link': r[3]} for r in cursor.fetchall()]

    def __init__(self, db_name="database.db"):
        self.db_name = db_name
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_name, check_same_thread=False) as conn:
            conn.execute("PRAGMA journal_mode=WAL;")
            cursor = conn.cursor()
            
            # 1. Tabela para as Páginas de Listagem do Buscador (PLB)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS plb (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL,
                    html_content TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 2. Tabela para os Metadados das Pesquisas (Minerados das PLBs)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pesquisas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    author TEXT,
                    ppb_link TEXT UNIQUE,
                    lap_link TEXT,
                    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)            
            
            # 3. Tabela para os Códigos HTML das Páginas de Pesquisa (PPB)
            # Relacionada à tabela 'pesquisas' via ppb_id
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ppb (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pesquisa_id INTEGER,
                    url TEXT NOT NULL,
                    html_content TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (pesquisa_id) REFERENCES pesquisas(id) ON DELETE CASCADE
                )
            """)

            # Tabela de Logs (Mantida para rastro de auditoria)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def save_plb(self, url, html_content):
        """Grava as páginas de listagem na tabela plb"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO plb (url, html_content) VALUES (?, ?)", (url, html_content))
            conn.commit()

    def save_pesquisas(self, data_list):
        """Grava os resultados minerados na tabela pesquisas"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            for item in data_list:
                cursor.execute("""
                    INSERT OR IGNORE INTO pesquisas (title, author, ppb_link, lap_link)
                    VALUES (?, ?, ?, ?)
                """, (item.get('title'), item.get('author'), item.get('ppb_link'), item.get('lap_link')))
            conn.commit()

    def save_ppb_content(self, url, html_content):
        """Grava o HTML da PPB relacionado à linha correspondente em pesquisas"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            # Localiza o ID da pesquisa pelo link da PPB
            cursor.execute("SELECT id FROM pesquisas WHERE ppb_link = ?", (url,))
            res = cursor.fetchone()
            if res:
                pesquisa_id = res[0]
                cursor.execute("""
                    INSERT INTO ppb (pesquisa_id, url, html_content)
                    VALUES (?, ?, ?)
                """, (pesquisa_id, url, html_content))
                conn.commit()

    def get_plb_list(self):
        """Recupera a lista de páginas de listagem da nova tabela plb"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, url, created_at FROM plb ORDER BY created_at DESC")
            return cursor.fetchall()

    def get_plb_content(self, plb_id):
        """Recupera o HTML de uma PLB específica pelo ID"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT html_content FROM plb WHERE id = ?", (plb_id,))
            result = cursor.fetchone()
            return result[0] if result else ""
            
    def get_history_item(self, plb_id):
        """Mantém compatibilidade com funções de extração usando a tabela plb"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT url, html_content FROM plb WHERE id = ?", (plb_id,))
            return cursor.fetchone()
        
    def get_all_pesquisas(self):
        """Recupera todos os registos da nova tabela pesquisas"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT title, author, ppb_link, lap_link FROM pesquisas ORDER BY extracted_at DESC")
            return [{'title': r[0], 'author': r[1], 'ppb_link': r[2], 'lap_link': r[3]} for r in cursor.fetchall()]

    def get_extracted_html(self, title, author):
        """Recupera o HTML da tabela 'ppb' através da relação com a tabela 'pesquisas'"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT b.html_content 
                FROM ppb b
                JOIN pesquisas p ON b.pesquisa_id = p.id
                WHERE p.title = ? AND p.author = ?
            """, (title, author))
            result = cursor.fetchone()
            return result[0] if result else None

    def get_lap_html(self, title, author):
        """
        Recupera o HTML do LAP (Repositório) buscando na tabela 'plb' 
        através da relação com a tabela 'pesquisas'.
        """
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            # Atualizado: De 'history' para 'plb' e de 'extracted_results' para 'pesquisas'
            cursor.execute("""
                SELECT p_content.html_content 
                FROM plb p_content
                JOIN pesquisas p_meta ON p_content.url = p_meta.lap_link
                WHERE p_meta.title = ? AND p_meta.author = ?
            """, (title, author))
            result = cursor.fetchone()
            return result[0] if result else None
