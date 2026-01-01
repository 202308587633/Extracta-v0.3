import sqlite3

class DatabaseModel:
    def __init__(self, db_name="database.db"):
        self.db_name = db_name
        self._init_db()

    def _init_db(self):
        """Inicializa o banco de dados com a estrutura relacional e modo WAL."""
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
                    ppr_link TEXT,
                    univ_sigla TEXT,
                    univ_nome TEXT,
                    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 3. Tabela para os Códigos HTML das Páginas de Pesquisa (PPB)
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

            # 4. Tabela de Logs
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 5. Tabela PPR
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
            conn.commit()

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

    # ESTA É A FUNÇÃO QUE O ERRO DIZIA ESTAR FALTANDO
    # Certifique-se de que a indentação (espaços à esquerda) está alinhada com as outras funções
    def get_all_pesquisas(self):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            # Adicionei univ_sigla e univ_nome para o retorno ser mais completo, se necessário
            cursor.execute("SELECT title, author, ppb_link, ppr_link, univ_sigla, univ_nome FROM pesquisas ORDER BY extracted_at DESC")
            return [
                {
                    'title': r[0], 
                    'author': r[1], 
                    'ppb_link': r[2], 
                    'ppr_link': r[3],
                    'univ_sigla': r[4],
                    'univ_nome': r[5]
                } for r in cursor.fetchall()
            ]

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

    def save_ppr_content(self, url, html_content):
        """Grava o HTML da PPR vinculado à pesquisa via ppr_link."""
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

    def update_univ_data(self, title, author, sigla, nome):
        """Armazena a sigla e o nome da universidade extraídos."""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE pesquisas 
                    SET univ_sigla = ?, univ_nome = ?
                    WHERE title = ? AND author = ?
                """, (sigla, nome, title, author))
                conn.commit()
        except sqlite3.Error as e:
            raise Exception(f"Erro ao atualizar dados da universidade: {e}")