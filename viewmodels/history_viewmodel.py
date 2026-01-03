import threading
import time
import re
import math
from bs4 import BeautifulSoup
from viewmodels.base_viewmodel import BaseViewModel
from urllib.parse import urlparse, parse_qs, unquote

class HistoryViewModel(BaseViewModel):
    def __init__(self, history_repo, results_repo, system_repo, scraper, view):
        super().__init__(system_repo)
        self.history_repo = history_repo
        self.results_repo = results_repo # Necessário para salvar dados extraídos
        self.scraper = scraper
        self.view = view
        self._stop_flag = False

    def load_data(self):
        """Carrega dados para a tabela."""
        raw_items = self.history_repo.get_all()
        structured_items = []
        for item in raw_items:
            try:
                # (id, url, created_at, term, year)
                item_id, url, created_at = item[0], item[1], item[2]
                db_term = item[3] if len(item) > 3 else None
                db_year = item[4] if len(item) > 4 else None
                
                if db_term and db_year:
                    termo, ano = db_term, db_year
                    try: pagina = parse_qs(urlparse(url).query).get('page', ['1'])[0]
                    except: pagina = '1'
                else:
                    # Fallback
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
        self._log("🛑 Parando...", "red")

    def check_pagination_and_scrape(self, history_id):
        record = self.history_repo.get_by_id(history_id)
        if not record: return
        
        url, html = record[1], record[2]
        term = record[3] if len(record) > 3 else "Man"
        year = record[4] if len(record) > 4 else "-"
        
        max_page = self._extract_max_page(html)
        if max_page > 1:
            self._log(f"DeepScrap: {max_page} páginas encontradas.", "yellow")
            self._toggle_ui(busy=True)
            threading.Thread(target=self._run_pagination, args=(url, max_page, term, year)).start()
        else:
            self._log("Apenas 1 página nesta pesquisa.", "yellow")

    def scrape_all_page1(self):
        """DeepScrap em massa para todas as pesquisas na página 1."""
        all_items = self.history_repo.get_all()
        ids_to_process = []
        for item in all_items:
            try:
                if int(parse_qs(urlparse(item[1]).query).get('page', ['1'])[0]) == 1:
                    ids_to_process.append(item[0])
            except: continue
        
        if ids_to_process:
            self._log(f"Iniciando DeepScrap em massa ({len(ids_to_process)} pesquisas).", "yellow")
            self._toggle_ui(busy=True)
            threading.Thread(target=self._run_batch_pagination, args=(ids_to_process,)).start()
        else:
            self._log("Nenhuma pesquisa na página 1 encontrada.", "yellow")

    def _run_pagination(self, base_url, max_page, term, year):
        self._stop_flag = False
        separator = "&" if "?" in base_url else "?"
        
        for i in range(2, max_page + 1):
            if self._stop_flag: break
            
            # Constrói URL da página seguinte
            if "page=" in base_url:
                current_url = re.sub(r'page=\d+', f'page={i}', base_url)
            else:
                current_url = f"{base_url}{separator}page={i}"
            
            if self.history_repo.check_url_exists(current_url):
                continue

            self._log(f"Baixando pág {i}/{max_page} ({term})...", "yellow")
            try:
                html = self.scraper.fetch_html(current_url)
                if html:
                    self.history_repo.save(current_url, html, term, year)
                    self._update_source_status(current_url, True)
                time.sleep(1.5)
            except Exception as e:
                self._log(f"Erro pág {i}: {e}", "red")
                self._update_source_status(current_url, False)
        
        self._toggle_ui(busy=False)
        self.load_data()
        self._log("DeepScrap finalizado.", "green")

    def _run_batch_pagination(self, ids):
        self._stop_flag = False
        total = len(ids)
        for idx, hid in enumerate(ids):
            if self._stop_flag: break
            rec = self.history_repo.get_by_id(hid)
            if not rec: continue
            
            # Extrai dados e roda paginação para cada um
            max_p = self._extract_max_page(rec[2])
            if max_p > 1:
                self._log(f"[{idx+1}/{total}] Processando '{rec[3]}'...", "white")
                self._run_pagination(rec[1], max_p, rec[3], rec[4])
        
        self._toggle_ui(busy=False)
        self._log("Lote finalizado.", "green")

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

    # --- Extração de Dados ---

    def extract_data(self, history_id):
        rec = self.history_repo.get_by_id(history_id)
        if not rec or not rec[2]: return
        
        try:
            from services.parser_factory import ParserFactory
            # Usa factory ou parser padrão (aqui simplificado para Vufind)
            from models.parsers.vufind_parser import VufindParser
            
            self._log(f"Extraindo dados: {rec[1]}", "yellow")
            parser = VufindParser()
            # Parser espera soup, então passamos o soup ou adaptamos o parser
            soup = BeautifulSoup(rec[2], 'html.parser')
            data = parser.parse(soup, base_url=rec[1])
            
            if data:
                count = self.results_repo.save_pesquisas(data, term=rec[3], year=rec[4])
                self._log(f"Salvo: {count} novos registros.", "green")
                # Avisa para atualizar a aba de resultados
                if hasattr(self.view, 'refresh_results_callback'):
                    self.view.after_thread_safe(self.view.refresh_results_callback)
            else:
                self._log("Nenhum dado extraído.", "yellow")
        except Exception as e:
            self._log(f"Erro extração: {e}", "red")

    # --- Helpers ---
    def delete_item(self, hid):
        self.history_repo.delete(hid)
        self.load_data()

    def open_browser(self, hid):
        rec = self.history_repo.get_by_id(hid)
        if rec and rec[2]: self.view.open_html_from_db_in_browser(rec[2])

    def _toggle_ui(self, busy):
        state = not busy
        self.view.after_thread_safe(lambda: self.view.history_tab.set_stop_button_state(busy))
        # Opcional: Bloquear outras abas