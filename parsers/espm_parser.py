from parsers.dspace_jspui import DSpaceJSPUIParser

class EspmParser(DSpaceJSPUIParser):
    def __init__(self):
        super().__init__(sigla="ESPM", universidade="Escola Superior de Propaganda e Marketing")

    # Não é necessário sobrescrever _find_program, pois a ESPM usa o padrão DC.publisher.program
    # que o DSpaceJSPUIParser já suporta.