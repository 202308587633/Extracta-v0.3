import threading
import time
import webbrowser
import traceback
from viewmodels.base_viewmodel import BaseViewModel

class ResultsViewModel(BaseViewModel):
    def __init__(self, results_repo, system_repo, scraper, view):
        super().__init__(system_repo)
        self.repo = results_repo
        self.scraper = scraper
        self.view = view # Guardamos a referência da View

    # --- CORREÇÃO CRÍTICA: Sobrescrevendo _log para atualizar a UI ---
    def _log(self, message, color="white"):
        """Salva no banco e atualiza a interface gráfica."""
        # 1. Tenta salvar no banco via BaseViewModel
        try: super()._log(message, color)
        except: pass
        
        # 2. Atualiza a tela (Thread-Safe)
        if self.view:
            self.view.after_thread_safe(lambda: self.view.update_status(message, color))

    def load_results(self):
        data = self.repo.get_all()
        self.view.after_thread_safe(lambda: self.view.results_tab.display_results(data))

    # --- Downloads (Scraping) ---

    def scrape_pending_pprs(self):
        pending = self.repo.get_pending_ppr()
        if not pending:
            self._log("Nenhum HTML pendente (pesquisas sem link ou já baixadas).", "green")
            return
        
        self._log(f"Baixando {len(pending)} pendentes...", "yellow")
        threading.Thread(target=self._run_batch_download, args=(pending,)).start()

    def scrape_specific_url(self, url, doc_type):
        self._log(f"Baixando {doc_type}: {url}", "yellow")
        threading.Thread(target=self._run_single_download, args=(url, doc_type)).start()

    def _run_single_download(self, url, doc_type):
        try:
            html = self.scraper.fetch_html(url)
            if html:
                self.repo.save_content(url, html, doc_type)
                self._update_source_status(url, True)
                self._log("Conteúdo salvo com sucesso.", "green")
                # Atualiza a tabela para refletir que já tem o conteúdo
                self.load_results()
            else:
                self._log("Conteúdo vazio recebido.", "red")
        except Exception as e:
            self._update_source_status(url, False)
            self._log(f"Erro: {e}", "red")

    def _run_batch_download(self, pending_list):
        count = 0
        total = len(pending_list)
        for idx, (pid, url) in enumerate(pending_list):
            if not self._check_source_allowed(url): 
                self._log(f"Fonte bloqueada: {url}", "red")
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
                self._log(f"Erro ao baixar {url}: {e}", "red")
        self._log(f"Lote concluído: {count} salvos.", "green")
        self.load_results()

    # --- Extração Universitária (Parser) ---

    def batch_extract_univ_data(self):
        """Chamado pelo botão 'Extrair Dados Univ. (Lote)'."""
        self._log("Verificando registros para extração...", "yellow")
        
        try:
            records = self.repo.get_all_ppr_with_html()
        except Exception as e:
            self._log(f"Erro ao ler banco de dados: {e}", "red")
            return

        if not records:
            self._log("Abortado: Nenhum HTML de repositório (PPR) encontrado no banco.", "red")
            self._log("Dica: Use o botão 'Baixar HTMLs Pendentes' primeiro.", "white")
            return
        
        self._log(f"Iniciando análise de {len(records)} repositórios...", "yellow")
        threading.Thread(target=self._run_univ_extraction, args=(records,)).start()

    def extract_single_data(self, title, author):
        """Extração individual via menu de contexto."""
        html = self.repo.get_extracted_html(title, author, 'ppr')
        if not html:
            self._log("HTML do Repositório (PPR) não encontrado. Faça o download primeiro.", "red")
            return
        
        # Emula uma lista de 1 registro para reusar a lógica
        records = [(title, author, "", html)]
        threading.Thread(target=self._run_univ_extraction, args=(records,)).start()

    def _run_univ_extraction(self, records):
        """Roda a extração em thread segura com tratamento de erros."""
        try:
            from services.parser_factory import ParserFactory
            factory = ParserFactory()
        except ImportError as e:
            self._log(f"Erro Crítico: Não foi possível importar ParserFactory. {e}", "red")
            return
        except Exception as e:
            self._log(f"Erro ao inicializar fábrica de parsers: {e}", "red")
            return

        count_success = 0
        total = len(records)
        
        for idx, (title, author, url, html) in enumerate(records):
            try:
                # Se URL vier vazia (caso individual), tenta extrair do HTML ou segue sem
                parser = factory.get_parser(url, html_content=html)
                if parser:
                    data = parser.extract(html, url)
                    if data:
                        # Verifica se extraiu algo útil antes de contar como sucesso
                        if data.get('sigla') or data.get('programa'):
                            self.repo.update_univ_data(title, author, 
                                                    data.get('sigla'), 
                                                    data.get('universidade'), 
                                                    data.get('programa'))
                            count_success += 1
                
                if idx > 0 and idx % 5 == 0:
                    self._log(f"Analisando item {idx}/{total}...", "white")
                    
            except Exception as e:
                print(f"Erro no registro {idx}: {e}") # Debug no console apenas

        self._log(f"Extração finalizada. {count_success} registros atualizados.", "green")
        self.load_results()