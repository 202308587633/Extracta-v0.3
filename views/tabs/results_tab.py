import customtkinter as ctk
import webbrowser

class ResultsTab(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        self.label_count = ctk.CTkLabel(self, text="Nenhum dado extraído.", font=("Roboto", 16, "bold"))
        self.label_count.pack(pady=10)

        self.scroll_results = ctk.CTkScrollableFrame(self)
        self.scroll_results.pack(fill="both", expand=True, padx=10, pady=10)

    def display_results(self, results):
        for widget in self.scroll_results.winfo_children():
            widget.destroy()

        self.label_count.configure(text=f"{len(results)} registros encontrados")

        for i, item in enumerate(results):
            self._create_card(item, i)

    def _create_card(self, item, index):
        card = ctk.CTkFrame(self.scroll_results, fg_color=("gray85", "gray25"))
        card.pack(fill="x", pady=5, padx=5)

        lbl_title = ctk.CTkLabel(card, text=f"Pesquisa: {item.get('title')}", font=("Roboto", 14, "bold"), anchor="w", wraplength=600)
        lbl_title.pack(fill="x", padx=10, pady=(10, 0))

        lbl_author = ctk.CTkLabel(card, text=f"Autor: {item.get('author')}", font=("Roboto", 12), text_color="gray70", anchor="w")
        lbl_author.pack(fill="x", padx=10, pady=(0, 5))

        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=10)

        if item.get('search_link'):
            btn_search = ctk.CTkButton(btn_frame, text="Link da Pesquisa", height=25, 
                                     command=lambda u=item['search_link']: self._open_url(u))
            btn_search.pack(side="left", padx=(0, 10))

        if item.get('repo_link'):
            btn_repo = ctk.CTkButton(btn_frame, text="Acessar Documento", height=25, fg_color="#E04F5F", hover_color="#C03949",
                                   command=lambda u=item['repo_link']: self._open_url(u))
            btn_repo.pack(side="left")

    def _open_url(self, url):
        if url:
            webbrowser.open(url)