import threading
import time
import re
import math
from bs4 import BeautifulSoup
from viewmodels.base_viewmodel import BaseViewModel
from urllib.parse import urlparse, parse_qs, unquote

class HistoryViewModel(BaseViewModel):
    def __init__(self, history_repo, results_repo, system_repo, scraper, view):
        super().__init__(system_repo, view)
        self.history_repo = history_repo
        self.results_repo = results_repo 
        self.scraper = scraper
        self._stop_flag = False

    def load_data(self):
        raw_items = self.history_repo.get_all()
        structured_items = []
        for item in raw_items:
            try:
                item_id, url, created_at = item[0], item[1], item[2]
                db_term = item[3] if len(item) > 3 else None
                db_year = item[4] if len(item) > 4 else None
                
                if db_term and db_year:
                    termo, ano = db_term, db_year
                    try: pagina = parse_qs(urlparse(url).query).get('page', ['1'])[0]
                    except: pagina = '1'
                else:
                    try:
                        p = parse_qs(urlparse(url).query)
                        termo = unquote(p.get('lookfor0[]', p.get('lookfor', ['-']))[0]).replace('"', '')
                        ano = p.get('publishDatefrom', ['-'])[0]
                        pagina = p.get('page', ['1'])[0]
                    except: termo, ano, pagina = "Link Manual", "-", "1"
                
                structured_items.append((item_id, termo, ano, pagina, created_at, url))
            except: continue
        
        self.view.after_thread_safe(lambda: self.view.history_tab.update_table(structured_items))

    # --- Ações de Scraping (DeepScrap) ---
    def stop_process(self):
        self._stop_flag = True
        self._log("🛑 Solicitado parada do processo...", "yellow")

    def check_pagination_and_scrape(self, history_id):
        record = self.history_repo.get_by_id(history_id)
        if not record: return
        url, html = record[1], record[2]
        term = record[3] if len(record) > 3 else "Man"
        year = record[4] if len(record) > 4 else "-"
        
        max_page = self._extract_max_page(html)
        if max_page > 1:
            self._log(f"DeepScrap: {max_page} páginas encontradas.", "yellow")
            threading.Thread(target=self._run_pagination, args=(url, max_page, term, year)).start()
        else:
            self._log("Apenas 1 página nesta pesquisa.", "yellow")

    def scrape_all_page1(self):
        all_items = self.history_repo.get_all()
        ids_to_process = []
        for item in all_items:
            try:
                if int(parse_qs(urlparse(item[1]).query).get('page', ['1'])[0]) == 1:
                    ids_to_process.append(item[0])
            except: continue
        
        if ids_to_process:
            self._log(f"Iniciando DeepScrap em massa ({len(ids_to_process)} pesquisas).", "yellow")
            threading.Thread(target=self._run_batch_pagination, args=(ids_to_process,)).start()
        else:
            self._log("Nenhuma pesquisa na página 1 encontrada.", "yellow")

    def _run_pagination(self, base_url, max_page, term, year):
        self._stop_flag = False
        separator = "&" if "?" in base_url else "?"
        self.view.after_thread_safe(lambda: self.view.history_tab.set_stop_button_state(True))

        for i in range(2, max_page + 1):
            if self._stop_flag: 
                self._log("DeepScrap interrompido pelo usuário.", "red")
                break
            
            if "page=" in base_url:
                current_url = re.sub(r'page=\d+', f'page={i}', base_url)
            else:
                current_url = f"{base_url}{separator}page={i}"
            
            if self.history_repo.check_url_exists(current_url): continue

            self._log(f"Baixando pág {i}/{max_page} ({term})...", "white")
            try:
                html = self.scraper.fetch_html(current_url)
                if html:
                    self.history_repo.save(current_url, html, term, year)
                    self._update_source_status(current_url, True)
                time.sleep(1.0)
            except Exception as e:
                self._log(f"Erro pág {i}: {e}", "red")
                self._update_source_status(current_url, False)
        
        self.view.after_thread_safe(lambda: self.view.history_tab.set_stop_button_state(False))
        self.load_data()
        if not self._stop_flag: self._log("DeepScrap finalizado.", "green")

    def _run_batch_pagination(self, ids):
        self._stop_flag = False
        total = len(ids)
        self.view.after_thread_safe(lambda: self.view.history_tab.set_stop_button_state(True))
        
        for idx, hid in enumerate(ids):
            if self._stop_flag: break
            rec = self.history_repo.get_by_id(hid)
            if not rec: continue
            
            max_p = self._extract_max_page(rec[2])
            if max_p > 1:
                self._log(f"[{idx+1}/{total}] Processando '{rec[3]}'...", "white")
                self._run_pagination(rec[1], max_p, rec[3], rec[4])
        
        self.view.after_thread_safe(lambda: self.view.history_tab.set_stop_button_state(False))
        if not self._stop_flag: self._log("Lote DeepScrap finalizado.", "green")

    def _extract_max_page(self, html):
        try:
            soup = BeautifulSoup(html, 'html.parser')
            stats = soup.find(string=re.compile(r"resultados de", re.IGNORECASE))
            if stats:
                txt = stats.find_parent().get_text(strip=True)
                match = re.search(r"resultados de\s*([\d\.]+)", txt, re.IGNORECASE)
                if match:
                    total = int(match.group(1).replace('.', ''))
                    return math.ceil(total / 20)
            return 1
        except: return 1

    # --- Extração de Dados (Parser) ---
    def extract_data(self, history_id, batch_mode=False):
        rec = self.history_repo.get_by_id(history_id)
        if not rec or not rec[2]: 
            if not batch_mode: self._log("HTML não encontrado.", "red")
            return False
        
        try:
            from services.parser_factory import ParserFactory
            factory = ParserFactory()
            parser = factory.get_parser(rec[1], html_content=rec[2])
            
            if parser:
                if not batch_mode: self._log(f"Parser selecionado: {parser.__class__.__name__}", "white")
                
                # Executa extração
                data = parser.extract(rec[2], base_url=rec[1])
                
                # CORREÇÃO: Garante que 'data' seja uma lista antes de salvar
                if isinstance(data, dict):
                    data = [data] # Converte single dict para list
                
                if data and isinstance(data, list) and len(data) > 0:
                    count = self.results_repo.save_pesquisas(data, term=rec[3], year=rec[4])
                    if count > 0:
                        if not batch_mode: 
                            self._log(f"Sucesso: {count} registros salvos.", "green")
                            if hasattr(self.view, 'refresh_results_callback'):
                                self.view.after_thread_safe(self.view.refresh_results_callback)
                        return True
                    else:
                        if not batch_mode: self._log("Registros já existentes.", "white")
                        return False
                else:
                     if not batch_mode: self._log("Nenhum dado válido extraído pelo parser.", "yellow")
                     return False
            else:
                if not batch_mode: self._log("Nenhum parser identificado.", "red")
                return False

        except Exception as e:
            self._log(f"Erro crítico na extração: {e}", "red")
            return False

    def extract_all_plbs(self):
        self._log("Extraindo dados de todo o histórico...", "yellow")
        threading.Thread(target=self._run_extract_all).start()

    def _run_extract_all(self):
        self._stop_flag = False
        items = self.history_repo.get_all()
        total = len(items)
        extracted_count = 0
        
        self.view.after_thread_safe(lambda: self.view.history_tab.set_stop_button_state(True))

        for idx, item in enumerate(items):
            if self._stop_flag:
                self._log("Processo interrompido.", "red")
                break
            
            if self.extract_data(item[0], batch_mode=True):
                extracted_count += 1
            
            if idx > 0 and idx % 5 == 0:
                self._log(f"Analisando PLB {idx}/{total}...", "white")
        
        self.view.after_thread_safe(lambda: self.view.history_tab.set_stop_button_state(False))
        if hasattr(self.view, 'refresh_results_callback'):
            self.view.after_thread_safe(self.view.refresh_results_callback)
            
        self._log(f"Finalizado. {extracted_count} páginas contribuíram com dados.", "green")

    # --- Helpers ---
    def delete_item(self, hid):
        self.history_repo.delete(hid)
        self.load_data()

    def open_browser(self, hid):
        rec = self.history_repo.get_by_id(hid)
        if rec and rec[2]: self.view.open_html_from_db_in_browser(rec[2])