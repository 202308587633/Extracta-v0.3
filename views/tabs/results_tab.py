import customtkinter as ctk
import webbrowser
from tkinter import ttk
import tkinter as tk

class ResultsTab(ctk.CTkFrame):
    def __init__(self, parent, on_scrape_callback, on_repo_scrape_callback):
        super().__init__(parent)
        self.on_scrape_callback = on_scrape_callback
        self.on_repo_scrape_callback = on_repo_scrape_callback
        self.link_map = {}
        self._setup_ui()
        self._setup_context_menu()

    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.label_count = ctk.CTkLabel(self, text="Aguardando dados...", font=("Roboto", 14))
        self.label_count.grid(row=0, column=0, pady=(10, 5), sticky="ew")

        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(0, weight=1)

        style = ttk.Style()
        style.theme_use("default")
        
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

        columns = ("title", "author", "search", "repo")
        self.tree = ttk.Treeview(self.container, columns=columns, show="headings", selectmode="browse")

        self.tree.heading("title", text="Título da Pesquisa", command=lambda: self._sort_column("title", False))
        self.tree.heading("author", text="Autor", command=lambda: self._sort_column("author", False))
        self.tree.heading("search", text="Link Busca", command=lambda: self._sort_column("search", False))
        self.tree.heading("repo", text="Documento", command=lambda: self._sort_column("repo", False))

        self.tree.column("title", width=400, minwidth=150, anchor="w")
        self.tree.column("author", width=200, minwidth=100, anchor="w")
        self.tree.column("search", width=100, minwidth=80, anchor="center")
        self.tree.column("repo", width=100, minwidth=80, anchor="center")

        self.scrollbar = ctk.CTkScrollbar(self.container, command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.scrollbar.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")

        self.tree.bind("<Double-1>", self._on_double_click)
        self.tree.bind("<Button-3>", self._show_context_menu)

    def _setup_context_menu(self):
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="🕷️ Scrap do Link de Busca", command=self._scrape_selected_row)
        self.context_menu.add_command(label="📂 Scrap do Link do Repositório", command=self._scrape_repo_row)

    def _show_context_menu(self, event):
        row_id = self.tree.identify_row(event.y)
        if row_id:
            self.tree.selection_set(row_id)
            try:
                self.context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                self.context_menu.grab_release()

    def _scrape_selected_row(self):
        selected = self.tree.selection()
        if not selected: return
        
        item_id = selected[0]
        links = self.link_map.get(item_id)
        
        if links and links.get('search'):
            self.on_scrape_callback(links['search'])
        else:
            print("Nenhum link de busca disponível para esta linha.")

    def display_results(self, results):
        self.link_map.clear()
        for item in self.tree.get_children():
            self.tree.delete(item)

        self.label_count.configure(text=f"{len(results)} registros encontrados (Duplo clique para abrir links)")

        for item in results:
            search_txt = "Abrir Link" if item.get('search_link') else "-"
            repo_txt = "Abrir PDF" if item.get('repo_link') else "-"

            values = (item.get('title'), item.get('author'), search_txt, repo_txt)
            item_id = self.tree.insert("", "end", values=values)

            self.link_map[item_id] = {
                'search': item.get('search_link'),
                'repo': item.get('repo_link')
            }

    def _sort_column(self, col, reverse):
        l = [(self.tree.set(k, col), k) for k in self.tree.get_children('')]
        try:
            l.sort(key=lambda t: t[0].lower(), reverse=reverse)
        except:
            l.sort(reverse=reverse)

        for index, (val, k) in enumerate(l):
            self.tree.move(k, '', index)

        self.tree.heading(col, command=lambda: self._sort_column(col, not reverse))

    def _on_double_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell": return

        row_id = self.tree.identify_row(event.y)
        col_id = self.tree.identify_column(event.x)

        links = self.link_map.get(row_id)
        if not links: return

        if col_id == "#3" and links['search']:
            self._open_url(links['search'])
        elif col_id == "#4" and links['repo']:
            self._open_url(links['repo'])

    def _open_url(self, url):
        if url:
            webbrowser.open(url)

    def _scrape_repo_row(self):
        selected = self.tree.selection()
        if not selected: return
        item_id = selected[0]
        links = self.link_map.get(item_id)
        if links and links.get('repo'):
            self.on_repo_scrape_callback(links['repo'])
