import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class PUCRioParser(BaseParser):
    def __init__(self):
        # Sigla e nome identificados no HTML do repositório Maxwell
        super().__init__(sigla="PUC-RIO", universidade="Pontifícia Universidade Católica do Rio de Janeiro")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Extrai dados do repositório Maxwell da PUC-Rio.
        Ajustado para capturar o programa dentro de estruturas <pre> e links de PDF no seletor.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("PUC-RIO: Analisando estrutura Maxwell...")

        # --- 1. EXTRAÇÃO DO PROGRAMA (Ajustado para estrutura <pre> e textos do autor) ---
        try:
            found_program = None
            
            # O sistema Maxwell organiza os dados do autor em divs com esta classe
            author_divs = soup.find_all('div', class_='colecao_tematicas')
            
            for div in author_divs:
                # O uso de separator=' ' é vital para evitar que as linhas do <pre> se fundam
                text = div.get_text(separator=' ', strip=True)
                
                if "Programa de Pós-Graduação" in text:
                    # Regex para capturar o nome do programa ignorando preposições e limpando a universidade
                    match = re.search(r'Programa de Pós-Graduação\s+(?:em|no|na|de)?\s*([^\r\n]+)', text, re.IGNORECASE)
                    if match:
                        found_program = match.group(1).strip()
                        # Limpeza final: remove sufixos institucionais comuns no texto
                        found_program = re.sub(r'\s*-\s*PUC-Rio.*$', '', found_program, flags=re.IGNORECASE).strip()
                        break

            if found_program:
                data['programa'] = found_program
            else:
                # Fallback: tenta localizar link direto da coleção se o texto falhar
                prog_link = soup.find('a', href=re.compile(r'colecao\.php\?strSecao=pos'))
                if prog_link:
                    data['programa'] = prog_link.get_text(strip=True)

        except Exception as e:
            if on_progress: on_progress(f"PUC-RIO: Erro no Programa: {str(e)[:20]}")

        # --- 2. EXTRAÇÃO DO PDF (Ajustado para o select 'file' e links diretos) ---
        try:
            pdf_url = None
            
            # Estratégia A: Busca no seletor de arquivos (dropdown comum no Maxwell)
            file_select = soup.find('select', id='file')
            if file_select:
                # Procura por opções que contenham '.PDF' no valor
                for option in file_select.find_all('option'):
                    val = option.get('value', '')
                    if val.upper().endswith('.PDF'):
                        # No Maxwell, o PDF costuma estar numa subpasta com o ID da sequência
                        # Tentamos obter o nrSeq da URL original para montar o link
                        match_seq = re.search(r'nrSeq=(\d+)', url)
                        if match_seq:
                            nr_seq = match_seq.group(1)
                            pdf_url = f"https://www.maxwell.vrac.puc-rio.br/{nr_seq}/{val}"
                        break

            # Estratégia B: Metatag citation_pdf_url
            if not pdf_url:
                pdf_meta = soup.find('meta', attrs={'name': 'citation_pdf_url'})
                if pdf_meta:
                    pdf_url = pdf_meta.get('content')
            
            # Estratégia C: Links físicos na tabela de arquivos
            if not pdf_url:
                pdf_link = soup.find('a', href=re.compile(r'\.pdf$|db_get_arq\.php', re.I))
                if pdf_link:
                    pdf_url = pdf_link['href']

            if pdf_url:
                data['link_pdf'] = urljoin(url, pdf_url)
                if on_progress: on_progress("PUC-RIO: PDF localizado.")
            else:
                if on_progress: on_progress("PUC-RIO: PDF não encontrado.")

        except Exception as e:
            if on_progress: on_progress(f"PUC-RIO: Erro no PDF: {str(e)[:20]}")

        return data