import customtkinter as ctk
import webbrowser
from tkinter import ttk
import tkinter as tk
from tkinter import messagebox

class ResultsTab(ctk.CTkFrame):
    def __init__(self, parent, viewmodel, on_scrape_callback, on_repo_scrape_callback):
        super().__init__(parent)
        self.viewmodel = viewmodel
        self.on_scrape_callback = on_scrape_callback
        self.on_repo_scrape_callback = on_repo_scrape_callback
        
        # Estruturas para dados
        self.all_data = [] # Lista completa de dicionários vinda do banco
        self.item_map = {} # Mapeia ID da Treeview -> Índice na lista self.all_data (filtrada ou não)
        self.link_map = {} # Mapeia ID da Treeview -> Links (para manter compatibilidade com menu de contexto)

        self._setup_ui()
        self._setup_context_menu()

    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1) # Tabela (linha 2) expande

        # --- 1. Barra de Ferramentas (Botões de Ação) ---
        self.toolbar = ctk.CTkFrame(self, fg_color="transparent")
        self.toolbar.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))

        # Botão: Baixar HTMLs Pendentes
        self.btn_scrape_pending = ctk.CTkButton(
            self.toolbar, 
            text="⬇️ Baixar HTMLs Pendentes", 
            command=self.viewmodel.scrape_pending_pprs,
            height=30,
            fg_color="#1f538d",
            hover_color="#14375e",
            font=("Roboto", 12, "bold")
        )
        self.btn_scrape_pending.pack(side="left", padx=(0, 10))

        # Botão: Extrair Dados em Lote
        self.btn_extract_batch = ctk.CTkButton(
            self.toolbar, 
            text="🏷️ Extrair Dados Univ. (Lote)", 
            command=self.viewmodel.batch_extract_univ_data,
            height=30,
            fg_color="#27ae60", 
            hover_color="#219150",
            font=("Roboto", 12, "bold")
        )
        self.btn_extract_batch.pack(side="left", padx=(0, 10))

        # Botão: Atualizar
        self.btn_refresh = ctk.CTkButton(
            self.toolbar,
            text="🔄 Atualizar",
            command=lambda: self.viewmodel.initialize_data(),
            height=30,
            fg_color="gray",
            hover_color="#555555",
            width=80
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
        
        style.configure("Treeview", background=bg_color, foreground=text_color, fieldbackground=bg_color, rowheight=30, borderwidth=0, font=("Roboto", 11))
        style.map('Treeview', background=[('selected', selected_bg)])
        style.configure("Treeview.Heading", background=header_bg, foreground=text_color, relief="flat", padding=(5, 5), font=("Roboto", 12, "bold"))
        style.map("Treeview.Heading", background=[('active', '#343638')])

        # Definição das Colunas
        columns = ("title", "author", "sigla", "universidade", "programa")
        self.tree = ttk.Treeview(self.container, columns=columns, show="headings", selectmode="browse")

        # Cabeçalhos com Ordenação
        self.tree.heading("title", text="Nome da Pesquisa", command=lambda: self._sort_column("title", False))
        self.tree.heading("author", text="Autor", command=lambda: self._sort_column("author", False))
        self.tree.heading("sigla", text="Sigla", command=lambda: self._sort_column("sigla", False))
        self.tree.heading("universidade", text="Universidade", command=lambda: self._sort_column("universidade", False))
        self.tree.heading("programa", text="Programa", command=lambda: self._sort_column("programa", False))

        # Larguras
        self.tree.column("title", width=300, minwidth=150, anchor="w")
        self.tree.column("author", width=150, minwidth=100, anchor="w")
        self.tree.column("sigla", width=60, anchor="center")
        self.tree.column("universidade", width=200, anchor="w")
        self.tree.column("programa", width=200, anchor="w")

        # Scrollbar
        self.scrollbar = ctk.CTkScrollbar(self.container, command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.scrollbar.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")

        # Eventos
        self.tree.bind("<Double-1>", self._on_double_click)
        self.tree.bind("<Button-3>", self._show_context_menu)
        self.tree.bind("<<TreeviewSelect>>", self._on_row_select)

    def display_results(self, results):
        """
        Recebe a lista de resultados do banco e atualiza a tabela.
        Salva em self.all_data para permitir filtragem local.
        """
        self.all_data = results
        self._apply_filters() # Aplica filtros (se houver) e popula a tabela

    def _apply_filters(self, event=None):
        """Filtra self.all_data e repopula a Treeview."""
        f_title = self.ent_filter_title.get().lower().strip()
        f_author = self.ent_filter_author.get().lower().strip()
        f_univ = self.ent_filter_univ.get().lower().strip()

        # Limpa tabela
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        self.link_map.clear()
        self.item_map.clear()

        count = 0
        for idx, item in enumerate(self.all_data):
            # Garante strings seguras
            title = str(item.get('title', '') or '').lower()
            author = str(item.get('author', '') or '').lower()
            univ_sigla = str(item.get('univ_sigla', '') or '').lower()
            univ_nome = str(item.get('univ_nome', '') or '').lower()

            # Lógica de Filtro (AND)
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
                
                # Insere na Treeview
                tree_id = self.tree.insert("", "end", values=values)
                
                # Mapeia para manter as funcionalidades
                self.link_map[tree_id] = {'search': item.get('ppb_link'), 'repo': item.get('ppr_link')}
                self.item_map[tree_id] = idx # Índice original em self.all_data
                count += 1

        self.label_count.configure(text=f"Total: {count}")

    def _sort_column(self, col, reverse):
        """Ordena a Treeview pela coluna clicada."""
        l = [(self.tree.set(k, col), k) for k in self.tree.get_children('')]
        
        try:
            # Tenta ordenar case-insensitive
            l.sort(key=lambda t: t[0].lower(), reverse=reverse)
        except:
            l.sort(reverse=reverse)

        # Reorganiza os itens
        for index, (val, k) in enumerate(l):
            self.tree.move(k, '', index)

        # Alterna a ordem para o próximo clique
        self.tree.heading(col, command=lambda: self._sort_column(col, not reverse))

    def _clear_filters(self):
        """Limpa os campos de filtro."""
        self.ent_filter_title.delete(0, "end")
        self.ent_filter_author.delete(0, "end")
        self.ent_filter_univ.delete(0, "end")
        self._apply_filters()

    # --- MÉTODOS MANTIDOS (Funcionalidades existentes) ---

    def _show_context_menu(self, event):
        row_id = self.tree.identify_row(event.y)
        if row_id:
            self.tree.selection_set(row_id)
            try: self.context_menu.tk_popup(event.x_root, event.y_root)
            finally: self.context_menu.grab_release()

    def _on_double_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell": return
        row_id = self.tree.identify_row(event.y)
        links = self.link_map.get(row_id)
        if links and links.get('repo'):
            webbrowser.open(links['repo'])

    def _on_row_select(self, event):
        selected = self.tree.selection()
        if not selected: return
        values = self.tree.item(selected[0])['values']
        self.viewmodel.handle_result_selection(values[0], values[1])

    def _scrape_selected_row(self):
        selected = self.tree.selection()
        if not selected: return
        item_id = selected[0]
        links = self.link_map.get(item_id)
        if links and links.get('search'):
            self.on_scrape_callback(links['search'])

    def _scrape_repo_row(self):
        selected = self.tree.selection()
        if not selected: return
        item_id = selected[0]
        links = self.link_map.get(item_id)
        if links and links.get('repo'):
            self.on_repo_scrape_callback(links['repo'])

    def _view_ppb_browser(self):
        selected = self.tree.selection()
        if not selected: return
        values = self.tree.item(selected[0])['values']
        html = self.viewmodel.db.get_extracted_html(values[0], values[1])
        self.viewmodel.view.open_html_from_db_in_browser(html)

    def _view_ppb_internal(self):
        selected = self.tree.selection()
        if not selected: return
        values = self.tree.item(selected[0])['values']
        self.viewmodel.handle_result_selection(values[0], values[1])
        self.viewmodel.view.switch_to_content_tab()

    def _view_ppr_internal(self):
        selected = self.tree.selection()
        if not selected: return
        values = self.tree.item(selected[0])['values']
        self.viewmodel.handle_result_selection(values[0], values[1])
        try: self.viewmodel.view.tabview.set("Conteúdo PPR")
        except ValueError: pass

    def _view_ppr_browser(self):
        selected = self.tree.selection()
        if not selected: return
        values = self.tree.item(selected[0])['values']
        self.viewmodel.handle_result_selection(values[0], values[1])
        self.viewmodel.open_ppr_in_browser()

    def _open_url(self, url):
        if url: webbrowser.open(url)

    def _setup_context_menu(self):
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="🕷️ Scrap do Link de Busca", command=self._scrape_selected_row)
        self.context_menu.add_command(label="📂 Scrap do Link do Repositório", command=self._scrape_repo_row)
        self.context_menu.add_separator()        
        self.context_menu.add_command(label="🔍 Visualizar PPB na Interface", command=self._view_ppb_internal)
        self.context_menu.add_command(label="🌐 Abrir PPB no Navegador", command=self._view_ppb_browser)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="📄 Visualizar PPR na Interface", command=self._view_ppr_internal)
        self.context_menu.add_command(label="🌍 Abrir PPR no Navegador", command=self._view_ppr_browser)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="🎓 Obter Dados da Universidade (via PPR)", command=self.viewmodel.extract_univ_data)