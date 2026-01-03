import customtkinter as ctk

# --- Aplicação ---
APP_TITLE = "Extracta v0.4"
WINDOW_SIZE = "1280x800"
THEME_MODE = "Dark"  # "System", "Dark", "Light"
COLOR_THEME = "blue" # "blue", "green", "dark-blue"

# --- Banco de Dados ---
DB_NAME = "database.db"

# --- Scraping ---
BASE_URL_BDTD = "https://bdtd.ibict.br/vufind/Search/Results"
REQUEST_TIMEOUT = 30
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
DELAY_BETWEEN_REQUESTS = 1.5

# --- Dados Padrão (Home Tab) ---
DEFAULT_SEARCH_TERMS = [
    "jurimetria",
    "inteligência artificial",
    "análise de discurso",
    "algoritmo",
    "direito digital",
    "tecnologia da informação",
    "machine learning",
    "big data"
]

DEFAULT_YEARS = [str(year) for year in range(2018, 2027)]

# --- UI & Estilos ---
COLORS = {
    "success": "#50FA7B",  # Verde
    "error": "#FF5555",    # Vermelho
    "warning": "#F1FA8C",  # Amarelo
    "info": "#8BE9FD",     # Ciano
    "text": "#F8F8F2",     # Branco/Cinza claro
    "sidebar_bg": "#212121",
    "panel_bg": "#2b2b2b"
}

FONTS = {
    "logo": ("Roboto", 20, "bold"),
    "header": ("Roboto", 16, "bold"),
    "normal": ("Roboto", 12),
    "small": ("Roboto", 11)
}