import re
from bs4 import BeautifulSoup
from parsers.base_parser import BaseParser

class SucupiraParser(BaseParser):
    def __init__(self):
        # A sigla e nome serão dinâmicos, baseados no conteúdo da página
        super().__init__(sigla="SUCUPIRA", universidade="Plataforma Sucupira")

    def extract(self, html_content, base_url, on_progress=None):
        return self.extract_pure_soup(html_content, base_url, on_progress)

    def extract_pure_soup(self, html_content, url, on_progress=None):
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            'sigla': 'SUCUPIRA', # Valor padrão, tentaremos extrair a IES real
            'universidade': '-',
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("Processando página da Plataforma Sucupira...")

        # 1. Extração da Instituição (IES)
        # O Sucupira usa IDs bem definidos, o que é ótimo.
        ies_span = soup.find('span', id='ies')
        if ies_span:
            ies_text = ies_span.get_text(strip=True)
            data['universidade'] = ies_text
            # Tenta criar uma sigla baseada no nome da universidade (ex: UNIFESP)
            # Para simplificar, mantemos SUCUPIRA no parser, ou usamos a primeira palavra se for sigla
            parts = ies_text.split(' - ')
            if len(parts) > 1:
                data['sigla'] = parts[0] # Ex: "UFRN - ..." pegaria UFRN
            elif "UNIVERSIDADE" in ies_text.upper():
                 # Tenta pegar siglas comuns (Ex: UNIVERSIDADE FEDERAL DE SÃO PAULO -> UNIFESP é complexo fazer auto)
                 # Então mantemos o identificador de origem
                 data['sigla'] = "SUCUPIRA"

        # 2. Extração do Programa
        prog_span = soup.find('span', id='programa')
        if prog_span:
            raw_prog = prog_span.get_text(strip=True)
            # Remove o código do programa que vem entre parênteses
            # Ex: "Tecnologia... (33009015082P0)" -> "Tecnologia..."
            clean_prog = re.sub(r'\s*\(\d+[A-Z0-9]*\)', '', raw_prog)
            data['programa'] = clean_prog.strip()
            if on_progress: on_progress(f"Programa: {data['programa']}")

        # 3. Extração de PDF
        # O Sucupira nem sempre tem o PDF direto. Às vezes diz "Não existem produções associadas".
        # Vamos procurar genericamente por links que contenham "download" ou extensões .pdf
        # Mas neste HTML específico, não há link.
        
        # Procura na tabela de arquivos se existir
        # (Lógica genérica para tentar achar links de arquivo caso existam em outras páginas do Sucupira)
        for link in soup.find_all('a', href=True):
            href = link['href'].lower()
            if '.pdf' in href or 'download' in href:
                # Ignora links de css/js ou imagens
                if not any(x in href for x in ['.css', '.js', '.png', '.jpg', '.ico']):
                    # Reconstrói URL absoluta se necessário
                    if not link['href'].startswith('http'):
                        # Assumindo base do sucupira
                        data['link_pdf'] = "https://sucupira.capes.gov.br" + link['href']
                        break

        return data