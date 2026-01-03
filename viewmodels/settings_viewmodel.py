import config
from tkinter import messagebox

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
            'years': ", ".join(config.DEFAULT_YEARS) # ADICIONADO
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
                # Avisa o MainViewModel para recarregar tudo via callback se necessário
                if hasattr(self.view, 'refresh_all_callback'):
                    self.view.refresh_all_callback()
                self.view.update_status("Banco de dados resetado com sucesso.", "yellow")
            except Exception as e:
                self.view.update_status(f"Erro ao limpar banco: {e}", "red")