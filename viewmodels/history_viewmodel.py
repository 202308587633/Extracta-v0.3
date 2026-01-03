from urllib.parse import urlparse, parse_qs, unquote

class HistoryViewModel:
    def __init__(self, repository, view):
        self.repo = repository
        self.view = view

    def load_data(self):
        """Carrega e formata os dados para a tabela."""
        raw_items = self.repo.get_all()
        structured_items = []

        for item in raw_items:
            try:
                # Adapte os índices conforme seu SELECT no repository
                item_id, url, created_at = item[0], item[1], item[2]
                db_term = item[3] if len(item) > 3 else None
                db_year = item[4] if len(item) > 4 else None
                
                if db_term and db_year:
                    termo, ano = db_term, db_year
                    try: pagina = parse_qs(urlparse(url).query).get('page', ['1'])[0]
                    except: pagina = '1'
                else:
                    # Lógica de fallback para extração da URL
                    try:
                        parsed = urlparse(url)
                        params = parse_qs(parsed.query)
                        termo = unquote(params.get('lookfor0[]', params.get('lookfor', ['-']))[0]).replace('"', '')
                        ano = params.get('publishDatefrom', ['-'])[0]
                        pagina = params.get('page', ['1'])[0]
                    except:
                        termo, ano, pagina = "URL Personalizada", "-", "1"

                structured_items.append((item_id, termo, ano, pagina, created_at, url))
            except Exception as e:
                continue
        
        # Atualiza a View
        self.view.after_thread_safe(lambda: self.view.history_tab.update_table(structured_items))

    def delete_item(self, history_id):
        try:
            self.repo.delete(history_id)
            self.load_data() # Recarrega a lista
            return True, f"Registro {history_id} excluído."
        except Exception as e:
            return False, f"Erro ao excluir: {e}"