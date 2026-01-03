from urllib.parse import urlparse

class BaseViewModel:
    def __init__(self, system_repo, view=None):
        self.sys_repo = system_repo
        self.view = view 

    def _log(self, message, color="white"):
        try: 
            if self.sys_repo:
                self.sys_repo.log_event(message)
        except Exception as e:
            print(f"Erro ao salvar log no banco: {e}")

        if self.view:
            self.view.after_thread_safe(lambda: self.view.update_status(message, color))
        else:
            print(f"[{color.upper()}] {message}")

    def _update_source_status(self, url, status):
        root = self._extract_root(url)
        if root and self.sys_repo:
            self.sys_repo.update_source_status(root, status)

    def _check_source_allowed(self, url):
        if self.sys_repo:
            return self.sys_repo.is_source_allowed(url)
        return True
    
    def _extract_root(self, url):
        """
        Extrai a raiz da URL (Esquema + Domínio) para corresponder
        exatamente à lógica do SystemRepository.
        Ex: https://repositorio.ufpa.br/handle/123 -> https://repositorio.ufpa.br
        """
        try: 
            parsed = urlparse(url)
            # CORREÇÃO: Inclui o scheme (http/https) para bater com a chave no banco
            return f"{parsed.scheme}://{parsed.netloc}"
        except: 
            return ""
