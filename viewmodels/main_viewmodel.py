import re
import time
import threading
from models.database import DatabaseModel
from models.scraper import ScraperModel
from models.parsers.vufind_parser import VufindParser # Import necessário para o Passo 2
import config
import os
import tempfile
import webbrowser

class MainViewModel: # Certifique-se de que o nome da classe está correto
    def check_pagination_and_scrape(self):
        if not self.current_history_id: return
        try:
            result = self.db.get_history_item(self.current_history_id)
            if not result: return
            original_url, html = result
            page_numbers = re.findall(r'[?&](?:amp;)?page=(\d+)', html)
            if not page_numbers:
                self._log("Nenhuma paginação numérica encontrada.", "yellow")
                return
            max_page = max(map(int, page_numbers))
            if max_page <= 1: return
            self._log(f"Paginação detectada ({max_page} páginas).", "green")
            thread = threading.Thread(target=self._run_pagination_task, args=(original_url, max_page))
            thread.start()
        except Exception as e:
            self._log(f"Erro na paginação: {e}", "red")

    def __init__(self, view):
        self.view = view
        self.db = DatabaseModel(db_name=config.DB_NAME)
        self.scraper = ScraperModel()
        self.current_history_id = None

    def start_scraping_command(self):
        url = self.view.get_url_input()
        if not url: return
        self.view.toggle_button(False)
        thread = threading.Thread(target=self._run_task, args=(url,))
        thread.start()

    def scrape_specific_search_url(self, url):
        self._log(f"Iniciando scrap de busca: {url}", "yellow")
        thread = threading.Thread(target=self._run_specific_scraping_task, args=(url, 'buscador'))
        thread.start()

    def scrape_repository_url(self, url):
        """Inicia o scrap do link do repositório (PDF/Documento)"""
        self._log(f"Iniciando scrap do repositório: {url}", "yellow")
        thread = threading.Thread(target=self._run_specific_scraping_task, args=(url, 'repositorio'))
        thread.start()

    def delete_history_item(self):
        if not self.current_history_id: 
            self._log("Tentativa de exclusão sem seleção.", "yellow")
            return
        try:
            self.db.delete_history(self.current_history_id)
            self._log(f"Atividade: Item {self.current_history_id} excluído do banco de dados.", "green")
            self.current_history_id = None
            self.view.display_history_content("")
            self.load_history_list()
        except Exception as e:
            self._log(f"Erro Crítico na exclusão: {e}", "red")

    def _log(self, message, color="white"):
        """
        Centraliza todos os logs: 
        1. Persiste a mensagem no Banco de Dados
        2. Atualiza a Barra de Status global na interface
        3. Registra a atividade na aba de Logs
        """
        try:
            self.db.save_log(message)
        except:
            pass
        self.view.update_status(message, color)

    def open_ppb_browser_from_db(self, title, author):
        """
        Recupera o HTML da PPB do banco de dados e abre-o no navegador.
        Garante a integridade dos dados visualizados (conforme capturados).
        """
        self._log(f"Iniciando visualização da PPB no navegador: {title}", "yellow")
        
        try:
            html_content = self.db.get_extracted_html(title, author)
            
            if not html_content:
                self._log("Erro: Não existe código HTML salvo para esta PPB.", "red")
                return

            import tempfile, webbrowser
            with tempfile.NamedTemporaryFile('w', delete=False, suffix='.html', encoding='utf-8') as f:
                f.write(html_content)
                temp_path = f.name

            webbrowser.open(f"file://{temp_path}")
            self._log(f"Sucesso: PPB aberta via ficheiro temporário: {temp_path}", "green")

        except Exception as e:
            self._log(f"Erro ao abrir PPB do banco no navegador: {e}", "red")

    def _run_pagination_task(self, base_url, max_page):
        """Executa o DeepScrap de PLBs: percorre e salva todas as páginas de listagem na tabela 'plb'"""
        try:
            self._log(f"Iniciando DeepScrap de PLBs: total de {max_page} páginas.", "yellow")
            separator = "&" if "?" in base_url else "?"
            
            for i in range(2, max_page + 1):
                if "page=" in base_url:
                    current_url = re.sub(r'page=\d+', f'page={i}', base_url)
                else:
                    current_url = f"{base_url}{separator}page={i}"
                
                self._log(f"Atividade: Capturando PLB {i} de {max_page}...", "yellow")
                
                html = self.scraper.fetch_html(current_url)
                # Atualizado para usar a nova tabela 'plb'
                self.db.save_plb(current_url, html)
                
                time.sleep(1.5)
                
            self._log(f"Sucesso: DeepScrap concluído. {max_page} PLBs armazenadas.", "green")
            self.view.after_thread_safe(self.load_history_list)
        except Exception as e:
            self._log(f"Erro Crítico no DeepScrap de PLBs: {e}", "red")

    def _run_task(self, url):
        """Executa o scrap inicial e salva na tabela 'plb'"""
        try:
            html = self.scraper.fetch_html(url)
            # Atualizado para a nova tabela 'plb'
            self.db.save_plb(url, html)
            self.view.display_html_content(html)
            self.view.after_thread_safe(self.load_history_list)
        except Exception as e:
            self._log(f"Falha: {e}", "red")
        finally:
            self.view.toggle_button(True)

    def load_history_list(self):
        """Atualizado para carregar da nova tabela 'plb'"""
        # Busca id, url e data da tabela plb em vez de history
        items = self.db.get_plb_list() 
        self.view.update_history_list(items)

    def load_history_details(self, history_id):
        """Atualizado para buscar conteúdo da nova tabela 'plb'"""
        self.current_history_id = history_id
        # Busca o HTML da tabela plb pelo ID selecionado
        html = self.db.get_plb_content(history_id) 
        self.view.display_history_content(html)
    
    def initialize_data(self):
        """Carrega o histórico de PLBs e os dados minerados (tabela pesquisas) na inicialização"""
        self.load_history_list()
        try:
            # Atualizado para chamar o método que consulta a tabela 'pesquisas'
            saved_data = self.db.get_all_pesquisas() 
            if saved_data:
                self.view.display_extracted_results(saved_data)
        except Exception as e:
            self._log(f"Erro ao carregar dados salvos: {e}", "red")
            
    def extract_data_command(self):
        """Extrai dados da PLB e salva na tabela 'pesquisas'"""
        if not self.current_history_id: 
            self._log("Selecione uma PLB no histórico para extrair dados.", "yellow")
            return
        try:
            result = self.db.get_history_item(self.current_history_id)
            url, html = result[0], result[1]
            self._log(f"Atividade: Iniciando DeepScrap na PLB: {url}", "yellow")
            
            data = self.scraper.extract_data(html, VufindParser(), base_url=url)
            
            if data:
                # Atualizado para a nova tabela 'pesquisas'
                self.db.save_pesquisas(data) 
                self._log(f"Atividade: {len(data)} pesquisas mineradas e salvas com sucesso.", "green")
                
                # Recupera os dados atualizados da tabela 'pesquisas'
                all_results = self.db.get_all_pesquisas()
                self.view.display_extracted_results(all_results)
                self.view.switch_to_results_tab()
            else:
                self._log("Aviso: Nenhum dado científico encontrado nesta PLB.", "red")
        except Exception as e:
            self._log(f"Erro Crítico na extração: {e}", "red")

    def handle_result_selection(self, title, author):
        """
        Executada a cada seleção de linha. 
        Apenas habilita ou desabilita as abas conforme o banco de dados.
        """
        # Guarda a referência da pesquisa selecionada atualmente
        self.selected_research = {"title": title, "author": author}
        
        # Verifica existência de dados nas novas tabelas 'ppb' e 'plb' (para LAP)
        html_ppb = self.db.get_extracted_html(title, author)
        html_lap = self.db.get_lap_html(title, author)

        # Atualiza o estado das abas na interface
        self.view.set_tab_state("Conteúdo Buscador", "normal" if html_ppb else "disabled")
        self.view.set_tab_state("Conteúdo Repositório", "normal" if html_lap else "disabled")
        
        # Se o usuário já estiver na aba de conteúdo, força a atualização imediata
        self.on_tab_changed()

    def on_tab_changed(self):
        """
        Atualiza o conteúdo da aba selecionada para refletir a pesquisa atual.
        """
        if not hasattr(self, 'selected_research'): return

        current_tab = self.view.tabview.get() # Obtém a aba visível
        title = self.selected_research["title"]
        author = self.selected_research["author"]

        # Carrega o HTML correspondente apenas se a aba estiver ativa
        if current_tab == "Conteúdo Buscador":
            html = self.db.get_extracted_html(title, author)
            if html:
                self.view.content_tab.display_html(html)
        
        elif current_tab == "Conteúdo Repositório":
            html = self.db.get_lap_html(title, author)
            if html:
                self.view.repo_tab.display_html(html)

    def _run_specific_scraping_task(self, url, doc_type='buscador'):
        """Versão refatorada e limpa da tarefa de scraping específico"""
        try:
            html = self.scraper.fetch_html(url)
            
            if doc_type == 'buscador':
                # Salva na tabela 'ppb' vinculando-a à pesquisa correspondente
                self.db.save_ppb_content(url, html)
                self._log(f"PPB capturada e vinculada com sucesso.", "green")
                # O conteúdo será exibido via on_tab_changed se a aba for selecionada
            else:
                # Salva o LAP (repositório) na tabela plb ou equivalente
                self.db.save_plb(url, html)
                self._log(f"Conteúdo do repositório salvo.", "green")
                
            self.view.after_thread_safe(self.load_history_list)
        except Exception as e:
            self._log(f"Erro ao raspar {doc_type}: {e}", "red")