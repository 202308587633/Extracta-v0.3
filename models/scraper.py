import requests
import time
import config 
from bs4 import BeautifulSoup

class ScraperModel:
    def __init__(self):
        # CORREÇÃO: Headers mais completos para evitar erro 403
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1'
        }
        
        # Tenta usar o do config se existir, mas mantém o fallback robusto acima
        if hasattr(config, 'USER_AGENT') and config.USER_AGENT:
             self.headers['User-Agent'] = config.USER_AGENT

        self.timeout = getattr(config, 'REQUEST_TIMEOUT', 30)
        self.delay = getattr(config, 'DELAY_BETWEEN_REQUESTS', 1.0)

    def fetch_html(self, url):
        """Faz a requisição HTTP e retorna o HTML."""
        time.sleep(self.delay)
        try:
            # Adicionado verify=False para evitar erros de certificado SSL em alguns repositórios acadêmicos antigos
            # Adicionado timeout explícito
            response = requests.get(url, headers=self.headers, timeout=self.timeout, verify=False)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Erro no request ({url}): {e}")
            # Retorna None para que o chamador saiba que falhou, em vez de quebrar a thread
            return None