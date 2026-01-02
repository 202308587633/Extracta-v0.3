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
        
    def __init__(self, parent, on_select_callback, on_delete_callback, on_pagination_callback, on_extract_callback, on_browser_callback, on_deep_scrape_callback):
        super().__init__(parent)
        self.on_select_callback = on_select_callback
        self.on_delete_callback = on_delete_callback
        self.on_pagination_callback = on_pagination_callback
        self.on_extract_callback = on_extract_callback
        self.on_browser_callback = on_browser_callback
        self.on_deep_scrape_callback = on_deep_scrape_callback
        self.item_map = {} 
        self._setup_ui()
        self._setup_context_menu()

    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Cabeçalho
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        
        self.lbl_title = ctk.CTkLabel(self.header_frame, text="Histórico de Pesquisas (PLB)", font=("Roboto", 16, "bold"))
        self.lbl_title.pack(side="left")

        # BOTÃO: DeepScrap em Massa (Todas as páginas)
        self.btn_deep_all = ctk.CTkButton(
            self.header_frame, 
            text="📚 DeepScrap (Todas as Páginas)", 
            command=self._on_deep_scrape_click,
            fg_color="#d35400", 
            hover_color="#a04000",
            width=200
        )
        self.btn_deep_all.pack(side="right", padx=5)

        # Tabela (Treeview)
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(0, weight=1)

        style = ttk.Style()
        style.theme_use("default")
        bg_color = "#2b2b2b"
        text_color = "#ffffff"
        selected_bg = "#1f538d"
        header_bg = "#1f1f1f"
        
        style.configure("Treeview", background=bg_color, foreground=text_color, 
                        fieldbackground=bg_color, rowheight=25, borderwidth=0, font=("Roboto", 11))
        style.map('Treeview', background=[('selected', selected_bg)])
        style.configure("Treeview.Heading", background=header_bg, foreground=text_color, relief="flat", font=("Roboto", 11, "bold"))
        style.map("Treeview.Heading", background=[('active', '#343638')])

        columns = ("id", "termo", "ano", "pagina", "data")
        self.tree = ttk.Treeview(self.container, columns=columns, show="headings", selectmode="browse")

        self.tree.heading("id", text="ID")
        self.tree.heading("termo", text="Termo Pesquisado")
        self.tree.heading("ano", text="Ano")
        self.tree.heading("pagina", text="Pág.")
        self.tree.heading("data", text="Data/Hora")

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

    def _on_deep_scrape_click(self):
        if messagebox.askyesno("Confirmar DeepScrap", "Isso irá buscar TODAS as páginas seguintes para cada pesquisa iniciada (Página 1).\n\nEste processo pode ser longo. Deseja continuar?"):
            self.on_deep_scrape_callback()

    def _setup_context_menu(self):
        self.context_menu = tk.Menu(self, tearoff=0, bg="#2b2b2b", fg="white", activebackground="#1f538d", activeforeground="white")
        self.context_menu.add_command(label="📄 Visualizar HTML (Navegador)", command=self._on_browser)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="➡️ Buscar Todas as Páginas Seguintes", command=self._on_pagination) # Texto atualizado
        self.context_menu.add_separator()
        self.context_menu.add_command(label="⛏️ Extrair Links (PLB)", command=self._on_extract)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="🗑️ Excluir Registro", command=self._on_delete)

    def update_table(self, items):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.item_map.clear()
        if not items: return
        for item in items:
            values = (item[0], item[1], item[2], item[3], item[4])
            tree_id = self.tree.insert("", "end", values=values)
            self.item_map[tree_id] = item[0]

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
        if db_id: self.on_browser_callback(db_id)

    def _on_pagination(self):
        db_id = self._get_selected_db_id()
        if db_id: self.on_pagination_callback(db_id)

    def _on_extract(self):
        db_id = self._get_selected_db_id()
        if db_id: self.on_extract_callback(db_id)

    def _on_delete(self):
        db_id = self._get_selected_db_id()
        if db_id:
            if messagebox.askyesno("Confirmar", "Deseja excluir este histórico e seus dados extraídos?"):
                self.on_delete_callback(db_id)