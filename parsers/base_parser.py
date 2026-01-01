import requests
from bs4 import BeautifulSoup

class BaseParser:
    """
    Classe base que define o comportamento padrão para todos os parsers.
    """
    
    def __init__(self, sigla="-", universidade="Desconhecida"):
        self.sigla = sigla
        self.universidade = universidade

    # --- ADICIONE ESTE MÉTODO ---
    def extract(self, html_content, base_url, on_progress=None):
        """
        Método padrão de extração. 
        Redireciona para extract_pure_soup, servindo de 'ponte' para 
        parsers que não precisam de lógica complexa antes do soup.
        """
        return self.extract_pure_soup(html_content, base_url, on_progress)
    # ----------------------------

    def fetch_and_extract(self, url, on_progress=None):
        data = self._get_default_data(url)
        if not url or not url.startswith("http"): return data

        try:
            if on_progress: on_progress(f"Iniciando download em {self.sigla}...")
            
            # Ajuste conforme sua importação de serviço de rede
            # from services.networking import NetworkingService
            # resp = NetworkingService().get(url, on_progress=on_progress)
            
            # Fallback simples para requests caso não use o serviço acima
            resp = requests.get(url, timeout=30) 
            
            if resp.status_code == 200:
                if on_progress: on_progress(f"Extraindo metadados de {self.sigla}...")
                data['html_source'] = resp.text
                # Agora chamamos o método extract interno
                extracted = self.extract(resp.text, url, on_progress)
                data.update(extracted)
            else:
                if on_progress: on_progress(f"Falha: Status {resp.status_code}")
        except Exception as e:
            if on_progress: on_progress(f"Erro em {self.sigla}: {str(e)[:50]}")
            
        return data

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Este método deve ser sobrescrito pelos parsers filhos.
        Realiza apenas o parsing do HTML (Modo Offline/Banco).
        """
        raise NotImplementedError("Os parsers filhos devem implementar o método extract_pure_soup")

    def _get_default_data(self, url):
        return {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': url,
            'html_source': ''
        }