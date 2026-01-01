from parsers.dspace_jspui import DSpaceJSPUIParser

class UEMParser(DSpaceJSPUIParser):
    def __init__(self):
        # Configuração da sigla e nome institucional
        super().__init__(sigla="UEM", universidade="Universidade Estadual de Maringá")

    # Não precisas de reescrever o método extract_pure_soup, 
    # a menos que a UEM tenha uma particularidade única.
    # A classe pai já tratará de tudo usando as estratégias _find_program e _find_pdf.