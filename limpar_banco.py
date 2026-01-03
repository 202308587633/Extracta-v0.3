import sqlite3
import os
import sys
import config

def connect_db():
    """Conecta ao banco de dados definido no config."""
    db_path = config.DB_NAME
    if not os.path.exists(db_path):
        print(f"❌ Banco de dados '{db_path}' não encontrado.")
        return None
    return sqlite3.connect(db_path)

def clean_tables(level):
    """
    Executa a limpeza baseada no nível escolhido.
    Level 1: Resultados (pesquisas, ppb, ppr)
    Level 2: Resultados + Histórico (plb)
    Level 3: Tudo (inclui logs e sources)
    """
    conn = connect_db()
    if not conn: return

    cursor = conn.cursor()
    
    try:
        # Desativa chaves estrangeiras para permitir limpeza rápida
        cursor.execute("PRAGMA foreign_keys = OFF;")
        
        tables_to_clean = []
        
        # --- Nível 1: Apenas Resultados (Dados Extraídos) ---
        if level >= 1:
            tables_to_clean.extend(['ppb', 'ppr', 'pesquisas'])
            print("Target: Dados extraídos (Pesquisas, HTMLs)...")

        # --- Nível 2: Histórico de Navegação ---
        if level >= 2:
            tables_to_clean.append('plb')
            print("Target: Histórico de navegação (PLB)...")

        # --- Nível 3: Sistema (Logs e Fontes) ---
        if level >= 3:
            tables_to_clean.extend(['logs', 'sources'])
            print("Target: Logs e status de fontes...")

        # Executa a limpeza e reseta os IDs
        for table in tables_to_clean:
            # Verifica se a tabela existe antes de tentar apagar
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if cursor.fetchone():
                cursor.execute(f"DELETE FROM {table}")
                cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table}'") # Reseta o ID (AutoIncrement)
                print(f"   ✓ Tabela '{table}' limpa.")

        cursor.execute("PRAGMA foreign_keys = ON;")
        conn.commit()
        
        # Otimiza o arquivo do banco após deleção em massa
        print("Dataset limpo. Otimizando banco de dados (VACUUM)...")
        cursor.execute("VACUUM;") 
        
        print("\n✅ Limpeza concluída com sucesso!")

    except sqlite3.Error as e:
        print(f"\n❌ Erro ao limpar banco: {e}")
        conn.rollback()
    finally:
        conn.close()

def main():
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("="*40)
        print(f"   MANUTENÇÃO DE BANCO: {config.DB_NAME}")
        print("="*40)
        print("Selecione o nível de limpeza:")
        print("\n[1] Limpar APENAS RESULTADOS")
        print("    (Mantém o histórico 'Já Pesquisado' na Home)")
        print("\n[2] Limpar RESULTADOS e HISTÓRICO (PLBs)")
        print("    (Reseta toda a mineração, mantém logs e fontes)")
        print("\n[3] RESET TOTAL (Fábrica)")
        print("    (Apaga absolutamente tudo)")
        print("\n[0] Sair")
        print("-" * 40)
        
        try:
            choice = input("Opção: ").strip()
            
            if choice == '0':
                print("Saindo...")
                break
            
            if choice in ['1', '2', '3']:
                confirm = input(f"\n⚠️  Tem certeza que deseja executar a opção {choice}? [s/N]: ").lower()
                if confirm == 's':
                    clean_tables(int(choice))
                    input("\nPressione ENTER para continuar...")
                else:
                    print("Operação cancelada.")
                    time.sleep(1)
            else:
                print("Opção inválida.")
        except KeyboardInterrupt:
            print("\nSaindo...")
            break
        except Exception as e:
            print(f"Erro: {e}")
            input("Enter para continuar...")

if __name__ == "__main__":
    # Import time apenas se for rodar o script (evita erro de import circular se usado como módulo)
    import time
    main()