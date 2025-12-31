import customtkinter as ctk
import config
from viewmodels.main_viewmodel import MainViewModel
from views.tabs.home_tab import HomeTab
from views.tabs.log_tab import LogTab
from views.tabs.history_tab import HistoryTab
from views.tabs.results_tab import ResultsTab
from views.tabs.content_tab import ContentTab
from views.tabs.repo_tab import RepoTab

class MainView(ctk.CTk):
    def _configure_window(self):
        self.title(config.APP_TITLE)
        self.geometry(config.WINDOW_SIZE)
        ctk.set_appearance_mode(config.THEME_MODE)
        ctk.set_default_color_theme(config.COLOR_THEME)

    def get_url_input(self):
        return self.home_tab.get_url()

    def toggle_button(self, state):
        self.home_tab.set_button_state(state)

    def update_history_list(self, items):
        self.history_tab.update_list(items)

    def display_extracted_results(self, data):
        self.results_tab.display_results(data)

    def switch_to_results_tab(self):
        self.tabview.set("Resultados")
    
    def after_thread_safe(self, func):
        self.after(0, func)

    def update_status(self, message, color_name="white"):
        """Atualiza o status global visível em todas as abas no rodapé"""
        colors = {"red": "#FF5555", "green": "#50FA7B", "yellow": "#F1FA8C", "white": "#F8F8F2"}
        # Atualiza o label fixo no rodapé criado em _setup_ui
        self.label_status.configure(text=message, text_color=colors.get(color_name, "white"))
        # Mantém o registro histórico na aba de Logs
        self.log_tab.append_log(message)

    def _setup_ui(self):
        """Configura a interface principal uma única vez"""
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(padx=20, pady=20, fill="both", expand=True)

        # 1. Aba Principal (Scraper)
        self.home_tab = HomeTab(
            parent=self.tabview.add("Scraper"), 
            command_callback=self.viewmodel.start_scraping_command
        )
        self.home_tab.pack(fill="both", expand=True)

        # 2. Aba de Histórico
        self.history_tab = HistoryTab(
            parent=self.tabview.add("Histórico"),
            on_select_callback=self.viewmodel.load_history_details,
            on_delete_callback=self.viewmodel.delete_history_item,
            on_pagination_callback=self.viewmodel.check_pagination_and_scrape,
            on_extract_callback=self.viewmodel.extract_data_command,
            on_browser_callback=self.viewmodel.open_plb_in_browser 
        )
        self.history_tab.pack(fill="both", expand=True)

        # 3. Aba de Resultados (Tabela)
        self.results_tab = ResultsTab(
            parent=self.tabview.add("Resultados"),
            viewmodel=self.viewmodel,  # Passa o viewmodel aqui
            on_scrape_callback=self.viewmodel.scrape_specific_search_url,
            on_repo_scrape_callback=self.viewmodel.scrape_repository_url
        )
        self.results_tab.pack(fill="both", expand=True)

        # 4. Aba de Conteúdo do Buscador
        self.content_tab = ContentTab(
            parent=self.tabview.add("Conteúdo PPB"),
            on_browser_callback=self.viewmodel.open_ppb_browser_from_db
        )
        self.content_tab.pack(fill="both", expand=True)

        # 5. Aba de Conteúdo do Repositório
        self.repo_tab = RepoTab(
            parent=self.tabview.add("Conteúdo PPR"),
            on_browser_callback=self.viewmodel.open_repo_in_browser 
        )
        self.repo_tab.pack(fill="both", expand=True)

        # 6. Aba de Logs do Sistema
        self.log_tab = LogTab(
            parent=self.tabview.add("Log")
        )
        self.log_tab.pack(fill="both", expand=True)
        
        # Container de Status Fixo no Rodapé (Garante visibilidade global)
        self.status_container = ctk.CTkFrame(self, height=30, corner_radius=0)
        self.status_container.pack(side="bottom", fill="x", padx=20, pady=(0, 10))
        
        self.label_status = ctk.CTkLabel(self.status_container, text="Pronto", font=("Roboto", 12))
        self.label_status.pack(side="left", padx=10)

        # Configura o carregamento sob demanda ao trocar de aba
        self.tabview.configure(command=self.viewmodel.on_tab_changed)

        # Estado inicial: Desabilita as abas de conteúdo no menu
        self.after(100, lambda: self.set_tab_state("Conteúdo Buscador", "disabled"))
        self.after(100, lambda: self.set_tab_state("Conteúdo Repositório", "disabled"))

    def open_html_from_db_in_browser(self, html_content):
        """Abre o código HTML passado (vindo do banco) no navegador"""
        if not html_content:
            self.update_status("Erro: Sem código HTML salvo para esta pesquisa.", "red")
            return
        
        import tempfile, webbrowser
        with tempfile.NamedTemporaryFile('w', delete=False, suffix='.html', encoding='utf-8') as f:
            f.write(html_content)
            temp_path = f.name
        webbrowser.open(f"file://{temp_path}")

    def get_current_tab(self):
        """Retorna o nome da aba selecionada atualmente"""
        return self.tabview.get()
    
    def __init__(self):
        super().__init__()
        self._configure_window()
        self.viewmodel = MainViewModel(self)
        self._setup_ui()
        
        # INICIALIZAÇÃO DE DADOS
        self.viewmodel.initialize_data()

        # VINCULAÇÃO DA MUDANÇA DE ABA (O passo que faltava)
        # Isso faz com que toda vez que o usuário trocar de aba, 
        # o método on_tab_changed do ViewModel seja disparado.
        self.tabview.configure(command=self.viewmodel.on_tab_changed)
        
    def set_tab_state(self, tab_name, state):
        """
        Habilita ou desabilita apenas a aba específica no menu superior.
        """
        try:
            # Acessamos o dicionário de botões interno do componente segmented_button
            # Isso garante que APENAS o botão da aba mencionada mude de estado
            self.tabview._segmented_button._buttons_dict[tab_name].configure(state=state)
        except KeyError:
            print(f"Erro: Aba '{tab_name}' não encontrada.")
        except Exception as e:
            print(f"Erro ao mudar estado da aba: {e}")
    
    def switch_to_content_tab(self):
        """Muda o foco visual para a aba Conteúdo Buscador"""
        self.tabview.set("Conteúdo Buscador")
    