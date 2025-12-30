import customtkinter as ctk
from viewmodels.main_viewmodel import MainViewModel

class MainView(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configurações da Janela
        self.title("Scraper Minimalista MVVM")
        self.geometry("600x400")
        ctk.set_appearance_mode("Dark")  # Moderno/Escuro
        ctk.set_default_color_theme("blue")

        # Inicializa o ViewModel
        self.viewmodel = MainViewModel(self)

        self._setup_ui()

    def _setup_ui(self):
        # Sistema de Abas
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(padx=20, pady=20, fill="both", expand=True)

        self.tab_home = self.tabview.add("Scraper")
        self.tab_about = self.tabview.add("Sobre")

        # --- Aba Scraper ---
        self.label_title = ctk.CTkLabel(self.tab_home, text="Web Scraper", font=("Roboto", 24))
        self.label_title.pack(pady=20)

        self.entry_url = ctk.CTkEntry(self.tab_home, placeholder_text="Digite a URL (ex: google.com)", width=400)
        self.entry_url.pack(pady=10)

        self.btn_run = ctk.CTkButton(self.tab_home, text="Executar Scraping", command=self.viewmodel.start_scraping_command)
        self.btn_run.pack(pady=10)

        self.label_status = ctk.CTkLabel(self.tab_home, text="")
        self.label_status.pack(pady=10)

        # --- Aba Sobre ---
        lbl_about = ctk.CTkLabel(self.tab_about, text="Versão 1.0\nArquitetura MVVM", font=("Roboto", 16))
        lbl_about.pack(pady=50, padx=50)

    # --- Métodos Públicos para o ViewModel acessar ---
    def get_url_input(self):
        return self.entry_url.get().strip()

    def update_status(self, message, color_name="white"):
        # CustomTkinter precisa de cores hex ou nomes padrão
        color_map = {"red": "#FF5555", "green": "#50FA7B", "yellow": "#F1FA8C", "white": "#F8F8F2"}
        self.label_status.configure(text=message, text_color=color_map.get(color_name, "white"))

    def toggle_button(self, state):
        self.btn_run.configure(state="normal" if state else "disabled")