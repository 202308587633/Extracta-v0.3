import customtkinter as ctk
from urllib.parse import quote

class HomeTab(ctk.CTkFrame):
    def __init__(self, parent, command_callback):
        super().__init__(parent)
        self.command_callback = command_callback
        self._setup_ui()

    def _setup_ui(self):
        # Configuração de Grid Principal
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0) # Título/Inputs (Tamanho fixo)
        self.grid_rowconfigure(1, weight=1) # Área de Texto (Expansível)

        # --- Container Superior (Inputs e Controles) ---
        self.top_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.top_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=10)
        self.top_frame.grid_columnconfigure(0, weight=1)
        self.top_frame.grid_columnconfigure(1, weight=0)

        # Título
        self.label_title = ctk.CTkLabel(
            self.top_frame, 
            text="Extracta - Extrator de Dados Científicos", 
            font=("Roboto", 24, "bold")
        )
        self.label_title.grid(row=0, column=0, columnspan=2, pady=(0, 15))

        # --- Filtros (Comboboxes) ---
        self.filter_frame = ctk.CTkFrame(self.top_frame, fg_color="transparent")
        self.filter_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        
        # Label e ComboBox de Termos
        self.lbl_terms = ctk.CTkLabel(self.filter_frame, text="Termo de Pesquisa:", font=("Roboto", 12))
        self.lbl_terms.pack(side="left", padx=(0, 5))

        self.terms_values = [
            "jurimetria", "inteligência artificial", "análise de discurso", 
            "algoritmo", "direito digital", "tecnologia da informação"
        ]
        self.cmb_terms = ctk.CTkComboBox(
            self.filter_frame, 
            values=self.terms_values,
            command=self._update_url_entry,
            width=300
        )
        self.cmb_terms.pack(side="left", padx=(0, 20))
        self.cmb_terms.set("Selecione um termo...")

        # Label e ComboBox de Ano
        self.lbl_year = ctk.CTkLabel(self.filter_frame, text="Ano:", font=("Roboto", 12))
        self.lbl_year.pack(side="left", padx=(0, 5))

        self.years_values = [str(y) for y in range(2020, 2026)]
        self.cmb_year = ctk.CTkComboBox(
            self.filter_frame, 
            values=self.years_values,
            command=self._update_url_entry,
            width=100
        )
        self.cmb_year.pack(side="left")
        self.cmb_year.set("2024")

        # --- URL e Botão ---
        self.label_info = ctk.CTkLabel(
            self.top_frame, 
            text="URL da Pesquisa (BDTD / Catálogo de Teses):",
            font=("Roboto", 14)
        )
        self.label_info.grid(row=2, column=0, columnspan=2, sticky="w", pady=(5, 2))

        self.url_entry = ctk.CTkEntry(
            self.top_frame, 
            placeholder_text="Cole a URL aqui ou use os filtros acima...",
            height=40,
            font=("Roboto", 12)
        )
        self.url_entry.grid(row=3, column=0, sticky="ew", padx=(0, 10), pady=(0, 10))

        self.btn_start = ctk.CTkButton(
            self.top_frame, 
            text="🚀 Iniciar Scraping", 
            command=self.command_callback,
            height=40,
            width=150,
            font=("Roboto", 14, "bold"),
            fg_color="#1f538d",
            hover_color="#14375e"
        )
        self.btn_start.grid(row=3, column=1, sticky="e", pady=(0, 10))

        # --- Container Inferior (Resultado HTML) ---
        # RESTAURAÇÃO: Aqui recriamos o container e a caixa de texto
        self.result_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.result_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self.result_frame.grid_columnconfigure(0, weight=1)
        self.result_frame.grid_rowconfigure(1, weight=1)

        self.label_preview = ctk.CTkLabel(self.result_frame, text="Pré-visualização do HTML (PLB):", font=("Roboto", 12, "bold"))
        self.label_preview.grid(row=0, column=0, sticky="w", pady=(5, 5))

        self.textbox_result = ctk.CTkTextbox(
            self.result_frame, 
            font=("Consolas", 11),
            activate_scrollbars=True
        )
        self.textbox_result.grid(row=1, column=0, sticky="nsew")
        self.textbox_result.insert("0.0", "O código HTML da página capturada aparecerá aqui...")
        self.textbox_result.configure(state="disabled")

    # --- Métodos de Lógica ---

    def _update_url_entry(self, _=None):
        term = self.cmb_terms.get()
        year = self.cmb_year.get()
        if term == "Selecione um termo..." or not term: return
        
        safe_term = quote(term)
        url = (
            f"https://bdtd.ibict.br/vufind/Search/Results"
            f"?lookfor=%22{safe_term}%22&type=AllFields"
            f"&daterange[]=publishDate&publishDatefrom={year}&publishDateto={year}"
        )
        self.url_entry.delete(0, "end")
        self.url_entry.insert(0, url)

    def get_url(self):
        return self.url_entry.get().strip()

    def get_search_details(self):
        """Retorna o termo e ano selecionados para uso no histórico."""
        term = self.cmb_terms.get()
        year = self.cmb_year.get()
        if term == "Selecione um termo...": term = ""
        return term, year

    def set_button_state(self, state):
        state_str = "normal" if state is True else "disabled" if state is False else state
        self.btn_start.configure(state=state_str)

    def display_html(self, html_content):
        """Exibe o conteúdo HTML na caixa de texto."""
        self.textbox_result.configure(state="normal")
        self.textbox_result.delete("0.0", "end")
        if html_content:
            # Limita o tamanho para não travar a interface se for gigante
            self.textbox_result.insert("0.0", html_content[:50000]) 
        else:
            self.textbox_result.insert("0.0", "Nenhum conteúdo capturado.")
        self.textbox_result.configure(state="disabled")