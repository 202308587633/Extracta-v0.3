import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

class ScraperModel:
    def fetch_html(self, url):
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            raise Exception(f"Erro ao acessar: {e}")

    def extract_search_results(self, html_content, base_url=""):
        soup = BeautifulSoup(html_content, 'html.parser')
        results = []

        for item in soup.select('.result.card-results'):
            data = {}
            
            title_tag = item.select_one('.title.getFull')
            if title_tag:
                data['title'] = title_tag.get_text(strip=True)
                href = title_tag.get('href', '')
                if href.startswith('/'):
                    if base_url:
                        data['search_link'] = urljoin(base_url, href)
                    else:
                        data['search_link'] = href
                else:
                    data['search_link'] = href
            else:
                data['title'] = "Título não encontrado"
                data['search_link'] = ""

            author_tag = item.select_one('.author a')
            data['author'] = author_tag.get_text(strip=True) if author_tag else "Autor desconhecido"

            repo_tag = item.select_one('.link a.fulltext')
            data['repo_link'] = repo_tag.get('href', '') if repo_tag else ""

            results.append(data)
            
        return results