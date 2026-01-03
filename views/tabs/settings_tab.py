import customtkinter as ctk
import config

class SettingsTab(ctk.CTkFrame):
    def __init__(self, parent, viewmodel):
        super().__init__(parent)
        self.viewmodel = viewmodel
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        
        # 1. Título
        ctk.CTkLabel(self, text="Configurações do Sistema", font=config.FONTS["header"]).pack(pady=20)

        # 2. Criação do Frame de Formulário (ESSENCIAL: Deve vir antes dos campos)
        self.form_frame = ctk.CTkFrame(self)
        self.form_frame.pack(fill="x", padx=20, pady=10)

        # --- Campos do Formulário ---

        # Timeout
        self._create_field("Timeout (segundos):", "ent_timeout")
        
        # Delay
        self._create_field("Intervalo entre Requisições (s):", "ent_delay")

        # User Agent
        ctk.CTkLabel(self.form_frame, text="User Agent:", font=config.FONTS["normal"]).pack(anchor="w", padx=10, pady=(10, 0))
        self.ent_user_agent = ctk.CTkEntry(self.form_frame, width=400)
        self.ent_user_agent.pack(fill="x", padx=10, pady=(0, 10))

        # Theme
        ctk.CTkLabel(self.form_frame, text="Tema (Reinício necessário):", font=config.FONTS["normal"]).pack(anchor="w", padx=10, pady=(10, 0))
        self.cmb_theme = ctk.CTkComboBox(self.form_frame, values=["Dark", "Light", "System"])
        self.cmb_theme.pack(fill="x", padx=10, pady=(0, 10))

        # Termos Padrão
        ctk.CTkLabel(self.form_frame, text="Termos Padrão (separados por vírgula):", font=config.FONTS["normal"]).pack(anchor="w", padx=10, pady=(10, 0))
        self.txt_terms = ctk.CTkTextbox(self.form_frame, height=80)
        self.txt_terms.pack(fill="x", padx=10, pady=(0, 10))

        # Anos Padrão (Novo Campo)
        ctk.CTkLabel(self.form_frame, text="Anos Disponíveis (separados por vírgula):", font=config.FONTS["normal"]).pack(anchor="w", padx=10, pady=(5, 0))
        self.ent_years = ctk.CTkEntry(self.form_frame)
        self.ent_years.pack(fill="x", padx=10, pady=(0, 10))

        # Botão Salvar
        self.btn_save = ctk.CTkButton(self, text="💾 Salvar Configurações", command=self._save, fg_color="#27ae60", hover_color="#219150")
        self.btn_save.pack(pady=20)

        # --- Área de Manutenção ---
        ctk.CTkLabel(self, text="Zona de Perigo / Manutenção", font=config.FONTS["header"], text_color="#FF5555").pack(pady=(20, 10))
        
        self.maint_frame = ctk.CTkFrame(self, fg_color="#4a1818") # Fundo avermelhado
        self.maint_frame.pack(fill="x", padx=20, pady=10)

        self.btn_clear = ctk.CTkButton(
            self.maint_frame, text="🗑️ Limpar Banco de Dados (Reset Total)", 
            command=self.viewmodel.maintenance_clear_db,
            fg_color="#c0392b", hover_color="#e74c3c"
        )
        self.btn_clear.pack(pady=20)

    def _create_field(self, label, attr_name):
        ctk.CTkLabel(self.form_frame, text=label, font=config.FONTS["normal"]).pack(anchor="w", padx=10, pady=(5, 0))
        entry = ctk.CTkEntry(self.form_frame)
        entry.pack(fill="x", padx=10, pady=(0, 10))
        setattr(self, attr_name, entry)

    def _load_data(self):
        """Carrega os dados do ViewModel para os campos."""
        data = self.viewmodel.load_current_settings()
        
        # Preenche campos simples
        self.ent_timeout.insert(0, str(data.get('timeout', '30')))
        self.ent_delay.insert(0, str(data.get('delay', '1.5')))
        self.ent_user_agent.insert(0, data.get('user_agent', ''))
        self.cmb_theme.set(data.get('theme', 'Dark'))
        
        # Preenche Textbox de Termos
        self.txt_terms.delete("0.0", "end")
        self.txt_terms.insert("0.0", data.get('terms', ''))
        
        # Preenche Entry de Anos
        self.ent_years.delete(0, "end")
        self.ent_years.insert(0, data.get('years', ''))

    def _save(self):
        """Captura os dados e envia para o ViewModel salvar."""
        new_data = {
            'timeout': self.ent_timeout.get(),
            'delay': self.ent_delay.get(),
            'user_agent': self.ent_user_agent.get(),
            'theme': self.cmb_theme.get(),
            'terms': self.txt_terms.get("0.0", "end").strip(),
            'years': self.ent_years.get().strip()
        }
        self.viewmodel.save_settings(new_data)