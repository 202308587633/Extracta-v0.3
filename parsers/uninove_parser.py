from bs4 import BeautifulSoup
from parsers.dspace_jspui import DSpaceJSPUIParser

class UninoveParser(DSpaceJSPUIParser):
    def __init__(self):
        super().__init__(sigla="UNINOVE", universidade="Universidade Nove de Julho")

    def _find_program(self, soup):
        """
        A UNINOVE lista várias tags DC.publisher. 
        Precisamos encontrar a que contém 'Programa de Pós-Graduação'.
        """
        # 1. Tenta encontrar nas meta tags DC.publisher
        meta_publishers = soup.find_all('meta', attrs={'name': 'DC.publisher'})
        for meta in meta_publishers:
            content = meta.get('content', '')
            if 'Programa de Pós-Graduação' in content:
                return content.strip()

        # 2. Fallback: Tenta encontrar na tabela de visualização
        # (O layout JSPUI padrão costuma ter uma tabela com classe itemDisplayTable)
        return super()._find_program(soup)