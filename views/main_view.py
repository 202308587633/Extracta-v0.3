import customtkinter as ctk
import config
from viewmodels.main_viewmodel import MainViewModel
# ... imports das abas ... (mantenha os imports existentes)
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
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.viewmodel = MainViewModel(self)

        self._setup_sidebar()
        self._setup_tabs()
        
        self.after(100, lambda: self.viewmodel.initialize_data())

    # ... _configure_window e _setup_sidebar mantidos iguais ...
    def _configure_window(self):
        self.title(config.APP_TITLE)
        self.geometry(config.WINDOW_SIZE)
        ctk.set_appearance_mode(config.THEME_MODE)
        ctk.set_default_color_theme(config.COLOR_THEME)

    def _setup_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="Extracta v0.4", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

    def _setup_tabs(self):
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=0, column=1, padx=10, pady=(10, 0), sticky="nsew")
        self.tabview.configure(command=self.viewmodel.on_tab_changed)

        self.tabview.add("Início")
        self.tabview.add("Histórico")
        self.tabview.add("Resultados")
        self.tabview.add("Conteúdo PPB")
        self.tabview.add("Conteúdo PPR")
        self.tabview.add("Fontes")
        self.tabview.add("Logs")

        # --- HOME ---
        self.home_tab = HomeTab(
            parent=self.tabview.tab("Início"),
            # Callback aponta para o Sub-VM
            command_callback=self.viewmodel.home_vm.start_scraping
        )
        self.home_tab.pack(fill="both", expand=True)

        # --- RESULTADOS ---
        self.results_tab = ResultsTab(
            parent=self.tabview.tab("Resultados"),
            viewmodel=self.viewmodel, # Passamos o MainVM para acesso aos Helpers de seleção
            # Callbacks apontam para o Sub-VM
            on_scrape_callback=lambda url: self.viewmodel.results_vm.scrape_specific_url(url, 'buscador'),
            on_repo_scrape_callback=lambda url: self.viewmodel.results_vm.scrape_specific_url(url, 'repositorio')
        )
        self.results_tab.pack(fill="both", expand=True)

        # --- HISTÓRICO ---
        self.history_tab = HistoryTab(
            parent=self.tabview.tab("Histórico"),
            on_select_callback=None,
            # Callbacks apontam para o Sub-VM
            on_delete_callback=self.viewmodel.history_vm.delete_item,
            on_pagination_callback=self.viewmodel.history_vm.check_pagination_and_scrape,
            on_extract_callback=self.viewmodel.history_vm.extract_data,
            on_browser_callback=self.viewmodel.history_vm.open_browser,
            on_deep_scrape_callback=self.viewmodel.history_vm.scrape_all_page1,
            on_stop_callback=self.viewmodel.history_vm.stop_process
        )
        self.history_tab.pack(fill="both", expand=True)

        # --- CONTEÚDO ---
        self.content_tab = ContentTab(
            parent=self.tabview.tab("Conteúdo PPB"),
            on_browser_callback=self.viewmodel.open_ppb_browser_from_db
        )
        self.content_tab.pack(fill="both", expand=True)

        self.repo_tab = RepoTab(
            parent=self.tabview.tab("Conteúdo PPR"),
            on_browser_callback=self.viewmodel.open_ppr_in_browser
        )
        self.repo_tab.pack(fill="both", expand=True)
        
        self.sources_tab = SourcesTab(self.tabview.tab("Fontes"))
        self.sources_tab.pack(fill="both", expand=True)

        self.log_tab = LogTab(parent=self.tabview.tab("Logs"))
        self.log_tab.pack(fill="both", expand=True)
        
        self.status_container = ctk.CTkFrame(self, height=30, corner_radius=0)
        self.status_container.grid(row=1, column=1, sticky="ew", padx=10, pady=10)
        self.label_status = ctk.CTkLabel(self.status_container, text="Pronto", font=("Roboto", 12))
        self.label_status.pack(side="left", padx=10)

    # Métodos Helpers da MainView (usados pelos VMs para atualizar UI)
    def filter_home_options(self, existing):
        self.home_tab.update_executed_searches(existing)
        
    def get_url_input(self): return self.home_tab.get_url()
    
    def get_current_selection(self): return self.home_tab.get_search_details()
    
    def set_button_state(self, state): self.home_tab.set_button_state(state)
    
    def update_status(self, message, color="white"):
        colors = {"red": "#FF5555", "green": "#50FA7B", "yellow": "#F1FA8C", "white": "#F8F8F2"}
        self.label_status.configure(text=message, text_color=colors.get(color, "white"))
        self.log_tab.append_log(message)

    def update_source_status(self, root, status):
        self.after(0, lambda: self.sources_tab.update_source_status(root, status))

    def after_thread_safe(self, func):
        self.after(0, func)

    def open_html_from_db_in_browser(self, html):
        import tempfile, webbrowser
        if not html: return
        with tempfile.NamedTemporaryFile('w', delete=False, suffix='.html', encoding='utf-8') as f:
            f.write(html)
            webbrowser.open(f"file://{f.name}")

    def switch_to_content_tab(self): self.tabview.set("Conteúdo PPB")

    def switch_to_results_tab(self): self.tabview.set("Resultados")

    def set_tab_state(self, tab, state):
        try: self.tabview._segmented_button._buttons_dict[tab].configure(state=state)
        except: pass
        
    def _setup_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(2, weight=1) # Empurra o resto para baixo se precisar

        # 1. Logo
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text=config.APP_TITLE, font=config.FONTS["logo"])
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # 2. Painel de Manutenção (Novo)
        self.maintenance_frame = ctk.CTkFrame(self.sidebar_frame, fg_color=config.COLORS["panel_bg"])
        self.maintenance_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        
        lbl_maint = ctk.CTkLabel(self.maintenance_frame, text="🔧 Manutenção", 
                                 font=config.FONTS["small"], text_color="gray")
        lbl_maint.pack(pady=(5, 0))

        # Botão Limpar Banco
        self.btn_clear_db = ctk.CTkButton(
            self.maintenance_frame, 
            text="🗑️ Limpar Banco",
            command=self.viewmodel.maintenance_clear_db,
            fg_color="#c0392b", 
            hover_color="#e74c3c",
            height=25,
            font=config.FONTS["small"]
        )
        self.btn_clear_db.pack(padx=10, pady=10, fill="x")

        # Botão Recarregar (Opcional, útil para debug)
        self.btn_reload = ctk.CTkButton(
            self.maintenance_frame, 
            text="🔄 Recarregar",
            command=self.viewmodel.initialize_data,
            fg_color="gray",
            height=25,
            font=config.FONTS["small"]
        )
        self.btn_reload.pack(padx=10, pady=(0, 10), fill="x")