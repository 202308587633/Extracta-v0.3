from models.parsers.base_parser import BaseParser
from urllib.parse import urljoin

class VufindParser(BaseParser):
    def parse(self, soup, base_url):
        results = []
        for item in soup.select('.result.card-results'):
            data = {}
            title_tag = item.select_one('.title.getFull')
            if title_tag:
                data['title'] = title_tag.get_text(strip=True)
                href = title_tag.get('href', '')
                data['search_link'] = urljoin(base_url, href)
            else:
                data['title'] = "Título não encontrado"
                data['search_link'] = ""

            author_tag = item.select_one('.author a')
            data['author'] = author_tag.get_text(strip=True) if author_tag else "Autor desconhecido"

            repo_tag = item.select_one('.link a.fulltext')
            data['repo_link'] = repo_tag.get('href', '') if repo_tag else ""
            results.append(data)
        return results