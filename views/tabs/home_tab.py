import customtkinter as ctk
import config
from urllib.parse import quote


class HomeTab(ctk.CTkFrame):
    def set_status(self, message, color_hex):
        self.label_status.configure(text=message, text_color=color_hex)

    def display_html(self, content):
        self.textbox_result.configure(state="normal")
        self.textbox_result.delete("0.0", "end")
        self.textbox_result.insert("0.0", content)
        self.textbox_result.configure(state="disabled")
        
    def __init__(self, parent, command_callback):
        super().__init__(parent)
        self.command_callback = command_callback
        self._setup_ui()

    def _setup_ui(self):
        # Configuração de Grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1) # Espaço superior
        self.grid_rowconfigure(5, weight=1) # Espaço inferior

        # Container Centralizado
        self.center_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.center_frame.grid(row=1, column=0, sticky="ew", padx=40)
        self.center_frame.grid_columnconfigure(0, weight=1)
        self.center_frame.grid_columnconfigure(1, weight=0) # Coluna para o ano

        # --- Título ---
        self.label_title = ctk.CTkLabel(
            self.center_frame, 
            text="Extracta - Extrator de Dados Científicos", 
            font=("Roboto", 24, "bold")
        )
        self.label_title.grid(row=0, column=0, columnspan=2, pady=(0, 20))

        # --- NOVAS COMBOBOXES (Filtros de Pesquisa) ---
        
        # Label e ComboBox de Termos
        self.lbl_terms = ctk.CTkLabel(self.center_frame, text="Termo de Pesquisa:", font=("Roboto", 12))
        self.lbl_terms.grid(row=1, column=0, sticky="w", padx=5, pady=(0, 2))

        self.terms_values = [
            "jurimetria", 
            "inteligência artificial", 
            "análise de discurso", 
            "algoritmo", 
            "direito digital", 
            "tecnologia da informação"
        ]
        self.cmb_terms = ctk.CTkComboBox(
            self.center_frame, 
            values=self.terms_values,
            command=self._update_url_entry,
            width=400
        )
        self.cmb_terms.grid(row=2, column=0, sticky="ew", padx=5, pady=(0, 15))
        self.cmb_terms.set("Selecione um termo...") # Placeholder

        # Label e ComboBox de Ano
        self.lbl_year = ctk.CTkLabel(self.center_frame, text="Ano:", font=("Roboto", 12))
        self.lbl_year.grid(row=1, column=1, sticky="w", padx=5, pady=(0, 2))

        self.years_values = [str(y) for y in range(2020, 2026)] # 2020 a 2025
        self.cmb_year = ctk.CTkComboBox(
            self.center_frame, 
            values=self.years_values,
            command=self._update_url_entry,
            width=100
        )
        self.cmb_year.grid(row=2, column=1, sticky="e", padx=5, pady=(0, 15))
        self.cmb_year.set("2024") # Padrão

        # --- Campo de URL (Preenchido automaticamente ou manual) ---
        self.label_info = ctk.CTkLabel(
            self.center_frame, 
            text="URL da Pesquisa (BDTD / Catálogo de Teses):",
            font=("Roboto", 14)
        )
        self.label_info.grid(row=3, column=0, columnspan=2, pady=(10, 5), sticky="w", padx=5)

        self.url_entry = ctk.CTkEntry(
            self.center_frame, 
            placeholder_text="Cole a URL aqui ou use os filtros acima...",
            height=40,
            font=("Roboto", 12)
        )
        self.url_entry.grid(row=4, column=0, columnspan=2, sticky="ew", padx=5, pady=(0, 20))

        # --- Botão de Ação ---
        self.btn_start = ctk.CTkButton(
            self.center_frame, 
            text="🚀 Iniciar Scraping", 
            command=self.command_callback,
            height=50,
            font=("Roboto", 16, "bold"),
            fg_color="#1f538d",
            hover_color="#14375e"
        )
        self.btn_start.grid(row=5, column=0, columnspan=2, sticky="ew", padx=5)

        # Instruções
        self.label_help = ctk.CTkLabel(
            self.center_frame,
            text="O sistema processará a página de resultados e baixará as teses automaticamente.",
            text_color="gray",
            font=("Roboto", 11)
        )
        self.label_help.grid(row=6, column=0, columnspan=2, pady=10)

    def _update_url_entry(self, _=None):
        """Gera a URL do BDTD baseada nas seleções e preenche o campo."""
        term = self.cmb_terms.get()
        year = self.cmb_year.get()

        # Validação simples para não gerar link incompleto
        if term == "Selecione um termo..." or not term:
            return

        # Codifica o termo para URL (ex: "inteligência artificial" -> "intelig%C3%AAncia+artificial")
        # O BDTD usa "+" para espaços na query string geralmente, mas quote funciona bem.
        safe_term = quote(term) 

        # Formato de URL de busca simples do BDTD (VuFind)
        # lookfor: termo pesquisado
        # type: AllFields (Todos os campos)
        # publishDatefrom / publishDateto: Filtro de ano
        url = (
            f"https://bdtd.ibict.br/vufind/Search/Results"
            f"?lookfor=%22{safe_term}%22"
            f"&type=AllFields"
            f"&daterange[]=publishDate"
            f"&publishDatefrom={year}"
            f"&publishDateto={year}"
        )

        # Atualiza o campo de texto
        self.url_entry.delete(0, "end")
        self.url_entry.insert(0, url)

    def get_url(self):
        return self.url_entry.get().strip()

    def set_button_state(self, state):
        """Habilita/Desabilita o botão (True/False ou 'normal'/'disabled')"""
        state_str = "normal" if state is True else "disabled" if state is False else state
        self.btn_start.configure(state=state_str)

