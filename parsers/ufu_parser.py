import re
from parsers.dspace_jspui import DSpaceJSPUIParser

class UfuParser(DSpaceJSPUIParser):
    def __init__(self):
        # Sigla e nome institucional para a UFU
        super().__init__(sigla="UFU", universidade="Universidade Federal de Uberlândia")

    def _find_program(self, soup):
        """
        Sobrescreve a busca do programa para focar no valor da célula 
        e não no rótulo 'Program:', usando o ID da classe CSS presente no HTML da UFU.
        """
        # Estratégia 1: Busca pelo ID da classe específica de valor do DSpace 6
        target = soup.find('td', class_='metadataFieldValue dc_publisher_program')
        if target:
            return target.get_text(strip=True)
            
        # Estratégia 2: Fallback para a lógica da classe pai (que busca por labels 'Programa', 'Program', etc.)
        return super()._find_program(soup)

    # A limpeza do nome (remover 'Programa de Pós-graduação em...') 
    # já é tratada automaticamente pela classe pai.