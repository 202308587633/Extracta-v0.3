import json
import os

# --- Caminho para persistência ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")

# --- Valores Padrão (Defaults) ---
APP_TITLE = "Extracta v0.4"
WINDOW_SIZE = "1280x800"
THEME_MODE = "Dark" 
COLOR_THEME = "blue"
DB_NAME = "database.db"

# Scraping Defaults
BASE_URL_BDTD = "https://bdtd.ibict.br/vufind/Search/Results"
SEARCH_URL_TEMPLATE = "https://bdtd.ibict.br/vufind/Search/Results?lookfor={term}&type=AllFields&filter%5B%5D=publishDate%3A%22{year}%22"
REQUEST_TIMEOUT = 30
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
DELAY_BETWEEN_REQUESTS = 1.5

# Dados de Negócio Defaults
DEFAULT_SEARCH_TERMS = [
    "jurimetria", "inteligência artificial", "análise de discurso",
    "algoritmo", "direito digital", "tecnologia da informação",
    "machine learning", "big data"
]
DEFAULT_YEARS = [str(year) for year in range(2018, 2027)]

# UI Colors
COLORS = {
    "success": "#50FA7B",
    "error": "#FF5555",
    "warning": "#F1FA8C",
    "info": "#8BE9FD",
    "text": "#F8F8F2",
    "sidebar_bg": "#212121",
    "panel_bg": "#2b2b2b",
    "table_bg": "#2b2b2b",
    "table_header": "#1f1f1f",
    "table_selected": "#1f538d"
}

FONTS = {
    "logo": ("Roboto", 20, "bold"),
    "header": ("Roboto", 16, "bold"),
    "normal": ("Roboto", 12),
    "small": ("Roboto", 11)
}

# --- Lógica de Carregamento e Salvamento ---

def load_settings():
    """Carrega configurações do JSON e atualiza as variáveis globais."""
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            globals()['REQUEST_TIMEOUT'] = data.get('REQUEST_TIMEOUT', REQUEST_TIMEOUT)
            globals()['USER_AGENT'] = data.get('USER_AGENT', USER_AGENT)
            globals()['DELAY_BETWEEN_REQUESTS'] = data.get('DELAY_BETWEEN_REQUESTS', DELAY_BETWEEN_REQUESTS)
            globals()['THEME_MODE'] = data.get('THEME_MODE', THEME_MODE)
            globals()['DEFAULT_SEARCH_TERMS'] = data.get('DEFAULT_SEARCH_TERMS', DEFAULT_SEARCH_TERMS)
            # ADICIONADO: Carregar anos
            globals()['DEFAULT_YEARS'] = data.get('DEFAULT_YEARS', DEFAULT_YEARS)
        except Exception as e:
            print(f"Erro ao carregar settings.json: {e}")

def save_settings(new_data):
    """Recebe um dicionário com novas configurações e salva no JSON."""
    globals()['REQUEST_TIMEOUT'] = float(new_data.get('timeout', REQUEST_TIMEOUT))
    globals()['USER_AGENT'] = new_data.get('user_agent', USER_AGENT)
    globals()['DELAY_BETWEEN_REQUESTS'] = float(new_data.get('delay', DELAY_BETWEEN_REQUESTS))
    globals()['THEME_MODE'] = new_data.get('theme', THEME_MODE)
    
    # Processa Termos
    terms_raw = new_data.get('terms', "")
    if isinstance(terms_raw, str):
        globals()['DEFAULT_SEARCH_TERMS'] = [t.strip() for t in terms_raw.split(',') if t.strip()]

    # ADICIONADO: Processa Anos
    years_raw = new_data.get('years', "")
    if isinstance(years_raw, str):
        # Cria lista de strings, limpando espaços
        globals()['DEFAULT_YEARS'] = [y.strip() for y in years_raw.split(',') if y.strip()]
    
    data_to_save = {
        'REQUEST_TIMEOUT': globals()['REQUEST_TIMEOUT'],
        'USER_AGENT': globals()['USER_AGENT'],
        'DELAY_BETWEEN_REQUESTS': globals()['DELAY_BETWEEN_REQUESTS'],
        'THEME_MODE': globals()['THEME_MODE'],
        'DEFAULT_SEARCH_TERMS': globals()['DEFAULT_SEARCH_TERMS'],
        'DEFAULT_YEARS': globals()['DEFAULT_YEARS'] # Salva no JSON
    }
    
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Erro ao salvar settings: {e}")
        return False

# Carrega ao iniciar o módulo
load_settings()



        
