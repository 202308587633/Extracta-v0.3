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
    def _log(self, message, color="white"):
        self.db.save_log(message)
        self.view.update_status(message, color)
        
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
        try:
            separator = "&" if "?" in base_url else "?"
            for i in range(2, max_page + 1):
                current_url = re.sub(r'page=\d+', f'page={i}', base_url) if "page=" in base_url else f"{base_url}{separator}page={i}"
                self._log(f"Capturando Página {i}/{max_page}...", "yellow")
                html = self.scraper.fetch_html(current_url)
                self.db.save_scraping(current_url, html)
                time.sleep(1)
            self._log("Ciclo de paginação concluído.", "green")
            self.view.after_thread_safe(self.load_history_list)
        except Exception as e:
            self._log(f"Erro no loop: {e}", "red")

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

    def delete_history_item(self):
        if self.current_history_id:
            self.db.delete_history(self.current_history_id)
            self.current_history_id = None
            self.load_history_list()

    def scrape_specific_search_url(self, url):
        self._log(f"Iniciando scrap de busca: {url}", "yellow")
        thread = threading.Thread(target=self._run_specific_scraping_task, args=(url, 'buscador'))
        thread.start()

    def extract_data_command(self):
        if not self.current_history_id: return
        try:
            from models.parsers.vufind_parser import VufindParser
            result = self.db.get_history_item(self.current_history_id)
            url, html = result[0], result[1]
            data = self.scraper.extract_data(html, VufindParser(), base_url=url)
            if data:
                self.db.save_extracted_results(data)
                self.view.display_extracted_results(self.db.get_all_extracted_results())
                self.view.switch_to_results_tab()
        except Exception as e:
            self._log(f"Erro na extração: {e}", "red")

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

    def _run_specific_scraping_task(self, url, doc_type='buscador'):
        try:
            html = self.scraper.fetch_html(url)
            self.db.save_scraping(url, html, doc_type)
            self._log(f"HTML do {doc_type} salvo com sucesso.", "green")
            
            # Direciona para a aba correta baseado no tipo
            if doc_type == 'buscador':
                self.view.after_thread_safe(lambda: self.view.display_content_in_fourth_tab(html))
            else:
                self.view.after_thread_safe(lambda: self.view.display_repo_content(html))
                
            self.view.after_thread_safe(self.load_history_list)
        except Exception as e:
            self._log(f"Erro ao raspar {doc_type}: {e}", "red")

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