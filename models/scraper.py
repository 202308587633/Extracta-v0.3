import requests

class ScraperModel:
    def fetch_html(self, url):
        # Garante que a URL tenha esquema http/https
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            raise Exception(f"Erro ao acessar: {e}")