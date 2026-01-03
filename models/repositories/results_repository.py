from .base_repository import BaseRepository
import sqlite3

class ResultsRepository(BaseRepository):
    def get_all(self):
        """Retorna todas as pesquisas salvas."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM pesquisas ORDER BY extracted_at DESC")
            cols = [description[0] for description in cursor.description]
            return [dict(zip(cols, row)) for row in cursor.fetchall()]

    def save_pesquisas(self, data, term=None, year=None):
        """Salva novas pesquisas verificando unicidade por (Título, Autor, Termo, Ano)."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            saved_count = 0
            for item in data:
                title = item.get('title')
                author = item.get('author')
                
                # Verifica unicidade
                cursor.execute("""
                    SELECT 1 FROM pesquisas 
                    WHERE title = ? AND author = ? AND search_term = ? AND search_year = ?
                """, (title, author, term, year))
                
                if cursor.fetchone():
                    continue

                try:
                    cursor.execute("""
                        INSERT INTO pesquisas (
                            title, author, ppb_link, ppr_link, 
                            univ_sigla, univ_nome, programa,
                            search_term, search_year
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        title, author, 
                        item.get('ppb_link'), item.get('ppr_link'), 
                        item.get('sigla'), item.get('universidade'), item.get('programa'),
                        term, year
                    ))
                    saved_count += 1
                except sqlite3.IntegrityError:
                    pass
            conn.commit()
            return saved_count

    def save_content(self, url, html_content, type_doc):
        """Salva HTML de PPB ou PPR."""
        table = "ppb" if type_doc == 'buscador' else "ppr"
        link_col = "ppb_link" if type_doc == 'buscador' else "ppr_link"
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT id FROM pesquisas WHERE {link_col} = ?", (url,))
            res = cursor.fetchone()
            if res:
                cursor.execute(f"""
                    INSERT INTO {table} (pesquisa_id, url, html_content)
                    VALUES (?, ?, ?)
                """, (res[0], url, html_content))
                conn.commit()

    def get_pending_ppr(self):
        """Retorna pesquisas com link PPR mas sem HTML baixado."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.id, p.ppr_link 
                FROM pesquisas p
                WHERE p.ppr_link IS NOT NULL AND p.ppr_link != '' 
                  AND NOT EXISTS (
                      SELECT 1 FROM ppr r 
                      WHERE r.pesquisa_id = p.id AND r.html_content IS NOT NULL
                  )
            """)
            return cursor.fetchall()

    def get_extracted_html(self, title, author, doc_type='ppb'):
        """Recupera o HTML salvo (PPB ou PPR) pelo título e autor."""
        table = "ppb" if doc_type == 'ppb' else "ppr"
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT t.html_content 
                FROM {table} t
                JOIN pesquisas p ON t.pesquisa_id = p.id
                WHERE p.title=? AND p.author=?
            """, (title, author))
            res = cursor.fetchone()
            return res[0] if res else None

    def get_all_ppr_with_html(self):
        """Para extração em lote de dados universitários."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.title, p.author, r.url, r.html_content 
                FROM ppr r
                JOIN pesquisas p ON r.pesquisa_id = p.id
                WHERE r.html_content IS NOT NULL AND r.html_content != ''
            """)
            return cursor.fetchall()

    def update_univ_data(self, title, author, sigla, nome, programa):
        with self.db.get_connection() as conn:
            conn.execute("""
                UPDATE pesquisas 
                SET univ_sigla = ?, univ_nome = ?, programa = ?
                WHERE title = ? AND author = ?
            """, (sigla, nome, programa, title, author))
            conn.commit()