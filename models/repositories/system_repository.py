from .base_repository import BaseRepository

class SystemRepository(BaseRepository):
    def log(self, message):
        with self.db.get_connection() as conn:
            conn.execute("INSERT INTO logs (message) VALUES (?)", (message,))
            conn.commit()

    def get_sources(self):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT root_url, status FROM sources")
            return {row[0]: bool(row[1]) for row in cursor.fetchall()}

    def update_source_status(self, root_url, status):
        val = 1 if status else 0
        with self.db.get_connection() as conn:
            conn.execute("""
                INSERT INTO sources (root_url, status) VALUES (?, ?)
                ON CONFLICT(root_url) DO UPDATE SET status = excluded.status
            """, (root_url, val))
            conn.commit()

    def get_source_status(self, root_url):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT status FROM sources WHERE root_url = ?", (root_url,))
            res = cursor.fetchone()
            return bool(res[0]) if res else True