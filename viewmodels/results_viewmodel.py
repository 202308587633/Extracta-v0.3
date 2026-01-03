import threading
import time
import webbrowser
import traceback
from viewmodels.base_viewmodel import BaseViewModel
from urllib.parse import urlparse

class ResultsViewModel(BaseViewModel):
    def __init__(self, results_repo, system_repo, scraper, view):
        super().__init__(system_repo, view)
        self.repo = results_repo
        self.scraper = scraper
        self._stop_flag = False

    def load_results(self):
        self._log("Recarregando tabela de resultados...", "white")
        data = self.repo.get_all()
        self.view.after_thread_safe(lambda: self.view.results_tab.display_results(data))
        self._log("Tabela atualizada.", "white")

    # --- Controle de Processo ---
    
    def stop_process(self):
        self._stop_flag = True
        self._log("🛑 Solicitado parada do processo...", "yellow")

    def _toggle_ui(self, busy):
        self.view.after_thread_safe(lambda: self.view.results_tab.set_stop_button_state(busy))

    # --- Downloads (Scraping) ---

    def scrape_pending_pprs(self):
        pending = self.repo.get_pending_ppr()
        if not pending:
            self._log("Nenhum HTML pendente.", "green")
            return
        
        self._log(f"Baixando {len(pending)} pendentes (fontes ativas)...", "yellow")
        self._toggle_ui(busy=True)
        # Modo normal: force=False
        threading.Thread(target=self._run_batch_download, args=(pending, False)).start()

    def force_scrape_specific_source(self, root_url):
        if not root_url:
            self._log("Selecione uma fonte para forçar.", "red")
            return

        all_pending = self.repo.get_pending_ppr()
        
        # Filtra apenas os links que pertencem à raiz selecionada
        target_list = []
        for pid, url in all_pending:
            if root_url in url:
                target_list.append((pid, url))
        
        if not target_list:
            self._log(f"Nenhum item pendente encontrado para a fonte: {root_url}", "yellow")
            return

        self._log(f"Forçando download de {len(target_list)} itens da fonte {root_url}...", "yellow")
        self._toggle_ui(busy=True)
        # Modo forçado: force=True (ignora status desativado)
        threading.Thread(target=self._run_batch_download, args=(target_list, True)).start()

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
                self.load_results()
            else:
                self._update_source_status(url, False)
                self._log("Conteúdo vazio. Fonte marcada como instável.", "red")
        except Exception as e:
            self._update_source_status(url, False)
            self._log(f"Erro: {e}", "red")

    def _run_batch_download(self, pending_list, force=False):
        self._stop_flag = False
        count = 0
        total = len(pending_list)
        
        for idx, (pid, url) in enumerate(pending_list):
            if self._stop_flag:
                self._log("Download em lote interrompido pelo usuário.", "red")
                break

            # Se NÃO for forçado, verifica se a fonte está permitida
            if not force:
                if not self._check_source_allowed(url): 
                    # Log silencioso ou apenas no console para não poluir demais se houver muitos bloqueados
                    print(f"Fonte bloqueada/ignorada: {url}")
                    continue

            try:
                self._log(f"[{idx+1}/{total}] Baixando...", "white")
                html = self.scraper.fetch_html(url)
                if html:
                    self.repo.save_content(url, html, 'repositorio')
                    self._update_source_status(url, True)
                    count += 1
                else:
                    self._update_source_status(url, False)
                    self._log(f"Falha (Vazio): {url}", "red")

                time.sleep(1.0)
            except Exception as e:
                self._update_source_status(url, False)
                self._log(f"Erro ao baixar {url}: {e}", "red")
        
        self._toggle_ui(busy=False)
        self._log(f"Lote concluído: {count} salvos.", "green")
        self.load_results()
        self._log("Processo finalizado. Aguardando novos comandos.", "white")

    # --- Extração Universitária (Parser) ---

    def batch_extract_univ_data(self):
        self._log("Verificando registros para extração...", "yellow")
        try:
            records = self.repo.get_all_ppr_with_html()
        except Exception as e:
            self._log(f"Erro ao ler banco de dados: {e}", "red")
            return

        if not records:
            self._log("Abortado: Nenhum HTML de repositório (PPR) encontrado no banco.", "red")
            return
        
        self._log(f"Iniciando análise de {len(records)} repositórios...", "yellow")
        self._toggle_ui(busy=True)
        threading.Thread(target=self._run_univ_extraction, args=(records,)).start()

    def extract_single_data(self, title, author):
        ppr_data = self.repo.get_ppr_data(title, author)
        
        if not ppr_data or not ppr_data[1]:
            self._log("HTML do Repositório (PPR) não encontrado. Faça o download primeiro.", "red")
            return
        
        url, html = ppr_data
        records = [(title, author, url, html)]
        
        self._log(f"Extraindo dados individuais (URL: {url})...", "yellow")
        threading.Thread(target=self._run_univ_extraction, args=(records,)).start()

    def _run_univ_extraction(self, records):
        self._stop_flag = False
        try:
            from services.parser_factory import ParserFactory
            factory = ParserFactory()
        except Exception as e:
            self._log(f"Erro ao inicializar fábrica de parsers: {e}", "red")
            self._toggle_ui(busy=False)
            return

        count_success = 0
        total = len(records)
        
        for idx, (title, author, url, html) in enumerate(records):
            if self._stop_flag: break

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
                        self._log(f"Sucesso: {data.get('sigla')} - {data.get('programa')}", "green")
            except Exception as e:
                print(f"Erro no registro {idx}: {e}")

        self._toggle_ui(busy=False)
        self._log(f"Extração finalizada. {count_success} registros atualizados.", "green")
        self.load_results()
        self._log("Processo finalizado. Aguardando novos comandos.", "white")
        
    # --- Auxiliares UI ---
    
    def get_disabled_sources_list(self):
        """Retorna lista de fontes desativadas para a ComboBox."""
        # CORREÇÃO: O nome correto do atributo na classe base é self.sys_repo
        return self.sys_repo.get_disabled_sources()
    