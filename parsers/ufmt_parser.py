from parsers.dspace_jspui import DSpaceJSPUIParser

class UfmtParser(DSpaceJSPUIParser):
    def __init__(self):
        # Configuração da sigla e nome da universidade para a UFMT
        super().__init__(sigla="UFMT", universidade="Universidade Federal de Mato Grosso")

    # A classe pai DSpaceJSPUIParser já resolve automaticamente:
    # 1. Extração do Programa (busca o selo 'Programa:' na tabela de metadados)
    # 2. Limpeza do nome (remove 'Mestrado em...', 'Programa de Pós-Graduação em...')
    # 3. Localização do PDF (via meta citation_pdf_url ou links /bitstream/)