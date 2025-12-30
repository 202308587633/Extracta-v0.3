import customtkinter as ctk
import webbrowser
from tkinter import ttk
import tkinter as tk

class ResultsTab(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.link_map = {}  # Armazena os links associados a cada linha
        self._setup_ui()

    def _setup_ui(self):
        # Layout principal da aba
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # 1. Label de contagem
        self.label_count = ctk.CTkLabel(self, text="Aguardando dados...", font=("Roboto", 14))
        self.label_count.grid(row=0, column=0, pady=(10, 5), sticky="ew")

        # 2. Container para a Tabela e Scrollbar
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(0, weight=1)

        # --- Configuração de Estilo do Treeview (Dark Theme) ---
        style = ttk.Style()
        style.theme_use("default")
        
        # Cores compatíveis com o tema 'Dark-Blue' do CustomTkinter
        bg_color = "#2b2b2b"
        text_color = "#ffffff"
        selected_bg = "#1f538d"
        header_bg = "#1f1f1f"
        
        style.configure("Treeview",
                        background=bg_color,
                        foreground=text_color,
                        fieldbackground=bg_color,
                        rowheight=30,
                        borderwidth=0,
                        font=("Roboto", 11))
        
        style.map('Treeview', background=[('selected', selected_bg)])
        
        style.configure("Treeview.Heading",
                        background=header_bg,
                        foreground=text_color,
                        relief="flat",
                        padding=(5, 5),
                        font=("Roboto", 12, "bold"))
        
        style.map("Treeview.Heading",
                  background=[('active', '#343638')])

        # --- Criação da Tabela (Treeview) ---
        columns = ("title", "author", "search", "repo")
        self.tree = ttk.Treeview(self.container, columns=columns, show="headings", selectmode="browse")

        # Cabeçalhos com comando de ordenação
        self.tree.heading("title", text="Título da Pesquisa", command=lambda: self._sort_column("title", False))
        self.tree.heading("author", text="Autor", command=lambda: self._sort_column("author", False))
        self.tree.heading("search", text="Link Busca", command=lambda: self._sort_column("search", False))
        self.tree.heading("repo", text="Documento", command=lambda: self._sort_column("repo", False))

        # Configuração das Colunas (Largura e Redimensionamento)
        self.tree.column("title", width=400, minwidth=150, anchor="w")
        self.tree.column("author", width=200, minwidth=100, anchor="w")
        self.tree.column("search", width=100, minwidth=80, anchor="center")
        self.tree.column("repo", width=100, minwidth=80, anchor="center")

        # Scrollbar Vertical
        self.scrollbar = ctk.CTkScrollbar(self.container, command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.scrollbar.set)

        # Posicionamento
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")

        # Bind de duplo clique para abrir links
        self.tree.bind("<Double-1>", self._on_double_click)

    def display_results(self, results):
        """Preenche a tabela com os dados extraídos"""
        # Limpa dados antigos
        self.link_map.clear()
        for item in self.tree.get_children():
            self.tree.delete(item)

        self.label_count.configure(text=f"{len(results)} registros encontrados (Duplo clique para abrir links)")

        for item in results:
            # Define o texto visual para as colunas de link
            search_txt = "Abrir Link" if item.get('search_link') else "-"
            repo_txt = "Abrir PDF" if item.get('repo_link') else "-"

            # Insere na tabela
            values = (item.get('title'), item.get('author'), search_txt, repo_txt)
            item_id = self.tree.insert("", "end", values=values)

            # Armazena as URLs reais associadas a este ID de linha
            self.link_map[item_id] = {
                'search': item.get('search_link'),
                'repo': item.get('repo_link')
            }

    def _sort_column(self, col, reverse):
        """Ordena a tabela ao clicar no cabeçalho"""
        # Obtém lista de (valor, ID) para a coluna
        l = [(self.tree.set(k, col), k) for k in self.tree.get_children('')]
        
        # Ordena a lista
        try:
            l.sort(key=lambda t: t[0].lower(), reverse=reverse)
        except:
            l.sort(reverse=reverse)

        # Reorganiza os itens na visualização
        for index, (val, k) in enumerate(l):
            self.tree.move(k, '', index)

        # Alterna a direção para o próximo clique
        self.tree.heading(col, command=lambda: self._sort_column(col, not reverse))

    def _on_double_click(self, event):
        """Identifica a célula clicada e abre o navegador se for um link"""
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell": return

        # Identifica linha e coluna clicada
        row_id = self.tree.identify_row(event.y)
        col_id = self.tree.identify_column(event.x) # Retorna string '#1', '#2'...

        # Recupera os links salvos para esta linha
        links = self.link_map.get(row_id)
        if not links: return

        # Lógica: Coluna #3 é Busca, Coluna #4 é Repositório
        if col_id == "#3" and links['search']:
            self._open_url(links['search'])
        elif col_id == "#4" and links['repo']:
            self._open_url(links['repo'])

    def _open_url(self, url):
        if url:
            webbrowser.open(url)