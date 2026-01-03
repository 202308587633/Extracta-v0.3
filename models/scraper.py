import requests
import time
import config  # Importa o config
from bs4 import BeautifulSoup

class ScraperModel:
    def __init__(self):
        # Usa configurações do config.py
        self.headers = {'User-Agent': config.USER_AGENT}
        self.timeout = config.REQUEST_TIMEOUT
        self.delay = config.DELAY_BETWEEN_REQUESTS

    def fetch_html(self, url):
        """Faz a requisição HTTP e retorna o HTML."""
        time.sleep(self.delay)  # Delay configurável
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            # Em produção, idealmente logar isso
            print(f"Erro no request: {e}")
            raise e