import customtkinter as ctk
import webbrowser
from tkinter import ttk
import tkinter as tk
from tkinter import messagebox
import config

class ResultsTab(ctk.CTkFrame):
    def __init__(self, parent, viewmodel, on_scrape_callback, on_repo_scrape_callback):
        super().__init__(parent)
        self.viewmodel = viewmodel
        self.on_scrape_callback = on_scrape_callback
        self.on_repo_scrape_callback = on_repo_scrape_callback
        
        # Estruturas para dados
        self.all_data = [] 
        self.item_map = {} 
        self.link_map = {} 

        self._setup_ui()
        self._setup_context_menu()

    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # --- 1. Barra de Ferramentas ---
        self.toolbar = ctk.CTkFrame(self, fg_color="transparent")
        self.toolbar.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))

        # Botão Baixar Pendentes
        self.btn_scrape_pending = ctk.CTkButton(
            self.toolbar, text="⬇️ Baixar HTMLs Pendentes", 
            command=self.viewmodel.scrape_pending_pprs, height=30,
            fg_color="#1f538d", hover_color="#14375e", font=config.FONTS["normal"]
        )
        self.btn_scrape_pending.pack(side="left", padx=(0, 10))

        # Botão Extrair em Lote
        self.btn_extract_batch = ctk.CTkButton(
            self.toolbar, text="🏷️ Extrair Dados Univ. (Lote)", 
            command=self.viewmodel.batch_extract_univ_data, height=30,
            fg_color="#27ae60", hover_color="#219150", font=config.FONTS["normal"]
        )
        self.btn_extract_batch.pack(side="left", padx=(0, 10))

        # --- NOVO BOTÃO: Parar ---
        self.btn_stop = ctk.CTkButton(
            self.toolbar, text="⏹️ Parar",
            # Chama diretamente o método do ResultsViewModel
            command=lambda: self.viewmodel.results_vm.stop_process(), 
            height=30, fg_color="#c0392b", hover_color="#e74c3c",
            state="disabled", font=config.FONTS["normal"]
        )
        self.btn_stop.pack(side="left", padx=(0, 10))
        # -------------------------

        self.btn_refresh = ctk.CTkButton(
            self.toolbar, text="🔄 Atualizar",
            command=lambda: self.viewmodel.initialize_data(), height=30,
            fg_color="gray", hover_color="#555555", width=80, font=config.FONTS["normal"]
        )
        self.btn_refresh.pack(side="left")

        # --- 2. Filtros ---
        self.filter_frame = ctk.CTkFrame(self)
        self.filter_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        
        ctk.CTkLabel(self.filter_frame, text="Título:", font=config.FONTS["small"]).pack(side="left", padx=(10, 2))
        self.ent_filter_title = ctk.CTkEntry(self.filter_frame, width=200, placeholder_text="Filtrar...")
        self.ent_filter_title.pack(side="left", padx=5)
        self.ent_filter_title.bind("<KeyRelease>", self._apply_filters)

        ctk.CTkLabel(self.filter_frame, text="Autor:", font=config.FONTS["small"]).pack(side="left", padx=(10, 2))
        self.ent_filter_author = ctk.CTkEntry(self.filter_frame, width=150, placeholder_text="Filtrar...")
        self.ent_filter_author.pack(side="left", padx=5)
        self.ent_filter_author.bind("<KeyRelease>", self._apply_filters)

        ctk.CTkLabel(self.filter_frame, text="Univ.:", font=config.FONTS["small"]).pack(side="left", padx=(10, 2))
        self.ent_filter_univ = ctk.CTkEntry(self.filter_frame, width=100, placeholder_text="Sigla...")
        self.ent_filter_univ.pack(side="left", padx=5)
        self.ent_filter_univ.bind("<KeyRelease>", self._apply_filters)

        self.label_count = ctk.CTkLabel(self.filter_frame, text="Total: 0", font=config.FONTS["small"])
        self.label_count.pack(side="right", padx=15)

        # --- 3. Tabela (Treeview) ---
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(0, weight=1)

        style = ttk.Style()
        style.theme_use("default")
        
        style.configure("Treeview", 
                        background=config.COLORS["table_bg"], 
                        foreground=config.COLORS["text"], 
                        fieldbackground=config.COLORS["table_bg"], 
                        rowheight=30, borderwidth=0, font=config.FONTS["small"])
        
        style.map('Treeview', background=[('selected', config.COLORS["table_selected"])])
        
        style.configure("Treeview.Heading", 
                        background=config.COLORS["table_header"], 
                        foreground=config.COLORS["text"], 
                        relief="flat", padding=(5, 5), font=config.FONTS["normal"])
        style.map("Treeview.Heading", background=[('active', '#343638')])

        columns = ("title", "author", "sigla", "universidade", "programa")
        self.tree = ttk.Treeview(self.container, columns=columns, show="headings", selectmode="browse")

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
        self.all_data = results
        self._apply_filters()

    # --- Controle de Estado dos Botões (Novo) ---
    def set_stop_button_state(self, busy):
        """Habilita o botão Parar se estiver ocupado, e desabilita os outros."""
        state_stop = "normal" if busy else "disabled"
        state_others = "disabled" if busy else "normal"
        
        self.btn_stop.configure(state=state_stop)
        self.btn_scrape_pending.configure(state=state_others)
        self.btn_extract_batch.configure(state=state_others)
        self.btn_refresh.configure(state=state_others)

    def _apply_filters(self, event=None):
        f_title = self.ent_filter_title.get().lower().strip()
        f_author = self.ent_filter_author.get().lower().strip()
        f_univ = self.ent_filter_univ.get().lower().strip()

        for item in self.tree.get_children(): self.tree.delete(item)
        self.link_map.clear()
        self.item_map.clear()

        count = 0
        for idx, item in enumerate(self.all_data):
            title = str(item.get('title', '') or '').lower()
            author = str(item.get('author', '') or '').lower()
            univ = (str(item.get('univ_sigla', '') or '') + str(item.get('univ_nome', '') or '')).lower()

            if (f_title in title) and (f_author in author) and (f_univ in univ):
                values = (
                    item.get('title'), item.get('author'), 
                    item.get('univ_sigla', '-'), item.get('univ_nome', 'Pendente...'),
                    item.get('programa', '-')
                )
                tree_id = self.tree.insert("", "end", values=values)
                self.link_map[tree_id] = {'search': item.get('ppb_link'), 'repo': item.get('ppr_link')}
                self.item_map[tree_id] = idx
                count += 1
        self.label_count.configure(text=f"Total: {count}")

    def _sort_column(self, col, reverse):
        l = [(self.tree.set(k, col), k) for k in self.tree.get_children('')]
        try: l.sort(key=lambda t: t[0].lower(), reverse=reverse)
        except: l.sort(reverse=reverse)
        for index, (val, k) in enumerate(l): self.tree.move(k, '', index)
        self.tree.heading(col, command=lambda: self._sort_column(col, not reverse))

    def _on_double_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region == "cell":
            sel = self.tree.selection()
            if sel:
                links = self.link_map.get(sel[0])
                if links and links.get('repo'): webbrowser.open(links['repo'])

    def _on_row_select(self, event):
        sel = self.tree.selection()
        if sel:
            idx = self.item_map.get(sel[0])
            if idx is not None:
                item = self.all_data[idx]
                self.viewmodel.handle_result_selection(item.get('title'), item.get('author'))

    def _scrape_selected_row(self):
        sel = self.tree.selection()
        if sel:
            links = self.link_map.get(sel[0])
            if links and links['search']: self.on_scrape_callback(links['search'])
    
    def _scrape_repo_row(self):
        sel = self.tree.selection()
        if sel:
            links = self.link_map.get(sel[0])
            if links and links['repo']: self.on_repo_scrape_callback(links['repo'])

    def _view_ppb_internal(self):
        selected = self.tree.selection()
        if not selected: return
        values = self.tree.item(selected[0])['values']
        self.viewmodel.handle_result_selection(values[0], values[1])
        try: self.viewmodel.view.tabview.set("Conteúdo PPB")
        except ValueError: pass

    def _view_ppb_browser(self):
        selected = self.tree.selection()
        if not selected: return
        values = self.tree.item(selected[0])['values']
        self.viewmodel.handle_result_selection(values[0], values[1])
        self.viewmodel.open_ppb_browser_from_db()

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
        self.context_menu.add_command(label="🌐 Abrir PPR no Navegador", command=self._view_ppr_browser)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="🎓 Obter Dados da Universidade (via PPR)", command=self.viewmodel.extract_univ_data)

    def _show_context_menu(self, event):
        row = self.tree.identify_row(event.y)
        if row:
            self.tree.selection_set(row)
            try: self.context_menu.tk_popup(event.x_root, event.y_root)
            finally: self.context_menu.grab_release()