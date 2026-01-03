import threading
import time
from viewmodels.base_viewmodel import BaseViewModel

class ResultsViewModel(BaseViewModel):
    def __init__(self, results_repo, system_repo, scraper, view):
        super().__init__(system_repo, view) # Passa view para o Base
        self.repo = results_repo
        self.scraper = scraper

    def load_results(self):
        self._log("Recarregando tabela de resultados...", "white")
        data = self.repo.get_all()
        self.view.after_thread_safe(lambda: self.view.results_tab.display_results(data))

    def scrape_pending_pprs(self):
        pending = self.repo.get_pending_ppr()
        if not pending:
            self._log("Nenhuma pendência encontrada.", "green")
            return
        
        self._log(f"Iniciando download de {len(pending)} arquivos pendentes.", "yellow")
        threading.Thread(target=self._run_batch_download, args=(pending,)).start()

    def scrape_specific_url(self, url, doc_type):
        self._log(f"Download manual iniciado ({doc_type}): {url}", "yellow")
        threading.Thread(target=self._run_single_download, args=(url, doc_type)).start()

    def _run_single_download(self, url, doc_type):
        try:
            html = self.scraper.fetch_html(url)
            if html:
                self.repo.save_content(url, html, doc_type)
                self._update_source_status(url, True)
                self._log("Conteúdo salvo e associado.", "green")
                self.load_results()
            else:
                self._log("Falha: Conteúdo vazio.", "red")
        except Exception as e:
            self._update_source_status(url, False)
            self._log(f"Erro no download: {e}", "red")

    def _run_batch_download(self, pending_list):
        count = 0
        total = len(pending_list)
        for idx, (pid, url) in enumerate(pending_list):
            if not self._check_source_allowed(url): 
                self._log(f"Ignorando fonte bloqueada: {url}", "red")
                continue
            try:
                self._log(f"[{idx+1}/{total}] Baixando...", "white")
                html = self.scraper.fetch_html(url)
                if html:
                    self.repo.save_content(url, html, 'repositorio')
                    self._update_source_status(url, True)
                    count += 1
                time.sleep(1.0)
            except Exception as e:
                self._log(f"Erro em {url}: {e}", "red")
        
        self._log(f"Lote finalizado. {count}/{total} sucessos.", "green")
        self.load_results()

    def batch_extract_univ_data(self):
        self._log("Preparando extração em lote (Parser)...", "yellow")
        try:
            records = self.repo.get_all_ppr_with_html()
        except Exception as e:
            self._log(f"Erro ao consultar banco: {e}", "red")
            return

        if not records:
            self._log("Sem registros com HTML para processar.", "red")
            return
        
        self._log(f"Analisando {len(records)} documentos...", "yellow")
        threading.Thread(target=self._run_univ_extraction, args=(records,)).start()

    def extract_single_data(self, title, author):
        html = self.repo.get_extracted_html(title, author, 'ppr')
        if not html:
            self._log("HTML não disponível para extração.", "red")
            return
        
        self._log(f"Extraindo dados de: {title[:30]}...", "yellow")
        records = [(title, author, "", html)]
        threading.Thread(target=self._run_univ_extraction, args=(records,)).start()

    def _run_univ_extraction(self, records):
        try:
            from services.parser_factory import ParserFactory
            factory = ParserFactory()
        except Exception as e:
            self._log(f"Erro crítico no ParserFactory: {e}", "red")
            return

        count_success = 0
        total = len(records)
        
        for idx, (title, author, url, html) in enumerate(records):
            try:
                parser = factory.get_parser(url, html_content=html)
                if parser:
                    data = parser.extract(html, url)
                    if data and (data.get('sigla') or data.get('programa')):
                        self.repo.update_univ_data(title, author, 
                                                data.get('sigla'), 
                                                data.get('universidade'), 
                                                data.get('programa'))
                        count_success += 1
                
                if idx > 0 and idx % 5 == 0:
                    self._log(f"Progresso extração: {idx}/{total}", "white")
                    
            except Exception as e:
                # Log silencioso no console para não poluir a UI com erros menores de parse
                print(f"Parser error {idx}: {e}")

        self._log(f"Processamento concluído. {count_success} atualizados.", "green")
        self.load_results()