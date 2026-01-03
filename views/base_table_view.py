import customtkinter as ctk
from tkinter import ttk
import config

class BaseTableFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.tree = None
        self.scrollbar = None

    def setup_treeview(self, container, columns_config):
        """
        Configura uma Treeview padrão com estilos e scrollbar.
        
        Args:
            container: O widget pai onde a tabela ficará.
            columns_config: Lista de tuplas (id, titulo, largura, ancora).
                            Ex: [("id", "ID", 50, "center"), ...]
        """
        # --- Configuração de Estilo ---
        style = ttk.Style()
        style.theme_use("default")
        
        # Obtém cores do config ou usa fallback seguro
        colors = getattr(config, 'COLORS', {})
        fonts = getattr(config, 'FONTS', {})
        
        bg_color = colors.get("table_bg", "#2b2b2b")
        text_color = colors.get("text", "#ffffff")
        header_bg = colors.get("table_header", "#1f1f1f")
        selected_bg = colors.get("table_selected", "#1f538d")
        
        font_main = fonts.get("small", ("Roboto", 11))
        font_head = fonts.get("normal", ("Roboto", 12))

        # Estilo das Linhas
        style.configure("Treeview", 
                        background=bg_color, 
                        foreground=text_color, 
                        fieldbackground=bg_color, 
                        rowheight=30, 
                        borderwidth=0, 
                        font=font_main)
        
        style.map('Treeview', background=[('selected', selected_bg)])
        
        # Estilo do Cabeçalho
        style.configure("Treeview.Heading", 
                        background=header_bg, 
                        foreground=text_color, 
                        relief="flat", 
                        padding=(5, 5), 
                        font=font_head)
        
        style.map("Treeview.Heading", background=[('active', '#343638')])

        # --- Criação da Tabela ---
        col_ids = [c[0] for c in columns_config]
        self.tree = ttk.Treeview(container, columns=col_ids, show="headings", selectmode="browse")

        # Configura colunas e cabeçalhos
        for col_id, title, width, anchor in columns_config:
            self.tree.heading(col_id, text=title, command=lambda c=col_id: self._sort_column(c, False))
            self.tree.column(col_id, width=width, anchor=anchor)

        # --- Scrollbar ---
        self.scrollbar = ctk.CTkScrollbar(container, command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.scrollbar.set)
        
        # --- Layout (Grid) ---
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")

    def _sort_column(self, col, reverse):
        """Lógica de ordenação da tabela ao clicar no cabeçalho."""
        l = [(self.tree.set(k, col), k) for k in self.tree.get_children('')]
        try:
            # Tenta ordenar como número
            l.sort(key=lambda t: float(t[0]), reverse=reverse)
        except ValueError:
            # Fallback para string
            l.sort(key=lambda t: t[0].lower(), reverse=reverse)

        for index, (val, k) in enumerate(l):
            self.tree.move(k, '', index)

        # Inverte o comando para a próxima vez (Ascendente <-> Descendente)
        self.tree.heading(col, command=lambda: self._sort_column(col, not reverse))

    def get_selected_values(self):
        """Retorna os valores da linha selecionada ou None."""
        selected = self.tree.selection()
        if not selected:
            return None
        return self.tree.item(selected[0])['values']