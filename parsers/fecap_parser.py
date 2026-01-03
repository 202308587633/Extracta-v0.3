import re
from parsers.dspace_jspui import DSpaceJSPUIParser

class FecapParser(DSpaceJSPUIParser):
    def __init__(self):
        super().__init__(sigla="FECAP", universidade="Fundação Escola de Comércio Álvares Penteado")

    def _find_program(self, soup):
        """
        Estratégia para FECAP:
        1. Tenta extrair da meta tag DC.relation (Citação Bibliográfica)
           Ex: "... Dissertação (Mestrado em Ciências Contábeis) ..."
        2. Tenta extrair da tabela 'Aparece nas coleções'
        """
        
        # Estratégia 1: Regex na citação (Mais preciso para nível + curso)
        # Procura por tags DC.relation ou citation_reference
        meta_tags = soup.find_all('meta', attrs={'name': ['DC.relation', 'DCTERMS.bibliographicCitation']})
        for meta in meta_tags:
            content = meta.get('content', '')
            # Regex para capturar: (Mestrado em X) ou (Doutorado em Y)
            match = re.search(r'\((Mestrado|Doutorado)\s+(?:em|na|no)?\s*(.*?)\)', content, re.IGNORECASE)
            if match:
                nivel = match.group(1)
                curso = match.group(2).strip()
                return f"{nivel} em {curso}"

        # Estratégia 2: Analisar a linha "Aparece nas coleções" da tabela
        # A estrutura no HTML é: 
        # <td class="metadataFieldLabel">Aparece nas coleções:</td><td...> <a ...>Ciências Contábeis</a>
        for row in soup.find_all('tr'):
            cols = row.find_all('td')
            if len(cols) >= 2:
                label = cols[0].get_text(strip=True)
                if 'Aparece nas coleções' in label:
                    # Pega o texto do link na segunda coluna
                    link = cols[1].find('a')
                    if link:
                        program_name = link.get_text(strip=True)
                        # Se o nome for genérico, ignoramos, senão retornamos formatado
                        if program_name and len(program_name) > 3:
                            return f"Programa de Pós-Graduação em {program_name}"

        # Fallback para o comportamento padrão (que provavelmente pegaria "PPG1" ou falharia)
        return super()._find_program(soup)