import customtkinter as ctk
import config
from viewmodels.main_viewmodel import MainViewModel
from views.tabs.home_tab import HomeTab
from views.tabs.log_tab import LogTab
from views.tabs.history_tab import HistoryTab
from views.tabs.results_tab import ResultsTab
from views.tabs.content_tab import ContentTab

class MainView(ctk.CTk):
    def __init__(self):
        super().__init__()
        self._configure_window()
        
        self.viewmodel = MainViewModel(self)
        
        self._setup_ui()
        
        self.viewmodel.load_history_list()

    def _configure_window(self):
        self.title(config.APP_TITLE)
        self.geometry(config.WINDOW_SIZE)
        ctk.set_appearance_mode(config.THEME_MODE)
        ctk.set_default_color_theme(config.COLOR_THEME)

    def _setup_ui(self):
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(padx=20, pady=20, fill="both", expand=True)

        self.home_tab = HomeTab(
            parent=self.tabview.add("Scraper"), 
            command_callback=self.viewmodel.start_scraping_command
        )
        self.home_tab.pack(fill="both", expand=True)

        self.history_tab = HistoryTab(
            parent=self.tabview.add("Histórico"),
            on_select_callback=self.viewmodel.load_history_details,
            on_delete_callback=self.viewmodel.delete_history_item,
            on_pagination_callback=self.viewmodel.check_pagination_and_scrape,
            on_extract_callback=self.viewmodel.extract_data_command
        )
        self.history_tab.pack(fill="both", expand=True)

        self.results_tab = ResultsTab(
            parent=self.tabview.add("Resultados"),
            on_scrape_callback=self.viewmodel.scrape_specific_search_url
        )
        self.results_tab.pack(fill="both", expand=True)

        self.content_tab = ContentTab(parent=self.tabview.add("Conteúdo do Buscador"))
        self.content_tab.pack(fill="both", expand=True)

        self.log_tab = LogTab(parent=self.tabview.add("Log"))
        self.log_tab.pack(fill="both", expand=True)

    def get_url_input(self):
        return self.home_tab.get_url()

    def update_status(self, message, color_name="white"):
        colors = {
            "red": "#FF5555", 
            "green": "#50FA7B", 
            "yellow": "#F1FA8C", 
            "white": "#F8F8F2"
        }
        
        self.home_tab.set_status(message, colors.get(color_name, "white"))
        self.log_tab.append_log(message)
        
    def toggle_button(self, state):
        self.home_tab.set_button_state(state)

    def display_html_content(self, html_content):
        self.home_tab.display_html(html_content)

    def update_history_list(self, items):
        self.history_tab.update_list(items)

    def display_history_content(self, html):
        self.history_tab.display_content(html)
    
    def display_extracted_results(self, data):
        self.results_tab.display_results(data)

    def switch_to_results_tab(self):
        self.tabview.set("Resultados")
    
    def display_content_in_fourth_tab(self, html):
        self.content_tab.display_html(html)
        self.tabview.set("Conteúdo do Buscador")
        
    def after_thread_safe(self, func):
        self.after(0, func)