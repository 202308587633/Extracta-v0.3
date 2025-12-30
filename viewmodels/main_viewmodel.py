# Adicione este import no topo
from models.parsers.vufind_parser import VufindParser

# Atualize apenas a função extract_data_command
def extract_data_command(self):
    if not self.current_history_id: return
    try:
        result = self.db.get_history_item(self.current_history_id)
        if not result: return
        url, html = result
        self._log("Extraindo dados com parser especializado...", "yellow")
        if not self.current_history_id: 
            self._log("Selecione um item do histórico.", "red") #
            return
        
        # Instancia o parser correto para este site
        parser = VufindParser()
        data = self.scraper.extract_data(html, parser, base_url=url)
        
        if not data:
            self._log("Nenhum dado encontrado.", "red")
        else:
            self._log(f"Sucesso! {len(data)} itens extraídos.", "green")
            self.view.display_extracted_results(data)
            self.view.switch_to_results_tab()
    except Exception as e:
        self._log(f"Erro na extração: {e}", "red")
