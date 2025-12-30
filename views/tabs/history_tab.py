import customtkinter as ctk
import tkinter as tk

class HistoryTab(ctk.CTkFrame):
    def __init__(self, parent, on_select_callback, on_delete_callback):
        super().__init__(parent)
        self.on_select_callback = on_select_callback
        self.on_delete_callback = on_delete_callback
        self._setup_ui()
        self._setup_context_menu()

    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=3)
        self.grid_rowconfigure(0, weight=1)

        self.scroll_list = ctk.CTkScrollableFrame(self, label_text="Páginas Salvas")
        self.scroll_list.grid(row=0, column=0, padx=(0, 10), pady=10, sticky="nsew")

        self.textbox_content = ctk.CTkTextbox(self, corner_radius=10)
        self.textbox_content.grid(row=0, column=1, pady=10, sticky="nsew")
        self.textbox_content.insert("0.0", "Selecione um item para ver o HTML...")
        self.textbox_content.configure(state="disabled", font=("Consolas", 12))

    def update_list(self, history_items):
        for widget in self.scroll_list.winfo_children():
            widget.destroy()

        for item_id, url, date in history_items:
            btn_text = f"{date}\n{url}"
            btn = ctk.CTkButton(
                self.scroll_list, 
                text=btn_text, 
                anchor="w", 
                height=50,
                fg_color="transparent", 
                border_width=1,
                text_color=("gray10", "gray90"),
                command=lambda i=item_id: self.on_select_callback(i)
            )
            btn.pack(fill="x", pady=2)

    def display_content(self, html_content):
        self.textbox_content.configure(state="normal")
        self.textbox_content.delete("0.0", "end")
        self.textbox_content.insert("0.0", html_content)
        self.textbox_content.configure(state="disabled")

    def _setup_context_menu(self):
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Excluir este HTML", command=self.on_delete_callback)
        self.textbox_content.bind("<Button-3>", self._show_context_menu)

    def _show_context_menu(self, event):
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()
