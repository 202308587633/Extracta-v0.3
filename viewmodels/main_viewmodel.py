import threading
from models.database import DatabaseModel
from models.scraper import ScraperModel
import config

class MainViewModel:
    def __init__(self, view):
        self.view = view
        # Injeção do nome do banco via config
        self.db = DatabaseModel(db_name=config.DB_NAME)
        self.scraper = ScraperModel()

    def start_scraping_command(self):
        url = self.view.get_url_input()
        
        if not url:
            self.view.update_status("Erro: Digite uma URL.", "red")
            return

        self.view.update_status("Processando...", "yellow")
        self.view.toggle_button(False)
        self.view.display_html_content("Aguarde...")

        thread = threading.Thread(target=self._run_task, args=(url,))
        thread.start()

    def _run_task(self, url):
        try:
            html = self.scraper.fetch_html(url)
            self.db.save_scraping(url, html)
            self.view.update_status("Sucesso! Salvo no Banco de Dados.", "green")
            self.view.display_html_content(html)
        except Exception as e:
            self.view.update_status(f"Falha: {str(e)}", "red")
            self.view.display_html_content(f"Erro: {str(e)}")
        finally:
            self.view.toggle_button(True)