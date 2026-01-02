import customtkinter as ctk
import config
from viewmodels.main_viewmodel import MainViewModel
from views.tabs.home_tab import HomeTab
from views.tabs.log_tab import LogTab
from views.tabs.history_tab import HistoryTab
from views.tabs.results_tab import ResultsTab
from views.tabs.content_tab import ContentTab
from views.tabs.repo_tab import RepoTab
from views.tabs.sources_tab import SourcesTab 

class MainView(ctk.CTk):
    def __init__(self):
        super().__init__()
        self._configure_window()
        
        # Configuração do Layout Principal (Grid)
        self.grid_columnconfigure(1, weight=1) # Coluna 1 (Conteúdo) expande
        self.grid_rowconfigure(0, weight=1)    # Linha 0 (Abas) expande

        # 1. Inicializa o ViewModel (Essencial para conectar a lógica)
        self.viewmodel = MainViewModel(self)

        # 2. Configura os Elementos da Interface
        self._setup_sidebar() # Agora este método existe
        self._setup_tabs()    # Configura as abas com os callbacks corretos
        
        # 3. Inicialização de dados pós-carregamento da interface
        self.after(100, lambda: self.viewmodel.initialize_data())

    def _configure_window(self):
        self.title(config.APP_TITLE)
        self.geometry(config.WINDOW_SIZE)
        ctk.set_appearance_mode(config.THEME_MODE)
        ctk.set_default_color_theme(config.COLOR_THEME)

    def _setup_sidebar(self):
        """Cria a barra lateral esquerda"""
        self.sidebar_frame = ctk.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)
        
        # Logo / Título
        self.logo_label = ctk.CTkLabel(
            self.sidebar_frame, 
            text="Extracta v0.3", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        # Você pode adicionar botões de navegação lateral aqui futuramente se desejar

    def get_url_input(self):
        return self.home_tab.get_url()

    def toggle_button(self, state):
        self.home_tab.set_button_state(state)

    def after_thread_safe(self, func):
        self.after(0, func)

    def update_status(self, message, color_name="white"):
        """Atualiza o status global e o log"""
        colors = {"red": "#FF5555", "green": "#50FA7B", "yellow": "#F1FA8C", "white": "#F8F8F2"}
        if hasattr(self, 'label_status'):
            self.label_status.configure(text=message, text_color=colors.get(color_name, "white"))
        
        # Persiste no log visual também
        if hasattr(self, 'log_tab'):
            self.log_tab.append_log(message)

    def update_source_status(self, url_root, is_success):
        """Atualiza a aba Fontes"""
        if hasattr(self, 'sources_tab'):
            self.after_thread_safe(lambda: self.sources_tab.update_source_status(url_root, is_success))

    def open_html_from_db_in_browser(self, html_content):
        if not html_content:
            self.update_status("Erro: Sem código HTML salvo.", "red")
            return
        
        import tempfile, webbrowser
        with tempfile.NamedTemporaryFile('w', delete=False, suffix='.html', encoding='utf-8') as f:
            f.write(html_content)
            temp_path = f.name
        webbrowser.open(f"file://{temp_path}")

    def set_tab_state(self, tab_name, state):
        try:
            self.tabview._segmented_button._buttons_dict[tab_name].configure(state=state)
        except Exception:
            pass

    def switch_to_results_tab(self):
        self.tabview.set("Resultados")
    
    def switch_to_content_tab(self):
        try:
            self.tabview.set("Conteúdo PPB") 
        except ValueError:
            pass
        
    def get_current_selection(self):
        """Recupera termo e ano da aba Home."""
        if hasattr(self, 'home_tab'):
            return self.home_tab.get_search_details()
        return None, None

    def _setup_tabs(self):
        """Configura as abas e injeta as dependências do ViewModel"""
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=0, column=1, padx=10, pady=(10, 0), sticky="nsew")
        
        # Vincula evento de troca de aba
        self.tabview.configure(command=self.viewmodel.on_tab_changed)

        # Adicionando as abas
        self.tabview.add("Início")
        self.tabview.add("Resultados")
        self.tabview.add("Histórico")
        self.tabview.add("Conteúdo PPB")
        self.tabview.add("Conteúdo PPR")
        self.tabview.add("Fontes")
        self.tabview.add("Logs")

        # --- 1. Aba Início ---
        self.home_tab = HomeTab(
            parent=self.tabview.tab("Início"), 
            command_callback=self.viewmodel.start_scraping_command
        )
        self.home_tab.pack(fill="both", expand=True)

        # --- 2. Aba Resultados ---
        self.results_tab = ResultsTab(
            parent=self.tabview.tab("Resultados"),
            viewmodel=self.viewmodel,
            on_scrape_callback=self.viewmodel.scrape_specific_search_url,
            on_repo_scrape_callback=self.viewmodel.scrape_repository_url
        )
        self.results_tab.pack(fill="both", expand=True)

        # --- 3. Aba Histórico ---
        self.history_tab = HistoryTab(
            parent=self.tabview.tab("Histórico"),
            on_select_callback=None, # Não utilizado na nova tabela
            on_delete_callback=self.viewmodel.delete_history_item,
            on_pagination_callback=self.viewmodel.check_pagination_and_scrape,
            on_extract_callback=self.viewmodel.extract_data_command,
            on_browser_callback=self.viewmodel.open_plb_in_browser,
            on_deep_scrape_callback=self.viewmodel.scrape_all_page1_pagination,
            on_stop_callback=self.viewmodel.stop_scraping_process # <--- NOVO CALLBACK PARA O BOTÃO PARAR
        )
        self.history_tab.pack(fill="both", expand=True)

        # --- 4. Aba Conteúdo PPB ---
        self.content_tab = ContentTab(
            parent=self.tabview.tab("Conteúdo PPB"),
            on_browser_callback=self.viewmodel.open_ppb_browser_from_db
        )
        self.content_tab.pack(fill="both", expand=True)

        # --- 5. Aba Conteúdo PPR ---
        self.repo_tab = RepoTab(
            parent=self.tabview.tab("Conteúdo PPR"),
            on_browser_callback=self.viewmodel.open_ppr_in_browser
        )
        self.repo_tab.pack(fill="both", expand=True)
        
        # --- 6. Aba Fontes ---
        self.sources_tab = SourcesTab(self.tabview.tab("Fontes"))
        self.sources_tab.pack(fill="both", expand=True)

        # --- 7. Aba Logs ---
        self.log_tab = LogTab(parent=self.tabview.tab("Logs"))
        self.log_tab.pack(fill="both", expand=True)
        
        # --- Barra de Status (Rodapé) ---
        self.status_container = ctk.CTkFrame(self, height=30, corner_radius=0)
        self.status_container.grid(row=1, column=1, sticky="ew", padx=10, pady=10)
        
        self.label_status = ctk.CTkLabel(self.status_container, text="Pronto", font=("Roboto", 12))
        self.label_status.pack(side="left", padx=10)

        # Estado Inicial das abas de conteúdo
        self.after(100, lambda: self.set_tab_state("Conteúdo PPB", "disabled"))
        self.after(100, lambda: self.set_tab_state("Conteúdo PPR", "disabled"))

    def toggle_stop_button(self, state):
        """Controla se o botão de parar está habilitado ou não."""
        if hasattr(self, 'history_tab'):
            self.after_thread_safe(lambda: self.history_tab.set_stop_button_state(state))
