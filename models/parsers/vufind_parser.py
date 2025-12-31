from urllib.parse import urljoin

class VufindParser:
    def parse(self, soup, base_url):
        results = []
        for item in soup.select('.result.card-results'):
            data = {}
            title_tag = item.select_one('.title.getFull')
            
            # Nome da Pesquisa e Link PPB
            if title_tag:
                data['title'] = title_tag.get_text(" ", strip=True)
                data['ppb_link'] = urljoin(base_url, title_tag.get('href', ''))
            else:
                data['title'] = "Título não encontrado"
                data['ppb_link'] = ""

            # Autor
            author_tag = item.select_one('.author a')
            data['author'] = author_tag.get_text(" ", strip=True) if author_tag else "Autor desconhecido"

            # Link de Acesso ao PDF (LAP)
            repo_tag = item.select_one('.link a.fulltext')
            data['ppr_link'] = repo_tag.get('href', '') if repo_tag else "" 

            results.append(data)
        return results
