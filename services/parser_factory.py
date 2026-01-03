import json
import os

from models.parsers.vufind_parser import VufindParser

from parsers.generic_parser import GenericParser
from parsers.dspace_jspui import DSpaceJSPUIParser
from parsers.dspace_angular import DSpaceAngularParser
from parsers.bdtd_parser import BDTDParser

# Importe APENAS os parsers que possuem lógica customizada complexa
from parsers.usp_parser import USPParser
from parsers.ucs_parser import UcsParser 
from parsers.uepg_parser import UEPGParser
from parsers.unicap_parser import UnicapParser
from parsers.ufpa_parser import UFPAParser
from parsers.unisa_parser import UnisaParser
from parsers.uniceub_parser import UniceubParser
from parsers.ufmt_parser import UfmtParser
from parsers.unifor_parser import UniforParser
from parsers.unisinos_parser import UnisinosParser

class ParserFactory:
    def __init__(self, config_filename="parsers_config.json"):
        self._default = GenericParser()
        
        base_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(base_dir, config_filename)
        
        self.config_map = self._load_config(config_path)
        
        self._custom_map = {
            'repositorio.jesuita.org.br': UnisinosParser, 
            '.unisinos.br': UnisinosParser,
            'biblioteca.sophia.com.br': UniforParser, 
            'uol.unifor.br': UniforParser,
            '.ufmt.br': UfmtParser,
            '.usp.br': USPParser,
            '.ucs.br': UcsParser,
            '.uepg.br': UEPGParser,
            'tede2.uepg.br': UEPGParser,
            '.unicap.br': UnicapParser,
            'tede2.unicap.br': UnicapParser,
            '.ufpa.br': UFPAParser,
            'repositorio.ufpa.br': UFPAParser,
            'dspace.unisa.br': UnisaParser,
            '.unisa.br': UnisaParser,
            'repositorio.uniceub.br': UniceubParser, # <--- [2] REGISTRO
            '.uniceub.br': UniceubParser             # <--- [2] REGISTRO
        }

    def _load_config(self, path):
        if not os.path.exists(path): return []
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("mappings", [])
        except: return []

    def get_parser(self, url, html_content=None):
        if not url: return self._default
        url_lower = url.lower()
        
        # 1. Customizados (Prioridade Alta)
        for domain, parser_cls in self._custom_map.items():
            if domain in url_lower: return parser_cls()

        # 2. Config JSON
        for entry in self.config_map:
            if entry['key'] in url_lower:
                if entry.get('type') == 'angular':
                    return DSpaceAngularParser(sigla=entry.get('sigla'), universidade=entry.get('name'))
                return DSpaceJSPUIParser(sigla=entry.get('sigla'), universidade=entry.get('name'))

        # 3. Detecção Genérica
        if html_content:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            html_lower = html_content.lower()

            if "vufind" in html_lower or "bdtd.ibict.br" in url_lower:
                if "search/results" in url_lower or soup.select('.result'):
                    return VufindParser()
                else:
                    return BDTDParser() 

            if soup.find('ds-app') or soup.find('ds-root'):
                return DSpaceAngularParser(sigla="DSpace7", universidade="Não identificada")

            if (soup.find('div', id='ds-main') or 
                len(soup.find_all('meta', attrs={'name': lambda x: x and x.startswith('DC.')})) > 3):
                return DSpaceJSPUIParser(sigla="DSpace", universidade="Não identificada")

        return self._default