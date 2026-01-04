import re
from bs4 import BeautifulSoup
from parsers.dspace_jspui import DSpaceJSPUIParser

class UfrpeParser(DSpaceJSPUIParser):
    def __init__(self):
        super().__init__(sigla="UFRPE", universidade="Universidade Federal Rural de Pernambuco")

    def _find_program(self, soup):
        """
        Estratégia para UFRPE:
        1. Link explícito com classe 'authority program'.
        2. Citação bibliográfica (DCTERMS.bibliographicCitation).
        3. Breadcrumbs.
        """
        
        # 1. Link explícito (muito confiável neste layout)
        # <a class="authority program" ...>Programa de Pós-Graduação...</a>
        prog_link = soup.find('a', class_='program')
        if prog_link:
            return prog_link.get_text(strip=True)

        # 2. Citação Bibliográfica
        # Ex: "... Tese (Programa de Pós-Graduação em...) - Universidade ..."
        meta_cit = soup.find('meta', attrs={'name': 'DCTERMS.bibliographicCitation'})
        if meta_cit:
            content = meta_cit.get('content', '')
            match = re.search(r'\((Programa de Pós-Graduação.*?)\)', content, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        # 3. Breadcrumbs
        breadcrumb = soup.find('ol', class_='breadcrumb')
        if breadcrumb:
            for li in breadcrumb.find_all('li'):
                text = li.get_text(strip=True)
                if 'PPG' in text or 'Pós-Graduação' in text:
                    return text.strip()

        return super()._find_program(soup)