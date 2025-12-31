import re
import time
import threading
from models.database import DatabaseModel
from models.scraper import ScraperModel
from models.parsers.vufind_parser import VufindParser
import config
import os
import tempfile
import webbrowser

class MainViewModel: # Certifique-se de que o nome da classe está correto
    def check_pagination_and_scrape(self):
        if not self.current_history_id: return
        try:
            # Substituído: get_history_item -> get_plb_content
            original_url, html = self.db.get_plb_content(self.current_history_id)
            if not html: return

            #original_url, html = result
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

    def __init__(self, view):
        self.view = view
        self.db = DatabaseModel(db_name=config.DB_NAME)
        self.scraper = ScraperModel()
        self.current_history_id = None

    def start_scraping_command(self):
        url = self.view.get_url_input()
        if not url: return
        self.view.toggle_button(False)
        thread = threading.Thread(target=self._run_task, args=(url,))
        thread.start()

    def scrape_specific_search_url(self, url):
        self._log(f"Iniciando scrap de busca: {url}", "yellow")
        thread = threading.Thread(target=self._run_specific_scraping_task, args=(url, 'buscador'))
        thread.start()

    def scrape_repository_url(self, url):
        """Inicia o scrap do link do repositório (PDF/Documento)"""
        self._log(f"Iniciando scrap do repositório: {url}", "yellow")
        thread = threading.Thread(target=self._run_specific_scraping_task, args=(url, 'repositorio'))
        thread.start()

    def delete_history_item(self):
        if not self.current_history_id: 
            self._log("Tentativa de exclusão sem seleção.", "yellow")
            return
        try:
            self.db.delete_history(self.current_history_id)
            self._log(f"Atividade: Item {self.current_history_id} excluído do banco de dados.", "green")
            self.current_history_id = None
            self.view.after_thread_safe(lambda: self.view.history_tab.display_content(""))
            self.load_history_list()
        except Exception as e:
            self._log(f"Erro Crítico na exclusão: {e}", "red")

    def _log(self, message, color="white"):
        """
        Centraliza todos os logs: 
        1. Persiste a mensagem no Banco de Dados
        2. Atualiza a Barra de Status global na interface
        3. Registra a atividade na aba de Logs
        """
        try:
            self.db.save_log(message)
        except:
            pass
        self.view.update_status(message, color)

    def _run_pagination_task(self, base_url, max_page):
        """Executa o DeepScrap de PLBs: percorre e salva todas as páginas de listagem na tabela 'plb'"""
        try:
            self._log(f"Iniciando DeepScrap de PLBs: total de {max_page} páginas.", "yellow")
            separator = "&" if "?" in base_url else "?"
            
            for i in range(2, max_page + 1):
                if "page=" in base_url:
                    current_url = re.sub(r'page=\d+', f'page={i}', base_url)
                else:
                    current_url = f"{base_url}{separator}page={i}"
                
                self._log(f"Atividade: Capturando PLB {i} de {max_page}...", "yellow")
                
                html = self.scraper.fetch_html(current_url)
                # Atualizado para usar a nova tabela 'plb'
                self.db.save_plb(current_url, html)
                
                time.sleep(1.5)
                
            self._log(f"Sucesso: DeepScrap concluído. {max_page} PLBs armazenadas.", "green")
            self.view.after_thread_safe(self.load_history_list)
        except Exception as e:
            self._log(f"Erro Crítico no DeepScrap de PLBs: {e}", "red")

    def load_history_details(self, history_id):
        """Busca conteúdo da tabela 'plb' e exibe na interface."""
        self.current_history_id = history_id
        # Agora o método retorna uma tupla, pegamos apenas o HTML (índice 1) para exibição
        _, html = self.db.get_plb_content(history_id) 
        
        self.view.after_thread_safe(lambda: self.view.history_tab.display_content(html))    

    def _run_specific_scraping_task(self, url, doc_type='buscador'):
        """Versão corrigida para gravar PPB na tabela ppb e PPR na tabela ppr"""
        try:
            html = self.scraper.fetch_html(url)
            
            if doc_type == 'buscador':
                # Salva na tabela 'ppb' vinculada à pesquisa correspondente
                self.db.save_ppb_content(url, html)
                self._log(f"PPB capturada e vinculada com sucesso.", "green")
            else:
                # CORREÇÃO: Salva na tabela 'ppr' vinculada à pesquisa
                self.db.save_ppr_content(url, html)
                self._log(f"Conteúdo do repositório (PPR) salvo e vinculado.", "green")
                
            self.view.after_thread_safe(self.load_history_list)
        except Exception as e:
            self._log(f"Erro ao raspar {doc_type}: {e}", "red")

    def load_history_list(self):
        """Carrega da tabela 'plb' e atualiza a lista diretamente na aba"""
        items = self.db.get_plb_list() 
        # Acesso direto ao método update_list da history_tab
        self.view.after_thread_safe(lambda: self.view.history_tab.update_list(items))

    def initialize_data(self):
        """Carrega PLBs e pesquisas mineradas na inicialização"""
        self.load_history_list()
        try:
            saved_data = self.db.get_all_pesquisas() 
            if saved_data:
                # Acesso direto à results_tab
                self.view.after_thread_safe(lambda: self.view.results_tab.display_results(saved_data))
        except Exception as e:
            self._log(f"Erro ao carregar dados salvos: {e}", "red")

    def extract_data_command(self):
        """Extrai dados tratando possíveis falhas no banco ou no parser"""
        if not self.current_history_id: 
            self._log("Selecione uma PLB no histórico primeiro.", "yellow")
            return
        try:
            url, html = self.db.get_plb_content(self.current_history_id)
            if not html: 
                raise Exception("Aviso: Conteúdo da PLB está vazio ou indisponível.")

            self._log(f"Minerando dados em: {url}", "yellow")
            data = self.scraper.extract_data(html, VufindParser(), base_url=url)
            
            if data:
                self.db.save_pesquisas(data) 
                self._log(f"Sucesso: {len(data)} pesquisas salvas.", "green")
                
                all_results = self.db.get_all_pesquisas()
                self.view.after_thread_safe(lambda: self.view.results_tab.display_results(all_results))
                self.view.switch_to_results_tab()
            else:
                self._log("Nenhum dado científico encontrado.", "red")
        except Exception as e:
            self._log(str(e), "red")

    def open_plb_in_browser(self):
        """Abre a PLB (Página de Listagem) no navegador."""
        if not self.current_history_id:
            self._log("Selecione um item do histórico primeiro.", "yellow")
            return
        _, html = self.db.get_plb_content(self.current_history_id)
        self._open_html_string_in_browser(html)

    def open_ppb_browser_from_db(self, title, author):
        """Abre a PPB (Página de Pesquisa) no navegador."""
        html = self.db.get_extracted_html(title, author)
        self._open_html_string_in_browser(html)

    def _run_task(self, url):
        """Executa o scrap inicial com tratamento de erros de rede."""
        try:
            html = self.scraper.fetch_html(url) # Trata RequestException internamente
            self.db.save_plb(url, html)        # Trata sqlite3.Error internamente
            self.view.after_thread_safe(lambda: self.view.home_tab.display_html(html))
            self.view.after_thread_safe(self.load_history_list)
            self._log("PLB capturada e salva com sucesso.", "green")
        except Exception as e:
            self._log(str(e), "red") # Feedback preciso na barra de status
        finally:
            self.view.toggle_button(True)

    def on_tab_changed(self):
        """Atualiza o conteúdo baseado no nome exato da aba selecionada"""
        if not hasattr(self, 'selected_research'): return

        current_tab = self.view.tabview.get()
        title = self.selected_research["title"]
        author = self.selected_research["author"]

        # Sincronize estes nomes com os nomes usados no self.tabview.add() da MainView
        if current_tab == "Conteúdo PPB":
            html = self.db.get_extracted_html(title, author)
            if html:
                self.view.content_tab.display_html(html)
        
        elif current_tab == "Conteúdo PPR":
            html = self.db.get_ppr_html(title, author)
            if html:
                self.view.repo_tab.display_html(html)

    def handle_result_selection(self, title, author):
        self.selected_research = {"title": title, "author": author}
        
        html_ppb = self.db.get_extracted_html(title, author)
        html_ppr = self.db.get_ppr_html(title, author)

        # Habilita ou desabilita as abas conforme a existência de dados
        self.view.set_tab_state("Conteúdo PPB", "normal" if html_ppb else "disabled")
        self.view.set_tab_state("Conteúdo PPR", "normal" if html_ppr else "disabled")
        
        # FORÇA a atualização do conteúdo caso o usuário já esteja visualizando a aba
        self.on_tab_changed()

    def _open_html_string_in_browser(self, html_content):
        """Método utilitário para abrir strings HTML no navegador."""
        if not html_content:
            self._log("Erro: Conteúdo HTML não disponível.", "red")
            return
        try:
            import tempfile, webbrowser
            with tempfile.NamedTemporaryFile('w', delete=False, suffix='.html', encoding='utf-8') as f:
                f.write(html_content)
                temp_path = f.name
            webbrowser.open(f"file://{temp_path}")
            self._log("PPR aberta no navegador com sucesso.", "green")
        except Exception as e:
            self._log(f"Erro ao abrir navegador: {e}", "red")

    def open_ppr_in_browser(self):
        """Recupera a PPR do banco e exibe no navegador."""
        if not hasattr(self, 'selected_research'):
            self._log("Selecione uma pesquisa nos resultados.", "yellow")
            return
        
        title = self.selected_research["title"]
        author = self.selected_research["author"]
        
        # Recupera o HTML da tabela ppr
        html = self.db.get_ppr_html(title, author)
        self._open_html_string_in_browser(html)
