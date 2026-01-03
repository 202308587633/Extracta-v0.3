import json
import re
from bs4 import BeautifulSoup
from parsers.base_parser import BaseParser
from urllib.parse import urljoin

class UFPAParser(BaseParser):
    def __init__(self):
        super().__init__(sigla="UFPA", universidade="Universidade Federal do Pará")

    def extract(self, html_content, base_url, on_progress=None):
        return self.extract_pure_soup(html_content, base_url, on_progress)

    def extract_pure_soup(self, html_content, url, on_progress=None):
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("UFPA (DSpace 7): Analisando...")

        # --- 1. Tentativa via JSON State (Mais confiável) ---
        found_in_json = False
        try:
            json_data = self._extract_from_json_state(soup)
            if json_data:
                data.update(json_data)
                found_in_json = True
                if on_progress: on_progress("Dados extraídos do estado da aplicação.")
        except Exception as e:
            print(f"Erro no JSON parse da UFPA: {e}")

        # --- 2. Tentativa Visual (Fallback se JSON falhar) ---
        if not found_in_json or data['programa'] == '-':
            visual_prog = self._extract_program_visual(soup)
            if visual_prog:
                data['programa'] = self._clean_program(visual_prog)
                if on_progress: on_progress("Dados extraídos via HTML visual.")

        # --- 3. Extração de PDF ---
        data['link_pdf'] = self._find_pdf(soup, url)

        return data

    def _extract_from_json_state(self, soup):
        script_tag = soup.find('script', id='dspace-angular-state')
        if not script_tag or not script_tag.string:
            return None

        # CORREÇÃO CRÍTICA: O DSpace da UFPA usa '&q;' no lugar de aspas duplas '"'
        raw_json = script_tag.string.replace('&q;', '"')
        
        try:
            state = json.loads(raw_json)
            # Caminho: NGRX_STATE -> core -> cache/object
            cache = state.get('NGRX_STATE', {}).get('core', {}).get('cache/object', {})
            
            for key, entry in cache.items():
                obj_data = entry.get('data', {})
                # Procura objeto do tipo 'item' que tenha metadados
                if obj_data.get('type') == 'item' and 'metadata' in obj_data:
                    metadata = obj_data['metadata']
                    
                    return {
                        'sigla': self._get_json_meta(metadata, 'dc.publisher.initials') or "UFPA",
                        'programa': self._clean_program(self._get_json_meta(metadata, 'dc.publisher.program')),
                        'universidade': self._get_json_meta(metadata, 'dc.publisher') or self.universidade
                    }
        except json.JSONDecodeError:
            return None
        
        return None

    def _get_json_meta(self, metadata, key):
        items = metadata.get(key, [])
        if items and len(items) > 0:
            return items[0].get('value')
        return None

    def _extract_program_visual(self, soup):
        """Busca visual (HTML) caso o JSON falhe."""
        # Procura headers h2 com texto "Programa"
        headers = soup.find_all('h2', string=re.compile(r'Programa', re.IGNORECASE))
        for h2 in headers:
            # O valor costuma estar em um link ou div logo após o header
            container = h2.find_parent('div', class_='simple-view-element')
            if container:
                value_div = container.find('div', class_='simple-view-element-body')
                if value_div:
                    return value_div.get_text(strip=True)
        return None

    def _find_pdf(self, soup, base_url):
        # 1. Meta tag (Geralmente funciona bem no DSpace 7)
        meta = soup.find('meta', attrs={'name': 'citation_pdf_url'})
        if meta: return meta.get('content')
        
        # 2. Busca link visual de download
        # <ds-file-download-link ... href="...">
        links = soup.find_all('a', href=True)
        for link in links:
            href = link['href']
            # Filtros para achar o PDF principal
            if ('.pdf' in href.lower() or 'download' in href.lower()) and 'bitstream' in href:
                return urljoin(base_url, href)
        
        return '-'

    def _clean_program(self, raw):
        if not raw: return "-"
        # Remove prefixos comuns
        clean = re.sub(r'^(Programa de Pós-Graduação em|Mestrado em|Doutorado em)\s*', '', raw, flags=re.IGNORECASE)
        return clean.strip()