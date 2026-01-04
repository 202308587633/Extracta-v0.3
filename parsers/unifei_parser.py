from bs4 import BeautifulSoup
from parsers.dspace_jspui import DSpaceJSPUIParser

class UnifeiParser(DSpaceJSPUIParser):
    def __init__(self):
        super().__init__(sigla="UNIFEI", universidade="Universidade Federal de Itajubá")

    def _find_program(self, soup):
        # 1. Busca nas meta tags DC.publisher
        # A UNIFEI coloca o programa como um dos publishers
        # Ex: "Programa de Pós-Graduação: Mestrado - Engenharia Elétrica"
        meta_publishers = soup.find_all('meta', attrs={'name': 'DC.publisher'})
        for meta in meta_publishers:
            content = meta.get('content', '')
            if 'Programa de Pós-Graduação' in content:
                return content.strip()

        # 2. Busca na tabela visual (onde aparece metadata.dc.publisher.program)
        # O JSPUI geralmente renderiza isso em uma tabela com classe itemDisplayTable
        table = soup.find('table', class_='itemDisplayTable')
        if table:
            for row in table.find_all('tr'):
                # Verifica se a label da linha contém 'program'
                label = row.find('td', class_='metadataFieldLabel')
                if label and 'program' in label.get_text(strip=True).lower():
                    value = row.find('td', class_='metadataFieldValue')
                    if value:
                        return value.get_text(strip=True)

        return super()._find_program(soup)