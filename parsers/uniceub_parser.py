import re
from bs4 import BeautifulSoup
from parsers.dspace_jspui import DSpaceJSPUIParser

class UniceubParser(DSpaceJSPUIParser):
    def __init__(self):
        super().__init__(sigla="UniCEUB", universidade="Centro Universitário de Brasília")

    def _find_program(self, soup):
        """
        No UniCEUB, o programa geralmente está dentro da citação bibliográfica.
        Ex: "... Tese (Doutorado em Direito) - Centro..."
        """
        # 1. Tenta extrair da Meta Tag de Citação (Mais rápido e confiável)
        meta_cit = soup.find('meta', attrs={'name': 'DCTERMS.bibliographicCitation'})
        if meta_cit:
            text = meta_cit.get('content', '')
            # Procura por "Tese (Curso)" ou "Dissertação (Curso)"
            match = re.search(r'(?:Tese|Dissertação)\s*\(([^)]+)\)', text, re.IGNORECASE)
            if match:
                return match.group(1) # Retorna "Doutorado em Direito"

        # 2. Tenta extrair da Tabela Visual (Fallback)
        # Procura a linha "Citation:"
        row = soup.find('td', class_='metadataFieldLabel', string=re.compile(r'Citation', re.IGNORECASE))
        if row:
            val = row.find_next_sibling('td', class_='metadataFieldValue')
            if val:
                text = val.get_text(strip=True)
                match = re.search(r'(?:Tese|Dissertação)\s*\(([^)]+)\)', text, re.IGNORECASE)
                if match:
                    return match.group(1)

        # 3. Se falhar, tenta o padrão (Coleções, Breadcrumbs)
        return super()._find_program(soup)