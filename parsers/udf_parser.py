import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.dspace_angular import DSpaceAngularParser

class UDFParser(DSpaceAngularParser):
    def __init__(self):
        # Define os dados institucionais fixos para a UDF
        super().__init__(sigla="UDF", universidade="Centro Universitário do Distrito Federal")

    def _check_dynamic_context(self, soup, on_progress=None):
        """Garante que a sigla UDF permaneça fixa, independente da versão do DSpace."""
        self.sigla = "UDF"
        self.universidade = "Centro Universitário do Distrito Federal"

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Extração robusta compatível com DSpace clássico e DSpace 8.2 Angular.
        """
        self.sigla = "UDF"
        self.universidade = "Centro Universitário do Distrito Federal"

        # 1. Tenta a extração padrão da classe pai (Angular/DSpace 7+)
        # Ela resolve a meta tag 'citation_pdf_url' que está presente no seu HTML
        data = super().extract_pure_soup(html_content, url, on_progress)

        # 2. Refinamento específico para a estrutura do DSpace 8.2 da UDF
        soup = BeautifulSoup(html_content, 'html.parser')

        # --- EXTRAÇÃO DO PROGRAMA ---
        if data['programa'] == '-':
            # Estratégia A: Componente de Coleções do Angular 8.2
            coll_tag = soup.select_one('ds-item-page-collections a')
            if coll_tag:
                data['programa'] = self._clean_program_name(coll_tag.get_text(strip=True))
            
            # Estratégia B: Breadcrumbs (Trilha de Navegação)
            if data['programa'] == '-':
                breads = soup.select('li.breadcrumb-item a')
                for b in reversed(breads):
                    txt = b.get_text(strip=True)
                    # O programa na UDF geralmente contém "Mestrado" ou "Direito"
                    if any(x in txt.upper() for x in ["MESTRADO", "DOUTORADO", "PROGRAMA"]):
                        data['programa'] = self._clean_program_name(txt)
                        break

        # --- EXTRAÇÃO DO PDF ---
        if data['link_pdf'] == '-':
            # No DSpace 8, o link pode estar no componente de download ou metatags
            pdf_link = soup.find('a', href=re.compile(r'/bitstreams/.*|/download$', re.I))
            if pdf_link:
                data['link_pdf'] = urljoin(url, pdf_link['href'])

        # 3. Força a sigla no dicionário final (evita que o GenericParser sobrescreva)
        data['sigla'] = "UDF"
        data['universidade'] = "Centro Universitário do Distrito Federal"
        
        return data

    def _clean_program_name(self, raw):
        """Limpa o nome removendo a sigla (UDF) e termos acadêmicos."""
        # Remove o sufixo "(UDF)" que o repositório coloca no nome das coleções
        name = re.sub(r'\(UDF\)', '', raw, flags=re.IGNORECASE).strip()
        # Usa a lógica de limpeza da classe pai para remover "Mestrado em...", etc.
        return super()._clean_program_name(name)