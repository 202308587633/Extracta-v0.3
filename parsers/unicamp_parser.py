import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class UnicampParser(BaseParser):
    def __init__(self):
        super().__init__(sigla="UNICAMP", universidade="Universidade Estadual de Campinas")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        soup = BeautifulSoup(html_content, 'html.parser')
        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("UNICAMP: Analisando estrutura Sophia...")

        # --- 1. EXTRAÇÃO DO PROGRAMA ---
        try:
            # Estratégia A: Busca o link que contém a hierarquia completa da UNICAMP
            prog_link = soup.find('a', title=re.compile(r'Programa de Pós-Graduação', re.I))
            if prog_link:
                raw_text = prog_link.get_text(strip=True)
                # Remove a parte da Universidade e Instituto, mantendo o Programa
                clean_name = re.sub(r'^.*?(Programa de Pós-Graduação)', r'\1', raw_text)
                data['programa'] = clean_name.strip()
            
            # Estratégia B: Caso esteja numa nota de tese (comum no Sophia)
            if data['programa'] == '-':
                nota_label = soup.find('label', string=re.compile(r'Nota de dissertação', re.I))
                if nota_label:
                    p_value = nota_label.find_next('p', class_='texto-completo')
                    if p_value:
                        # Extrai o programa após o nome da universidade
                        match = re.search(r'Universidade Estadual de Campinas,\s*(.*)$', p_value.get_text(), re.I)
                        if match:
                            data['programa'] = match.group(1).strip()
        except Exception as e:
            if on_progress: on_progress(f"UNICAMP: Erro no Programa: {str(e)[:20]}")

        # --- 2. EXTRAÇÃO DO PDF ---
        try:
            # No Sophia, o link de download é um endpoint específico
            pdf_link = soup.find('a', href=re.compile(r'/Busca/Download', re.I))
            if pdf_link:
                # Importante: O link no Sophia/UNICAMP é relativo à raiz (ex: /Busca/Download...)
                data['link_pdf'] = urljoin(url, pdf_link['href'])
            
            # Fallback: Meta Tag citation_pdf_url
            if data['link_pdf'] == '-':
                meta_pdf = soup.find('meta', attrs={'name': 'citation_pdf_url'})
                if meta_pdf:
                    data['link_pdf'] = meta_pdf.get('content')
        except Exception as e:
            if on_progress: on_progress(f"UNICAMP: Erro no PDF: {str(e)[:20]}")

        return data