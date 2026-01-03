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
        self.history_vm = HistoryViewModel(self.history_repo, view)
        self.results_vm = ResultsViewModel(self.results_repo, self.sys_repo, self.scraper, view)

        # Configura callbacks cruzados (Ex: Home atualiza lista do Histórico)
        self.view.refresh_history_callback = self.history_vm.load_data

    def initialize_data(self):
        """Chamado ao iniciar a aplicação."""
        self.history_vm.load_data()
        self.results_vm.load_results()
        self._load_sources()

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
        
    def batch_extract_univ_data(self):
        # Implementar no ResultsVM se necessário
        pass

    # Status e Logs (Centralizado)
    def update_status(self, message, color="white"):
        self.view.update_status(message, color)