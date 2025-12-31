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

    def _run_pagination_task(self, base_url, max_page):
        """Executa o DeepScrap de PLBs: percorre e salva todas as páginas de listagem"""
        try:
            self._log(f"Iniciando DeepScrap de PLBs: total de {max_page} páginas.", "yellow")
            
            # O separador depende se a URL já tem parâmetros (?) ou não
            separator = "&" if "?" in base_url else "?"
            
            for i in range(2, max_page + 1):
                # Constrói a URL da próxima PLB (ajustar conforme o buscador, ex: &page=i)
                if "page=" in base_url:
                    current_url = re.sub(r'page=\d+', f'page={i}', base_url)
                else:
                    current_url = f"{base_url}{separator}page={i}"
                
                self._log(f"Atividade: Capturando PLB {i} de {max_page}...", "yellow")
                
                # Faz o download e salva no banco como tipo 'PLB'
                html = self.scraper.fetch_html(current_url)
                self.db.save_scraping(current_url, html, doc_type='PLB')
                
                # Pausa técnica para evitar bloqueio pelo servidor (polidez do bot)
                time.sleep(1.5)
                
            self._log(f"Sucesso: DeepScrap concluído. {max_page} PLBs armazenadas.", "green")
            self.view.after_thread_safe(self.load_history_list)
            
        except Exception as e:
            self._log(f"Erro Crítico no DeepScrap de PLBs: {e}", "red")            

    def _run_repo_scraping_task(self, url):
        try:
            html = self.scraper.fetch_html(url)
            self.db.save_scraping(url, html, doc_type='repositorio')
            self._log("HTML do repositório salvo com sucesso.", "green")
            
            # Atualiza a 5ª aba e a lista de histórico
            self.view.after_thread_safe(lambda: self.view.display_repo_content(html))
            self.view.after_thread_safe(self.load_history_list)
        except Exception as e:
            self._log(f"Erro ao raspar repositório: {e}", "red")

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

    def _run_task(self, url):
        try:
            html = self.scraper.fetch_html(url)
            self.db.save_scraping(url, html)
            self.view.display_html_content(html)
            self.view.after_thread_safe(self.load_history_list)
        except Exception as e:
            self._log(f"Falha: {e}", "red")
        finally:
            self.view.toggle_button(True)

    def load_history_list(self):
        items = self.db.get_history_list()
        self.view.update_history_list(items)

    def load_history_details(self, history_id):
        self.current_history_id = history_id
        html = self.db.get_history_content(history_id)
        self.view.display_history_content(html)

    def scrape_specific_search_url(self, url):
        self._log(f"Iniciando scrap de busca: {url}", "yellow")
        thread = threading.Thread(target=self._run_specific_scraping_task, args=(url, 'buscador'))
        thread.start()

    def initialize_data(self):
        """Carrega o histórico e os dados minerados na inicialização"""
        self.load_history_list()
        try:
            saved_data = self.db.get_all_extracted_results()
            if saved_data:
                self.view.display_extracted_results(saved_data)
        except Exception as e:
            self._log(f"Erro ao carregar dados salvos: {e}", "red")

    def scrape_repository_url(self, url):
        """Inicia o scrap do link do repositório (PDF/Documento)"""
        self._log(f"Iniciando scrap do repositório: {url}", "yellow")
        thread = threading.Thread(target=self._run_specific_scraping_task, args=(url, 'repositorio'))
        thread.start()

    def open_html_in_browser(self):
        """Recupera o HTML do banco e abre em uma aba do navegador"""
        if not self.current_history_id:
            self._log("Selecione um item do histórico primeiro.", "red")
            return
        try:
            html_content = self.db.get_history_content(self.current_history_id)
            if not html_content: return

            with tempfile.NamedTemporaryFile('w', delete=False, suffix='.html', encoding='utf-8') as f:
                f.write(html_content)
                temp_path = f.name
            webbrowser.open(f"file://{temp_path}")
        except Exception as e:
            self._log(f"Erro ao abrir no navegador: {e}", "red")
           
    def open_repo_html_in_browser(self):
        """Recupera o HTML do repositório do banco e abre no navegador"""
        self._log("Iniciando abertura do HTML do repositório no navegador...", "yellow")
        
        if not self.current_history_id:
            self._log("Erro: Nenhum item selecionado no histórico.", "red")
            return

        try:
            # Recupera o conteúdo HTML do banco de dados
            html_content = self.db.get_history_content(self.current_history_id)
            
            if not html_content:
                self._log("Erro: Conteúdo HTML do repositório está vazio.", "red")
                return

            # Log de atividade de banco de dados
            self._log(f"Atividade: HTML recuperado para o ID {self.current_history_id}.", "green")

            import tempfile, webbrowser
            with tempfile.NamedTemporaryFile('w', delete=False, suffix='.html', encoding='utf-8') as f:
                f.write(html_content)
                temp_path = f.name

            webbrowser.open(f"file://{temp_path}")
            self._log(f"Sucesso: Repositório aberto via arquivo temporário: {temp_path}", "green")

        except Exception as e:
            self._log(f"Erro Crítico ao abrir repositório: {e}", "red")

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

    def extract_data_command(self):
        """Executa a mineração de PPBs e LAPs a partir de uma PLB selecionada"""
        if not self.current_history_id: 
            self._log("Selecione uma PLB no histórico para extrair dados.", "yellow")
            return
        try:
            result = self.db.get_history_item(self.current_history_id)
            url, html = result[0], result[1]
            self._log(f"Atividade: Iniciando DeepScrap na PLB: {url}", "yellow")
            
            data = self.scraper.extract_data(html, VufindParser(), base_url=url)
            
            if data:
                self.db.save_extracted_results(data)
                self._log(f"Atividade: {len(data)} pesquisas mineradas e salvas com sucesso.", "green")
                self.view.display_extracted_results(self.db.get_all_extracted_results())
                self.view.switch_to_results_tab()
            else:
                self._log("Aviso: Nenhum dado científico encontrado nesta PLB.", "red")
        except Exception as e:
            self._log(f"Erro Crítico na extração: {e}", "red")

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

    def _run_specific_scraping_task(self, url, doc_type='buscador'):
        """
        Unifica a tarefa de scraping para diferentes tipos de documentos (Buscador/PLB ou Repositório/PPB)
        """
        try:
            html = self.scraper.fetch_html(url)
            self.db.save_scraping(url, html, doc_type)
            self._log(f"Atividade: HTML do {doc_type} salvo com sucesso.", "green")
            
            # Direciona o conteúdo para a aba correspondente baseada no doc_type
            if doc_type == 'buscador':
                self.view.after_thread_safe(lambda: self.view.display_content_in_fourth_tab(html))
            else:
                self.view.after_thread_safe(lambda: self.view.display_repo_content(html))
                
            self.view.after_thread_safe(self.load_history_list)
        except Exception as e:
            self._log(f"Erro ao raspar {doc_type}: {e}", "red")

    def handle_result_selection(self, title, author):
        """
        Gerencia a seleção de uma pesquisa na lista de resultados.
        Verifica a existência de HTML salvo (PPB e LAP) e atualiza as abas.
        """
        # 1. Tenta recuperar o HTML da PPB (Página da Pesquisa)
        html_ppb = self.db.get_extracted_html(title, author)
        if html_ppb:
            self.view.display_content_in_fourth_tab(html_ppb)
            self.view.set_tab_state("Conteúdo Buscador", "normal")
            self._log(f"Atividade: PPB de '{title}' carregada do banco.", "green")
        else:
            self.view.set_tab_state("Conteúdo Buscador", "disabled")
            self._log(f"Aviso: PPB de '{title}' não possui HTML salvo.", "yellow")

        # 2. Tenta recuperar o HTML do LAP (Link de Acesso ao PDF / Repositório)
        html_lap = self.db.get_lap_html(title, author)
        if html_lap:
            self.view.display_repo_content(html_lap)
            self.view.set_tab_state("Conteúdo Repositório", "normal")
        else:
            self.view.set_tab_state("Conteúdo Repositório", "disabled")

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