import sqlite3

class DatabaseModel:
    def save_ppb_content(self, url, html_content):
        """Grava o HTML da PPB relacionado à linha correspondente em pesquisas."""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM pesquisas WHERE ppb_link = ?", (url,))
            res = cursor.fetchone()
            if res:
                cursor.execute("""
                    INSERT INTO ppb (pesquisa_id, url, html_content)
                    VALUES (?, ?, ?)
                """, (res[0], url, html_content))
                conn.commit()

    def get_extracted_html(self, title, author):
        """Recupera o HTML da PPB via relação com pesquisas."""
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

    def delete_history(self, plb_id):
        """Remove uma PLB da tabela plb."""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM plb WHERE id = ?", (plb_id,))
            conn.commit()

    def save_pesquisas(self, data_list):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            for item in data_list:
                cursor.execute("""
                    INSERT OR IGNORE INTO pesquisas (title, author, ppb_link, ppr_link)
                    VALUES (?, ?, ?, ?)
                """, (item.get('title'), item.get('author'), item.get('ppb_link'), item.get('ppr_link')))
            conn.commit()

    def get_plb_content(self, plb_id):
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT url, html_content FROM plb WHERE id = ?", (plb_id,))
                result = cursor.fetchone()
                return result if result else (None, None)
        except sqlite3.Error as e:
            raise Exception(f"Erro ao ler dados da PLB: {e}")

    def get_ppr_html(self, title, author):
        """Busca o HTML na tabela ppr através da relação relacional."""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT r.html_content 
                    FROM ppr r
                    JOIN pesquisas p ON r.pesquisa_id = p.id
                    WHERE p.title = ? AND p.author = ?
                """, (title, author))
                result = cursor.fetchone()
                return result[0] if result else None
        except sqlite3.Error as e:
            raise Exception(f"Erro na consulta SQL (PPR): {e}")

    def get_ppr_full_content(self, title, author):
        """
        Retorna (URL, HTML) da tabela PPR baseado no título e autor.
        Usado pelo main_viewmodel.py linha 273.
        """
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT r.url, r.html_content 
                    FROM ppr r
                    JOIN pesquisas p ON r.pesquisa_id = p.id
                    WHERE p.title = ? AND p.author = ?
                """, (title, author))
                result = cursor.fetchone()
                # Retorna (url, html) se achar, ou (None, None) se não achar
                return result if result else (None, None)
        except sqlite3.Error as e:
            raise Exception(f"Erro na consulta SQL (PPR Full): {e}")

    def __init__(self, db_name="database.db"):
        self.db_name = db_name
        self._init_db()
        self._check_and_migrate()

    def _init_db(self):
        with sqlite3.connect(self.db_name, check_same_thread=False) as conn:
            conn.execute("PRAGMA journal_mode=WAL;")
            cursor = conn.cursor()
            
            # Atualizamos a criação da tabela para incluir as novas colunas
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS plb (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL,
                    html_content TEXT,
                    search_term TEXT,
                    search_year TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # ... (Demais tabelas: pesquisas, ppb, logs, ppr, sources mantidas iguais) ...
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pesquisas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    author TEXT,
                    ppb_link TEXT UNIQUE,
                    ppr_link TEXT,
                    univ_sigla TEXT,
                    univ_nome TEXT,
                    programa TEXT,
                    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
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
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ppr (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pesquisa_id INTEGER,
                    url TEXT NOT NULL,
                    html_content TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (pesquisa_id) REFERENCES pesquisas(id) ON DELETE CASCADE
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sources (
                    root_url TEXT PRIMARY KEY,
                    status INTEGER DEFAULT 1
                )
            """)
            conn.commit()
            self._check_and_migrate()

    def _check_and_migrate(self):
        """Verifica se as tabelas precisam de colunas novas (Migração)."""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            
            # Verifica colunas da tabela PLB
            cursor.execute("PRAGMA table_info(plb)")
            columns = [info[1] for info in cursor.fetchall()]
            
            if 'search_term' not in columns:
                cursor.execute("ALTER TABLE plb ADD COLUMN search_term TEXT")
            if 'search_year' not in columns:
                cursor.execute("ALTER TABLE plb ADD COLUMN search_year TEXT")
            
            conn.commit()

    def save_plb(self, url, html_content, term=None, year=None):
        """Salva a página de lista (PLB) com termo e ano."""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO plb (url, html_content, search_term, search_year) 
                    VALUES (?, ?, ?, ?)
                """, (url, html_content, term, year))
                conn.commit()
        except sqlite3.Error as e:
            raise Exception(f"Erro ao salvar PLB: {e}")

    def get_plb_list(self):
        """Retorna lista de PLBs incluindo termo e ano."""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, url, created_at, search_term, search_year 
                FROM plb 
                ORDER BY created_at DESC
            """)
            return cursor.fetchall()

    def get_plb_by_id(self, plb_id):
        """Retorna detalhes de uma PLB específica."""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, url, html_content, search_term, search_year 
                FROM plb WHERE id = ?
            """, (plb_id,))
            return cursor.fetchone()

    def save_log(self, message):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO logs (message) VALUES (?)", (message,))
            conn.commit()

    def save_ppb_content(self, url, html_content):
        # Lógica de vínculo com pesquisa baseada na URL
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                # Tenta achar a pesquisa pelo link PPB
                cursor.execute("SELECT id FROM pesquisas WHERE ppb_link = ?", (url,))
                res = cursor.fetchone()
                
                if res:
                    pesquisa_id = res[0]
                    cursor.execute("""
                        INSERT INTO ppb (pesquisa_id, url, html_content)
                        VALUES (?, ?, ?)
                    """, (pesquisa_id, url, html_content))
                    conn.commit()
        except sqlite3.Error as e:
            raise Exception(f"Erro de Banco de Dados (PPB): {e}")

    def save_ppr_content(self, url, html_content):
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM pesquisas WHERE ppr_link = ?", (url,))
                res = cursor.fetchone()
                if res:
                    cursor.execute("""
                        INSERT INTO ppr (pesquisa_id, url, html_content)
                        VALUES (?, ?, ?)
                    """, (res[0], url, html_content))
                    conn.commit()
        except sqlite3.Error as e:
            raise Exception(f"Erro de Banco de Dados (PPR): {e}")

    def get_all_pesquisas(self):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM pesquisas ORDER BY extracted_at DESC")
            cols = [description[0] for description in cursor.description]
            return [dict(zip(cols, row)) for row in cursor.fetchall()]

    def get_pending_ppr_records(self):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, ppr_link 
                FROM pesquisas 
                WHERE ppr_link IS NOT NULL 
                  AND ppr_link != '' 
                  AND id NOT IN (
                      SELECT pesquisa_id FROM ppr 
                      WHERE html_content IS NOT NULL AND html_content != ''
                  )
            """)
            return cursor.fetchall()

    def save_source_status(self, root_url, status):
        val = 1 if status else 0
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sources (root_url, status) 
                VALUES (?, ?)
                ON CONFLICT(root_url) DO UPDATE SET status = excluded.status
            """, (root_url, val))
            conn.commit()

    def get_all_sources(self):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT root_url, status FROM sources")
            return {row[0]: bool(row[1]) for row in cursor.fetchall()}
            
    def get_source_status(self, root_url):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT status FROM sources WHERE root_url = ?", (root_url,))
            res = cursor.fetchone()
            if res: return bool(res[0])
            return True

    def get_all_ppr_with_html(self):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.title, p.author, r.url, r.html_content 
                FROM ppr r
                JOIN pesquisas p ON r.pesquisa_id = p.id
                WHERE r.html_content IS NOT NULL AND r.html_content != ''
            """)
            return cursor.fetchall()
            
    def update_univ_data(self, title, author, sigla, nome, programa):
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE pesquisas 
                    SET univ_sigla = ?, univ_nome = ?, programa = ?
                    WHERE title = ? AND author = ?
                """, (sigla, nome, programa, title, author))
                conn.commit()
        except sqlite3.Error as e:
            raise Exception(f"Erro ao atualizar dados da universidade: {e}")

    def delete_plb(self, plb_id):
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM plb WHERE id = ?", (plb_id,))
                conn.commit()
        except sqlite3.Error as e:
            raise Exception(f"Erro ao excluir histórico: {e}")