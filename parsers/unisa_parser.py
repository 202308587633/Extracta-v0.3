import json
import re
from bs4 import BeautifulSoup
from parsers.base_parser import BaseParser
from urllib.parse import urljoin

class UnisaParser(BaseParser):
    def __init__(self):
        super().__init__(sigla="UNISA", universidade="Universidade Santo Amaro")

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

        if on_progress: on_progress("UNISA (DSpace 7): Varrendo cache de objetos...")

        # 1. Tenta extrair do JSON de estado do DSpace 7
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

        # Obtém o texto do script com segurança
        script_content = script_tag.string or script_tag.get_text()
        if not script_content:
            return None

        # Decodifica as aspas HTML (&q;) para aspas JSON (")
        # Fundamental para o DSpace 7 funcionar
        raw_json = script_content.replace('&q;', '"')
        
        try:
            state = json.loads(raw_json)
            
            # O Cache contém todos os objetos carregados na página
            # Caminho: NGRX_STATE -> core -> cache/object
            cache = state.get('NGRX_STATE', {}).get('core', {}).get('cache/object', {})
            
            program_name = "-"
            
            # ESTRATÉGIA ROBUSTA: 
            # Em vez de tentar seguir links complexos (Item -> Link -> Request -> UUID -> Objeto),
            # simplesmente varremos o cache procurando pelo objeto do tipo "collection".
            # Em 99% dos casos, a coleção presente na página do item é o Programa.
            
            for key, entry in cache.items():
                obj = entry.get('data', {})
                
                # Se acharmos um objeto do tipo coleção
                if obj.get('type') == 'collection':
                    name = obj.get('_name', '')
                    
                    # Filtro de segurança: Prioriza nomes que pareçam cursos
                    if any(x in name for x in ['Mestrado', 'Doutorado', 'Programa', 'Pós-Graduação']):
                        program_name = name
                        break
                    
                    # Fallback: guarda o primeiro que achar se não tiver os termos acima
                    if program_name == "-":
                        program_name = name

            return {
                'programa': self._clean_program(program_name),
                'universidade': self.universidade 
            }

        except json.JSONDecodeError:
            return None
        
        return None

    def _find_pdf(self, soup, base_url):
        # 1. Meta tag (Padrão mais confiável)
        meta = soup.find('meta', attrs={'name': 'citation_pdf_url'})
        if meta: return meta.get('content')
        
        # 2. Busca links visuais de download
        links = soup.find_all('a', href=True)
        for link in links:
            href = link['href']
            # Filtra links que parecem ser downloads de PDF do DSpace
            if ('bitstreams' in href or 'bitstream' in href) and ('.pdf' in href.lower() or 'download' in href.lower()):
                return urljoin(base_url, href)
        return '-'

    def _clean_program(self, raw):
        if not raw or raw == '-': return "-"
        # A UNISA retorna nomes limpos como "Mestrado em Direito Médico".
        # Retornamos o nome original pois já está no formato correto.
        return raw.strip()