import json
import re
from bs4 import BeautifulSoup
from parsers.base_parser import BaseParser
from urllib.parse import urljoin

class FeiParser(BaseParser):
    def __init__(self):
        super().__init__(sigla="FEI", universidade="Centro Universitário FEI")

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

        if on_progress: on_progress("FEI (DSpace 8): Analisando estado da aplicação...")

        # 1. Tenta extrair do JSON de estado do DSpace
        try:
            json_data = self._extract_from_json_state(soup)
            if json_data:
                data.update(json_data)
                if on_progress: on_progress(f"Programa encontrado: {data['programa']}")
        except Exception as e:
            if on_progress: on_progress(f"Erro na leitura JSON: {e}")

        # 2. Extração de PDF
        data['link_pdf'] = self._find_pdf(soup, url)

        return data

    def _extract_from_json_state(self, soup):
        script_tag = soup.find('script', id='dspace-angular-state')
        if not script_tag:
            return None

        script_content = script_tag.string or script_tag.get_text()
        
        # Normalização de entidades HTML se necessário
        if '&q;' in script_content:
            raw_json = script_content.replace('&q;', '"')
        else:
            raw_json = script_content
        
        try:
            state = json.loads(raw_json)
            cache = state.get('NGRX_STATE', {}).get('core', {}).get('cache/object', {})
            
            # Lista de candidatos a Programa
            candidates = []
            
            for key, entry in cache.items():
                obj = entry.get('data', {})
                obj_type = obj.get('type')
                
                if obj_type in ['community', 'collection']:
                    name = obj.get('_name', '')
                    # A FEI usa nomes bem descritivos. Ex:
                    # "Programa de Pós-Graduação de Mestrado e Doutorado em Engenharia Elétrica"
                    if "Programa de Pós-Graduação" in name or "Mestrado" in name or "Doutorado" in name:
                        candidates.append(name)
            
            # Lógica de Seleção:
            # Preferência por quem tem "Programa de Pós-Graduação" no nome
            final_program = "-"
            
            # Filtra o candidato mais longo (geralmente o nome completo do programa)
            # Ex: "Engenharia Elétrica" (curto) vs "Programa de Pós..." (longo)
            candidates.sort(key=len, reverse=True)
            
            for c in candidates:
                if "Programa de Pós-Graduação" in c:
                    final_program = c
                    break
            
            # Se não achou com "Programa", pega o primeiro da lista ordenada (o mais longo)
            if final_program == "-" and candidates:
                final_program = candidates[0]

            return {
                'programa': self._clean_program(final_program),
                'universidade': self.universidade 
            }

        except json.JSONDecodeError:
            return None
        
        return None

    def _find_pdf(self, soup, base_url):
        # 1. Meta tag (A FEI usa citation_pdf_url)
        meta = soup.find('meta', attrs={'name': 'citation_pdf_url'})
        if meta: return meta.get('content')
        
        # 2. Busca links de bitstreams
        links = soup.find_all('a', href=True)
        for link in links:
            href = link['href']
            if ('/bitstreams/' in href) and ('download' in href):
                return urljoin(base_url, href)
        return '-'

    def _clean_program(self, raw):
        if not raw or raw == '-': return "-"
        # Remove prefixos comuns para deixar o nome mais limpo na tabela
        clean = re.sub(r'Programa de Pós-Graduação (de|em)?\s*', '', raw, flags=re.IGNORECASE)
        clean = re.sub(r'Mestrado e Doutorado (de|em)?\s*', '', clean, flags=re.IGNORECASE)
        return clean.strip()