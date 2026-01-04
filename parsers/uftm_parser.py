from parsers.dspace_jspui import DSpaceJSPUIParser

class UftmParser(DSpaceJSPUIParser):
    def __init__(self):
        super().__init__(sigla="UFTM", universidade="Universidade Federal do Triângulo Mineiro")

    # O método _find_program do DSpaceJSPUIParser já busca DC.publisher.program
    # ou DC.publisher com "Programa de...".
    # Não precisamos sobrescrever se a estrutura for padrão.