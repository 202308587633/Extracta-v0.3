import customtkinter as ctk

class RepoTab(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.textbox = ctk.CTkTextbox(self, corner_radius=10, font=("Consolas", 12))
        self.textbox.pack(fill="both", expand=True, padx=10, pady=10)
        self.textbox.insert("0.0", "O conteúdo do repositório aparecerá aqui...")
        self.textbox.configure(state="disabled")

    def display_html(self, html_content):
        self.textbox.configure(state="normal")
        self.textbox.delete("0.0", "end")
        self.textbox.insert("0.0", html_content)
        self.textbox.configure(state="disabled")