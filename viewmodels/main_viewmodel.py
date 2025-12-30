import re
import time
import threading
from models.database import DatabaseModel
from models.scraper import ScraperModel
import config

class MainViewModel:
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
            
            self._log("Executando: Salvando dados no banco...", "yellow")
            self.db.save_scraping(url, html)
            
            self._log("Executando: Renderizando conteúdo na tela...", "green")
            self.view.display_html_content(html)
            
            self._log("Sucesso! Processo finalizado.", "green")
            
            self.view.after_thread_safe(self.load_history_list)
            
        except Exception as e:
            error_msg = f"Falha: {str(e)}"
            self._log(error_msg, "red")
            self.view.display_html_content(error_msg)
        finally:
            self.view.toggle_button(True)

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
        if not self.current_history_id:
            return

        try:
            self.db.delete_history(self.current_history_id)
            self._log(f"Item {self.current_history_id} excluído com sucesso.", "green")
            
            self.current_history_id = None
            self.view.display_history_content("")
            self.load_history_list()
            
        except Exception as e:
            self._log(f"Erro ao excluir item: {e}", "red")

    def check_pagination_and_scrape(self):
        if not self.current_history_id:
            return

        try:
            result = self.db.get_history_item(self.current_history_id)
            if not result:
                return
            original_url, html = result

            page_numbers = re.findall(r'[?&](?:amp;)?page=(\d+)', html)
            
            if not page_numbers:
                self._log("Nenhuma paginação numérica encontrada neste HTML.", "yellow")
                return

            max_page = max(map(int, page_numbers))
            
            if max_page <= 1:
                self._log("Apenas 1 página detectada.", "yellow")
                return

            self._log(f"Paginação detectada! Total: {max_page} páginas. Iniciando captura...", "green")
            self.view.toggle_button(False)

            thread = threading.Thread(
                target=self._run_pagination_task, 
                args=(original_url, max_page)
            )
            thread.start()

        except Exception as e:
            self._log(f"Erro na análise de paginação: {e}", "red")

    def _run_pagination_task(self, base_url, max_page):
        try:
            separator = "&" if "?" in base_url else "?"
            
            for i in range(2, max_page + 1):
                if "page=" in base_url:
                    current_url = re.sub(r'page=\d+', f'page={i}', base_url)
                else:
                    current_url = f"{base_url}{separator}page={i}"

                self._log(f"Capturando Página {i}/{max_page}...", "yellow")
                
                html = self.scraper.fetch_html(current_url)
                self.db.save_scraping(current_url, html)
                
                time.sleep(1)

            self._log(f"Ciclo completo! {max_page} páginas capturadas.", "green")
            self.view.after_thread_safe(self.load_history_list)

        except Exception as e:
            self._log(f"Erro no loop de paginação: {e}", "red")
        finally:
            self.view.toggle_button(True)
