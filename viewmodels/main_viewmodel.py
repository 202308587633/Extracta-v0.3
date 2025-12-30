import re
import time
import threading
from models.database import DatabaseModel
from models.scraper import ScraperModel
from models.parsers.vufind_parser import VufindParser # Import necessário para o Passo 2
import config
import os
import tempfile
import webbrowser

class MainViewModel: # Certifique-se de que o nome da classe está correto
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
            self.db.save_scraping(url, html)
            self.view.display_html_content(html)
            self._log("Sucesso! Processo finalizado.", "green")
            self.view.after_thread_safe(self.load_history_list)
        except Exception as e:
            error_msg = f"Falha: {str(e)}"
            self._log(error_msg, "red")
            self.view.display_html_content(error_msg)
        finally:
            self.view.toggle_button(True)

    def scrape_specific_search_url(self, url):
        self._log(f"Iniciando scrap de link específico: {url}", "yellow")
        thread = threading.Thread(target=self._run_specific_scraping_task, args=(url,))
        thread.start()

    def _run_specific_scraping_task(self, url):
        try:
            html = self.scraper.fetch_html(url)
            self.db.save_scraping(url, html)
            self._log("Conteúdo do buscador salvo com sucesso.", "green")
            self.view.after_thread_safe(lambda: self.view.display_content_in_fourth_tab(html))
            self.view.after_thread_safe(self.load_history_list)
        except Exception as e:
            self._log(f"Erro ao raspar link específico: {e}", "red")

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
        if not self.current_history_id: return
        try:
            self.db.delete_history(self.current_history_id)
            self._log(f"Item {self.current_history_id} excluído.", "green")
            self.current_history_id = None
            self.view.display_history_content("")
            self.load_history_list()
        except Exception as e:
            self._log(f"Erro ao excluir item: {e}", "red")

    def check_pagination_and_scrape(self):
        if not self.current_history_id: return
        try:
            result = self.db.get_history_item(self.current_history_id)
            if not result: return
            original_url, html = result
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

    def _run_pagination_task(self, base_url, max_page):
        try:
            separator = "&" if "?" in base_url else "?"
            for i in range(2, max_page + 1):
                current_url = re.sub(r'page=\d+', f'page={i}', base_url) if "page=" in base_url else f"{base_url}{separator}page={i}"
                self._log(f"Capturando Página {i}/{max_page}...", "yellow")
                html = self.scraper.fetch_html(current_url)
                self.db.save_scraping(current_url, html)
                time.sleep(1)
            self._log("Ciclo de paginação concluído.", "green")
            self.view.after_thread_safe(self.load_history_list)
        except Exception as e:
            self._log(f"Erro no loop: {e}", "red")

    def extract_data_command(self):
        if not self.current_history_id: return
        try:
            result = self.db.get_history_item(self.current_history_id)
            if not result: return
            url, html = result
            self._log("Extraindo e salvando dados...", "yellow")
            
            parser = VufindParser()
            data = self.scraper.extract_data(html, parser, base_url=url)
            
            if not data:
                self._log("Nenhum dado novo encontrado.", "red")
            else:
                # GRAVAÇÃO EM BANCO DE DADOS
                self.db.save_extracted_results(data)
                
                # Recupera lista completa (novos + antigos) para atualizar a tela
                all_data = self.db.get_all_extracted_results()
                self._log(f"Extração concluída e salva! Total: {len(all_data)}", "green")
                self.view.display_extracted_results(all_data)
                self.view.switch_to_results_tab()
        except Exception as e:
            self._log(f"Erro na extração: {e}", "red")

    def open_html_in_browser(self):
        """Recupera o HTML do banco e abre em uma aba do navegador"""
        if not self.current_history_id:
            self._log("Selecione um item do histórico primeiro.", "red")
            return

        try:
            # Recupera o conteúdo HTML do banco de dados
            html_content = self.db.get_history_content(self.current_history_id)
            
            if not html_content:
                self._log("Erro: Conteúdo HTML vazio.", "red")
                return

            # Cria um arquivo HTML temporário para visualização
            with tempfile.NamedTemporaryFile('w', delete=False, suffix='.html', encoding='utf-8') as f:
                f.write(html_content)
                temp_path = f.name

            # Abre o arquivo no navegador padrão
            webbrowser.open(f"file://{temp_path}")
            self._log("HTML aberto no navegador com sucesso.", "green")

        except Exception as e:
            self._log(f"Erro ao abrir no navegador: {e}", "red")

    def initialize_data(self):
        """Carrega o histórico e os dados minerados na inicialização"""
        self.load_history_list()
        try:
            saved_data = self.db.get_all_extracted_results()
            if saved_data:
                self.view.display_extracted_results(saved_data)
        except Exception as e:
            self._log(f"Erro ao carregar dados salvos: {e}", "red")
