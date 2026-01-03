from .base_repository import BaseRepository
import sqlite3

class ResultsRepository(BaseRepository):
    def get_all(self):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            # Left Join para verificar existência de conteúdo HTML
            cursor.execute("""
                SELECT p.*,
                       CASE WHEN b.html_content IS NOT NULL AND b.html_content != '' THEN 1 ELSE 0 END as has_ppb,
                       CASE WHEN r.html_content IS NOT NULL AND r.html_content != '' THEN 1 ELSE 0 END as has_ppr
                FROM pesquisas p
                LEFT JOIN ppb b ON b.pesquisa_id = p.id
                LEFT JOIN ppr r ON r.pesquisa_id = p.id
                ORDER BY p.extracted_at DESC
            """)
            cols = [description[0] for description in cursor.description]
            return [dict(zip(cols, row)) for row in cursor.fetchall()]

    def save_pesquisas(self, data, term=None, year=None):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            saved_count = 0
            for item in data:
                title = item.get('title')
                author = item.get('author')
                
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
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        title, author, item.get('ppb_link'), item.get('ppr_link'),
                        '-', 'Pendente', '-', 
                        term, year
                    ))
                    
                    pesquisa_id = cursor.lastrowid
                    
                    cursor.execute("INSERT OR IGNORE INTO ppb (pesquisa_id, url) VALUES (?, ?)", (pesquisa_id, item.get('ppb_link')))
                    cursor.execute("INSERT OR IGNORE INTO ppr (pesquisa_id, url) VALUES (?, ?)", (pesquisa_id, item.get('ppr_link')))
                    
                    saved_count += 1
                except sqlite3.Error:
                    pass
            
            conn.commit()
            return saved_count

    def get_pending_ppr(self):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.id, p.ppr_link 
                FROM pesquisas p
                LEFT JOIN ppr r ON r.pesquisa_id = p.id
                WHERE p.ppr_link IS NOT NULL AND p.ppr_link != '' 
                  AND (r.html_content IS NULL OR r.html_content = '')
            """)
            return cursor.fetchall()

    def save_content(self, url, html, doc_type):
        table = "ppb" if doc_type == 'buscador' else "ppr"
        with self.db.get_connection() as conn:
            conn.execute(f"""
                UPDATE {table} 
                SET html_content = ?, extracted_at = CURRENT_TIMESTAMP
                WHERE url = ?
            """, (html, url))
            conn.commit()

    def get_extracted_html(self, title, author, doc_type='ppb'):
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

    # --- NOVO MÉTODO PARA CORREÇÃO DO PARSER ---
    def get_ppr_data(self, title, author):
        """Retorna (url, html) do PPR para extração correta baseada no domínio."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT t.url, t.html_content 
                FROM ppr t
                JOIN pesquisas p ON t.pesquisa_id = p.id
                WHERE p.title=? AND p.author=?
            """, (title, author))
            return cursor.fetchone()

    def get_all_ppr_with_html(self):
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
            
    # Adicione este método na classe ResultsRepository
    def get_ppr_for_reprocessing(self):
        """
        Busca registros que têm HTML (PPR) mas a sigla ainda não foi 
        identificada corretamente ('-' ou 'DSpace').
        """
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                # Ajuste os nomes das colunas (title, author, ppr_link, etc) 
                # conforme a estrutura real da sua tabela 'results'
                cursor.execute("""
                    SELECT p.title, p.author, p.ppr_link, r.html_content 
                    FROM ppr r
                    JOIN pesquisas p ON r.pesquisa_id = p.id
                    WHERE r.html_content IS NOT NULL AND r.html_content != ''
                    AND (univ_sigla = '-' OR univ_sigla = 'DSpace' OR univ_sigla IS NULL)
                """)
                return cursor.fetchall()
        except Exception as e:
            print(f"Erro ao buscar registros para reprocessamento: {e}")
            return []
        
    def clear_html_content(self, title, author, target_type):
        """
        Define como NULL o conteúdo HTML de um registro.
        target_type: 'ppb' ou 'ppr'
        """
        column = "ppb_html" if target_type == 'ppb' else "ppr_html"
        try:
            with self.db.get_connection() as conn:
                conn.execute(f"""
                    UPDATE results 
                    SET {column} = NULL 
                    WHERE title = ? AND author = ?
                """, (title, author))
                conn.commit()
            return True
        except Exception as e:
            print(f"Erro ao limpar HTML ({target_type}): {e}")
            return False