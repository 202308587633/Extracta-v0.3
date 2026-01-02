import sqlite3
import os

# Nome do arquivo do banco de dados (verifique se é este mesmo no seu config.py)
DB_NAME = "database.db"

def limpar_tabela_pesquisas():
    if not os.path.exists(DB_NAME):
        print(f"❌ Erro: O arquivo '{DB_NAME}' não foi encontrado nesta pasta.")
        return

    try:
        # Conecta ao banco
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # Habilita chaves estrangeiras para garantir que o CASCADE funcione
        # (Isso garante que apagar a pesquisa apague também os PPBs e PPRs associados)
        cursor.execute("PRAGMA foreign_keys = ON;")

        # Verifica quantos registros existem
        cursor.execute("SELECT COUNT(*) FROM pesquisas")
        total = cursor.fetchone()[0]

        print(f"📊 Estado atual do banco '{DB_NAME}':")
        print(f"   -> {total} registros na tabela 'pesquisas'.")

        if total == 0:
            print("\n✅ O banco já está vazio. Nenhuma ação necessária.")
            conn.close()
            return

        # Solicita confirmação do usuário
        confirmacao = input("\n⚠️  ATENÇÃO: Isso apagará TODOS os resultados e seus links associados.\n   Deseja continuar? (s/n): ").strip().lower()

        if confirmacao == 's':
            print("\nApagando registros...")
            
            # 1. Apaga os dados
            cursor.execute("DELETE FROM pesquisas")
            
            # 2. Reinicia o contador de IDs (AUTOINCREMENT) para 1
            # (Opcional, mas útil para deixar o banco limpo)
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='pesquisas'")
            
            conn.commit()
            print("✅ Sucesso! Todas as pesquisas foram removidas e o contador de IDs reiniciado.")
        else:
            print("❌ Operação cancelada pelo usuário.")

    except sqlite3.Error as e:
        print(f"❌ Erro no SQLite: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    limpar_tabela_pesquisas()
    input("\nPressione Enter para sair...")