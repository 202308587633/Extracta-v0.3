from models.db.manager import DatabaseManager
from models.repositories.history_repository import HistoryRepository
from models.repositories.results_repository import ResultsRepository
from models.repositories.system_repository import SystemRepository
from models.scraper import ScraperModel

from viewmodels.home_viewmodel import HomeViewModel
from viewmodels.history_viewmodel import HistoryViewModel
from viewmodels.results_viewmodel import ResultsViewModel

class MainViewModel:
    def __init__(self, view):
        self.view = view
        
        # 1. Infraestrutura
        self.db_manager = DatabaseManager()
        self.scraper = ScraperModel()

        # 2. Repositórios
        self.history_repo = HistoryRepository(self.db_manager)
        self.results_repo = ResultsRepository(self.db_manager)
        self.sys_repo = SystemRepository(self.db_manager)

        # 3. Sub-ViewModels (Filhos)
        self.home_vm = HomeViewModel(self.history_repo, self.sys_repo, self.scraper, view)
        
        # results_repo passado para history_vm para salvar extrações da PLB
        self.history_vm = HistoryViewModel(self.history_repo, self.results_repo, self.sys_repo, self.scraper, view)
        
        self.results_vm = ResultsViewModel(self.results_repo, self.sys_repo, self.scraper, view)

        # Configura callbacks cruzados
        self.view.refresh_history_callback = self.history_vm.load_data
        self.view.refresh_results_callback = self.results_vm.load_results

    def initialize_data(self):
        """Chamado ao iniciar a aplicação."""
        self.history_vm.load_data()
        self.results_vm.load_results()
        self._load_sources()
        
        # Carrega filtros da Home
        existing = self.history_repo.get_existing_searches()
        if hasattr(self.view, 'filter_home_options'):
            self.view.filter_home_options(existing)

    def _load_sources(self):
        sources = self.sys_repo.get_sources()
        for root, status in sources.items():
            self.view.update_source_status(root, status)

    # --- Delegators (Métodos que a View chama e repassam para os filhos) ---
    
    # Home Actions
    def start_scraping_command(self):
        self.home_vm.start_scraping()

    # History Actions
    def delete_history_item(self, item_id):
        self.history_vm.delete_item(item_id)

    # Results Actions
    def scrape_pending_pprs(self):
        self.results_vm.scrape_pending_pprs()
        
    # --- MÉTODO QUE FALTAVA ---
    def batch_extract_univ_data(self):
        self.results_vm.batch_extract_univ_data()

    def extract_univ_data(self):
        """Chamado pelo menu de contexto 'Obter Dados da Universidade'."""
        if hasattr(self, 'selected_research') and self.selected_research:
            self.results_vm.extract_single_data(
                self.selected_research['title'], 
                self.selected_research['author']
            )
        else:
            self.update_status("Nenhuma pesquisa selecionada.", "yellow")

    # Helpers de Navegação e Visualização
    def open_ppb_browser_from_db(self, title=None, author=None):
        if hasattr(self, 'selected_research'):
            t = title or self.selected_research.get('title')
            a = author or self.selected_research.get('author')
            html = self.results_repo.get_extracted_html(t, a, 'ppb')
            self.view.open_html_from_db_in_browser(html)

    def open_ppr_in_browser(self):
        if hasattr(self, 'selected_research'):
            t = self.selected_research.get('title')
            a = self.selected_research.get('author')
            html = self.results_repo.get_extracted_html(t, a, 'ppr')
            self.view.open_html_from_db_in_browser(html)

    def handle_result_selection(self, title, author):
        self.selected_research = {'title': title, 'author': author}
        
        # Verifica se tem HTML salvo para habilitar as abas
        h1 = self.results_repo.get_extracted_html(title, author, 'ppb')
        h2 = self.results_repo.get_extracted_html(title, author, 'ppr')
        
        self.view.set_tab_state("Conteúdo PPB", "normal" if h1 else "disabled")
        self.view.set_tab_state("Conteúdo PPR", "normal" if h2 else "disabled")
        
        # Atualiza conteúdo se a aba estiver visível
        if hasattr(self.view, 'tabview'):
            current = self.view.tabview.get()
            if current == "Conteúdo PPB" and h1:
                self.view.content_tab.display_html(h1)
            elif current == "Conteúdo PPR" and h2:
                self.view.repo_tab.display_html(h2)

    def on_tab_changed(self):
        if hasattr(self, 'selected_research') and self.selected_research:
            self.handle_result_selection(self.selected_research['title'], self.selected_research['author'])

    def update_status(self, message, color="white"):
        self.view.update_status(message, color)