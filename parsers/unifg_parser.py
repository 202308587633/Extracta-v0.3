import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class UNIFGParser(BaseParser):
    def __init__(self):
        # Mantém a identificação original da instituição
        super().__init__(sigla="UNIFG", universidade="Centro Universitário FG")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Extrai dados do repositório da UNIFG (DSpace 9.1 - Rede Ânima).
        Otimizado para capturar Programa via Breadcrumbs e PDF via Meta Tags/Links UUID.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("UNIFG: A analisar estrutura DSpace 9...")

        # --- 1. EXTRAÇÃO DO PROGRAMA (Breadcrumbs ou Coleções) ---
        try:
            # No DSpace 9, o programa aparece nos breadcrumbs (penúltimo item)
            # Ex: Início > UNIFG (BA) > Teses e dissertações > Programa de Pós-Graduação em Direito
            breadcrumb_items = soup.select('li.breadcrumb-item')
            if breadcrumb_items and len(breadcrumb_items) >= 2:
                # O último é o título, o penúltimo costuma ser o programa/coleção
                prog_text = breadcrumb_items[-2].get_text(strip=True)
                if "Programa" in prog_text or "Pós-Graduação" in prog_text:
                    data['programa'] = prog_text

            # Alternativa: Busca na div de coleções caso o breadcrumb falhe
            if data['programa'] == '-':
                coll_link = soup.find('a', href=re.compile(r'/collections/'))
                if coll_link:
                    span = coll_link.find('span')
                    data['programa'] = span.get_text(strip=True) if span else coll_link.get_text(strip=True)

        except Exception as e:
            if on_progress: on_progress(f"UNIFG: Erro no programa: {str(e)[:20]}")

        # --- 2. EXTRAÇÃO DO PDF (Meta Tags ou Links de Bitstreams) ---
        try:
            pdf_url = None
            
            # Estratégia A: Meta Tag citation_pdf_url (Presente no seu HTML)
            # <meta name="citation_pdf_url" content="https://.../download">
            pdf_meta = soup.find('meta', attrs={'name': 'citation_pdf_url'})
            if pdf_meta and pdf_meta.get('content'):
                pdf_url = pdf_meta.get('content')
            
            # Estratégia B: Link físico na página (Padrão DSpace 9 com /bitstreams/)
            if not pdf_url:
                # Procura links que contenham '/bitstreams/' e terminem em '/download'
                pdf_link_tag = soup.find('a', href=re.compile(r'/bitstreams/.*/download'))
                if pdf_link_tag:
                    pdf_url = pdf_link_tag['href']

            if pdf_url:
                # Resolve a URL absoluta (importante se o link for relativo)
                data['link_pdf'] = urljoin(url, pdf_url)
                if on_progress: on_progress("UNIFG: Link do PDF extraído.")
            else:
                if on_progress: on_progress("UNIFG: PDF não localizado.")

        except Exception as e:
            if on_progress: on_progress(f"UNIFG: Erro no PDF: {str(e)[:20]}")

        return data