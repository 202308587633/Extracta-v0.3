import customtkinter as ctk
from urllib.parse import quote

class HomeTab(ctk.CTkFrame):
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

    def __init__(self, parent, command_callback):
        super().__init__(parent)
        self.command_callback = command_callback
        
        # --- Definições Padrão ---
        self.default_terms = [
            "jurimetria", "inteligência artificial", "análise de discurso", 
            "algoritmo", "direito digital", "tecnologia da informação"
        ]
        self.default_years = [str(y) for y in range(2020, 2026)]
        
        # Armazena histórico para evitar repetição: set de tuplas (termo, ano)
        self.executed_searches = set()
        
        self._setup_ui()

    def _setup_ui(self):
        # Configuração de Grid Principal
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0) 
        self.grid_rowconfigure(1, weight=1) 

        self.center_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.center_frame.grid(row=0, column=0, sticky="ew", padx=40, pady=10)
        self.center_frame.grid_columnconfigure(0, weight=1)
        self.center_frame.grid_columnconfigure(1, weight=0)

        self.label_title = ctk.CTkLabel(
            self.center_frame, 
            text="Extracta - Extrator de Dados Científicos", 
            font=("Roboto", 24, "bold")
        )
        self.label_title.grid(row=0, column=0, columnspan=2, pady=(0, 20))

        # --- TERMOS ---
        self.lbl_terms = ctk.CTkLabel(self.center_frame, text="Termo de Pesquisa:", font=("Roboto", 12))
        self.lbl_terms.grid(row=1, column=0, sticky="w", padx=5, pady=(0, 2))

        self.cmb_terms = ctk.CTkComboBox(
            self.center_frame, 
            values=self.default_terms,
            command=self._on_term_selected, # <--- MUDANÇA: Aciona filtro de anos ao selecionar termo
            width=400
        )
        self.cmb_terms.grid(row=2, column=0, sticky="ew", padx=5, pady=(0, 15))
        self.cmb_terms.set("Selecione um termo...")

        # --- ANOS ---
        self.lbl_year = ctk.CTkLabel(self.center_frame, text="Ano:", font=("Roboto", 12))
        self.lbl_year.grid(row=1, column=1, sticky="w", padx=5, pady=(0, 2))

        self.cmb_year = ctk.CTkComboBox(
            self.center_frame, 
            values=self.default_years,
            command=self._update_url_entry,
            width=100
        )
        self.cmb_year.grid(row=2, column=1, sticky="e", padx=5, pady=(0, 15))
        self.cmb_year.set("Ano")

        # --- URL e Botões ---
        self.label_info = ctk.CTkLabel(
            self.center_frame, text="URL da Pesquisa (BDTD / Catálogo de Teses):",
            font=("Roboto", 14)
        )
        self.label_info.grid(row=3, column=0, columnspan=2, pady=(10, 5), sticky="w", padx=5)

        self.url_entry = ctk.CTkEntry(
            self.center_frame, placeholder_text="Cole a URL aqui ou use os filtros acima...",
            height=40, font=("Roboto", 12)
        )
        self.url_entry.grid(row=4, column=0, columnspan=2, sticky="ew", padx=5, pady=(0, 20))

        self.btn_start = ctk.CTkButton(
            self.center_frame, text="🚀 Iniciar Scraping", 
            command=self.command_callback, height=50,
            font=("Roboto", 16, "bold"), fg_color="#1f538d", hover_color="#14375e"
        )
        self.btn_start.grid(row=5, column=0, columnspan=2, sticky="ew", padx=5)

        self.label_help = ctk.CTkLabel(
            self.center_frame,
            text="O sistema processará a página de resultados e baixará as teses automaticamente.",
            text_color="gray", font=("Roboto", 11)
        )
        self.label_help.grid(row=6, column=0, columnspan=2, pady=10)

        # --- Resultado HTML (Inferior) ---
        self.result_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.result_frame.grid(row=1, column=0, sticky="nsew", padx=40, pady=(0, 20))
        self.result_frame.grid_columnconfigure(0, weight=1)
        self.result_frame.grid_rowconfigure(1, weight=1)

        self.label_preview = ctk.CTkLabel(self.result_frame, text="Pré-visualização do HTML (PLB):", font=("Roboto", 12, "bold"))
        self.label_preview.grid(row=0, column=0, sticky="w", pady=(5, 5))

        self.textbox_result = ctk.CTkTextbox(self.result_frame, font=("Consolas", 11), activate_scrollbars=True)
        self.textbox_result.grid(row=1, column=0, sticky="nsew")
        self.textbox_result.insert("0.0", "O código HTML da página capturada aparecerá aqui...")
        self.textbox_result.configure(state="disabled")

    def update_executed_searches(self, executed_list):
        """Atualiza a lista interna de pesquisas já realizadas (vindas do banco)."""
        self.executed_searches = set()
        for t, y in executed_list:
            if t and y:
                # Normaliza para evitar problemas de case/espaços
                self.executed_searches.add((str(t).lower().strip(), str(y).strip()))
        
        # Atualiza a visualização com base na seleção atual
        current = self.cmb_terms.get()
        if current and current != "Selecione um termo...":
            self._on_term_selected(current)

    def _on_term_selected(self, selected_term):
        """Filtra os anos na combobox, removendo os já pesquisados para o termo escolhido."""
        if not selected_term or selected_term == "Selecione um termo...":
            return

        term_key = selected_term.lower().strip()
        available_years = []

        # Para cada ano padrão, verifica se já foi pesquisado com este termo
        for year in self.default_years:
            if (term_key, year) not in self.executed_searches:
                available_years.append(year)
        
        # Atualiza a ComboBox de Anos
        if available_years:
            self.cmb_year.configure(values=available_years)
            self.cmb_year.set(available_years[0]) # Seleciona o primeiro disponível
        else:
            self.cmb_year.configure(values=["Concluído"])
            self.cmb_year.set("Concluído") # Indica que todos os anos para este termo já foram feitos

        # Atualiza a URL
        self._update_url_entry()

    def _update_url_entry(self, _=None):
        term = self.cmb_terms.get()
        year = self.cmb_year.get()
        
        # Validações para não gerar URL inválida
        if term == "Selecione um termo..." or not term: return
        if year == "Concluído" or not year: return
        
        safe_term = quote(term)
        url = (
            f"https://bdtd.ibict.br/vufind/Search/Results"
            f"?lookfor=%22{safe_term}%22&type=AllFields"
            f"&daterange[]=publishDate&publishDatefrom={year}&publishDateto={year}"
        )
        self.url_entry.delete(0, "end")
        self.url_entry.insert(0, url)
