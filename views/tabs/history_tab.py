import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

class HistoryTab(ctk.CTkFrame):
    def update_list(self, history_items):
        """Atualiza a lista de PLBs e vincula o menu de contexto a cada botão"""
        for widget in self.scroll_list.winfo_children():
            widget.destroy()

        for item_id, url, date in history_items:
            btn_text = f"{date}\n{url}"
            btn = ctk.CTkButton(
                self.scroll_list, 
                text=btn_text, 
                anchor="w", 
                height=50,
                fg_color="transparent", 
                border_width=1,
                command=lambda i=item_id: self.on_select_callback(i)
            )
            btn.pack(fill="x", pady=2)
            
            # Vincula o clique direito no botão da lista para selecionar e abrir o menu
            btn.bind("<Button-3>", lambda e, i=item_id: self._right_click_list(e, i))

    def _right_click_list(self, event, item_id):
        """Seleciona a PLB automaticamente e abre o menu de contexto"""
        self.on_select_callback(item_id)
        self._show_context_menu(event)

    def display_content(self, html_content):
        self.textbox_content.configure(state="normal")
        self.textbox_content.delete("0.0", "end")
        self.textbox_content.insert("0.0", html_content)
        self.textbox_content.configure(state="disabled")

    def __init__(self, parent, on_select_callback, on_delete_callback, on_pagination_callback, on_extract_callback, on_browser_callback, on_deep_scrape_callback, on_stop_callback):
        super().__init__(parent)
        # Callbacks
        self.on_select_callback = on_select_callback
        self.on_delete_callback = on_delete_callback
        self.on_pagination_callback = on_pagination_callback
        self.on_extract_callback = on_extract_callback
        self.on_browser_callback = on_browser_callback
        self.on_deep_scrape_callback = on_deep_scrape_callback
        self.on_stop_callback = on_stop_callback

        # Armazenamento de dados para Filtros e Ordenação
        self.item_map = {} 
        self.all_data = [] # Lista completa: [(id, termo, ano, pagina, data, url), ...]
        
        self._setup_ui()
        self._setup_context_menu()

    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1) # A tabela (linha 2) é que deve expandir

        # --- 1. Cabeçalho Superior (Botões de Ação Global) ---
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        
        self.lbl_title = ctk.CTkLabel(self.header_frame, text="Histórico de Pesquisas (PLB)", font=("Roboto", 16, "bold"))
        self.lbl_title.pack(side="left")

        # Botão: Parar (Vermelho) - Inicia desabilitado
        self.btn_stop = ctk.CTkButton(
            self.header_frame,
            text="⏹️ Parar",
            command=self._on_stop_click,
            fg_color="#c0392b",
            hover_color="#e74c3c",
            width=80,
            state="disabled"
        )
        self.btn_stop.pack(side="right", padx=5)

        # Botão: DeepScrap em Massa
        self.btn_deep_all = ctk.CTkButton(
            self.header_frame, 
            text="📚 DeepScrap (Todas as Páginas)", 
            command=self._on_deep_scrape_click,
            fg_color="#d35400", 
            hover_color="#a04000",
            width=200
        )
        self.btn_deep_all.pack(side="right", padx=5)

        # --- 2. Barra de Filtros (NOVA FUNCIONALIDADE) ---
        self.filter_frame = ctk.CTkFrame(self)
        self.filter_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        
        # Filtro: Termo
        ctk.CTkLabel(self.filter_frame, text="Filtrar Termo:", font=("Roboto", 12)).pack(side="left", padx=(10, 5))
        self.entry_filter_term = ctk.CTkEntry(self.filter_frame, width=200, placeholder_text="Digite para filtrar...")
        self.entry_filter_term.pack(side="left", padx=5)
        self.entry_filter_term.bind("<KeyRelease>", self._apply_filters)

        # Filtro: Ano
        ctk.CTkLabel(self.filter_frame, text="Filtrar Ano:", font=("Roboto", 12)).pack(side="left", padx=(20, 5))
        self.entry_filter_year = ctk.CTkEntry(self.filter_frame, width=100, placeholder_text="Ex: 2024")
        self.entry_filter_year.pack(side="left", padx=5)
        self.entry_filter_year.bind("<KeyRelease>", self._apply_filters)

        # Botão Limpar
        self.btn_clear_filters = ctk.CTkButton(
            self.filter_frame, 
            text="❌ Limpar", 
            width=80, 
            fg_color="gray", 
            command=self._clear_filters
        )
        self.btn_clear_filters.pack(side="left", padx=20)

        # --- 3. Tabela Treeview (Listagem) ---
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(0, weight=1)

        style = ttk.Style()
        style.theme_use("default")
        bg_color = "#2b2b2b"
        text_color = "#ffffff"
        selected_bg = "#1f538d"
        header_bg = "#1f1f1f"
        
        style.configure("Treeview", background=bg_color, foreground=text_color, fieldbackground=bg_color, rowheight=25, borderwidth=0, font=("Roboto", 11))
        style.map('Treeview', background=[('selected', selected_bg)])
        style.configure("Treeview.Heading", background=header_bg, foreground=text_color, relief="flat", font=("Roboto", 11, "bold"))
        style.map("Treeview.Heading", background=[('active', '#343638')])

        columns = ("id", "termo", "ano", "pagina", "data")
        self.tree = ttk.Treeview(self.container, columns=columns, show="headings", selectmode="browse")

        # Configuração dos Cabeçalhos com COMANDO DE ORDENAÇÃO
        self.tree.heading("id", text="ID", command=lambda: self._sort_column("id", False))
        self.tree.heading("termo", text="Termo Pesquisado", command=lambda: self._sort_column("termo", False))
        self.tree.heading("ano", text="Ano", command=lambda: self._sort_column("ano", False))
        self.tree.heading("pagina", text="Pág.", command=lambda: self._sort_column("pagina", False))
        self.tree.heading("data", text="Data/Hora", command=lambda: self._sort_column("data", False))

        self.tree.column("id", width=40, anchor="center")
        self.tree.column("termo", width=300, anchor="w")
        self.tree.column("ano", width=60, anchor="center")
        self.tree.column("pagina", width=50, anchor="center")
        self.tree.column("data", width=150, anchor="center")

        self.scrollbar = ctk.CTkScrollbar(self.container, command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.scrollbar.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")

        self.tree.bind("<Button-3>", self._show_context_menu)
        self.tree.bind("<Double-1>", self._on_double_click)

    def _sort_column(self, col, reverse):
        """Ordena a árvore baseada na coluna clicada."""
        l = [(self.tree.set(k, col), k) for k in self.tree.get_children('')]
        
        # Tenta converter para número para ordenar corretamente IDs e Anos
        try:
            l.sort(key=lambda t: int(t[0]) if t[0].isdigit() else t[0].lower(), reverse=reverse)
        except ValueError:
            l.sort(reverse=reverse)

        # Reorganiza os itens
        for index, (val, k) in enumerate(l):
            self.tree.move(k, '', index)

        # Alterna a ordem para o próximo clique
        self.tree.heading(col, command=lambda: self._sort_column(col, not reverse))

    def update_table(self, items):
        """Recebe os dados do ViewModel e armazena na memória local."""
        self.all_data = items # Guarda cópia completa: (id, termo, ano, pagina, data, url)
        self._apply_filters() # Popula a árvore aplicando filtros

    def _apply_filters(self, event=None):
        """Filtra self.all_data e atualiza a visualização."""
        filter_term = self.entry_filter_term.get().lower().strip()
        filter_year = self.entry_filter_year.get().lower().strip()

        # Limpa tabela atual
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.item_map.clear()

        # Filtra e Reinsere
        for item in self.all_data:
            # item = (id, termo, ano, pagina, data, url)
            db_id = item[0]
            termo = str(item[1]).lower()
            ano = str(item[2]).lower()

            # Verifica se corresponde aos filtros
            match_term = filter_term in termo if filter_term else True
            match_year = filter_year in ano if filter_year else True

            if match_term and match_year:
                values = (item[0], item[1], item[2], item[3], item[4])
                tree_id = self.tree.insert("", "end", values=values)
                self.item_map[tree_id] = db_id

    def _clear_filters(self):
        self.entry_filter_term.delete(0, "end")
        self.entry_filter_year.delete(0, "end")
        self._apply_filters()

    def set_stop_button_state(self, state):
        """Habilita ou desabilita o botão parar (True=Normal, False=Disabled)"""
        s = "normal" if state else "disabled"
        self.btn_stop.configure(state=s)

    def _on_stop_click(self):
        if self.on_stop_callback:
            self.on_stop_callback()
        
    def _on_deep_scrape_click(self):
        if messagebox.askyesno("Confirmar DeepScrap", "Buscar TODAS as páginas seguintes?\nO sistema verificará páginas já baixadas e continuará de onde parou."):
            if self.on_deep_scrape_callback:
                self.on_deep_scrape_callback()

    def _setup_context_menu(self):
        self.context_menu = tk.Menu(self, tearoff=0, bg="#2b2b2b", fg="white", activebackground="#1f538d", activeforeground="white")
        self.context_menu.add_command(label="📄 Visualizar HTML", command=self._on_browser)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="➡️ Buscar Todas as Páginas Seguintes", command=self._on_pagination)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="⛏️ Extrair Links", command=self._on_extract)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="🗑️ Excluir", command=self._on_delete)

    def _get_selected_db_id(self):
        selected = self.tree.selection()
        if not selected: return None
        return self.item_map.get(selected[0])

    def _show_context_menu(self, event):
        row_id = self.tree.identify_row(event.y)
        if row_id:
            self.tree.selection_set(row_id)
            try:
                self.context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                self.context_menu.grab_release()

    def _on_double_click(self, event):
        if self._get_selected_db_id():
            self._on_browser()

    def _on_browser(self):
        db_id = self._get_selected_db_id()
        if db_id and self.on_browser_callback: self.on_browser_callback(db_id)

    def _on_pagination(self):
        db_id = self._get_selected_db_id()
        if db_id and self.on_pagination_callback: self.on_pagination_callback(db_id)

    def _on_extract(self):
        db_id = self._get_selected_db_id()
        if db_id and self.on_extract_callback: self.on_extract_callback(db_id)

    def _on_delete(self):
        db_id = self._get_selected_db_id()
        if db_id and self.on_delete_callback:
            if messagebox.askyesno("Confirmar", "Deseja excluir este histórico e seus dados extraídos?"):
                self.on_delete_callback(db_id)

