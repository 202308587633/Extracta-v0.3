import re
from bs4 import BeautifulSoup
from parsers.base_parser import BaseParser
from urllib.parse import urljoin

class SidUeceParser(BaseParser):
    def __init__(self):
        super().__init__(sigla="UECE", universidade="Universidade Estadual do Ceará")

    def extract(self, html_content, base_url, on_progress=None):
        return self.extract_pure_soup(html_content, base_url, on_progress)

    def extract_pure_soup(self, html_content, url, on_progress=None):
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("UECE (SidUece): Processando estrutura JSF/Bootstrap...")

        # 1. Extração de Metadados via Grid Bootstrap
        # A estrutura é:
        # <span class="col-lg-2"><h5>Rótulo:</h5></span>
        # <span class="col-lg-10"><h5>Valor</h5></span>
        
        labels = soup.find_all('span', class_='col-lg-2')
        
        for label_span in labels:
            label_text = label_span.get_text(strip=True).replace(':', '')
            
            # Encontra o próximo irmão que seja o container do valor (col-lg-10)
            value_span = label_span.find_next_sibling('span', class_='col-lg-10')
            if not value_span:
                continue
                
            value_text = value_span.get_text(strip=True)

            if 'Referência' in label_text:
                # Tenta extrair o programa da referência bibliográfica
                # Ex: "... Dissertação (Mestrado em Saúde) - Universidade ..."
                # Nota: No HTML fornecido, o programa parece genérico, mas tentamos capturar.
                match = re.search(r'\((Mestrado|Doutorado)(.*?)\)', value_text, re.IGNORECASE)
                if match:
                    nivel = match.group(1)
                    area = match.group(2).strip()
                    # Limpa conectivos comuns
                    area = re.sub(r'^(em|de|no|na)\s+', '', area, flags=re.IGNORECASE)
                    # Se a área for apenas "Acadêmico ou Profissional", fica genérico, 
                    # mas é o que temos disponível no texto.
                    if area:
                        data['programa'] = f"{nivel} em {area}"
                    else:
                        data['programa'] = f"{nivel}"
                
                # Se não achou na referência, verifica se há outro campo explícito (às vezes ocorre)
            
            # Mapeamento para log/debug (opcional)
            if 'Título' in label_text and on_progress:
                # O título não é salvo neste dicionário pois é responsabilidade do crawler principal,
                # mas podemos usar para validar se é a página certa.
                pass

        # 2. Extração de PDF (Tag Object)
        # <object type="application/pdf" data="/siduece/report;jsessionid=...?id=95365&amp;tipo=3" ...>
        obj_tag = soup.find('object', attrs={'type': 'application/pdf'})
        if obj_tag and obj_tag.get('data'):
            relative_link = obj_tag['data']
            data['link_pdf'] = urljoin(url, relative_link)

        return data