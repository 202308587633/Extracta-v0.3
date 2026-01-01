import customtkinter as ctk

class SourcesTab(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.sources_map = {} 
        self._setup_ui()

    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.label_header = ctk.CTkLabel(
            self, 
            text="Gerenciamento de Fontes (Raízes)", 
            font=("Roboto", 16, "bold")
        )
        self.label_header.grid(row=0, column=0, pady=(10, 5), sticky="w", padx=15)

        self.scroll_frame = ctk.CTkScrollableFrame(self, label_text="Domínios Identificados")
        self.scroll_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.scroll_frame.grid_columnconfigure(0, weight=1)

    def update_source_status(self, url_root, is_active):
        """
        Atualiza visualmente o checkbox.
        is_active: True (marcado/sucesso), False (desmarcado/falha)
        """
        if not url_root: return

        if url_root in self.sources_map:
            checkbox = self.sources_map[url_root]
            if is_active:
                checkbox.select()
            else:
                checkbox.deselect()
        else:
            # Cria novo checkbox se não existir
            checkbox = ctk.CTkCheckBox(
                self.scroll_frame, 
                text=url_root, 
                font=("Roboto", 12),
                command=lambda root=url_root: self._on_manual_toggle(root) # Callback para clique manual
            )
            checkbox.pack(anchor="w", pady=5, padx=5)
            
            if is_active:
                checkbox.select()
            else:
                checkbox.deselect()
            
            self.sources_map[url_root] = checkbox

    def _on_manual_toggle(self, root_url):
        """
        Opcional: Permite que o usuário reative uma fonte manualmente.
        Se o usuário clicar, precisamos atualizar o banco de dados.
        Isso requer acesso ao ViewModel ou DB. 
        Como esta view é 'burra', idealmente passamos um callback no init, 
        mas para manter simples, deixaremos apenas visual por enquanto 
        ou você pode injetar o viewmodel aqui se desejar persistência no clique manual.
        """
        # Para persistência no clique manual, seria necessário:
        # self.viewmodel.db.save_source_status(root_url, status)
        pass