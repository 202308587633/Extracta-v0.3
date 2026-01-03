import json
import os
from parsers.generic_parser import GenericParser
from parsers.dspace_jspui import DSpaceJSPUIParser
from parsers.dspace_angular import DSpaceAngularParser
from parsers.bdtd_parser import BDTDParser

# Importe APENAS os parsers que possuem lógica customizada complexa
# (Exemplo: USPParser, VufindParser. Os simples podem ser removidos daqui)
from parsers.usp_parser import USPParser
from parsers.ucs_parser import UcsParser 
from models.parsers.vufind_parser import VufindParser

# Adicione outros imports de classes CUSTOMIZADAS se necessário (ex: UfrgsParser se tiver lógica única)

class ParserFactory:
    def __init__(self, config_filename="parsers_config.json"):
        self._default = GenericParser()
        
        # CORREÇÃO: Constrói o caminho absoluto baseado na localização deste arquivo
        # Isso garante que ele encontre o JSON dentro da pasta 'services'
        base_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(base_dir, config_filename)
        
        self.config_map = self._load_config(config_path)
        
        # Mapa de Parsers com lógica CUSTOMIZADA (prioridade alta)
        # Mantenha aqui apenas o que não for padrão DSpace
        self._custom_map = {
            '.usp.br': USPParser,
            '.ucs.br': UcsParser,
            # Se a UFRGS tiver lógica muito específica, mantenha aqui, senão use o JSON
            # 'lume.ufrgs.br': UfrgsParser 
        }

    def _load_config(self, path):
        """Carrega o JSON de configuração."""
        if not os.path.exists(path):
            print(f"Aviso: Arquivo de configuração {path} não encontrado.")
            return []
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("mappings", [])
        except Exception as e:
            print(f"Erro ao ler config de parsers: {e}")
            return []

    def get_parser(self, url, html_content=None):
        """
        Seleciona o parser adequado.
        Ordem:
        1. Custom Map (Classes Python específicas)
        2. Config Map (JSON - Boilerplate DSpace)
        3. Detecção Genérica (HTML)
        """
        if not url: 
            return self._default
        
        url_lower = url.lower()
        
        # --- 1. Verifica Parsers Customizados (Prioridade Máxima) ---
        for domain, parser_cls in self._custom_map.items():
            if domain in url_lower:
                return parser_cls()

        # --- 2. Verifica Configuração JSON (Parsers Padrão) ---
        for entry in self.config_map:
            if entry['key'] in url_lower:
                sigla = entry.get('sigla', '-')
                nome = entry.get('name', 'Universidade Identificada')
                tipo = entry.get('type', 'jspui')
                
                # Instancia a classe base correta com os dados do JSON
                if tipo == 'angular':
                    return DSpaceAngularParser(sigla=sigla, universidade=nome)
                else:
                    # Padrão JSPUI
                    return DSpaceJSPUIParser(sigla=sigla, universidade=nome)

        # --- Lógica de Repositórios Compartilhados (Cruzeiro do Sul etc) ---
        # (Mantém sua lógica existente aqui, se houver)
        
        # --- 3. Detecção Genérica baseada em HTML ---
        if html_content:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            html_lower = html_content.lower()

            # Detecção de Buscador
            if "vufind" in html_lower or "bdtd.ibict.br" in url_lower:
                return BDTDParser() # ou VufindParser

            # Detecção Inteligente DSpace
            if soup.find('ds-app') or soup.find('ds-root'):
                return DSpaceAngularParser(sigla="DSpace7", universidade="Não identificada")

            if (soup.find('div', id='ds-main') or 
                soup.find('div', id='aspect_artifactbrowser_ItemViewer_div_item-view') or
                len(soup.find_all('meta', attrs={'name': lambda x: x and x.startswith('DC.')})) > 3):
                
                return DSpaceJSPUIParser(sigla="DSpace", universidade="Não identificada")

        return self._default