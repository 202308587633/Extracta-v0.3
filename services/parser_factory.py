from parsers.unifg_parser import UNIFGParser
from parsers.generic_parser import GenericParser
from parsers.ufop_parser import UfopParser
from parsers.ufms_parser import UFMSParser
from parsers.ufscar_parser import UFSCARParser
from parsers.ufrrj_parser import UFRRJParser
from parsers.ufn_parser import UFNParser
from parsers.unioeste_parser import UNIOESTEParser
from parsers.utfpr_parser import UTFPRParser
from parsers.ufersa_parser import UFERSAParser
from parsers.ucsal_parser import UCSALParser
from parsers.unipampa_parser import UNIPAMPAParser
from parsers.fgv_parser import FGVParser
from parsers.unisantos_parser import UNISANTOSParser
from parsers.unifal_parser import UNIFALParser
from parsers.fdv_parser import FDVParser
from parsers.uninove_parser import UninoveParser
from parsers.usp_parser import USPParser
from parsers.ufgd_parser import UFGDParser
from parsers.uff_parser import UFFParser
from parsers.pucgoias_parser import PUCGOIASParser
from parsers.ufrr_parser import UFRRParser
from parsers.unifesp_parser import UNIFESPParser
from parsers.unifacs_parser import UNIFACSParser
from parsers.uel_parser import UelParser
from parsers.ifro_parser import IFROParser
from parsers.ufma_parser import UfmaParser 
from parsers.ufsc_parser import UfscParser
from parsers.ufg_parser import UfgParser
from parsers.ufpr_parser import UfprParser
from parsers.unisinos_parser import UnisinosParser
from parsers.ufpe_parser import UfpeParser
from parsers.ufpb_parser import UfpbParser
from parsers.ufjf_parser import UfjfParser
from parsers.ufrgs_parser import UfrgsParser
from parsers.unb_parser import UnbParser
from parsers.ucb_parser import UcbParser
from parsers.upf_parser import UpfParser
from parsers.ufu_parser import UfuParser
from parsers.ucs_parser import UcsParser
from parsers.ufba_parser import UfbaParser
from parsers.fiocruz_parser import FiocruzParser
from parsers.unicap_parser import UnicapParser
from parsers.pucsp_parser import PucspParser
from parsers.ufmg_parser import UfmgParser
from parsers.mackenzie_parser import MackenzieParser
from parsers.unicamp_parser import UnicampParser
from parsers.umesp_parser import UMESPParser    
from parsers.uenp_parser import UenpParser
from parsers.ufc_parser import UfcParser
from parsers.ufs_parser import UfsParser
from parsers.ufv_parser import UfvParser
from parsers.unicesumar_parser import UnicesumarParser
from parsers.uea_parser import UeaParser
from parsers.unesp_parser import UnespParser
from parsers.ufsm_parser import UfsmParser
from parsers.uepb_parser import UepbParser
from parsers.pucrs_parser import PucrsParser
from parsers.unifor_parser import UniforParser
from parsers.ufpel_parser import UfpelParser
from parsers.uninter_parser import UninterParser
from parsers.ufrn_parser import UfrnParser
from parsers.ufes_parser import UfesParser
from parsers.enap_parser import ENAPParser
from parsers.pucrio_parser import PUCRioParser
from parsers.uem_parser import UEMParser
from parsers.ufmt_parser import UfmtParser


class ParserFactory:
    def __init__(self):
        self._default = GenericParser()
        # Mapeamento URL/Handle -> Classe
        self._map = {
            # --- Novos Mapeamentos Específicos (Incluindo Handles) ---
            'ri.ufmt.br': UfmtParser,
            'repositorio.unb.br': UnbParser,
            'hdl.handle.net/10482': UnbParser,    # Handle UnB
            'repositorio.ufmg.br': UfmgParser,
            'hdl.handle.net/1843': UfmgParser,     # Handle UFMG
            'repositorio.enap.gov.br': ENAPParser,
            'maxwell.vrac.puc-rio.br': PUCRioParser,
            'puc-rio.br': PUCRioParser,
            'uem.br': UEMParser,
            
            # --- Mapeamento para Sistema Sophia (Multi-instituição) ---
            'biblioteca.sophia.com.br/terminalri/9575': UniforParser, # UNIFOR
            'unifor.br': UniforParser,
            '.unicamp.br': UnicampParser,
            'hdl.handle.net/20.500.12733': UnicampParser, # Prefixo Handle da UNICAMP

            # --- Mapeamentos Existentes (Mantidos conforme seu código original) ---
            '.animaeducacao.com.br': UNIFGParser,
            '.ufes.br': UfesParser,
            '.ufrn.br': UfrnParser,
            '.uninter.com': UninterParser,
            '.ufpel.edu.br': UfpelParser,
            '.pucrs.br': PucrsParser,
            '.uepb.edu.br': UepbParser,
            '.ufsm.br': UfsmParser,
            '.unesp.br': UnespParser,
            '.uea.edu.br': UeaParser,
            '.unicesumar.edu.br': UnicesumarParser,
            '.ufv.br': UfvParser,
            '.ufs.br': UfsParser,
            '.ufc.br': UfcParser,
            '.uenp.edu.br': UenpParser,
            '.metodista.br': UMESPParser,
            '.mackenzie.br': MackenzieParser,
            '.ufmg.br': UfmgParser,
            '.pucsp.br': PucspParser,
            '.unicap.br': UnicapParser,
            '.fiocruz.br': FiocruzParser,
            '.ufba.br': UfbaParser,
            '.ucs.br': UcsParser,
            '.ufu.br': UfuParser,
            '.upf.br': UpfParser,
            '.ucb.br': UcbParser,
            '.ufrgs.br': UfrgsParser,
            '.ufjf.br': UfjfParser,
            '.ufpb.br': UfpbParser,
            '.ufpe.br': UfpeParser,
            ".ufop.br": UfopParser,
            ".ufms.br": UFMSParser,
            ".ufscar.br": UFSCARParser,
            ".ufrrj.br": UFRRJParser,
            ".universidadefranciscana.edu.br": UFNParser,
            ".unioeste.br": UNIOESTEParser,
            ".utfpr.edu.br": UTFPRParser,
            ".ufersa.edu.br": UFERSAParser,
            ".ucsal.br": UCSALParser,
            ".unipampa.edu.br": UNIPAMPAParser,
            ".fgv.br": FGVParser,
            ".unisantos.br": UNISANTOSParser,
            ".unifal-mg.edu.br": UNIFALParser,
            ".fdv.br": FDVParser,
            "191.252.194.60": FDVParser,
            "/fdv/": FDVParser,
            ".uninove.br": UninoveParser,
            ".usp.br": USPParser,
            ".ufgd.edu.br": UFGDParser,
            ".uff.br": UFFParser,
            ".riuff": UFFParser,
            ".pucgoias.edu.br": PUCGOIASParser,
            ".ufrr.br": UFRRParser,            
            ".unifesp.br": UNIFESPParser,
            ".hdl.handle.net/11600": UNIFESPParser,
            ".deposita.ibict.br": UNIFACSParser,
            ".unifacs.br": UNIFACSParser,
            ".uel.br": UelParser,
            ".ifro.edu.br": IFROParser,
            '.ufma.br': UfmaParser,
            '.ufsc.br': UfscParser,            
            '.ufg.br': UfgParser,
            '.ufpr.br': UfprParser,
            '.repositorio.jesuita.org.br': UnisinosParser,
            '.unisinos.br': UnisinosParser,                        
        }

    def get_parser(self, url, html_content=None):
        """
        Seleciona o parser adequado. Prioriza o BDTDParser se o HTML for do buscador VuFind.
        """
        if not url: 
            return self._default
        
        url_lower = url.lower()
        html_lower = html_content.lower() if html_content else ""

        # PRIORIDADE: Detecção de Buscador (VuFind/BDTD)
        # Verifica se o HTML possui a marca do sistema VuFind ou se a URL é do IBICT
        if "vufind" in html_lower or "bdtd.ibict.br" in url_lower:
            from parsers.bdtd_parser import BDTDParser
            return BDTDParser()

        # Lógica para Repositórios Compartilhados (Cruzeiro do Sul / UDF / UNIPÊ)
        if "repositorio.cruzeirodosul.edu.br" in url_lower:
            if html_content:
                html_upper = html_content.upper()
                if "UNIPÊ" in html_upper or "JOÃO PESSOA" in html_upper:
                    from parsers.unipe_parser import UNIPEParser
                    return UNIPEParser()
                if "UDF" in html_upper or "DISTRITO FEDERAL" in html_upper:
                    from parsers.udf_parser import UDFParser
                    return UDFParser()
            return self._default

        # Lógica Padrão por Domínio/Handle
        for domain, parser_cls in self._map.items():
            if domain in url_lower:
                return parser_cls()
        
        return self._default    