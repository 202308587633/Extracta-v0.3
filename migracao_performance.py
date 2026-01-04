import sqlite3
import os

def migrar_banco(db_name="extracta.db"):
    """
    Aplica índices de performance ao banco de dados existente.
    Não apaga dados.
    """
    if not os.path.exists(db_name):
        print(f"O arquivo de banco de dados '{db_name}' não foi encontrado.")
        print("Execute o programa principal primeiro para gerar o banco, ou verifique o caminho.")
        return

    print(f"Iniciando otimização do banco de dados: {db_name}...")
    
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        # 1. Índice para Link PDF (Critical para verificação de duplicidade)
        print("- Criando índice para link_pdf na tabela resultados...")
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_resultados_link_pdf ON resultados (link_pdf)')

        # 2. Índice para Sigla (Filtros rápidos)
        print("- Criando índice para sigla na tabela resultados...")
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_resultados_sigla ON resultados (sigla)')

        # 3. Índice para Data de Coleta (Relatórios)
        print("- Criando índice para data_coleta na tabela resultados...")
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_resultados_data_coleta ON resultados (data_coleta)')

        # 4. Índice para Data de Execução (Ordenação do histórico)
        print("- Criando índice para data_execucao na tabela historico...")
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_historico_data ON historico (data_execucao)')

        # Otimização: Analisar estatísticas para o planejador de consultas do SQLite
        print("- Otimizando estatísticas do banco (ANALYZE)...")
        cursor.execute('ANALYZE')

        conn.commit()
        conn.close()
        print("✅ Migração concluída com sucesso! Performance aprimorada.")

    except sqlite3.Error as e:
        print(f"❌ Erro durante a migração: {e}")

if __name__ == "__main__":
    migrar_banco()