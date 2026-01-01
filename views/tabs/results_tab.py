import customtkinter as ctk
import webbrowser
from tkinter import ttk
import tkinter as tk

class ResultsTab(ctk.CTkFrame):
    def _sort_column(self, col, reverse):
        l = [(self.tree.set(k, col), k) for k in self.tree.get_children('')]
        try:
            l.sort(key=lambda t: t[0].lower(), reverse=reverse)
        except:
            l.sort(reverse=reverse)

        for index, (val, k) in enumerate(l):
            self.tree.move(k, '', index)

        self.tree.heading(col, command=lambda: self._sort_column(col, not reverse))

    def _open_url(self, url):
        if url:
            webbrowser.open(url)

    def _scrape_repo_row(self):
        """Dispara o callback para o link do repositório"""
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
        """Solicita carregamento e muda para a aba de busca"""
        selected = self.tree.selection()
        if not selected: return
        
        values = self.tree.item(selected[0])['values']
        self.viewmodel.handle_result_selection(values[0], values[1])
        
        # Chama o método da MainView que agora está protegido por try/except
        self.viewmodel.view.switch_to_content_tab()

    def _view_ppr_internal(self):
        """Solicita carregamento e muda para a aba PPR"""
        selected = self.tree.selection()
        if not selected: return
        
        values = self.tree.item(selected[0])['values']
        title, author = values[0], values[1]
        
        self.viewmodel.handle_result_selection(title, author)
        
        # Mude para o nome novo
        try:
            self.viewmodel.view.tabview.set("Conteúdo PPR")
        except ValueError:
            self.viewmodel._log("Erro: Aba 'Conteúdo PPR' não encontrada.", "red")

    def _view_ppr_browser(self):
        """Recupera o HTML da PPR do banco e abre no navegador"""
        selected = self.tree.selection()
        if not selected: return
        
        # Obtém os valores da linha selecionada (Título e Autor)
        values = self.tree.item(selected[0])['values']
        title, author = values[0], values[1]
        
        # Define a pesquisa selecionada no ViewModel para garantir a sincronia
        self.viewmodel.handle_result_selection(title, author)
        
        # Chama a função unificada no ViewModel para abrir a PPR
        self.viewmodel.open_ppr_in_browser()

    def __init__(self, parent, viewmodel, on_scrape_callback, on_repo_scrape_callback):
        super().__init__(parent)
        self.viewmodel = viewmodel
        self.on_scrape_callback = on_scrape_callback
        self.on_repo_scrape_callback = on_repo_scrape_callback
        self.link_map = {}
        self._setup_ui()
        self._setup_context_menu()

    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # --- 1. Barra de Ferramentas ---
        self.toolbar = ctk.CTkFrame(self, fg_color="transparent")
        self.toolbar.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))

        # Botão: Baixar HTMLs Pendentes (PPR)
        self.btn_scrape_pending = ctk.CTkButton(
            self.toolbar, 
            text="⬇️ Baixar HTMLs Pendentes", 
            command=self.viewmodel.scrape_pending_pprs,
            height=35,
            fg_color="#1f538d",
            hover_color="#14375e",
            font=("Roboto", 12, "bold")
        )
        self.btn_scrape_pending.pack(side="left", padx=(0, 10))

        # --- NOVO BOTÃO: Extrair Dados em Lote ---
        self.btn_extract_batch = ctk.CTkButton(
            self.toolbar, 
            text="🏷️ Extrair Dados Univ. (Lote)", 
            command=self.viewmodel.batch_extract_univ_data,
            height=35,
            fg_color="#27ae60", # Verde para diferenciar da ação de download
            hover_color="#219150",
            font=("Roboto", 12, "bold")
        )
        self.btn_extract_batch.pack(side="left", padx=(0, 10))
        # -----------------------------------------

        # Botão: Atualizar Tabela
        self.btn_refresh = ctk.CTkButton(
            self.toolbar,
            text="🔄 Atualizar Tabela",
            command=lambda: self.viewmodel.initialize_data(),
            height=35,
            fg_color="gray",
            hover_color="#555555",
            width=120
        )
        self.btn_refresh.pack(side="left")

        # --- 2. Label Info ---
        self.label_count = ctk.CTkLabel(self, text="Os resultados aparecerão aqui...", font=("Roboto", 14))
        self.label_count.grid(row=1, column=0, pady=(5, 5), sticky="ew")

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
        
        style.configure("Treeview",
                        background=bg_color,
                        foreground=text_color,
                        fieldbackground=bg_color,
                        rowheight=30,
                        borderwidth=0,
                        font=("Roboto", 11))
        
        style.map('Treeview', background=[('selected', selected_bg)])
        
        style.configure("Treeview.Heading",
                        background=header_bg,
                        foreground=text_color,
                        relief="flat",
                        padding=(5, 5),
                        font=("Roboto", 12, "bold"))
        
        style.map("Treeview.Heading",
                  background=[('active', '#343638')])

        columns = ("title", "author", "sigla", "universidade", "programa")
        self.tree = ttk.Treeview(self.container, columns=columns, show="headings", selectmode="browse")

        self.tree.heading("title", text="Nome da Pesquisa")
        self.tree.heading("author", text="Autor")
        self.tree.heading("sigla", text="Sigla")
        self.tree.heading("universidade", text="Universidade")
        self.tree.heading("programa", text="Programa")

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
        self.link_map.clear()
        for item in self.tree.get_children():
            self.tree.delete(item)

        for item in results:
            values = (
                item.get('title'), 
                item.get('author'), 
                item.get('univ_sigla', '-'), 
                item.get('univ_nome', 'Pendente...'),
                item.get('programa', '-') 
            )
            item_id = self.tree.insert("", "end", values=values)
            self.link_map[item_id] = {'search': item.get('ppb_link'), 'repo': item.get('ppr_link')}
            
        self.label_count.configure(text=f"Total de registros: {len(results)}")

    def _show_context_menu(self, event):
        row_id = self.tree.identify_row(event.y)
        if row_id:
            self.tree.selection_set(row_id)
            try:
                self.context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                self.context_menu.grab_release()

    def _scrape_selected_row(self):
        selected = self.tree.selection()
        if not selected: return
        item_id = selected[0]
        links = self.link_map.get(item_id)
        if links and links.get('search'):
            self.on_scrape_callback(links['search'])

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

    def _setup_context_menu(self):
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="🕷️ Scrap do Link de Busca", command=self._scrape_selected_row)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="🎓 Obter Dados da Universidade (Item)", command=self.viewmodel.extract_univ_data)