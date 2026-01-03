from bs4 import BeautifulSoup
from urllib.parse import urljoin

class VufindParser:
    """
    Parser especializado nas páginas de resultados de busca do BDTD (Vufind).
    Retorna uma LISTA de dicionários.
    """
    
    def extract(self, html_content, base_url):
        """Método padrão chamado pelo HistoryViewModel."""
        soup = BeautifulSoup(html_content, 'html.parser')
        return self.parse(soup, base_url)

    def parse(self, soup, base_url):
        results = []
        # Seletores ajustados para o padrão BDTD / Vufind
        for item in soup.select('.result'):
            data = {}
            
            # Título e Link PPB
            title_tag = item.select_one('.title')
            if title_tag:
                data['title'] = title_tag.get_text(" ", strip=True)
                # Pega o link do título (href)
                link_tag = title_tag if title_tag.name == 'a' else title_tag.find('a')
                if link_tag:
                    data['ppb_link'] = urljoin(base_url, link_tag.get('href', ''))
                else:
                    data['ppb_link'] = ""
            else:
                data['title'] = "Título não encontrado"
                data['ppb_link'] = ""

            # Autor
            # Tenta diferentes seletores de autor comuns no Vufind
            author_tag = item.select_one('.author a') or item.select_one('.author')
            if author_tag:
                data['author'] = author_tag.get_text(" ", strip=True).replace("Por:", "").strip()
            else:
                data['author'] = "Autor desconhecido"

            # Link de Acesso ao Repositório (PPR)
            # Geralmente é um botão 'Texto completo' ou ícone
            repo_tag = item.select_one('.link a.fulltext') or item.select_one('a.icon-link')
            data['ppr_link'] = urljoin(base_url, repo_tag.get('href', '')) if repo_tag else "" 

            results.append(data)
            
        return results