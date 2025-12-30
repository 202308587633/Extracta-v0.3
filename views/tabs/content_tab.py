import customtkinter as ctk

class ContentTab(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self._setup_ui()

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