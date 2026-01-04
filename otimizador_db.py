import sqlite3
import os
import sys

# Configuração do banco
DB_NAME = "database.db"

# Definição das melhorias ideais (Tabela -> Coluna -> Motivo)
# O script verificará se a coluna existe antes de sugerir o índice.
MELHORIAS_DEFINIDAS = {
    'plb': [
        {'coluna': 'url', 'indice': 'idx_plb_url', 'motivo': 'Acelera verificação de duplicidade de páginas de busca.'},
        {'coluna': 'created_at', 'indice': 'idx_plb_date', 'motivo': 'Melhora ordenação por data.'}
    ],
    'pesquisas': [
        {'coluna': 'link', 'indice': 'idx_pesquisas_link', 'motivo': 'CRÍTICO: Evita baixar o mesmo TCC/Tese duas vezes.'},
        {'coluna': 'url', 'indice': 'idx_pesquisas_url', 'motivo': 'Alternativa para link (legado).'},
        {'coluna': 'status', 'indice': 'idx_pesquisas_status', 'motivo': 'Acelera busca por itens pendentes de processamento.'},
        {'coluna': 'plb_id', 'indice': 'idx_pesquisas_plb_id', 'motivo': 'Acelera junção (JOIN) com a tabela pai PLB.'}
    ],
    'ppr': [
        {'coluna': 'pesquisa_id', 'indice': 'idx_ppr_pesquisa_id', 'motivo': 'Acelera junção (JOIN) com tabela de pesquisas.'},
        {'coluna': 'url', 'indice': 'idx_ppr_url', 'motivo': 'Verificação de unicidade.'}
    ],
    'ppb': [
        {'coluna': 'pesquisa_id', 'indice': 'idx_ppb_pesquisa_id', 'motivo': 'Acelera junção (JOIN) com tabela de pesquisas.'},
        {'coluna': 'titulo', 'indice': 'idx_ppb_titulo', 'motivo': 'Acelera buscas textuais por título.'},
        {'coluna': 'instituicao', 'indice': 'idx_ppb_instituicao', 'motivo': 'Melhora filtros por instituição.'}
    ],
    'logs': [
        {'coluna': 'created_at', 'indice': 'idx_logs_date', 'motivo': 'Acelera limpeza e visualização de logs recentes.'}
    ],
    'sources': [
        {'coluna': 'url', 'indice': 'idx_sources_url', 'motivo': 'Garante unicidade das fontes.'}
    ]
}

def conectar():
    if not os.path.exists(DB_NAME):
        print(f"❌ Erro: O arquivo '{DB_NAME}' não foi encontrado.")
        return None
    return sqlite3.connect(DB_NAME)

def obter_tabelas(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    return [r[0] for r in cursor.fetchall()]

def obter_colunas(conn, tabela):
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({tabela})")
    return [r[1] for r in cursor.fetchall()]

def obter_indices_existentes(conn, tabela):
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA index_list({tabela})")
    return [r[1] for r in cursor.fetchall()]

def analisar_tabela(conn, tabela):
    """Retorna lista de melhorias aplicáveis para a tabela."""
    if tabela not in MELHORIAS_DEFINIDAS:
        return []

    colunas_reais = obter_colunas(conn, tabela)
    indices_reais = obter_indices_existentes(conn, tabela)
    
    sugestoes = []
    
    for melhoria in MELHORIAS_DEFINIDAS[tabela]:
        # Só sugere se a coluna existe na tabela E o índice ainda não existe
        if melhoria['coluna'] in colunas_reais and melhoria['indice'] not in indices_reais:
            sugestoes.append(melhoria)
            
    return sugestoes

def aplicar_indice(conn, tabela, sugestao):
    try:
        cursor = conn.cursor()
        print(f"   ⏳ Criando índice '{sugestao['indice']}' em {tabela}({sugestao['coluna']})...")
        cursor.execute(f"CREATE INDEX IF NOT EXISTS {sugestao['indice']} ON {tabela}({sugestao['coluna']})")
        conn.commit()
        print(f"   ✅ Sucesso!")
    except Exception as e:
        print(f"   ❌ Erro: {e}")

def otimizar_banco(conn):
    print("   🔄 Executando 'VACUUM' e 'ANALYZE' para compactar e atualizar estatísticas...")
    try:
        conn.execute("ANALYZE")
        conn.execute("VACUUM")
        print("   ✅ Otimização geral concluída.")
    except Exception as e:
        print(f"   ⚠️ Aviso: Não foi possível executar VACUUM (o banco pode estar em uso). Erro: {e}")

def menu_principal():
    conn = conectar()
    if not conn:
        return

    while True:
        print("\n" + "="*60)
        print(f"OTIMIZADOR DE PERFORMANCE: {DB_NAME}")
        print("="*60)
        
        tabelas = obter_tabelas(conn)
        tabelas_com_melhorias = {}

        print("Tabelas encontradas e status de otimização:\n")
        
        i = 1
        opcoes_validas = {}

        for tabela in tabelas:
            sugestoes = analisar_tabela(conn, tabela)
            status = "✅ Otimizada" if not sugestoes else f"⚠️  {len(sugestoes)} melhorias disponíveis"
            print(f"  [{i}] {tabela.upper().ljust(15)} - {status}")
            
            if sugestoes:
                tabelas_com_melhorias[i] = (tabela, sugestoes)
                opcoes_validas[i] = tabela
            i += 1

        print("\n  [99] Otimizar TODO o banco (VACUUM + ANALYZE)")
        print("  [0]  Sair")
        print("="*60)

        opcao = input("Escolha uma tabela para ver detalhes ou uma opção: ").strip()

        if opcao == '0':
            print("Saindo...")
            break
        
        if opcao == '99':
            otimizar_banco(conn)
            input("\nPressione Enter para continuar...")
            continue

        if not opcao.isdigit() or int(opcao) not in tabelas_com_melhorias:
            print("❌ Opção inválida ou tabela já está otimizada.")
            input("Pressione Enter para continuar...")
            continue

        # Submenu da tabela
        idx_tabela = int(opcao)
        nome_tabela, sugestoes = tabelas_com_melhorias[idx_tabela]
        
        while True:
            print(f"\n--- Melhorias para tabela: {nome_tabela.upper()} ---")
            for idx, sug in enumerate(sugestoes, 1):
                print(f"  [{idx}] Criar índice em '{sug['coluna']}'")
                print(f"      Motivo: {sug['motivo']}")
            
            print(f"  [A] Aplicar TODAS as sugestões acima")
            print(f"  [V] Voltar")
            
            sub_opt = input("Escolha: ").strip().upper()

            if sub_opt == 'V':
                break
            
            elif sub_opt == 'A':
                confirmar = input(f"Confirma criar {len(sugestoes)} índices em {nome_tabela}? (S/N): ")
                if confirmar.upper() == 'S':
                    for sug in sugestoes:
                        aplicar_indice(conn, nome_tabela, sug)
                    input("\nOperação concluída. Pressione Enter...")
                    break
            
            elif sub_opt.isdigit() and 1 <= int(sub_opt) <= len(sugestoes):
                sug_selecionada = sugestoes[int(sub_opt) - 1]
                aplicar_indice(conn, nome_tabela, sug_selecionada)
                # Remove a sugestão aplicada da lista temporária para atualizar a view
                sugestoes.pop(int(sub_opt) - 1)
                if not sugestoes:
                    print("Todas as melhorias aplicadas nesta tabela!")
                    break
            else:
                print("Opção inválida.")

    conn.close()

if __name__ == "__main__":
    try:
        menu_principal()
    except KeyboardInterrupt:
        print("\nOperação cancelada pelo usuário.")