import customtkinter as ctk
import tkinter as tk

class ContentTab(ctk.CTkFrame):
    def __init__(self, parent, on_browser_callback): # Adicionado o argumento
        super().__init__(parent)
        self.on_browser_callback = on_browser_callback # Armazena o callback
        self._setup_ui()
        self._setup_context_menu() # Novo método para o menu

    def _setup_ui(self):
        self.textbox_content = ctk.CTkTextbox(self, corner_radius=10, font=("Consolas", 12))
        self.textbox_content.pack(fill="both", expand=True, padx=10, pady=10)
        self.textbox_content.insert("0.0", "O conteúdo do link raspado aparecerá aqui...")
        self.textbox_content.configure(state="disabled")

    def display_html(self, html_content):
        self.textbox_content.configure(state="normal")
        self.textbox_content.delete("0.0", "end")
        self.textbox_content.insert("0.0", html_content)
        self.textbox_content.configure(state="disabled")        

    def _setup_context_menu(self):
        """Cria o menu de contexto para abrir a PPB no navegador"""
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(
            label="🌐 Abrir PPB no Navegador", 
            command=self.on_browser_callback
        )
        # Vincula o clique do botão direito (Button-3) ao menu
        self.textbox_content.bind("<Button-3>", self._show_context_menu)

    def _show_context_menu(self, event):
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

