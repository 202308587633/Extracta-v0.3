import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class UNIPEParser(BaseParser):
    def __init__(self):
        super().__init__(sigla="UNIPÊ", universidade="Centro Universitário de João Pessoa")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        soup = BeautifulSoup(html_content, 'html.parser')
        data = {'sigla': self.sigla, 'universidade': self.universidade, 'programa': '-', 'link_pdf': '-'}

        # Extração do Programa via Breadcrumb
        breads = soup.select('li.breadcrumb-item')
        if len(breads) >= 2:
            data['programa'] = breads[-2].get_text(strip=True)

        # Extração do PDF
        pdf_meta = soup.find('meta', attrs={'name': 'citation_pdf_url'})
        if pdf_meta:
            data['link_pdf'] = urljoin(url, pdf_meta.get('content'))

        return data