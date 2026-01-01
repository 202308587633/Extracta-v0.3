import re
from bs4 import BeautifulSoup
from parsers.base_parser import BaseParser

class BDTDParser(BaseParser):
    def __init__(self):
        # Inicializa com valores padrão que serão sobrescritos no extract
        super().__init__(sigla="-", universidade="-")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        soup = BeautifulSoup(html_content, 'html.parser')
        data = {'sigla': '-', 'universidade': '-', 'programa': '-', 'link_pdf': '-'}

        # Localiza a Sigla (ex: UDF) e Universidade (ex: Centro Univ. Distrito Federal)
        sigla_row = soup.find('th', string=re.compile(r'Sigla da instituição', re.I))
        if sigla_row:
            data['sigla'] = sigla_row.find_next_sibling('td').get_text(strip=True)
            
        univ_row = soup.find('th', string=re.compile(r'Instituição de defesa', re.I))
        if univ_row:
            data['universidade'] = univ_row.find_next_sibling('td').get_text(strip=True)

        # Localiza o Link de acesso (que é o link do repositório final)
        link_row = soup.find('th', string=re.compile(r'Link de acesso', re.I))
        if link_row:
            link = link_row.find_next('a', href=True)
            if link: data['link_pdf'] = link['href']

        return data    
