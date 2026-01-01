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

    def save_log(self, message):
        """Persiste mensagens de log no banco."""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO logs (message) VALUES (?)", (message,))
            conn.commit()

    def get_plb_list(self):
        """Recupera a lista de PLBs."""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, url, created_at FROM plb ORDER BY created_at DESC")
            return cursor.fetchall()

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

    def save_plb(self, url, html_content):
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO plb (url, html_content) VALUES (?, ?)", (url, html_content))
                conn.commit()
        except sqlite3.Error as e:
            raise Exception(f"Erro de Banco de Dados (PLB): {e}")

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

    def _check_and_migrate(self):
        """Verifica se a coluna 'programa' existe e a cria se necessário."""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA table_info(pesquisas)")
                columns = [info[1] for info in cursor.fetchall()]
                
                if 'programa' not in columns:
                    cursor.execute("ALTER TABLE pesquisas ADD COLUMN programa TEXT")
                    conn.commit()
        except sqlite3.Error as e:
            print(f"Erro na migração do banco: {e}")

    def get_all_pesquisas(self):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            # Adicionado campo 'programa' na query
            cursor.execute("SELECT title, author, ppb_link, ppr_link, univ_sigla, univ_nome, programa FROM pesquisas ORDER BY extracted_at DESC")
            return [
                {
                    'title': r[0], 
                    'author': r[1], 
                    'ppb_link': r[2], 
                    'ppr_link': r[3],
                    'univ_sigla': r[4],
                    'univ_nome': r[5],
                    'programa': r[6]
                } for r in cursor.fetchall()
            ]

    def _init_db(self):
        with sqlite3.connect(self.db_name, check_same_thread=False) as conn:
            conn.execute("PRAGMA journal_mode=WAL;")
            cursor = conn.cursor()
            
            # ... (Tabelas existentes: plb, pesquisas, ppb, logs, ppr) ...
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS plb (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL,
                    html_content TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
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

            # --- NOVA TABELA: SOURCES (Fontes/Raízes) ---
            # status: 1 = Ativo (Sucesso/Marcado), 0 = Inativo (Falha/Desmarcado)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sources (
                    root_url TEXT PRIMARY KEY,
                    status INTEGER DEFAULT 1
                )
            """)
            
            conn.commit()
            self._check_and_migrate()

    def save_source_status(self, root_url, status):
        """Salva ou atualiza o status de uma raiz (True=1, False=0)."""
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
        """Retorna um dicionário {root_url: bool} com todas as fontes salvas."""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT root_url, status FROM sources")
            # Retorna True se 1, False se 0
            return {row[0]: bool(row[1]) for row in cursor.fetchall()}
            
    def get_source_status(self, root_url):
        """
        Verifica o status de uma raiz específica.
        Retorna:
            True: Se existe e está marcado (1) OU se não existe (assume novo como permitido).
            False: Se existe e está desmarcado (0).
        """
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT status FROM sources WHERE root_url = ?", (root_url,))
            res = cursor.fetchone()
            if res:
                return bool(res[0])
            return True # Padrão para novas fontes é "tentar baixar"

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
        
    def __init__(self, db_name="database.db"):
        self.db_name = db_name
        self._init_db()
        self._check_and_migrate()

    def get_all_ppr_with_html(self):
        """
        Retorna (title, author, url, html_content) de todas as pesquisas 
        que possuem o HTML da PPR salvo.
        """
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
        """Armazena a sigla, nome da universidade e programa extraídos."""
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
