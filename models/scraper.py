import requests
from bs4 import BeautifulSoup
from requests.exceptions import RequestException, Timeout, ConnectionError, HTTPError

class ScraperModel:
    def fetch_html(self, url):
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.text
        except Timeout:
            raise Exception("Erro: O servidor demorou muito a responder (Timeout).")
        except ConnectionError:
            raise Exception("Erro: Falha na ligação. Verifique a sua internet.")
        except HTTPError as e:
            raise Exception(f"Erro HTTP: O servidor retornou o código {e.response.status_code}.")
        except RequestException as e:
            raise Exception(f"Erro de Rede: {str(e)}")

    def extract_data(self, html_content, parser, base_url=""):
        """Usa um parser específico para extrair dados do HTML"""
        soup = BeautifulSoup(html_content, 'html.parser')
        return parser.parse(soup, base_url)
