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
from parsers.ufop_parser import UfopParser
from parsers.uff_parser import UFFParser
from parsers.fei_parser import FeiParser
from parsers.ufrn_parser import UfrnParser
from parsers.cefetmg_parser import CefetMgParser
from parsers.upf_parser import UpfParser
from parsers.sucupira_parser import SucupiraParser
from parsers.udesc_parser import UdescParser
from parsers.siduece_parser import SidUeceParser
from parsers.fecap_parser import FecapParser
from parsers.utfpr_parser import UTFPRParser
from parsers.uninove_parser import UninoveParser
from parsers.ucb_parser import UcbParser
from parsers.ufsm_parser import UfsmParser
from parsers.ufcg_parser import UFCGParser
from parsers.enap_parser import ENAPParser
from parsers.idp_parser import IDPParser
from parsers.ufpel_parser import UfpelParser

class ParserFactory:
    def __init__(self, config_filename="parsers_config.json"):
        self._default = GenericParser()
        self.config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), config_filename)
        
        # Mapa de classes disponíveis (String -> Classe Real)
        # Isso permite instanciar a classe baseada no nome que está no JSON
        self.available_parsers = {
            'UfpelParser': UfpelParser,
            'IdpParser': IDPParser,
            'EnapParser': ENAPParser,
            'UfcgParser': UFCGParser,
            'UfsmParser': UfsmParser,
            'UcbParser': UcbParser,
            'UninoveParser': UninoveParser,
            'VufindParser': VufindParser,
            'BDTDParser': BDTDParser,
            'DSpaceJSPUIParser': DSpaceJSPUIParser,
            'DSpaceAngularParser': DSpaceAngularParser,
            'USPParser': USPParser,
            'UcsParser': UcsParser,
            'UEPGParser': UEPGParser,
            'UnicapParser': UnicapParser,
            'UFPAParser': UFPAParser,
            'UnisaParser': UnisaParser,
            'UniceubParser': UniceubParser,
            'UfmtParser': UfmtParser,
            'UniforParser': UniforParser,
            'UnisinosParser': UnisinosParser,
            'UfopParser': UfopParser,
            'UFFParser': UFFParser,
            'FeiParser': FeiParser,
            'UfrnParser': UfrnParser,
            'CefetMgParser': CefetMgParser,
            'UpfParser': UpfParser,
            'SucupiraParser': SucupiraParser,
            'UdescParser': UdescParser,
            'SidUeceParser': SidUeceParser,
            'FecapParser': FecapParser,
            'UtfprParser': UTFPRParser
        }

        # Carrega o mapeamento do JSON
        self.domain_map = self._load_config()

    def _load_config(self):
        """Lê o arquivo JSON e retorna o dicionário de mapeamentos."""
        if not os.path.exists(self.config_file):
            print(f"Aviso: Arquivo de configuração '{self.config_file}' não encontrado.")
            return {}
            
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("mappings", {})
        except Exception as e:
            print(f"Erro ao ler configuração de parsers: {e}")
            return {}

    def get_parser(self, url, html_content=None):
        if not url: return self._default
        
        from urllib.parse import urlparse
        domain = urlparse(url).netloc.lower()
        
        # 1. Tenta encontrar o parser pelo domínio no JSON
        parser_class_name = None
        
        # Busca exata
        if domain in self.domain_map:
            parser_class_name = self.domain_map[domain]
        else:
            # Busca por sufixo (ex: .ufrn.br)
            for key_domain, p_name in self.domain_map.items():
                if key_domain.startswith('.'):
                    if domain.endswith(key_domain):
                        parser_class_name = p_name
                        break
                elif key_domain in domain: # Fallback para substrings
                     parser_class_name = p_name
                     break
        
        # Se encontrou no JSON e a classe existe, instancia
        if parser_class_name and parser_class_name in self.available_parsers:
            return self.available_parsers[parser_class_name]()

        # 2. Detecção Genérica (Fallback se não estiver no JSON)
        if html_content:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            html_lower = html_content.lower()

            if "vufind" in html_lower or "bdtd.ibict.br" in domain:
                if "search/results" in url.lower() or soup.select('.result'):
                    return VufindParser()
                else:
                    return BDTDParser() 

            # DSpace 7/Angular
            if soup.find('ds-app') or soup.find('ds-root') or "dspace-angular" in html_lower:
                return DSpaceAngularParser(sigla="DSpace7", universidade="Não identificada")

            # DSpace JSPUI / XMLUI genérico
            if (soup.find('div', id='ds-main') or 
                len(soup.find_all('meta', attrs={'name': lambda x: x and x.startswith('DC.')})) > 3):
                return DSpaceJSPUIParser(sigla="DSpace", universidade="Não identificada")

        return self._default