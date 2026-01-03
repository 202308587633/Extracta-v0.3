from .base_repository import BaseRepository
import sqlite3

class HistoryRepository(BaseRepository):
    def get_all(self):
        """Retorna histórico para a tabela."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    SELECT id, url, created_at, search_term, search_year 
                    FROM plb ORDER BY created_at DESC
                """)
            except sqlite3.OperationalError:
                # Fallback para compatibilidade
                cursor.execute("SELECT id, url, created_at, NULL, NULL FROM plb ORDER BY created_at DESC")
            return cursor.fetchall()

    def get_by_id(self, plb_id):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, url, html_content, search_term, search_year 
                FROM plb WHERE id = ?
            """, (plb_id,))
            return cursor.fetchone()

    def save(self, url, html_content, term=None, year=None):
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO plb (url, html_content, search_term, search_year) 
                    VALUES (?, ?, ?, ?)
                """, (url, html_content, term, year))
                conn.commit()
        except sqlite3.Error as e:
            raise Exception(f"Erro ao salvar PLB: {e}")

    def delete(self, plb_id):
        with self.db.get_connection() as conn:
            conn.execute("DELETE FROM plb WHERE id = ?", (plb_id,))
            conn.commit()

    def check_url_exists(self, url):
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM plb WHERE url = ? LIMIT 1", (url,))
                return cursor.fetchone() is not None
        except sqlite3.Error:
            return False

    def get_existing_searches(self):
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT DISTINCT search_term, search_year 
                    FROM plb 
                    WHERE search_term IS NOT NULL AND search_term != ''
                """)
                return cursor.fetchall()
        except sqlite3.Error:
            return []
