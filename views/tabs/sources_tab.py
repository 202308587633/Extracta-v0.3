import customtkinter as ctk

class SourcesTab(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.sources_map = {} # Dicionário para evitar duplicatas: {'url_root': checkbox_widget}
        self._setup_ui()

    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Cabeçalho
        self.label_header = ctk.CTkLabel(
            self, 
            text="Status dos Repositórios (Raízes)", 
            font=("Roboto", 16, "bold")
        )
        self.label_header.grid(row=0, column=0, pady=(10, 5), sticky="w", padx=15)

        # Área de Rolagem para as Fontes
        self.scroll_frame = ctk.CTkScrollableFrame(self, label_text="Domínios Acessados")
        self.scroll_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.scroll_frame.grid_columnconfigure(0, weight=1)

    def update_source_status(self, url_root, is_success):
        """
        Adiciona ou atualiza o status de uma raiz de URL.
        Se já existe, apenas atualiza o estado do checkbox.
        Se não existe, cria um novo.
        """
        if not url_root:
            return

        # Verifica se já existe na lista (evita duplicidade visual)
        if url_root in self.sources_map:
            checkbox = self.sources_map[url_root]
            if is_success:
                checkbox.select()
            else:
                checkbox.deselect()
        else:
            # Cria novo checkbox
            checkbox = ctk.CTkCheckBox(
                self.scroll_frame, 
                text=url_root, 
                font=("Roboto", 12),
                hover=False # Opcional: desativa efeito de hover se desejar
            )
            checkbox.pack(anchor="w", pady=5, padx=5)
            
            # Define o estado inicial
            if is_success:
                checkbox.select()
            else:
                checkbox.deselect()
            
            # Armazena no mapa
            self.sources_map[url_root] = checkbox
            
            # Bloqueia interação do usuário (apenas visualização do sistema)
            # Nota: O state="disabled" no CTK muda a cor para cinza. 
            # Se quiser manter a cor original, remova a linha abaixo, 
            # mas o usuário poderá clicar (o que não afeta a lógica).
            checkbox.configure(state="disabled")