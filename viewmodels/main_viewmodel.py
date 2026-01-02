

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
from urllib.parse import urlparse, parse_qs, unquote, urlencode, urlunparse
from bs4 import BeautifulSoup
import math
import customtkinter as ctk
from tkinter import ttk

class MainViewModel: # Certifique-se de que o nome da classe está correto
    def load_history_details(self, history_id):
        """Busca conteúdo da tabela 'plb' e exibe na interface."""
        self.current_history_id = history_id
        # Agora o método retorna uma tupla, pegamos apenas o HTML (índice 1) para exibição
        _, html = self.db.get_plb_content(history_id) 
        
        self.view.after_thread_safe(lambda: self.view.history_tab.display_content(html))    

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

    def _extract_meta_content(self, soup, meta_names):
        """Busca conteúdo em tags <meta name='...'>"""
        for name in meta_names:
            tag = soup.find('meta', attrs={'name': name})
            if not tag:
                tag = soup.find('meta', attrs={'name': name.lower()})
            if tag and tag.get('content'):
                return tag['content'].strip()
        return None

    def _find_meta_value(self, soup, names, filter_word=None):
        """Busca valor em meta tags."""
        for name in names:
            tags = soup.find_all('meta', attrs={'name': name})
            if not tags: # Tenta lowercase se não achar
                tags = soup.find_all('meta', attrs={'name': name.lower()})
                
            for tag in tags:
                content = tag.get('content', '')
                if filter_word:
                    if filter_word.lower() in content.lower():
                        return content
                else:
                    # Se não tem filtro, retorna o primeiro que não seja vazio
                    if content and len(content) > 3:
                        return content
        return None

    def _extract_from_dspace_angular(self, soup, keywords):
        """Extrai dados de estruturas DSpace 7+ (Header + Body divs)."""
        # Procura por headers que contenham as palavras-chave
        headers = soup.find_all(['h2', 'h3', 'h4', 'h5', 'h6'], class_=lambda x: x and 'header' in x)
        
        for header in headers:
            header_text = header.get_text().strip().lower()
            if any(k in header_text for k in keywords):
                # O valor geralmente está em uma div irmã ou próxima com class '...body'
                # Sobe para o pai e procura o body
                parent = header.find_parent()
                if parent:
                    body = parent.find(class_=lambda x: x and 'body' in x)
                    if body:
                        return body.get_text(" ", strip=True)
        return None

    def _extract_from_tables(self, soup, keywords):
        """Varre tabelas procurando chaves nas células de rótulo."""
        # Procura células que pareçam rótulos (terminam com : ou têm classe label)
        cells = soup.find_all(['td', 'th'])
        for cell in cells:
            text = cell.get_text(" ", strip=True).lower()
            # Verifica se contém a keyword e é curto o suficiente para ser um label (ex: "Programa:")
            if any(k in text for k in keywords) and len(text) < 50:
                # O valor é geralmente a próxima célula
                next_cell = cell.find_next_sibling(['td', 'th'])
                if next_cell:
                    return next_cell.get_text(" ", strip=True)
        return None

    def _extract_program_from_breadcrumbs(self, soup):
        """Tenta achar o programa em listas de navegação (ul/ol class breadcrumb)."""
        # Procura por qualquer lista que tenha 'breadcrumb' na classe ou id
        trails = soup.find_all(['ul', 'ol', 'nav'], class_=lambda x: x and 'breadcrumb' in x)
        
        for trail in trails:
            links = trail.find_all('li') # Itens da lista
            if not links:
                links = trail.find_all('a') # Ou links diretos
                
            # Geralmente o programa está no penúltimo ou antepenúltimo item
            # Ex: Home > Teses > Programa X > Item
            if len(links) >= 2:
                # Itera de trás para frente, ignorando o último (que é o título do item)
                for i in range(len(links)-2, -1, -1):
                    txt = links[i].get_text(strip=True)
                    # Validação heurística para ver se parece um programa
                    if ("programa" in txt.lower() or "mestrado" in txt.lower() or 
                        "doutorado" in txt.lower() or "pós-graduação" in txt.lower() or 
                        "direito" in txt.lower()): # Adicionado 'direito' para o caso Mackenzie
                        return txt
        return None

    def _infer_sigla(self, univ_nome):
        """Deduz a sigla a partir do nome da universidade."""
        if not univ_nome or univ_nome == "Não identificada": return "-"
        
        nome = univ_nome.upper()
        
        # 1. Mapa manual (Prioridade Alta)
        mapa = {
            "UNIVERSIDADE DE SÃO PAULO": "USP",
            "UNIVERSIDADE ESTADUAL PAULISTA": "UNESP",
            "UNIVERSIDADE ESTADUAL DE CAMPINAS": "UNICAMP",
            "UNIVERSIDADE FEDERAL DE SANTA CATARINA": "UFSC",
            "UNIVERSIDADE FEDERAL DE GOIÁS": "UFG", # Adicionado
            "UNIVERSIDADE FEDERAL DE MINAS GERAIS": "UFMG",
            "UNIVERSIDADE FEDERAL DO RIO DE JANEIRO": "UFRJ",
            "UNIVERSIDADE FEDERAL DO RIO GRANDE DO SUL": "UFRGS",
            "UNIVERSIDADE DE BRASÍLIA": "UnB",
            "UNIVERSIDADE ESTADUAL DA PARAÍBA": "UEPB", # Adicionado
            "UNIVERSIDADE PRESBITERIANA MACKENZIE": "MACKENZIE", # Adicionado
            "PONTIFÍCIA UNIVERSIDADE CATÓLICA": "PUC", # Genérico
            "FUNDAÇÃO GETULIO VARGAS": "FGV"
        }

    def _update_source_ui(self, url, success):
        """Atualiza a aba de Fontes na interface"""
        root = self._extract_root_url(url)
        self.view.update_source_status(root, success)

    def toggle_source_manually(self, root_url, new_status):
        self.db.save_source_status(root_url, new_status)
        self._log(f"Fonte {root_url} alterada manualmente para {new_status}", "white")

    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1) # Tabela na linha 2 expande

        # --- 1. Barra de Ferramentas ---
        self.toolbar = ctk.CTkFrame(self, fg_color="transparent")
        self.toolbar.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))

        # Botões de Ação
        self.btn_scrape_pending = ctk.CTkButton(
            self.toolbar, text="⬇️ Baixar HTMLs Pendentes", 
            command=self.viewmodel.scrape_pending_pprs, height=30,
            fg_color="#1f538d", hover_color="#14375e", font=("Roboto", 12, "bold")
        )
        self.btn_scrape_pending.pack(side="left", padx=(0, 10))

        self.btn_extract_batch = ctk.CTkButton(
            self.toolbar, text="🏷️ Extrair Dados Univ. (Lote)", 
            command=self.viewmodel.batch_extract_univ_data, height=30,
            fg_color="#27ae60", hover_color="#219150", font=("Roboto", 12, "bold")
        )
        self.btn_extract_batch.pack(side="left", padx=(0, 10))

        self.btn_refresh = ctk.CTkButton(
            self.toolbar, text="🔄 Atualizar", 
            command=lambda: self.viewmodel.initialize_data(), height=30,
            fg_color="gray", hover_color="#555555", width=80
        )
        self.btn_refresh.pack(side="left")

        # --- 2. Barra de Filtros (NOVO) ---
        self.filter_frame = ctk.CTkFrame(self)
        self.filter_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        
        # Filtro Título
        ctk.CTkLabel(self.filter_frame, text="Título:", font=("Roboto", 11)).pack(side="left", padx=(10, 2))
        self.ent_filter_title = ctk.CTkEntry(self.filter_frame, width=200, placeholder_text="Filtrar...")
        self.ent_filter_title.pack(side="left", padx=5)
        self.ent_filter_title.bind("<KeyRelease>", self._apply_filters)

        # Filtro Autor
        ctk.CTkLabel(self.filter_frame, text="Autor:", font=("Roboto", 11)).pack(side="left", padx=(10, 2))
        self.ent_filter_author = ctk.CTkEntry(self.filter_frame, width=150, placeholder_text="Filtrar...")
        self.ent_filter_author.pack(side="left", padx=5)
        self.ent_filter_author.bind("<KeyRelease>", self._apply_filters)

        # Filtro Universidade
        ctk.CTkLabel(self.filter_frame, text="Univ.:", font=("Roboto", 11)).pack(side="left", padx=(10, 2))
        self.ent_filter_univ = ctk.CTkEntry(self.filter_frame, width=100, placeholder_text="Sigla...")
        self.ent_filter_univ.pack(side="left", padx=5)
        self.ent_filter_univ.bind("<KeyRelease>", self._apply_filters)

        # Label de Contagem
        self.label_count = ctk.CTkLabel(self.filter_frame, text="Total: 0", font=("Roboto", 11, "bold"))
        self.label_count.pack(side="right", padx=15)

        # --- 3. Tabela ---
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(0, weight=1)

        style = ttk.Style()
        style.theme_use("default")
        bg_color = "#2b2b2b"
        text_color = "#ffffff"
        selected_bg = "#1f538d"
        header_bg = "#1f1f1f"
        
        style.configure("Treeview", background=bg_color, foreground=text_color, 
                        fieldbackground=bg_color, rowheight=30, borderwidth=0, font=("Roboto", 11))
        style.map('Treeview', background=[('selected', selected_bg)])
        style.configure("Treeview.Heading", background=header_bg, foreground=text_color, 
                        relief="flat", padding=(5, 5), font=("Roboto", 12, "bold"))
        style.map("Treeview.Heading", background=[('active', '#343638')])

        columns = ("title", "author", "sigla", "universidade", "programa")
        self.tree = ttk.Treeview(self.container, columns=columns, show="headings", selectmode="browse")

        # Cabeçalhos com Ordenação
        self.tree.heading("title", text="Nome da Pesquisa", command=lambda: self._sort_column("title", False))
        self.tree.heading("author", text="Autor", command=lambda: self._sort_column("author", False))
        self.tree.heading("sigla", text="Sigla", command=lambda: self._sort_column("sigla", False))
        self.tree.heading("universidade", text="Universidade", command=lambda: self._sort_column("universidade", False))
        self.tree.heading("programa", text="Programa", command=lambda: self._sort_column("programa", False))

        self.tree.column("title", width=300, minwidth=150, anchor="w")
        self.tree.column("author", width=150, minwidth=100, anchor="w")
        self.tree.column("sigla", width=60, anchor="center")
        self.tree.column("universidade", width=200, anchor="w")
        self.tree.column("programa", width=200, anchor="w")

        self.scrollbar = ctk.CTkScrollbar(self.container, command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.scrollbar.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")

        self.tree.bind("<Double-1>", self._on_double_click)
        self.tree.bind("<Button-3>", self._show_context_menu)
        self.tree.bind("<<TreeviewSelect>>", self._on_row_select)

    def display_results(self, results):
        """Salva os dados brutos e aplica os filtros para exibição."""
        self.all_data = results
        self._apply_filters()

    def _apply_filters(self, event=None):
        """Filtra os dados em memória e atualiza a Treeview."""
        f_title = self.ent_filter_title.get().lower().strip()
        f_author = self.ent_filter_author.get().lower().strip()
        f_univ = self.ent_filter_univ.get().lower().strip()

        # Limpa tabela atual
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        self.link_map.clear()
        self.item_map.clear()

        count = 0
        for idx, item in enumerate(self.all_data):
            # Obtém valores seguros para comparação
            title = str(item.get('title', '') or '').lower()
            author = str(item.get('author', '') or '').lower()
            univ_sigla = str(item.get('univ_sigla', '') or '').lower()
            univ_nome = str(item.get('univ_nome', '') or '').lower()

            # Verifica correspondência (AND)
            match_title = f_title in title
            match_author = f_author in author
            match_univ = (f_univ in univ_sigla) or (f_univ in univ_nome)

            if match_title and match_author and match_univ:
                values = (
                    item.get('title'), 
                    item.get('author'), 
                    item.get('univ_sigla', '-'), 
                    item.get('univ_nome', 'Pendente...'),
                    item.get('programa', '-') 
                )
                tree_id = self.tree.insert("", "end", values=values)
                
                # Mapeia IDs para funcionalidades originais
                self.link_map[tree_id] = {'search': item.get('ppb_link'), 'repo': item.get('ppr_link')}
                self.item_map[tree_id] = idx 
                count += 1

        self.label_count.configure(text=f"Total: {count}")

    def _sort_column(self, col, reverse):
        """Ordena a visualização atual da tabela."""
        l = [(self.tree.set(k, col), k) for k in self.tree.get_children('')]
        try:
            l.sort(key=lambda t: t[0].lower(), reverse=reverse)
        except:
            l.sort(reverse=reverse)

        for index, (val, k) in enumerate(l):
            self.tree.move(k, '', index)

        self.tree.heading(col, command=lambda: self._sort_column(col, not reverse))

    def _get_selected_data(self):
        """Helper para recuperar o dicionário de dados da linha selecionada."""
        sel = self.tree.selection()
        if not sel: return None
        idx = self.item_map.get(sel[0])
        if idx is not None and 0 <= idx < len(self.all_data):
            return self.all_data[idx]
        return None

    def _scrape_repo_row(self):
        """Dispara o callback para o link do repositório (usando link_map)."""
        selected = self.tree.selection()
        if not selected: return
        item_id = selected[0]
        links = self.link_map.get(item_id)
        if links and links.get('repo'):
            self.on_repo_scrape_callback(links['repo'])

    def _view_ppb_browser(self):
        """Abre o HTML da PPB no navegador."""
        item = self._get_selected_data()
        if item:
            html = self.viewmodel.db.get_extracted_html(item.get('title'), item.get('author'))
            self.viewmodel.view.open_html_from_db_in_browser(html)

    def _view_ppb_internal(self):
        """Muda para a aba interna de PPB."""
        item = self._get_selected_data()
        if item:
            self.viewmodel.handle_result_selection(item.get('title'), item.get('author'))
            self.viewmodel.view.switch_to_content_tab()

    def _view_ppr_internal(self):
        """Muda para a aba interna de PPR."""
        item = self._get_selected_data()
        if item:
            self.viewmodel.handle_result_selection(item.get('title'), item.get('author'))
            try: self.viewmodel.view.tabview.set("Conteúdo PPR")
            except ValueError: pass

    def _view_ppr_browser(self):
        """Abre o HTML da PPR no navegador."""
        item = self._get_selected_data()
        if item:
            self.viewmodel.handle_result_selection(item.get('title'), item.get('author'))
            self.viewmodel.open_ppr_in_browser()

    def _on_row_select(self, event):
        """Atualiza a seleção no ViewModel ao clicar na linha."""
        item = self._get_selected_data()
        if item:
            self.viewmodel.handle_result_selection(item.get('title'), item.get('author'))

    def __init__(self, view):
        self.view = view
        self.db = DatabaseModel(db_name=config.DB_NAME)
        self.scraper = ScraperModel()
        self.current_history_id = None
        self.selected_research = None
        
        # Flag de controle para interrupção (Botão Parar)
        self._stop_execution = False

    def initialize_data(self):
        """
        Carrega dados iniciais:
        1. Histórico na tabela.
        2. Status das fontes (checkboxes).
        3. Resultados já extraídos.
        4. Filtros da Home (evitar pesquisas repetidas).
        """
        self.load_history_list()
        
        # 1. Status das Fontes
        try:
            if hasattr(self.db, 'get_all_sources'):
                sources = self.db.get_all_sources()
                for root, status in sources.items():
                    self.view.update_source_status(root, status)
        except Exception: pass

        # 2. Resultados Salvos
        try:
            saved_data = self.db.get_all_pesquisas() 
            if saved_data:
                self.view.after_thread_safe(lambda: self.view.results_tab.display_results(saved_data))
        except Exception as e:
            self._log(f"Erro ao carregar resultados: {e}", "red")

        # 3. Filtros da Home (Exclusão de já pesquisados)
        try:
            if hasattr(self.db, 'get_existing_searches'):
                existing_combinations = self.db.get_existing_searches()
                self.view.after_thread_safe(lambda: self.view.filter_home_options(existing_combinations))
        except Exception as e:
            self._log(f"Erro ao carregar filtros de histórico: {e}", "yellow")

    def load_history_list(self):
        """
        Prepara a lista de histórico para a Tabela (Treeview).
        Extrai Termo, Ano e Página para as colunas.
        """
        raw_items = self.db.get_plb_list() 
        structured_items = []

        for item in raw_items:
            try:
                # (id, url, created_at, search_term, search_year)
                item_id = item[0]
                url = item[1]
                created_at = item[2]
                db_term = item[3] if len(item) > 3 else None
                db_year = item[4] if len(item) > 4 else None
            except IndexError:
                continue

            if db_term and db_year:
                termo = db_term
                ano = db_year
                try: pagina = parse_qs(urlparse(url).query).get('page', ['1'])[0]
                except: pagina = '1'
            else:
                # Fallback: Extrair da URL
                try:
                    parsed = urlparse(url)
                    params = parse_qs(parsed.query)
                    termo_raw = params.get('lookfor0[]', params.get('lookfor', ['-']))[0]
                    termo = unquote(termo_raw).replace('"', '')
                    ano = params.get('publishDatefrom', ['-'])[0]
                    pagina = params.get('page', ['1'])[0]
                except:
                    termo, ano, pagina = "URL Personalizada", "-", "1"

            structured_items.append((item_id, termo, ano, pagina, created_at, url))

        self.view.after_thread_safe(lambda: self.view.history_tab.update_table(structured_items))

    def stop_scraping_process(self):
        self._stop_execution = True
        self._log("🛑 Parando... Aguarde o fim da requisição atual.", "red")

    def _reset_stop_flag(self):
        self._stop_execution = False

    def start_scraping_command(self):
        url = self.view.get_url_input()
        if not url: return
        
        term, year = None, None
        if hasattr(self.view, 'get_current_selection'):
            term, year = self.view.get_current_selection()
        
        self.view.toggle_button(False)
        threading.Thread(target=self._run_task, args=(url, term, year)).start()

    def _run_task(self, url, term=None, year=None):
        try:
            html = self.scraper.fetch_html(url)
            self.db.save_plb(url, html, term, year)
            
            self.view.after_thread_safe(lambda: self.view.home_tab.display_html(html))
            self.view.after_thread_safe(self.load_history_list)
            
            # Atualiza filtros para remover a pesquisa feita
            self.initialize_data()
            
            if hasattr(self, '_update_source_ui_and_db'):
                self._update_source_ui_and_db(url, True)
            
            self._log("PLB capturada e salva com sucesso.", "green")
        except Exception as e:
            if hasattr(self, '_update_source_ui_and_db'):
                self._update_source_ui_and_db(url, False)
            self._log(f"Erro: {str(e)}", "red")
        finally:
            self.view.toggle_button(True)

    def check_pagination_and_scrape(self, history_id):
        try:
            record = self.db.get_plb_by_id(history_id)
            if not record: return
            
            url = record[1]
            html = record[2]
            term = record[3] if len(record) > 3 else None
            year = record[4] if len(record) > 4 else None
            
            max_page = self._extract_max_page(html)
            
            if max_page > 1:
                self._log(f"Iniciando DeepScrap Individual (Total: {max_page} págs)...", "yellow")
                self.view.toggle_button(False)
                if hasattr(self.view, 'toggle_stop_button'): 
                    self.view.toggle_stop_button(True)
                
                threading.Thread(target=self._run_pagination_task, args=(url, max_page, term, year)).start()
            else:
                self._log("Esta pesquisa parece ter apenas 1 página.", "yellow")
        except Exception as e:
            self._log(f"Erro ao iniciar paginação: {e}", "red")

    def scrape_all_page1_pagination(self):
        raw_items = self.db.get_plb_list()
        page1_ids = []
        for item in raw_items:
            try:
                # Verifica se é página 1 pela URL
                parsed = urlparse(item[1])
                page = int(parse_qs(parsed.query).get('page', ['1'])[0])
                if page == 1: page1_ids.append(item[0])
            except: continue

        if not page1_ids:
            self._log("Nenhuma 'Página 1' encontrada.", "yellow")
            return

        self._log(f"DeepScrap em Massa: {len(page1_ids)} pesquisas.", "yellow")
        self.view.toggle_button(False)
        if hasattr(self.view, 'toggle_stop_button'): 
            self.view.toggle_stop_button(True)
            
        threading.Thread(target=self._run_batch_deep_scraping, args=(page1_ids,)).start()

    def _run_pagination_task(self, base_url, max_page, term=None, year=None):
        self._reset_stop_flag()
        self._run_pagination_task_sync(base_url, max_page, term, year)
        
        self.view.toggle_button(True)
        if hasattr(self.view, 'toggle_stop_button'): self.view.toggle_stop_button(False)
        self._log("DeepScrap individual concluído.", "green")

    def _run_batch_deep_scraping(self, history_ids):
        self._reset_stop_flag()
        total = len(history_ids)
        
        for index, h_id in enumerate(history_ids):
            if self._stop_execution: break
            try:
                record = self.db.get_plb_by_id(h_id)
                if not record: continue
                url, html, term, year = record[1], record[2], record[3], record[4]
                
                max_page = self._extract_max_page(html)
                if max_page > 1:
                    self._log(f"[{index+1}/{total}] '{term}': {max_page} págs.", "white")
                    self._run_pagination_task_sync(url, max_page, term, year)
                else:
                    self._log(f"[{index+1}/{total}] '{term}' só tem 1 pág.", "white")
            except Exception as e:
                self._log(f"Erro item {index+1}: {e}", "red")
        
        self.view.toggle_button(True)
        if hasattr(self.view, 'toggle_stop_button'): self.view.toggle_stop_button(False)
        self._log("Processo em massa finalizado.", "green" if not self._stop_execution else "red")

    def _run_pagination_task_sync(self, base_url, max_page, term, year):
        separator = "&" if "?" in base_url else "?"
        count_new = 0
        count_skipped = 0

        for i in range(2, max_page + 1):
            if self._stop_execution:
                self._log(f"🛑 Interrompido na página {i-1}.", "red")
                break

            if "page=" in base_url:
                current_url = re.sub(r'page=\d+', f'page={i}', base_url)
            else:
                current_url = f"{base_url}{separator}page={i}"
            
            # Resume: Pula se já existe
            if hasattr(self.db, 'check_url_exists') and self.db.check_url_exists(current_url):
                if count_skipped == 0 or i % 10 == 0:
                    self._log(f"  -> Pág {i} já salva. Pulando...", "white")
                count_skipped += 1
                continue

            self._log(f"  -> Baixando pág {i}/{max_page}...", "yellow")
            try:
                html = self.scraper.fetch_html(current_url)
                if html:
                    self.db.save_plb(current_url, html, term, year)
                    if hasattr(self, '_update_source_ui_and_db'):
                        self._update_source_ui_and_db(current_url, True)
                    count_new += 1
                time.sleep(1.5)
            except Exception as e:
                self._log(f"Falha pág {i}: {e}", "red")
                if hasattr(self, '_update_source_ui_and_db'):
                    self._update_source_ui_and_db(current_url, False)
        
        if count_new > 0 or count_skipped > 0:
            self._log(f"Item: {count_new} novos, {count_skipped} pulados.", "green")
        self.view.after_thread_safe(self.load_history_list)

    def _extract_max_page(self, html_content):
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            stats_node = soup.find(string=re.compile(r"resultados de", re.IGNORECASE))
            if stats_node:
                full_text = stats_node.find_parent().get_text(strip=True)
                match = re.search(r"resultados de\s*([\d\.]+)", full_text, re.IGNORECASE)
                if match:
                    total = int(match.group(1).replace('.', ''))
                    return math.ceil(total / 20)
            
            page_links = soup.select('.pagination a')
            max_p = 1
            for link in page_links:
                numbers = re.findall(r'\d+', link.get_text(strip=True))
                if numbers:
                    val = int(numbers[-1])
                    if val > max_p: max_p = val
            return max_p
        except: return 1

    def extract_data_command(self, history_id):
        try:
            record = self.db.get_plb_by_id(history_id)
            if not record: return

            url = record[1]
            html = record[2]
            term = record[3] if len(record) > 3 else "Desconhecido"
            year = record[4] if len(record) > 4 else "-"
            
            if not html: return

            self._log(f"Minerando: {url}", "yellow")
            
            from models.parsers.vufind_parser import VufindParser

            data = self.scraper.extract_data(html, VufindParser(), base_url=url)
            
            if data:
                # Salva com Termo e Ano para unicidade
                if hasattr(self.db, 'save_pesquisas'):
                    self.db.save_pesquisas(data, term, year)
                
                self._log(f"Sucesso: {len(data)} itens extraídos.", "green")
                
                all_results = self.db.get_all_pesquisas()
                self.view.after_thread_safe(lambda: self.view.results_tab.display_results(all_results))
                self.view.switch_to_results_tab()
            else:
                self._log("Nenhum dado encontrado.", "red")
        except Exception as e:
            self._log(f"Erro na extração: {e}", "red")

    def delete_history_item(self, history_id):
        try:
            if hasattr(self.db, 'delete_plb'): self.db.delete_plb(history_id)
            else: self.db.delete_history(history_id)
            self.load_history_list()
            self._log(f"Registro {history_id} excluído.", "white")
        except Exception as e: self._log(f"Erro: {e}", "red")

    def open_plb_in_browser(self, history_id):
        try:
            record = self.db.get_plb_by_id(history_id)
            if record and len(record) > 2 and record[2]:
                self.view.open_html_from_db_in_browser(record[2])
            else: self._log("HTML não encontrado.", "yellow")
        except Exception as e: self._log(f"Erro: {e}", "red")

    def scrape_specific_search_url(self, url):
        self._log(f"Scrap Busca: {url}", "yellow")
        threading.Thread(target=self._run_specific_scraping_task, args=(url, 'buscador')).start()

    def scrape_repository_url(self, url):
        self._log(f"Scrap Repositório: {url}", "yellow")
        threading.Thread(target=self._run_specific_scraping_task, args=(url, 'repositorio')).start()

    def _run_specific_scraping_task(self, url, doc_type):
        try:
            html = self.scraper.fetch_html(url)
            if html:
                if doc_type == 'buscador': self.db.save_ppb_content(url, html)
                else: self.db.save_ppr_content(url, html)
                
                self._update_source_ui_and_db(url, True)
                self.view.after_thread_safe(self.load_history_list)
                self._log(f"Conteúdo de {doc_type} salvo.", "green")
            else:
                raise Exception("HTML vazio")
        except Exception as e:
            self._update_source_ui_and_db(url, False)
            self._log(f"Erro em {url}: {e}", "red")

    def scrape_pending_pprs(self):
        pending = self.db.get_pending_ppr_records()
        if not pending:
            self._log("Nenhum HTML pendente.", "green")
            return
        self._log(f"Baixando {len(pending)} pendentes...", "yellow")
        threading.Thread(target=self._run_batch_ppr_scraping, args=(pending,)).start()

    def _run_batch_ppr_scraping(self, pending_list):
        count = 0
        for pid, url in pending_list:
            root = self._extract_root_url(url)
            if not self.db.get_source_status(root):
                continue # Fonte bloqueada/falha
            try:
                html = self.scraper.fetch_html(url)
                if html:
                    self.db.save_ppr_content(url, html)
                    self._update_source_ui_and_db(url, True)
                    count += 1
                time.sleep(1.0)
            except:
                self._update_source_ui_and_db(url, False)
        self._log(f"Lote finalizado. {count} baixados.", "green")
        self.initialize_data()

    def batch_extract_univ_data(self):
        records = self.db.get_all_ppr_with_html()
        if not records:
            self._log("Sem HTMLs de repositório para analisar.", "yellow")
            return
        self._log(f"Analisando {len(records)} repositórios...", "yellow")
        threading.Thread(target=self._run_batch_extraction, args=(records,)).start()

    def _run_batch_extraction(self, records):
        try: from services.parser_factory import ParserFactory
        except: return
        factory = ParserFactory()
        count = 0
        for idx, (title, author, url, html) in enumerate(records):
            try:
                parser = factory.get_parser(url, html_content=html)
                data = parser.extract(html, url)
                self.db.update_univ_data(title, author, 
                                         data.get('sigla'), 
                                         data.get('universidade'), 
                                         data.get('programa'))
                count += 1
                if idx % 10 == 0: self._log(f"Processando {idx}...", "white")
            except: pass
        self._log(f"Extração concluída. {count} atualizados.", "green")
        self.initialize_data()

    def extract_univ_data(self):
        # Lógica individual (chamada pelo menu de contexto)
        if not hasattr(self, 'selected_research'): return
        title = self.selected_research["title"]
        author = self.selected_research["author"]
        res = self.db.get_ppr_full_content(title, author)
        if res and res[0] and res[1]:
            self._run_batch_extraction([(title, author, res[0], res[1])])
        else:
            self._log("HTML não encontrado. Faça o scrap primeiro.", "red")

    def on_tab_changed(self):
        if not hasattr(self, 'selected_research') or not self.selected_research: return
        current = self.view.tabview.get()
        t, a = self.selected_research["title"], self.selected_research["author"]
        
        if current == "Conteúdo PPB":
            h = self.db.get_extracted_html(t, a)
            if h: self.view.content_tab.display_html(h)
        elif current == "Conteúdo PPR":
            h = self.db.get_ppr_html(t, a)
            if h: self.view.repo_tab.display_html(h)

    def handle_result_selection(self, title, author):
        self.selected_research = {"title": title, "author": author}
        h1 = self.db.get_extracted_html(title, author)
        h2 = self.db.get_ppr_html(title, author)
        self.view.set_tab_state("Conteúdo PPB", "normal" if h1 else "disabled")
        self.view.set_tab_state("Conteúdo PPR", "normal" if h2 else "disabled")
        self.on_tab_changed()

    def open_ppb_browser_from_db(self, title=None, author=None):
        if not title:
            if hasattr(self, 'selected_research') and self.selected_research:
                title = self.selected_research["title"]
                author = self.selected_research["author"]
            else: return
        h = self.db.get_extracted_html(title, author)
        if h: self.view.open_html_from_db_in_browser(h)

    def open_ppr_in_browser(self):
        if hasattr(self, 'selected_research') and self.selected_research:
            h = self.db.get_ppr_html(self.selected_research["title"], self.selected_research["author"])
            if h: self.view.open_html_from_db_in_browser(h)
            
    def _log(self, message, color="white"):
        try: self.db.save_log(message)
        except: pass
        self.view.update_status(message, color)

    def _extract_root_url(self, url):
        try: return urlparse(url).netloc.split(':')[0]
        except: return ""

    def _update_source_ui_and_db(self, url, success):
        root = self._extract_root_url(url)
        if root:
            self.db.save_source_status(root, success)
            self.view.update_source_status(root, success)
