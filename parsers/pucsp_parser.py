import json
import re
from bs4 import BeautifulSoup
from parsers.base_parser import BaseParser
from urllib.parse import urljoin

class PucSpParser(BaseParser):
    def __init__(self):
        super().__init__(sigla="PUC-SP", universidade="Pontifícia Universidade Católica de São Paulo")

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

        if on_progress: on_progress("PUC-SP (DSpace 7): Analisando estado da aplicação...")

        # 1. Tenta extrair do JSON de estado
        try:
            json_data = self._extract_from_json_state(soup)
            if json_data:
                data.update(json_data)
        except Exception as e:
            if on_progress: on_progress(f"Erro na leitura JSON: {e}")

        # 2. Extração de PDF (Meta tag padrão ou busca de links)
        data['link_pdf'] = self._find_pdf(soup, url)

        return data

    def _extract_from_json_state(self, soup):
        script_tag = soup.find('script', id='dspace-angular-state')
        if not script_tag:
            return None

        raw_json = script_tag.string or script_tag.get_text()
        # Decodifica entidades HTML
        raw_json = raw_json.replace('&q;', '"')

        try:
            state = json.loads(raw_json)
            # Navega até o cache de objetos
            cache = state.get('NGRX_STATE', {}).get('core', {}).get('cache/object', {})
            
            program_name = "-"
            
            for key, entry in cache.items():
                obj_data = entry.get('data', {})
                metadata = obj_data.get('metadata', {})
                
                # A PUC-SP usa 'dc.publisher.program'
                prog_field = metadata.get('dc.publisher.program', [])
                if prog_field:
                    raw_prog = prog_field[0].get('value')
                    # Limpa sufixos como (FD), (FEA), etc.
                    program_name = re.sub(r'\s*\([A-Z]+\)$', '', raw_prog).strip()
                    break
            
            # Fallback: Coleções
            if program_name == "-":
                for key, entry in cache.items():
                    obj_data = entry.get('data', {})
                    if obj_data.get('type') == 'collection':
                        name = obj_data.get('_name', '')
                        if "Programa de" in name or "Mestrado" in name or "Doutorado" in name:
                             program_name = re.sub(r'\s*\([A-Z]+\)$', '', name).strip()
                             break

            return {'programa': program_name}

        except json.JSONDecodeError:
            return None

    def _find_pdf(self, soup, base_url):
        # Meta tag padrão
        meta = soup.find('meta', attrs={'name': 'citation_pdf_url'})
        if meta: return meta.get('content')
        
        # Link do bitstream
        for a in soup.find_all('a', href=True):
            if '/bitstreams/' in a['href'] and 'download' in a['href']:
                return urljoin(base_url, a['href'])
        return '-'