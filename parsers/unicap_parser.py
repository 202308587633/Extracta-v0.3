from parsers.dspace_jspui import DSpaceJSPUIParser
from urllib.parse import urljoin

class UnicapParser(DSpaceJSPUIParser):
    def __init__(self):
        # Fixa a identidade da instituição, já que os metadados falham nisso
        super().__init__(sigla="UNICAP", universidade="Universidade Católica de Pernambuco")

    def _find_program(self, soup):
        """
        Estratégia específica para UNICAP.
        Prioriza links com a classe 'program', que é um padrão específico deste tema.
        """
        # Ex: <a class="program" href="...">Mestrado em Direito</a>
        prog_link = soup.find('a', class_='program')
        if prog_link:
            return prog_link.get_text(strip=True)

        return super()._find_program(soup)

    def _find_pdf(self, soup, base_url):
        """
        Sobrescreve a busca de PDF para evitar links 'localhost' quebrados 
        que aparecem nos metadados da UNICAP.
        """
        # 1. Tenta pegar o link visual da tabela (Bitstream)
        # Procura link que tenha 'bitstream' na URL e termine em .pdf
        link = soup.find('a', href=lambda h: h and ('/bitstream/' in h or 'bitstream' in h) and h.lower().endswith('.pdf'))
        if link:
            return urljoin(base_url, link['href'])
            
        # 2. Fallback para o padrão (mesmo que seja localhost, é o que tem)
        return super()._find_pdf(soup, base_url)