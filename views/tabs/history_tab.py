import customtkinter as ctk
import tkinter as tk

class HistoryTab(ctk.CTkFrame):
    def __init__(self, parent, on_select_callback, on_delete_callback, on_pagination_callback, on_extract_callback, on_browser_callback):
        super().__init__(parent)
        self.on_select_callback = on_select_callback
        self.on_delete_callback = on_delete_callback
        self.on_pagination_callback = on_pagination_callback
        self.on_extract_callback = on_extract_callback
        self.on_browser_callback = on_browser_callback
        self._setup_ui()
        self._setup_context_menu()

    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=3)
        self.grid_rowconfigure(0, weight=1)

        # Listagem de PLBs (Esquerda)
        self.scroll_list = ctk.CTkScrollableFrame(self, label_text="Páginas de Listagem (PLB)")
        self.scroll_list.grid(row=0, column=0, padx=(0, 10), pady=10, sticky="nsew")

        # Exibição do HTML da PLB (Direita)
        self.textbox_content = ctk.CTkTextbox(self, corner_radius=10)
        self.textbox_content.grid(row=0, column=1, pady=10, sticky="nsew")
        self.textbox_content.configure(state="disabled", font=("Consolas", 12))

    def _setup_context_menu(self):
        """Cria o menu único para DeepScrap e visualização"""
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="📋 Fazer DeepScrap (Extrair Pesquisas, PPBs e LAPs)", command=self.on_extract_callback)
        self.context_menu.add_command(label="🔍 Buscar Paginação e Raspar PLBs seguintes", command=self.on_pagination_callback)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="🌐 Abrir PLB no Navegador", command=self.on_browser_callback)
        self.context_menu.add_command(label="❌ Excluir esta PLB", command=self.on_delete_callback)
        
        # Vincula o menu à caixa de texto (Direita)
        self.textbox_content.bind("<Button-3>", self._show_context_menu)
        # O vínculo com a listagem é feito dinamicamente na criação dos botões

    def _show_context_menu(self, event):
        """Exibe o menu na posição do clique"""
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

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