from urllib.parse import urljoin

class VufindParser:
    def parse(self, soup, base_url):
        results = []
        # Procura pelos blocos de resultado no HTML
        for item in soup.select('.result.card-results'):
            data = {}
            
            # Título e Link do buscador
            title_tag = item.select_one('.title.getFull')
            if title_tag:
                data['title'] = title_tag.get_text(" ", strip=True)
                href = title_tag.get('href', '')
                data['search_link'] = urljoin(base_url, href)
            else:
                data['title'] = "Título não encontrado"
                data['search_link'] = ""

            # Autor
            author_tag = item.select_one('.author a')
            data['author'] = author_tag.get_text(" ", strip=True) if author_tag else "Autor desconhecido"

            # Link do documento original
            repo_tag = item.select_one('.link a.fulltext')
            data['repo_link'] = repo_tag.get('href', '') if repo_tag else ""

            results.append(data)
        return results