import threading
from models.database import DatabaseModel
from models.scraper import ScraperModel
import config

class MainViewModel:
    def __init__(self, view):
        self.view = view
        self.db = DatabaseModel(db_name=config.DB_NAME)
        self.scraper = ScraperModel()

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
