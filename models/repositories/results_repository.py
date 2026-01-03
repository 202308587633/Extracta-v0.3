from .base_repository import BaseRepository
import sqlite3

class ResultsRepository(BaseRepository):
    def get_all(self):
        """
        Retorna todas as pesquisas salvas, incluindo flags indicando 
        se possuem HTML de busca (PPB) e repositório (PPR) salvos.
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            # MODIFICADO: Left Join para verificar existência de conteúdo HTML
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
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        title, author, item.get('ppb_link'), item.get('ppr_link'),
                        '-', 'Pendente', '-', 
                        term, year
                    ))
                    
                    # Recupera o ID gerado para criar as entradas vazias nas tabelas filhas (opcional, mas bom para consistência)
                    pesquisa_id = cursor.lastrowid
                    
                    # Cria entradas iniciais (links) nas tabelas de conteúdo
                    cursor.execute("INSERT OR IGNORE INTO ppb (pesquisa_id, url) VALUES (?, ?)", (pesquisa_id, item.get('ppb_link')))
                    cursor.execute("INSERT OR IGNORE INTO ppr (pesquisa_id, url) VALUES (?, ?)", (pesquisa_id, item.get('ppr_link')))
                    
                    saved_count += 1
                except sqlite3.Error:
                    pass
            
            conn.commit()
            return saved_count

    def get_pending_ppr(self):
        """Retorna lista de (pesquisa_id, ppr_link) que AINDA NÃO têm HTML salvo."""
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
        """Salva o HTML na tabela correta (ppb ou ppr) baseado na URL."""
        table = "ppb" if doc_type == 'buscador' else "ppr"
        with self.db.get_connection() as conn:
            # Atualiza baseando-se na URL que foi baixada
            conn.execute(f"""
                UPDATE {table} 
                SET html_content = ?, extracted_at = CURRENT_TIMESTAMP
                WHERE url = ?
            """, (html, url))
            conn.commit()

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