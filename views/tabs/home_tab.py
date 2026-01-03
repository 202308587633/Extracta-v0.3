import customtkinter as ctk
import config
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
        
        # Garante que as listas do config sejam carregadas
        self.executed_searches = set() 
        self.default_terms = config.DEFAULT_SEARCH_TERMS
        self.default_years = config.DEFAULT_YEARS

        self._setup_ui()

    def _setup_ui(self):
        # 1. Configuração do Layout Principal
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1) # Faz a área de texto (linha 2) expandir

        # 2. CRIAÇÃO DO CONTAINER (Correção: Deve vir antes de adicionar widgets nele)
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.grid(row=0, column=0, sticky="ew", padx=20, pady=20)
        
        # 3. Cabeçalho
        lbl_title = ctk.CTkLabel(self.container, text="Nova Pesquisa (BDTD)", font=("Roboto", 16, "bold"))
        lbl_title.pack(anchor="w", pady=(0, 10))

        # 4. Filtros de Pesquisa
        self.filter_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        self.filter_frame.pack(fill="x", pady=5)

        # ComboBox Termos
        ctk.CTkLabel(self.filter_frame, text="Termo:").pack(side="left", padx=(0, 5))
        self.cmb_terms = ctk.CTkComboBox(
            self.filter_frame, 
            values=self.default_terms,
            width=300,
            command=self._on_term_change
        )
        self.cmb_terms.set("Selecione um termo...")
        self.cmb_terms.pack(side="left", padx=5)

        # ComboBox Anos
        ctk.CTkLabel(self.filter_frame, text="Ano:").pack(side="left", padx=(15, 5))
        self.cmb_year = ctk.CTkComboBox(
            self.filter_frame,
            values=self.default_years,
            width=100,
            command=self._update_url_entry
        )
        # Define valor padrão seguro
        default_year = "Ano"
        self.cmb_year.set(default_year)
        self.cmb_year.pack(side="left", padx=5)

        # 5. Entrada de URL
        lbl_url = ctk.CTkLabel(self.container, text="URL Gerada:", font=("Roboto", 12))
        lbl_url.pack(anchor="w", pady=(15, 0))

        self.url_entry = ctk.CTkEntry(self.container, width=600)
        self.url_entry.pack(fill="x", pady=(5, 10))
        
        # Botão Iniciar
        self.btn_start = ctk.CTkButton(
            self.container, 
            text="🚀 Iniciar Mineração", 
            command=self.command_callback,
            height=40,
            font=("Roboto", 14, "bold"),
            fg_color="#009688", 
            hover_color="#00796b"
        )
        self.btn_start.pack(fill="x", pady=10)

        # 6. Área de Resultado (Fica fora do container, direto no self, para expandir)
        self.result_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.result_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 20))
        
        lbl_res = ctk.CTkLabel(self.result_frame, text="Pré-visualização do HTML:", anchor="w")
        lbl_res.pack(fill="x")

        self.textbox_result = ctk.CTkTextbox(self.result_frame, wrap="none")
        self.textbox_result.pack(fill="both", expand=True)
        self.textbox_result.configure(state="disabled")

        # Inicializa a URL com os valores padrão
        self._update_url_entry()

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

    def update_executed_searches(self, existing_list):
        """Recebe lista de (termo, ano) já pesquisados para filtrar as opções."""
        # existing_list vem do banco como [(termo, ano), ...]
        self.executed_searches = set()
        for t, y in existing_list:
            if t and y:
                self.executed_searches.add((t.lower().strip(), str(y).strip()))
        
        # Atualiza a interface para refletir o que já foi feito (se houver termo selecionado)
        if hasattr(self, 'cmb_terms') and self.cmb_terms.get():
            self._on_term_change(self.cmb_terms.get())

    def _on_term_change(self, selected_term):
        """Filtra os anos disponíveis com base no termo selecionado."""
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
        if not hasattr(self, 'cmb_terms') or not hasattr(self, 'cmb_year'):
            return

        term = self.cmb_terms.get()
        year = self.cmb_year.get()
        
        if term == "Selecione um termo..." or not term: return
        if year == "Concluído" or not year: return
        
        # --- MODIFICAÇÃO: Usa o Template do Config ---
        safe_term = quote(term)
        try:
            # Pega o template do config (ou usa um default se falhar)
            template = getattr(config, 'SEARCH_URL_TEMPLATE', "https://bdtd.ibict.br/vufind/Search/Results?lookfor={term}")
            
            # Formata a string injetando os valores
            url = template.format(term=safe_term, year=year)
            
            self.url_entry.delete(0, "end")
            self.url_entry.insert(0, url)
        except Exception as e:
            self.url_entry.delete(0, "end")
            self.url_entry.insert(0, f"Erro ao gerar URL: {e}")

