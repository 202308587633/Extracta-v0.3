import requests
from bs4 import BeautifulSoup

class ScraperModel:
    def fetch_html(self, url):
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            raise Exception(f"Erro ao acessar: {e}")

    def extract_data(self, html_content, parser, base_url=""):
        """Usa um parser específico para extrair dados do HTML"""
        soup = BeautifulSoup(html_content, 'html.parser')
        return parser.parse(soup, base_url)