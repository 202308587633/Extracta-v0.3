import threading
import time
import webbrowser
from viewmodels.base_viewmodel import BaseViewModel

class ResultsViewModel(BaseViewModel):
    def __init__(self, results_repo, system_repo, scraper, view):
        super().__init__(system_repo)
        self.repo = results_repo
        self.scraper = scraper
        self.view = view

    def load_results(self):
        """Carrega dados do banco para a tabela."""
        data = self.repo.get_all()
        self.view.after_thread_safe(lambda: self.view.results_tab.display_results(data))

    def scrape_pending_pprs(self):
        """Baixa HTMLs de repositórios que ainda não temos."""
        pending = self.repo.get_pending_ppr()
        if not pending:
            self._log("Nenhum HTML pendente para baixar.", "green")
            return

        self._log(f"Baixando {len(pending)} pendentes...", "yellow")
        threading.Thread(target=self._run_batch_download, args=(pending,)).start()

    def _run_batch_download(self, pending_list):
        count = 0
        for pid, url in pending_list:
            if not self._check_source_allowed(url): continue
            
            try:
                html = self.scraper.fetch_html(url)
                if html:
                    self.repo.save_content(url, html, 'repositorio')
                    self._update_source_status(url, True)
                    count += 1
                time.sleep(1.0)
            except:
                self._update_source_status(url, False)
        
        self._log(f"Finalizado. {count} novos downloads.", "green")
        self.load_results() # Atualiza interface se necessário

    def open_link(self, url):
        if url: webbrowser.open(url)