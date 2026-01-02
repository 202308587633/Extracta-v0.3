import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class DSpaceAngularParser(BaseParser):
    def extract(self, html_content, base_url, on_progress=None):
        return self.extract_pure_soup(html_content, base_url, on_progress)

    def extract_pure_soup(self, html_content, url, on_progress=None):
        soup = BeautifulSoup(html_content, 'html.parser')
        
        self._check_dynamic_context(soup, on_progress)

        data = {
            'sigla': getattr(self, 'sigla', '-'),
            'universidade': getattr(self, 'universidade', 'Não identificada'),
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress(f"Analisando (Angular/DSpace 7+)...")

        # 1. Programa
        raw_program = self._find_program_in_breadcrumbs(soup)
        if not raw_program:
            raw_program = self._find_program_fallback(soup)

        if raw_program:
            data['programa'] = self._clean_program_name(raw_program)
            if on_progress: on_progress(f"Programa identificado: {data['programa']}")

        # 2. PDF
        data['link_pdf'] = self._find_pdf(soup, url)

        return data

    def _check_dynamic_context(self, soup, on_progress):
        pass

    def _find_program_in_breadcrumbs(self, soup):
        crumbs = soup.select('ol.breadcrumb li, ul.breadcrumb li')
        for crumb in reversed(crumbs):
            text = crumb.get_text(strip=True)
            if 'active' in crumb.get('class', []): continue
            if text in ["Início", "Home", "Página inicial", "Teses e Dissertações", "Comunidades e Coleções"]: continue
            if "Acervos" in text or "Biblioteca" in text: continue

            if any(x in text for x in ["Programa", "Mestrado", "Doutorado", "Pós-Graduação"]):
                return text
            return text
        return None

    def _find_program_fallback(self, soup):
        return None

    def _clean_program_name(self, raw):
        name = re.sub(
            r'^(?:Programa de |)(?:Pós-Graduação(?: Interdisciplinar)?(?: em)? |)(?:Mestrado|Doutorado)(?:\s+(?:Profissional|Acadêmico))?(?: em| no| na)?\s*', 
            '', raw, flags=re.IGNORECASE
        )
        name = re.sub(r'^[A-Z0-9-]+\s+-\s+', '', name)
        return name.strip('.,- ')

    def _find_pdf(self, soup, base_url):
        meta = soup.find('meta', attrs={'name': 'citation_pdf_url'})
        if meta: return meta.get('content')
        
        link = soup.find('a', href=lambda h: h and ('/bitstream/' in h or '/download' in h))
        if link:
            href = link['href']
            if href.lower().endswith('.pdf') or '/download' in href:
                return urljoin(base_url, href)
        return '-'
    
    def __init__(self, sigla="-", universidade="Desconhecida"):
        super().__init__(sigla, universidade)
