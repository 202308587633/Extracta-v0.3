from parsers.dspace_angular import DSpaceAngularParser

class UfmgParser(DSpaceAngularParser):
    def __init__(self):
        super().__init__(sigla="UFMG", universidade="Universidade Federal de Minas Gerais")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        self.sigla = "UFMG"
        data = super().extract_pure_soup(html_content, url, on_progress)
        
        # Garante que os campos institucionais não retornem vazios
        data['sigla'] = "UFMG"
        data['universidade'] = "Universidade Federal de Minas Gerais"
        return data
    
    def _check_dynamic_context(self, soup, on_progress=None):
        # Bloqueia a limpeza da sigla feita pela classe base
        self.sigla = "UFMG"
        self.universidade = "Universidade Federal de Minas Gerais"
