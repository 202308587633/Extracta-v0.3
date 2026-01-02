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

    def delete_history(self, plb_id):
        """Remove uma PLB da tabela plb."""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM plb WHERE id = ?", (plb_id,))
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

    def __init__(self, db_name="database.db"):
        self.db_name = db_name
        self._init_db()
        self._check_and_migrate()

    def check_url_exists(self, url):
        """Verifica se uma URL já existe na tabela PLB."""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM plb WHERE url = ? LIMIT 1", (url,))
                return cursor.fetchone() is not None
        except sqlite3.Error:
            return False
    
    def get_plb_by_id(self, plb_id):
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
            
    def get_all_sources(self):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT root_url, status FROM sources")
            return {row[0]: bool(row[1]) for row in cursor.fetchall()}
    
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

    def get_all_pesquisas(self):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM pesquisas ORDER BY extracted_at DESC")
            cols = [description[0] for description in cursor.description]
            return [dict(zip(cols, row)) for row in cursor.fetchall()]
            
    def get_extracted_html(self, title, author):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT html_content FROM ppb JOIN pesquisas ON ppb.pesquisa_id = pesquisas.id WHERE title=? AND author=?", (title, author))
            res = cursor.fetchone()
            return res[0] if res else None

    def delete_plb(self, plb_id):
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM plb WHERE id = ?", (plb_id,))
                conn.commit()
        except sqlite3.Error as e:
            raise Exception(f"Erro ao excluir histórico: {e}")

    def get_existing_searches(self):
        """
        Retorna uma lista de tuplas (termo, ano) que já estão salvas no banco.
        Usado para filtrar as opções na aba Home e evitar retrabalho.
        """
        try:
            self._check_and_migrate() # Garante que as colunas existem
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT DISTINCT search_term, search_year 
                    FROM plb 
                    WHERE search_term IS NOT NULL 
                      AND search_year IS NOT NULL 
                      AND search_term != ''
                """)
                return cursor.fetchall()
        except sqlite3.Error:
            return []

    def save_plb(self, url, html_content, term=None, year=None):
        """Salva a página PLB com os metadados de termo e ano."""
        try:
            self._check_and_migrate() # Garante que as colunas existem
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
        """Retorna histórico para a tabela, lidando com colunas novas ou antigas."""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            try:
                # Tenta buscar com as novas colunas
                cursor.execute("""
                    SELECT id, url, created_at, search_term, search_year 
                    FROM plb 
                    ORDER BY created_at DESC
                """)
            except sqlite3.OperationalError:
                # Fallback para banco antigo sem as colunas
                cursor.execute("""
                    SELECT id, url, created_at, NULL, NULL 
                    FROM plb 
                    ORDER BY created_at DESC
                """)
            return cursor.fetchall()

    def _init_db(self):
        with sqlite3.connect(self.db_name, check_same_thread=False) as conn:
            conn.execute("PRAGMA journal_mode=WAL;")
            cursor = conn.cursor()
            
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
            
            # ATUALIZADO: Tabela pesquisas agora inclui search_term e search_year.
            # Nota: ppb_link não deve ser UNIQUE globalmente se quisermos registrar
            # o mesmo link para termos de busca diferentes.
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pesquisas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    author TEXT,
                    ppb_link TEXT,
                    ppr_link TEXT,
                    univ_sigla TEXT,
                    univ_nome TEXT,
                    programa TEXT,
                    search_term TEXT,
                    search_year TEXT,
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
        """Garante que as colunas de termo e ano existam nas tabelas."""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                
                # Migração Tabela PLB
                cursor.execute("PRAGMA table_info(plb)")
                columns_plb = [info[1] for info in cursor.fetchall()]
                
                if 'search_term' not in columns_plb:
                    cursor.execute("ALTER TABLE plb ADD COLUMN search_term TEXT")
                if 'search_year' not in columns_plb:
                    cursor.execute("ALTER TABLE plb ADD COLUMN search_year TEXT")

                # Migração Tabela Pesquisas (NOVO)
                cursor.execute("PRAGMA table_info(pesquisas)")
                columns_pesq = [info[1] for info in cursor.fetchall()]
                
                if 'search_term' not in columns_pesq:
                    cursor.execute("ALTER TABLE pesquisas ADD COLUMN search_term TEXT")
                if 'search_year' not in columns_pesq:
                    cursor.execute("ALTER TABLE pesquisas ADD COLUMN search_year TEXT")
                    
                conn.commit()
        except sqlite3.Error:
            pass 

    def save_pesquisas(self, data, term=None, year=None):
        """
        Salva as pesquisas no banco de dados.
        A unicidade agora é definida pela combinação: Título + Autor + Termo + Ano.
        """
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            for item in data:
                title = item.get('title')
                author = item.get('author')
                
                # 1. Verifica se já existe um registro idêntico (mesmo título/autor E mesmo contexto de busca)
                cursor.execute("""
                    SELECT 1 FROM pesquisas 
                    WHERE title = ? AND author = ? AND search_term = ? AND search_year = ?
                """, (title, author, term, year))
                
                if cursor.fetchone():
                    continue # Registro já existe para este termo/ano, pula.

                # 2. Insere o novo registro
                try:
                    cursor.execute("""
                        INSERT INTO pesquisas (
                            title, author, ppb_link, ppr_link, 
                            univ_sigla, univ_nome, programa,
                            search_term, search_year
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        title, author, item.get('link_page'), 
                        item.get('link_file'), item.get('sigla'), 
                        item.get('universidade'), item.get('programa'),
                        term, year
                    ))
                except sqlite3.IntegrityError:
                    # Em bancos de dados criados anteriormente, ppb_link pode ter constraint UNIQUE.
                    # Se cairmos aqui, ignoramos para não quebrar a execução, mas o ideal 
                    # seria recriar o banco se desejar duplicar links para termos diferentes.
                    pass
            conn.commit()
            
