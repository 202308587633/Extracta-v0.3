from urllib.parse import urlparse

class BaseViewModel:
    def __init__(self, system_repo, view=None):
        self.sys_repo = system_repo
        self.view = view # Referência opcional à interface para atualizar status

    def _log(self, message, color="white"):
        """
        Log Centralizado:
        1. Salva no banco de dados (tabela logs).
        2. Atualiza a barra de status na interface.
        3. Adiciona na aba 'Logs' da interface.
        """
        # 1. Salva no Banco
        try: 
            if self.sys_repo:
                self.sys_repo.log(message)
        except Exception as e:
            print(f"Erro ao salvar log no banco: {e}")

        # 2. Atualiza Interface (Status Bar + Aba Log)
        if self.view:
            # Garante que roda na thread principal da UI
            self.view.after_thread_safe(lambda: self.view.update_status(message, color))
        else:
            # Fallback para console se não tiver view (ex: testes)
            print(f"[{color.upper()}] {message}")

    def _extract_root(self, url):
        try: return urlparse(url).netloc.split(':')[0]
        except: return ""

    def _update_source_status(self, url, status):
        root = self._extract_root(url)
        if root and self.sys_repo: 
            self.sys_repo.update_source_status(root, status)

    def _check_source_allowed(self, url):
        root = self._extract_root(url)
        if self.sys_repo:
            return self.sys_repo.get_source_status(root)
        return True