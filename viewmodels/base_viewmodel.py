from urllib.parse import urlparse

class BaseViewModel:
    def __init__(self, system_repo):
        self.sys_repo = system_repo

    def _log(self, message, color="white"):
        # Salva no banco e avisa a view
        try: self.sys_repo.log(message)
        except: pass
        # Assume que a View tem um método central de status ou log
        # Em uma arquitetura MVVM pura, usaríamos Observables/Events
        pass 

    def _extract_root(self, url):
        try: return urlparse(url).netloc.split(':')[0]
        except: return ""

    def _update_source_status(self, url, status):
        root = self._extract_root(url)
        if root: self.sys_repo.update_source_status(root, status)

    def _check_source_allowed(self, url):
        root = self._extract_root(url)
        return self.sys_repo.get_source_status(root)