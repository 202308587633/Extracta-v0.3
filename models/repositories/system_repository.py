from .base_repository import BaseRepository
import sqlite3

class SystemRepository(BaseRepository):
    def log_event(self, message):
        """Salva log no banco."""
        try:
            with self.db.get_connection() as conn:
                conn.execute("INSERT INTO logs (message) VALUES (?)", (message,))
                conn.commit()
        except Exception as e:
            print(f"Erro ao salvar log: {e}")

    def update_source_status(self, root_url, status):
        """Atualiza status da fonte (1=Ativo, 0=Inativo/Erro)."""
        try:
            with self.db.get_connection() as conn:
                conn.execute("""
                    INSERT INTO sources (root_url, status) VALUES (?, ?)
                    ON CONFLICT(root_url) DO UPDATE SET status = excluded.status
                """, (root_url, 1 if status else 0))
                conn.commit()
        except Exception as e:
            print(f"Erro ao atualizar source: {e}")

    def get_disabled_sources(self):
        """Retorna lista de URLs raízes que estão desativadas (status = 0)."""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT root_url FROM sources WHERE status = 0 ORDER BY root_url")
                return [row[0] for row in cursor.fetchall()]
        except:
            return []

    def is_source_allowed(self, url):
        """Verifica se a URL raiz está marcada como ativa (1)."""
        from urllib.parse import urlparse
        try:
            parsed = urlparse(url)
            # Padronização: Sempre usa scheme + netloc (https://site.com)
            root = f"{parsed.scheme}://{parsed.netloc}"
            
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT status FROM sources WHERE root_url = ?", (root,))
                res = cursor.fetchone()
                # Se não existe, assume permitido (1). Se existe, retorna status.
                if res is None: return True
                return res[0] == 1
        except:
            return True

    def get_sources(self):
        """Retorna dicionário {url: status} de todas as fontes."""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT root_url, status FROM sources")
                return {row[0]: row[1] for row in cursor.fetchall()}
        except:
            return {}
