import customtkinter as ctk
import config
from viewmodels.main_viewmodel import MainViewModel
from views.tabs.home_tab import HomeTab
from views.tabs.log_tab import LogTab

class MainView(ctk.CTk):
    def __init__(self):
        super().__init__()
        self._configure_window()
        
        # Inicializa ViewModel passando self (View Principal)
        self.viewmodel = MainViewModel(self)
        
        self._setup_ui()

    def _configure_window(self):
        self.title(config.APP_TITLE)
        self.geometry(config.WINDOW_SIZE)
        ctk.set_appearance_mode(config.THEME_MODE)
        ctk.set_default_color_theme(config.COLOR_THEME)

    def _setup_ui(self):
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(padx=20, pady=20, fill="both", expand=True)

        # Criação das Abas
        self.home_tab = HomeTab(
            parent=self.tabview.add("Scraper"), 
            command_callback=self.viewmodel.start_scraping_command
        )
        self.home_tab.pack(fill="both", expand=True)

        self.log_tab = LogTab(parent=self.tabview.add("Log"))
        self.log_tab.pack(fill="both", expand=True)

    def get_url_input(self):
        return self.home_tab.get_url()

    def update_status(self, message, color_name="white"):
        # Mapeamento de cores (mantido do config ou local)
        colors = {
            "red": "#FF5555", 
            "green": "#50FA7B", 
            "yellow": "#F1FA8C", 
            "white": "#F8F8F2"
        }
        
        # 1. Atualiza o label visual na aba Home
        self.home_tab.set_status(message, colors.get(color_name, "white"))
        
        # 2. Registra no histórico da aba Log
        self.log_tab.append_log(message)
        
    def toggle_button(self, state):
        self.home_tab.set_button_state(state)

    def display_html_content(self, html_content):
        self.home_tab.display_html(html_content)
