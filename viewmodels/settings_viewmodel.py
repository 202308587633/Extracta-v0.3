import config
from tkinter import messagebox
from models.repositories.system_repository import SystemRepository

class SettingsViewModel:
    def __init__(self, db_manager, view):
        self.db_manager = db_manager
        self.view = view

    def load_current_settings(self):
        """Retorna um dict com os valores atuais do config."""
        return {
            'timeout': config.REQUEST_TIMEOUT,
            'user_agent': config.USER_AGENT,
            'delay': config.DELAY_BETWEEN_REQUESTS,
            'theme': config.THEME_MODE,
            'terms': ", ".join(config.DEFAULT_SEARCH_TERMS),
            'years': ", ".join(config.DEFAULT_YEARS) 
        }
        
    def save_settings(self, new_data):
        """Salva configurações e aplica."""
        if config.save_settings(new_data):
            self.view.update_status("Configurações salvas! Reinicie para aplicar algumas alterações.", "green")
        else:
            self.view.update_status("Erro ao salvar configurações.", "red")

    def maintenance_clear_db(self):
        """Ação de limpeza do banco."""
        if messagebox.askyesno("⚠️ Perigo", "Isso apagará TODO o histórico e resultados capturados.\nTem certeza absoluta?"):
            try:
                self.db_manager.clear_all_tables()
                if hasattr(self.view, 'refresh_all_callback'):
                    self.view.refresh_all_callback()
                self.view.update_status("Banco de dados resetado com sucesso.", "yellow")
            except Exception as e:
                self.view.update_status(f"Erro ao limpar banco: {e}", "red")

    def reset_blocked_sources(self):
        """Reseta apenas as fontes marcadas como bloqueadas (erro 403/falha)."""
        if messagebox.askyesno("Confirmar", "Deseja desbloquear todas as fontes marcadas como inativas?"):
            try:
                # Instancia o repositório usando o gerenciador de banco existente
                sys_repo = SystemRepository(self.db_manager)
                if sys_repo.reset_blocked_sources():
                    self.view.update_status("Fontes desbloqueadas com sucesso!", "green")
                else:
                    self.view.update_status("Erro ao desbloquear fontes.", "red")
            except Exception as e:
                self.view.update_status(f"Erro: {e}", "red")