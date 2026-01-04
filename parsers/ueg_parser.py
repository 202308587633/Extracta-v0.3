from parsers.dspace_jspui import DSpaceJSPUIParser

class UegParser(DSpaceJSPUIParser):
    def __init__(self):
        super().__init__(sigla="UEG", universidade="Universidade Estadual de Goiás")

    # O método _find_program do DSpaceJSPUIParser já busca DC.publisher.program
    # que está presente neste HTML.
    # Mas podemos adicionar fallback para breadcrumbs ou links com classe 'program' 
    # caso mude a estrutura no futuro.