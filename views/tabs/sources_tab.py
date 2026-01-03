import customtkinter as ctk

class SourcesTab(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.sources_map = {} 
        self._setup_ui()

    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        # Ajustei para row=2 expandir, pois o filtro ocupará a row=1
        self.grid_rowconfigure(2, weight=1)

        # 1. Cabeçalho
        self.label_header = ctk.CTkLabel(
            self, 
            text="Gerenciamento de Fontes (Raízes)", 
            font=("Roboto", 16, "bold")
        )
        self.label_header.grid(row=0, column=0, pady=(10, 5), sticky="w", padx=15)

        # 2. Campo de Filtro (NOVO)
        self.filter_entry = ctk.CTkEntry(
            self, 
            placeholder_text="🔍 Filtrar domínios..."
        )
        self.filter_entry.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
        # Liga o evento de digitação à função de filtro
        self.filter_entry.bind("<KeyRelease>", self._apply_filters)

        # 3. Lista Rolável
        self.scroll_frame = ctk.CTkScrollableFrame(self, label_text="Domínios Identificados")
        self.scroll_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)
        self.scroll_frame.grid_columnconfigure(0, weight=1)

    def _apply_filters(self, event=None):
        """
        Oculta ou exibe os checkboxes com base no texto digitado.
        """
        filter_text = self.filter_entry.get().lower().strip()

        for root, checkbox in self.sources_map.items():
            if filter_text in root.lower():
                # Se der match, exibe novamente
                checkbox.pack(anchor="w", pady=5, padx=5)
            else:
                # Se não der match, remove da visualização (mas mantém na memória)
                checkbox.pack_forget()

    def update_source_status(self, url_root, is_active):
        """
        Atualiza visualmente o checkbox ou cria um novo se não existir.
        """
        if not url_root: return

        # Verifica se já existe ou cria novo
        if url_root in self.sources_map:
            checkbox = self.sources_map[url_root]
        else:
            checkbox = ctk.CTkCheckBox(
                self.scroll_frame, 
                text=url_root, 
                font=("Roboto", 12),
                command=lambda root=url_root: self._on_manual_toggle(root)
            )
            self.sources_map[url_root] = checkbox

        # Atualiza o estado (Checked/Unchecked)
        if is_active:
            checkbox.select()
        else:
            checkbox.deselect()

        # Lógica de exibição: Só mostra o checkbox se ele passar no filtro atual
        # Isso impede que uma nova fonte apareça se o usuário estiver filtrando por outra coisa
        current_filter = self.filter_entry.get().lower().strip()
        if current_filter in url_root.lower():
            checkbox.pack(anchor="w", pady=5, padx=5)
        else:
            checkbox.pack_forget()

    def _on_manual_toggle(self, root_url):
        # Callback reservado para futura implementação de persistência manual
        pass