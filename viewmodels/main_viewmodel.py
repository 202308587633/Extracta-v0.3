import re
import time
import threading
from models.database import DatabaseModel
from models.scraper import ScraperModel
from models.parsers.vufind_parser import VufindParser # Import necessário para o Passo 2
import config

class MainViewModel: # Certifique-se de que o nome da classe está correto
    def __init__(self, view):
        self.view = view
        self.db = DatabaseModel(db_name=config.DB_NAME)
        self.scraper = ScraperModel()
        self.current_history_id = None

    def start_scraping_command(self):
        url = self.view.get_url_input()
        if not url:
            self._log("Erro: Digite uma URL.", "red")
            return
        self.view.toggle_button(False)
        self.view.display_html_content("Aguarde...")
        self._log(f"Iniciando tarefa para: {url}", "yellow")
        thread = threading.Thread(target=self._run_task, args=(url,))
        thread.start()

    def _run_task(self, url):
        try:
            self._log("Executando: Conectando e baixando HTML...", "yellow")
            html = self.scraper.fetch_html(url)
            self.db.save_scraping(url, html)
            self.view.display_html_content(html)
            self._log("Sucesso! Processo finalizado.", "green")
            self.view.after_thread_safe(self.load_history_list)
        except Exception as e:
            error_msg = f"Falha: {str(e)}"
            self._log(error_msg, "red")
            self.view.display_html_content(error_msg)
        finally:
            self.view.toggle_button(True)

    def scrape_specific_search_url(self, url):
        self._log(f"Iniciando scrap de link específico: {url}", "yellow")
        thread = threading.Thread(target=self._run_specific_scraping_task, args=(url,))
        thread.start()

    def _run_specific_scraping_task(self, url):
        try:
            html = self.scraper.fetch_html(url)
            self.db.save_scraping(url, html)
            self._log("Conteúdo do buscador salvo com sucesso.", "green")
            self.view.after_thread_safe(lambda: self.view.display_content_in_fourth_tab(html))
            self.view.after_thread_safe(self.load_history_list)
        except Exception as e:
            self._log(f"Erro ao raspar link específico: {e}", "red")

    def _log(self, message, color="white"):
        try:
            self.db.save_log(message)
        except:
            pass
        self.view.update_status(message, color)

    def load_history_list(self):
        try:
            items = self.db.get_history_list()
            self.view.update_history_list(items)
        except Exception as e:
            self._log(f"Erro ao carregar histórico: {e}", "red")

    def load_history_details(self, history_id):
        self.current_history_id = history_id
        try:
            html = self.db.get_history_content(history_id)
            self.view.display_history_content(html)
        except Exception as e:
            self._log(f"Erro ao carregar detalhe: {e}", "red")

    def delete_history_item(self):
        if not self.current_history_id: return
        try:
            self.db.delete_history(self.current_history_id)
            self._log(f"Item {self.current_history_id} excluído.", "green")
            self.current_history_id = None
            self.view.display_history_content("")
            self.load_history_list()
        except Exception as e:
            self._log(f"Erro ao excluir item: {e}", "red")

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

    def extract_data_command(self):
        if not self.current_history_id: return
        try:
            result = self.db.get_history_item(self.current_history_id)
            if not result: return
            url, html = result
            self._log("Extraindo dados com parser especializado...", "yellow")
            
            parser = VufindParser()
            data = self.scraper.extract_data(html, parser, base_url=url)
            
            if not data:
                self._log("Nenhum dado encontrado.", "red")
            else:
                self._log(f"Sucesso! {len(data)} itens extraídos.", "green")
                self.view.display_extracted_results(data)
                self.view.switch_to_results_tab()
        except Exception as e:
            self._log(f"Erro na extração: {e}", "red")