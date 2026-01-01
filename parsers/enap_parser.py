import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class ENAPParser(BaseParser):
    def __init__(self):
        super().__init__(sigla="ENAP", universidade="Escola Nacional de Administração Pública")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        soup = BeautifulSoup(html_content, 'html.parser')
        data = {'sigla': self.sigla, 'universidade': self.universidade, 'programa': '-', 'link_pdf': '-'}

        if on_progress: on_progress("ENAP: Extraindo metadados...")

        # 1. Extração do Programa (DC.description)
        prog_meta = soup.find_all('meta', attrs={'name': 'DC.description'})
        for meta in prog_meta:
            content = meta.get('content', '')
            if any(k in content for k in ["Governança", "Políticas Públicas", "Mestrado"]):
                data['programa'] = content
                break

        # 2. Extração do PDF (Meta citation_pdf_url ou Link bitstream)
        pdf_meta = soup.find('meta', attrs={'name': 'citation_pdf_url'})
        if pdf_meta:
            data['link_pdf'] = urljoin(url, pdf_meta.get('content'))
        else:
            pdf_link = soup.find('a', href=re.compile(r'/bitstream/.*\.pdf'))
            if pdf_link:
                data['link_pdf'] = urljoin(url, pdf_link['href'])

        return data