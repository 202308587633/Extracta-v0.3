import customtkinter as ctk
import webbrowser
import tkinter as tk
from tkinter import ttk
from views.base_table_view import BaseTableFrame
import config

class HistoryTab(BaseTableFrame):
    def __init__(self, parent, on_select_callback, on_delete_callback, 
                 on_pagination_callback, on_extract_callback, on_browser_callback,
                 on_deep_scrape_callback, on_stop_callback, on_extract_all_callback): # Adicionado parametro
        
        super().__init__(parent)
        self.on_select_callback = on_select_callback
        self.on_delete_callback = on_delete_callback
        self.on_pagination_callback = on_pagination_callback
        self.on_extract_callback = on_extract_callback
        self.on_browser_callback = on_browser_callback
        self.on_deep_scrape_callback = on_deep_scrape_callback
        self.on_stop_callback = on_stop_callback
        self.on_extract_all_callback = on_extract_all_callback # NOVO CALLBACK

        self._setup_ui()
        self._setup_context_menu()

    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # --- Toolbar ---
        self.toolbar = ctk.CTkFrame(self, fg_color="transparent")
        self.toolbar.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))

        self.btn_deep = ctk.CTkButton(
            self.toolbar, text="⏬ DeepScrap (Paginação)", 
            command=self.on_deep_scrape_callback, 
            height=30, fg_color="#8e44ad", hover_color="#732d91", font=config.FONTS["normal"]
        )
        self.btn_deep.pack(side="left", padx=(0, 10))

        # --- NOVOS BOTÕES ---
        self.btn_extract_all = ctk.CTkButton(
            self.toolbar, text="📑 Extrair Tudo (Parse)", 
            command=self.on_extract_all_callback, 
            height=30, fg_color="#d35400", hover_color="#a04000", font=config.FONTS["normal"]
        )
        self.btn_extract_all.pack(side="left", padx=(0, 10))

        self.btn_stop = ctk.CTkButton(
            self.toolbar, text="⏹️ Parar", 
            command=self.on_stop_callback, 
            height=30, fg_color="#c0392b", hover_color="#e74c3c", 
            state="disabled", font=config.FONTS["normal"]
        )
        self.btn_stop.pack(side="left")

        # --- Tabela ---
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(0, weight=1)

        cols_config = [
            ("id", "ID", 50, "center"),
            ("termo", "Termo", 200, "w"),
            ("ano", "Ano", 60, "center"),
            ("pagina", "Pág.", 50, "center"),
            ("data", "Capturado em", 150, "center"),
            ("url", "URL", 400, "w")
        ]
        
        self.setup_treeview(self.container, cols_config)
        self.tree.bind("<Double-1>", self._on_double_click)
        self.tree.bind("<Button-3>", self._show_context_menu)

    def update_table(self, data):
        self.tree.delete(*self.tree.get_children())
        for item in data:
            self.tree.insert("", "end", values=item)

    def _on_double_click(self, event):
        item = self.get_selected_values()
        if item and self.on_browser_callback:
            self.on_browser_callback(item[0])

    def _setup_context_menu(self):
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="🔍 Verificar Paginação e Baixar (DeepScrap)", command=self._ctx_pagination)
        self.context_menu.add_command(label="📑 Extrair Dados (Parse)", command=self._ctx_extract)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="🌐 Abrir no Navegador", command=self._ctx_browser)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="🗑️ Excluir", command=self._ctx_delete)

    def _show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            try: self.context_menu.tk_popup(event.x_root, event.y_root)
            finally: self.context_menu.grab_release()

    def _ctx_pagination(self):
        val = self.get_selected_values()
        if val: self.on_pagination_callback(val[0])

    def _ctx_extract(self):
        val = self.get_selected_values()
        if val: self.on_extract_callback(val[0])

    def _ctx_browser(self):
        val = self.get_selected_values()
        if val: self.on_browser_callback(val[0])

    def _ctx_delete(self):
        val = self.get_selected_values()
        if val: self.on_delete_callback(val[0])

    def set_stop_button_state(self, busy):
        state = "normal" if busy else "disabled"
        self.btn_stop.configure(state=state)
        # Opcional: Desabilitar outros botões enquanto processa
        btn_state = "disabled" if busy else "normal"
        self.btn_deep.configure(state=btn_state)
        self.btn_extract_all.configure(state=btn_state)