import threading
import time
from viewmodels.base_viewmodel import BaseViewModel # Vamos criar esse base logo abaixo

class HomeViewModel(BaseViewModel):
    def __init__(self, history_repo, system_repo, scraper, view):
        super().__init__(system_repo)
        self.history_repo = history_repo
        self.scraper = scraper
        self.view = view

    def start_scraping(self):
        """Iniciado pelo botão na Home Tab."""
        url = self.view.get_url_input()
        if not url:
            self._log("URL inválida ou vazia.", "red")
            return
        
        term, year = None, None
        if hasattr(self.view, 'get_current_selection'):
            term, year = self.view.get_current_selection()
        
        self.view.set_button_state(False)
        threading.Thread(target=self._run_scraping_task, args=(url, term, year)).start()

    def _run_scraping_task(self, url, term, year):
        try:
            self._log(f"Iniciando captura: {url}", "yellow")
            html = self.scraper.fetch_html(url)
            
            # Salva usando o repositório, não mais o database.py direto
            self.history_repo.save(url, html, term, year)
            
            # Atualiza UI
            self.view.after_thread_safe(lambda: self.view.home_tab.display_html(html))
            
            # Atualiza status da fonte (bloqueado/desbloqueado)
            self._update_source_status(url, True)
            
            self._log("Página capturada com sucesso!", "green")
            
            # Sinaliza para atualizar a lista de histórico (via callback ou evento)
            if hasattr(self.view, 'refresh_history_callback'):
                self.view.after_thread_safe(self.view.refresh_history_callback)

        except Exception as e:
            self._update_source_status(url, False)
            self._log(f"Erro na captura: {e}", "red")
        finally:
            self.view.set_button_state(True)