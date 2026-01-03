import json
import re
from bs4 import BeautifulSoup
from parsers.base_parser import BaseParser
from urllib.parse import urljoin

class CefetMgParser(BaseParser):
    def __init__(self):
        super().__init__(sigla="CEFET-MG", universidade="Centro Federal de Educação Tecnológica de Minas Gerais")

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

        if on_progress: on_progress("CEFET-MG (DSpace 7): Analisando estado da aplicação...")

        # 1. Tenta extrair do JSON de estado (Fonte mais confiável)
        try:
            json_data = self._extract_from_json_state(soup)
            if json_data:
                data.update(json_data)
                if on_progress: on_progress(f"Dados encontrados via JSON: {data.get('programa')}")
        except Exception as e:
            if on_progress: on_progress(f"Erro na leitura JSON: {e}")

        # 2. Extração de PDF
        data['link_pdf'] = self._find_pdf(soup, url)

        return data

    def _extract_from_json_state(self, soup):
        script_tag = soup.find('script', id='dspace-angular-state')
        if not script_tag:
            return None

        # Decodifica entidades HTML se necessário (&q; -> ")
        raw_json = script_tag.string or script_tag.get_text()
        if '&q;' in raw_json:
            raw_json = raw_json.replace('&q;', '"')

        try:
            state = json.loads(raw_json)
            cache = state.get('NGRX_STATE', {}).get('core', {}).get('cache/object', {})
            
            program_name = "-"
            
            for key, entry in cache.items():
                obj_data = entry.get('data', {})
                metadata = obj_data.get('metadata', {})
                
                # O CEFET-MG usa o campo específico 'dc.publisher.program'
                program_field = metadata.get('dc.publisher.program', [])
                if program_field:
                    raw_prog = program_field[0].get('value')
                    program_name = self._clean_program(raw_prog)
                    break
            
            # Fallback: Tenta pela hierarquia de comunidades se o campo específico falhar
            if program_name == "-":
                for key, entry in cache.items():
                    obj_data = entry.get('data', {})
                    if obj_data.get('type') in ['community', 'collection']:
                        name = obj_data.get('_name', '')
                        if "Programa de Pós" in name or "Mestrado" in name or "Doutorado" in name:
                            program_name = self._clean_program(name)
                            if "Programa" in name: 
                                break

            return {
                'programa': program_name,
                'universidade': self.universidade
            }

        except json.JSONDecodeError:
            return None
        
        return None

    def _find_pdf(self, soup, base_url):
        # 1. Meta tag padrão
        meta = soup.find('meta', attrs={'name': 'citation_pdf_url'})
        if meta: return meta.get('content')
        
        # 2. Busca no HTML (Angular geralmente renderiza links com '/bitstreams/')
        links = soup.find_all('a', href=True)
        for link in links:
            href = link['href']
            if '/bitstreams/' in href and 'download' in href:
                return urljoin(base_url, href)
        return '-'

    def _clean_program(self, raw):
        if not raw or raw == '-': return "-"
        # Remove "Programa de Pós-Graduação em" para limpar
        clean = re.sub(r'Programa de Pós[- ]Graduação (em|de)?\s*', '', raw, flags=re.IGNORECASE).strip()
        # Remove sufixos como " - PPGMMC"
        clean = clean.split(' - ')[0].strip()
        return clean.title()