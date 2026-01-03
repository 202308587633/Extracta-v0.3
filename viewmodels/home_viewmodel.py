import threading
import time
from viewmodels.base_viewmodel import BaseViewModel 

class HomeViewModel(BaseViewModel):
    def __init__(self, history_repo, system_repo, scraper, view):
        # Passamos 'view' para o BaseViewModel habilitar o log na tela
        super().__init__(system_repo, view)
        self.history_repo = history_repo
        self.scraper = scraper

    def start_scraping(self):
        url = self.view.get_url_input()
        if not url:
            self._log("Tentativa de iniciar sem URL válida.", "red")
            return
        
        term, year = self.view.get_current_selection()
        self._log(f"Iniciando processo para: {term} ({year})", "yellow")
        
        self.view.set_button_state(False)
        threading.Thread(target=self._run_scraping_task, args=(url, term, year)).start()

    def _run_scraping_task(self, url, term, year):
        try:
            self._log(f"Conectando a: {url}", "white")
            html = self.scraper.fetch_html(url)
            
            if not html:
                self._log("HTML vazio recebido. Verifique sua conexão.", "red")
                return

            self._log("Página baixada. Salvando no histórico...", "white")
            self.history_repo.save(url, html, term, year)
            
            self.view.after_thread_safe(lambda: self.view.home_tab.display_html(html))
            self._update_source_status(url, True)
            
            self._log("✅ Pesquisa inicial capturada com sucesso!", "green")
            
            # Atualiza lista de histórico
            if hasattr(self.view, 'refresh_history_callback'):
                self.view.after_thread_safe(self.view.refresh_history_callback)

        except Exception as e:
            self._update_source_status(url, False)
            self._log(f"❌ Erro crítico na captura: {e}", "red")
        finally:
            self.view.set_button_state(True)