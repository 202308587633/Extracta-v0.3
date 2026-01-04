import json
import re
from bs4 import BeautifulSoup
from parsers.base_parser import BaseParser
from urllib.parse import urljoin

class UnijuiParser(BaseParser):
    def __init__(self):
        super().__init__(sigla="UNIJUÍ", universidade="Universidade Regional do Noroeste do Estado do Rio Grande do Sul")

    def extract(self, html_content, base_url, on_progress=None):
        soup = BeautifulSoup(html_content, 'html.parser')
        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("UNIJUÍ (DSpace Angular): Analisando estado da aplicação...")

        script_tag = soup.find('script', id='dspace-angular-state')
        if script_tag:
            try:
                raw_json = script_tag.string.replace('&q;', '"')
                state = json.loads(raw_json)
                cache = state.get('NGRX_STATE', {}).get('core', {}).get('cache/object', {})

                # 1. Tenta encontrar o programa através das Comunidades/Coleções
                # A UNIJUÍ estrutura bem: Comunidade (Programa) -> Coleção (Curso/Nível)
                for key, entry in cache.items():
                    obj_data = entry.get('data', {})
                    if obj_data.get('type') == 'community':
                        name = obj_data.get('_name', '')
                        if "PROGRAMA DE PÓS-GRADUAÇÃO" in name.upper():
                            # Remove "PROGRAMA DE PÓS-GRADUAÇÃO EM " para ficar só a área
                            clean_name = re.sub(r'PROGRAMA DE PÓS-GRADUAÇÃO EM\s+', '', name, flags=re.IGNORECASE)
                            data['programa'] = clean_name.strip()
                            break
                    
                    # Fallback: Tenta achar na coleção se a comunidade falhar
                    if data['programa'] == '-' and obj_data.get('type') == 'collection':
                         name = obj_data.get('_name', '')
                         # Ex: "Doutorado em Fitotecnia" -> Fitotecnia
                         if "Mestrado em" in name or "Doutorado em" in name:
                             clean_name = re.sub(r'(Mestrado|Doutorado) em\s+', '', name, flags=re.IGNORECASE)
                             data['programa'] = clean_name.strip()

            except Exception as e:
                if on_progress: on_progress(f"Erro ao ler JSON da UNIJUÍ: {e}")

        # 2. PDF
        meta_pdf = soup.find('meta', attrs={'name': 'citation_pdf_url'})
        if meta_pdf:
            data['link_pdf'] = meta_pdf.get('content')

        return data