import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class UEPGParser(BaseParser):
    def __init__(self):
        # Define fixo, pois este parser é exclusivo da UEPG
        super().__init__(sigla="UEPG", universidade="Universidade Estadual de Ponta Grossa")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("UEPG: Analisando estrutura específica...")

        # --- 1. EXTRAÇÃO DO PROGRAMA ---
        try:
            found_program = None
            
            # Estratégia Principal: Campo Citation (Onde a UEPG coloca o programa)
            # Ex: "... 2024. Dissertação (Mestrado Profissional em Direito) ..."
            labels = [r'Citation', r'Citação', r'Referência', r'bibliographicCitation']
            for lbl in labels:
                # Procura a label na tabela
                label_td = soup.find('td', class_='metadataFieldLabel', string=re.compile(lbl, re.IGNORECASE))
                if label_td:
                    value_td = label_td.find_next_sibling('td', class_='metadataFieldValue')
                    if value_td:
                        text = value_td.get_text(strip=True)
                        # Regex para capturar o conteúdo dentro dos parênteses após Dissertação/Tese
                        match = re.search(r'(?:Dissertação|Tese)\s*\(([^)]+)\)', text, re.IGNORECASE)
                        if match:
                            found_program = match.group(1) # Pega "Mestrado Profissional em Direito"
                            break

            # Limpeza do nome encontrado (Remove "Mestrado Profissional em", etc)
            if found_program:
                clean_name = re.sub(
                    r'^(?:Programa de |)(?:Pós-Graduação(?: Interdisciplinar)?|Mestrado|Doutorado)(?:\s+(?:Profissional|Acadêmico))?(?: em| no| na)?\s*', 
                    '', found_program, flags=re.IGNORECASE
                )
                data['programa'] = clean_name.strip()
                if on_progress: on_progress(f"UEPG: Programa identificado via Citação: {data['programa']}")

            # Estratégia Fallback (Breadcrumbs/Meta) caso a Citação falhe
            else:
                self._fallback_program_extraction(soup, data, on_progress)

        except Exception as e:
            if on_progress: on_progress(f"UEPG: Erro ao extrair programa: {str(e)[:20]}")

        # --- 2. EXTRAÇÃO DO PDF ---
        data['link_pdf'] = self._extract_pdf(soup, url, on_progress)

        return data

    def _fallback_program_extraction(self, soup, data, on_progress):
        # Tenta Breadcrumbs
        crumbs = soup.select('ul.breadcrumb li a, ol.breadcrumb li a, .breadcrumb a')
        for crumb in crumbs:
            text = crumb.get_text(strip=True)
            if "Programa de Pós" in text:
                clean_name = re.sub(r'Programa de Pós\s*[-–]?\s*Graduação (em|no|na)\s*', '', text, flags=re.IGNORECASE)
                clean_name = re.sub(r'\s+(Mestrado|Doutorado).*$', '', clean_name, flags=re.IGNORECASE)
                data['programa'] = clean_name.strip()
                if on_progress: on_progress(f"UEPG: Programa (Breadcrumb): {data['programa']}")
                return

    def _extract_pdf(self, soup, base_url, on_progress):
        try:
            # Tenta meta tag primeiro
            pdf_meta = soup.find('meta', attrs={'name': 'citation_pdf_url'})
            if pdf_meta: return pdf_meta.get('content')
            
            # Tenta links bitstream
            link_tag = soup.find('a', href=lambda h: h and 'bitstream' in h and h.lower().endswith('.pdf'))
            if link_tag: return urljoin(base_url, link_tag['href'])
            
            return '-'
        except: return '-'