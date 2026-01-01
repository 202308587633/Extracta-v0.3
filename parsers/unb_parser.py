import re
from bs4 import BeautifulSoup
from parsers.dspace_jspui import DSpaceJSPUIParser

class UnbParser(DSpaceJSPUIParser):
    def __init__(self):
        super().__init__(sigla="UnB", universidade="Universidade de Brasília")

    def _find_program(self, soup):
        """
        Busca específica para a estrutura customizada da UnB.
        """
        # Estratégia 1: Busca pela classe CSS específica da UnB na tabela
        target = soup.find('td', class_='dc_description_ppg')
        if target:
            # Pega a célula seguinte (o valor)
            value_td = target.find_next_sibling('td')
            if value_td:
                return value_td.get_text(strip=True)

        # Estratégia 2: Busca refinada nas meta tags DC.description
        # Na UnB existem várias, buscamos a que contém o texto do curso
        meta_descriptions = soup.find_all('meta', attrs={'name': 'DC.description'})
        for meta in meta_descriptions:
            content = meta.get('content', '')
            if "Programa de Pós-Graduação" in content:
                return content

        # Estratégia 3: Fallback para a lógica padrão do DSpace
        return super()._find_program(soup)