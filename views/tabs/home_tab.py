import customtkinter as ctk
import config

class HomeTab(ctk.CTkFrame):
    def __init__(self, parent, command_callback):
        super().__init__(parent)
        self.command_callback = command_callback # Referência para chamar o ViewModel
        self._setup_ui()

    def _setup_ui(self):
        # Título
        self.label_title = ctk.CTkLabel(self, text="Web Scraper", font=("Roboto", 24))
        self.label_title.pack(pady=20)

        # Input
        self.entry_url = ctk.CTkEntry(self, placeholder_text="Digite a URL...", width=500)
        self.entry_url.pack(pady=10)

        # Botão
        self.btn_run = ctk.CTkButton(self, text="Executar Scraping", command=self.command_callback)
        self.btn_run.pack(pady=10)

        # Status
        self.label_status = ctk.CTkLabel(self, text="")
        self.label_status.pack(pady=10)

        # Resultado
        self.textbox_result = ctk.CTkTextbox(self, width=700, height=300, corner_radius=10)
        self.textbox_result.pack(pady=10, fill="both", expand=True)
        self.textbox_result.configure(state="disabled", font=("Consolas", 12))

    # --- Métodos de Acesso (API da View) ---
    def get_url(self):
        return self.entry_url.get().strip()

    def set_status(self, message, color_hex):
        self.label_status.configure(text=message, text_color=color_hex)

    def set_button_state(self, is_enabled):
        state = "normal" if is_enabled else "disabled"
        self.btn_run.configure(state=state)

    def display_html(self, content):
        self.textbox_result.configure(state="normal")
        self.textbox_result.delete("0.0", "end")
        self.textbox_result.insert("0.0", content)
        self.textbox_result.configure(state="disabled")