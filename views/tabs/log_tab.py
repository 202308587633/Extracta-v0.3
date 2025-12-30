import customtkinter as ctk
from datetime import datetime

class LogTab(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        # Título
        self.label_title = ctk.CTkLabel(self, text="Log de Execução", font=("Roboto", 20, "bold"))
        self.label_title.pack(pady=(20, 10))

        # Caixa de Log
        self.textbox_log = ctk.CTkTextbox(self, width=700, height=350, corner_radius=10)
        self.textbox_log.pack(pady=10, padx=20, fill="both", expand=True)
        
        # Configuração inicial
        self.textbox_log.configure(font=("Consolas", 12))
        self.append_log("Sistema iniciado.")
        
    def append_log(self, message):
        """Adiciona uma mensagem com carimbo de hora e faz auto-scroll"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = f"[{timestamp}] {message}\n"
        
        self.textbox_log.configure(state="normal")  # Destrava para escrever
        self.textbox_log.insert("end", entry)       # Escreve no final
        self.textbox_log.see("end")                 # Rola para a última linha
        self.textbox_log.configure(state="disabled") # Trava novamente