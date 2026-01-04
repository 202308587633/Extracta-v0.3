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

    def clear_all_tables(self):
        """Limpa todas as tabelas (Zera o banco)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys = OFF;")
            
            tables = ['ppb', 'ppr', 'pesquisas', 'plb', 'logs', 'sources']
            for table in tables:
                cursor.execute(f"DELETE FROM {table}")
                cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table}'")
            
            cursor.execute("PRAGMA foreign_keys = ON;")
            conn.commit()

    def _init_schema(self):
        """Cria as tabelas se não existirem (para novos bancos)."""
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
                    plb_id INTEGER,
                    titulo TEXT,
                    link TEXT,
                    status TEXT DEFAULT 'pending', -- pending, processed, error
                    search_term TEXT,  -- Coluna adicionada via migração
                    search_year TEXT,   -- Coluna adicionada via migração
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (plb_id) REFERENCES plb(id)
                )
            """)
            
            # Tabela PPR (Páginas de Pesquisa e Resultado - Detalhes)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ppr (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pesquisa_id INTEGER,
                    url TEXT,
                    html_content TEXT,
                    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Coluna adicionada via migração
                    FOREIGN KEY (pesquisa_id) REFERENCES pesquisas(id)
                )
            """)
            
            # Tabela PPB (Páginas de Pesquisa e Busca - Detalhes finais)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ppb (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pesquisa_id INTEGER,
                    titulo TEXT,
                    autor TEXT,
                    orientador TEXT,
                    resumo TEXT,
                    palavras_chave TEXT,
                    data_defesa TEXT,
                    instituicao TEXT,
                    programa TEXT,
                    link_pdf TEXT,
                    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Coluna adicionada via migração
                    FOREIGN KEY (pesquisa_id) REFERENCES pesquisas(id)
                )
            """)

            # Tabela de Logs de Erro
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT,
                    erro TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Tabela de Sources (URLs base para busca)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL UNIQUE,
                    nome TEXT,
                    ativo BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            
            # Cria índices para melhorar performance
            self._create_indexes(conn)

    def _create_indexes(self, conn):
        """Cria índices no banco de dados para melhorar a performance de consultas."""
        cursor = conn.cursor()
        
        # Índices para tabela 'pesquisas'
        #cursor.execute("CREATE INDEX IF NOT EXISTS idx_pesquisas_link ON pesquisas(link)")
        #cursor.execute("CREATE INDEX IF NOT EXISTS idx_pesquisas_status ON pesquisas(status)")
        #cursor.execute("CREATE INDEX IF NOT EXISTS idx_pesquisas_plb_id ON pesquisas(plb_id)")
        
        # Índices para tabela 'ppr'
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ppr_pesquisa_id ON ppr(pesquisa_id)")
        
        # Índices para tabela 'ppb'
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ppb_pesquisa_id ON ppb(pesquisa_id)")
        
        # Índices para tabela 'plb'
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_plb_url ON plb(url)")
        
        conn.commit()

    def _run_migrations(self):
        """Roda scripts de migração para atualizar bancos existentes sem perder dados."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Verifica colunas na tabela 'pesquisas'
            cursor.execute("PRAGMA table_info(pesquisas)")
            cols_pesq = [info[1] for info in cursor.fetchall()]
            
            if 'search_term' not in cols_pesq:
                cursor.execute("ALTER TABLE pesquisas ADD COLUMN search_term TEXT")
            if 'search_year' not in cols_pesq:
                cursor.execute("ALTER TABLE pesquisas ADD COLUMN search_year TEXT")
            
            # --- NOVA MIGRAÇÃO: Corrigir erro 'no such column: extracted_at' ---
            
            # Para tabela PPB
            cursor.execute("PRAGMA table_info(ppb)")
            cols_ppb = [info[1] for info in cursor.fetchall()]
            if 'extracted_at' not in cols_ppb:
                cursor.execute("ALTER TABLE ppb ADD COLUMN extracted_at TIMESTAMP")
            
            # Para tabela PPR
            cursor.execute("PRAGMA table_info(ppr)")
            cols_ppr = [info[1] for info in cursor.fetchall()]
            if 'extracted_at' not in cols_ppr:
                cursor.execute("ALTER TABLE ppr ADD COLUMN extracted_at TIMESTAMP")
            
            conn.commit()
            
            # Aplica índices em bancos existentes durante a migração
            self._create_indexes(conn)