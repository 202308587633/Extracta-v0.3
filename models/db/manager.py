import sqlite3
import config

class DatabaseManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.db_name = config.DB_NAME
        self._init_schema()
        self._run_migrations()

    def get_connection(self):
        """Retorna uma nova conexão com o banco."""
        return sqlite3.connect(self.db_name, check_same_thread=False)

    def _init_schema(self):
        """Cria as tabelas se não existirem."""
        with self.get_connection() as conn:
            conn.execute("PRAGMA journal_mode=WAL;")
            cursor = conn.cursor()
            
            # Tabela PLB (Páginas de Lista de Busca - Histórico)
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
            
            # Tabela Pesquisas (Resultados extraídos)
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
            
            # Tabelas de Conteúdo (PPB e PPR)
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
                CREATE TABLE IF NOT EXISTS ppr (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pesquisa_id INTEGER,
                    url TEXT NOT NULL,
                    html_content TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (pesquisa_id) REFERENCES pesquisas(id) ON DELETE CASCADE
                )
            """)
            
            # Tabelas Auxiliares
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sources (
                    root_url TEXT PRIMARY KEY,
                    status INTEGER DEFAULT 1
                )
            """)
            conn.commit()

    def _run_migrations(self):
        """Aplica alterações estruturais em bancos existentes."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Migração para PLB
            cursor.execute("PRAGMA table_info(plb)")
            cols_plb = [info[1] for info in cursor.fetchall()]
            if 'search_term' not in cols_plb:
                cursor.execute("ALTER TABLE plb ADD COLUMN search_term TEXT")
            if 'search_year' not in cols_plb:
                cursor.execute("ALTER TABLE plb ADD COLUMN search_year TEXT")

            # Migração para Pesquisas
            cursor.execute("PRAGMA table_info(pesquisas)")
            cols_pesq = [info[1] for info in cursor.fetchall()]
            if 'search_term' not in cols_pesq:
                cursor.execute("ALTER TABLE pesquisas ADD COLUMN search_term TEXT")
            if 'search_year' not in cols_pesq:
                cursor.execute("ALTER TABLE pesquisas ADD COLUMN search_year TEXT")
            
            conn.commit()
            
    def clear_all_tables(self):
        """Limpa todas as tabelas (Zera o banco)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Desativa chaves estrangeiras temporariamente
            cursor.execute("PRAGMA foreign_keys = OFF;")
            
            tables = ['ppb', 'ppr', 'pesquisas', 'plb', 'logs', 'sources']
            for table in tables:
                cursor.execute(f"DELETE FROM {table}")
                # Reinicia o contador de ID (Auto Increment)
                cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table}'")
            
            cursor.execute("PRAGMA foreign_keys = ON;")
            conn.commit()