import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class UniforParser(BaseParser):
    def __init__(self):
        # Sigla e nome institucional conforme identificado nas meta tags do Sophia
        super().__init__(sigla="UNIFOR", universidade="Universidade de Fortaleza")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Extrai dados do repositório Sophia da UNIFOR.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("UNIFOR: Analisando metadados Sophia...")

        # --- 1. EXTRAÇÃO DO PROGRAMA ---
        try:
            # No Sophia, o programa geralmente está listado na seção de 'Autoria' 
            # com o rótulo 'Dissertação (mestrado)' ou 'Tese (doutorado)'
            autoria_section = soup.find('label', text=re.compile(r'Autoria', re.I))
            if autoria_section:
                # Procura o container pai e busca o texto associado ao nível acadêmico
                parent_div = autoria_section.find_parent('div', class_='form-group')
                if parent_div:
                    # Busca por blocos que contenham o nome da universidade e o programa
                    program_box = parent_div.find('a', title=re.compile(r'Programa de Pós-Graduação', re.I))
                    if program_box:
                        raw_text = program_box.get_text(strip=True)
                        # Limpa o nome da universidade do texto (ex: "Universidade de Fortaleza. ")
                        data['programa'] = raw_text.replace("Universidade de Fortaleza.", "").strip()

            # Fallback: Meta tag citation_dissertation_institution (menos específico, mas útil)
            if data['programa'] == '-':
                meta_inst = soup.find('meta', attrs={'name': 'citation_dissertation_institution'})
                if meta_inst:
                    data['programa'] = meta_inst.get('content', '-')

        except Exception as e:
            if on_progress: on_progress(f"UNIFOR: Erro no Programa: {str(e)[:20]}")

        # --- 2. EXTRAÇÃO DO LINK DO PDF ---
        try:
            pdf_url = None
            
            # Estratégia A: O Sophia costuma colocar o link real em um parágrafo de classe 'sites'
            url_p = soup.find('p', class_='sites')
            if url_p:
                pdf_link_tag = url_p.find('a', href=re.compile(r'/exibicao/'))
                if pdf_link_tag:
                    pdf_url = pdf_link_tag.get('href')

            # Estratégia B: Atributo citation_pdf_url (se disponível)
            if not pdf_url:
                pdf_meta = soup.find('meta', attrs={'name': 'citation_pdf_url'})
                if pdf_meta:
                    pdf_url = pdf_meta.get('content')

            if pdf_url:
                data['link_pdf'] = urljoin(url, pdf_url)
                if on_progress: on_progress("UNIFOR: Link do documento localizado.")
            else:
                if on_progress: on_progress("UNIFOR: PDF não encontrado.")

        except Exception as e:
            if on_progress: on_progress(f"UNIFOR: Erro no PDF: {str(e)[:20]}")

        return data