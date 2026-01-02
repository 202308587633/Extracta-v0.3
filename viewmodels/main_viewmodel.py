import re
import time
import threading
from models.database import DatabaseModel
from models.scraper import ScraperModel
from models.parsers.vufind_parser import VufindParser
import config
import os
import tempfile
import webbrowser
from urllib.parse import urlparse, parse_qs, unquote

class MainViewModel: # Certifique-se de que o nome da classe está correto
    def scrape_specific_search_url(self, url):
        self._log(f"Iniciando scrap de busca: {url}", "yellow")
        thread = threading.Thread(target=self._run_specific_scraping_task, args=(url, 'buscador'))
        thread.start()

    def scrape_repository_url(self, url):
        """Inicia o scrap do link do repositório (PDF/Documento)"""
        self._log(f"Iniciando scrap do repositório: {url}", "yellow")
        thread = threading.Thread(target=self._run_specific_scraping_task, args=(url, 'repositorio'))
        thread.start()

    def _run_pagination_task(self, base_url, max_page):
        """Executa o DeepScrap de PLBs: percorre e salva todas as páginas de listagem na tabela 'plb'"""
        try:
            self._log(f"Iniciando DeepScrap de PLBs: total de {max_page} páginas.", "yellow")
            separator = "&" if "?" in base_url else "?"
            
            for i in range(2, max_page + 1):
                if "page=" in base_url:
                    current_url = re.sub(r'page=\d+', f'page={i}', base_url)
                else:
                    current_url = f"{base_url}{separator}page={i}"
                
                self._log(f"Atividade: Capturando PLB {i} de {max_page}...", "yellow")
                
                html = self.scraper.fetch_html(current_url)
                # Atualizado para usar a nova tabela 'plb'
                self.db.save_plb(current_url, html)
                
                time.sleep(1.5)
                
            self._log(f"Sucesso: DeepScrap concluído. {max_page} PLBs armazenadas.", "green")
            self.view.after_thread_safe(self.load_history_list)
        except Exception as e:
            self._log(f"Erro Crítico no DeepScrap de PLBs: {e}", "red")

    def load_history_details(self, history_id):
        """Busca conteúdo da tabela 'plb' e exibe na interface."""
        self.current_history_id = history_id
        # Agora o método retorna uma tupla, pegamos apenas o HTML (índice 1) para exibição
        _, html = self.db.get_plb_content(history_id) 
        
        self.view.after_thread_safe(lambda: self.view.history_tab.display_content(html))    

    def extract_data_command(self):
        """Extrai dados tratando possíveis falhas no banco ou no parser"""
        if not self.current_history_id: 
            self._log("Selecione uma PLB no histórico primeiro.", "yellow")
            return
        try:
            url, html = self.db.get_plb_content(self.current_history_id)
            if not html: 
                raise Exception("Aviso: Conteúdo da PLB está vazio ou indisponível.")

            self._log(f"Minerando dados em: {url}", "yellow")
            data = self.scraper.extract_data(html, VufindParser(), base_url=url)
            
            if data:
                self.db.save_pesquisas(data) 
                self._log(f"Sucesso: {len(data)} pesquisas salvas.", "green")
                
                all_results = self.db.get_all_pesquisas()
                self.view.after_thread_safe(lambda: self.view.results_tab.display_results(all_results))
                self.view.switch_to_results_tab()
            else:
                self._log("Nenhum dado científico encontrado.", "red")
        except Exception as e:
            self._log(str(e), "red")

    def open_plb_in_browser(self):
        """Abre a PLB (Página de Listagem) no navegador."""
        if not self.current_history_id:
            self._log("Selecione um item do histórico primeiro.", "yellow")
            return
        _, html = self.db.get_plb_content(self.current_history_id)
        self._open_html_string_in_browser(html)

    def open_ppb_browser_from_db(self, title, author):
        """Abre a PPB (Página de Pesquisa) no navegador."""
        html = self.db.get_extracted_html(title, author)
        self._open_html_string_in_browser(html)

    def on_tab_changed(self):
        """Atualiza o conteúdo baseado no nome exato da aba selecionada"""
        if not hasattr(self, 'selected_research'): return

        current_tab = self.view.tabview.get()
        title = self.selected_research["title"]
        author = self.selected_research["author"]

        # Sincronize estes nomes com os nomes usados no self.tabview.add() da MainView
        if current_tab == "Conteúdo PPB":
            html = self.db.get_extracted_html(title, author)
            if html:
                self.view.content_tab.display_html(html)
        
        elif current_tab == "Conteúdo PPR":
            html = self.db.get_ppr_html(title, author)
            if html:
                self.view.repo_tab.display_html(html)

    def _open_html_string_in_browser(self, html_content):
        """Método utilitário para abrir strings HTML no navegador."""
        if not html_content:
            self._log("Erro: Conteúdo HTML não disponível.", "red")
            return
        try:
            import tempfile, webbrowser
            with tempfile.NamedTemporaryFile('w', delete=False, suffix='.html', encoding='utf-8') as f:
                f.write(html_content)
                temp_path = f.name
            webbrowser.open(f"file://{temp_path}")
            self._log("PPR aberta no navegador com sucesso.", "green")
        except Exception as e:
            self._log(f"Erro ao abrir navegador: {e}", "red")

    def open_ppr_in_browser(self):
        """Recupera a PPR do banco e exibe no navegador."""
        if not hasattr(self, 'selected_research'):
            self._log("Selecione uma pesquisa nos resultados.", "yellow")
            return
        
        title = self.selected_research["title"]
        author = self.selected_research["author"]
        
        # Recupera o HTML da tabela ppr
        html = self.db.get_ppr_html(title, author)
        self._open_html_string_in_browser(html)

    def handle_result_selection(self, title, author):
        """Atualiza o estado das abas e injeta o conteúdo conforme a seleção na tabela."""
        self.selected_research = {"title": title, "author": author}
        
        # Busca a existência de conteúdo nas tabelas PPB e PPR
        html_ppb = self.db.get_extracted_html(title, author)
        html_ppr = self.db.get_ppr_html(title, author)

        # Habilita ou desabilita as abas conforme a existência de dados no banco
        self.view.set_tab_state("Conteúdo PPB", "normal" if html_ppb else "disabled")
        self.view.set_tab_state("Conteúdo PPR", "normal" if html_ppr else "disabled")
        
        # Força a atualização imediata caso o usuário já esteja na aba
        self.on_tab_changed()

    def delete_history_item(self):
        """Remove um item do histórico e limpa a visualização."""
        if not self.current_history_id: return
        try:
            self.db.delete_history(self.current_history_id)
            self._log(f"Atividade: Item {self.current_history_id} excluído.", "green")
            self.current_history_id = None
            self.view.after_thread_safe(lambda: self.view.history_tab.display_content(""))
            self.load_history_list()
        except Exception as e:
            self._log(f"Erro Crítico: {e}", "red")

    def _extract_meta_content(self, soup, meta_names):
        """Busca conteúdo em tags <meta name='...'>"""
        for name in meta_names:
            tag = soup.find('meta', attrs={'name': name})
            if not tag:
                tag = soup.find('meta', attrs={'name': name.lower()})
            if tag and tag.get('content'):
                return tag['content'].strip()
        return None

    def _find_meta_value(self, soup, names, filter_word=None):
        """Busca valor em meta tags."""
        for name in names:
            tags = soup.find_all('meta', attrs={'name': name})
            if not tags: # Tenta lowercase se não achar
                tags = soup.find_all('meta', attrs={'name': name.lower()})
                
            for tag in tags:
                content = tag.get('content', '')
                if filter_word:
                    if filter_word.lower() in content.lower():
                        return content
                else:
                    # Se não tem filtro, retorna o primeiro que não seja vazio
                    if content and len(content) > 3:
                        return content
        return None

    def _extract_from_dspace_angular(self, soup, keywords):
        """Extrai dados de estruturas DSpace 7+ (Header + Body divs)."""
        # Procura por headers que contenham as palavras-chave
        headers = soup.find_all(['h2', 'h3', 'h4', 'h5', 'h6'], class_=lambda x: x and 'header' in x)
        
        for header in headers:
            header_text = header.get_text().strip().lower()
            if any(k in header_text for k in keywords):
                # O valor geralmente está em uma div irmã ou próxima com class '...body'
                # Sobe para o pai e procura o body
                parent = header.find_parent()
                if parent:
                    body = parent.find(class_=lambda x: x and 'body' in x)
                    if body:
                        return body.get_text(" ", strip=True)
        return None

    def _extract_from_tables(self, soup, keywords):
        """Varre tabelas procurando chaves nas células de rótulo."""
        # Procura células que pareçam rótulos (terminam com : ou têm classe label)
        cells = soup.find_all(['td', 'th'])
        for cell in cells:
            text = cell.get_text(" ", strip=True).lower()
            # Verifica se contém a keyword e é curto o suficiente para ser um label (ex: "Programa:")
            if any(k in text for k in keywords) and len(text) < 50:
                # O valor é geralmente a próxima célula
                next_cell = cell.find_next_sibling(['td', 'th'])
                if next_cell:
                    return next_cell.get_text(" ", strip=True)
        return None

    def _extract_program_from_breadcrumbs(self, soup):
        """Tenta achar o programa em listas de navegação (ul/ol class breadcrumb)."""
        # Procura por qualquer lista que tenha 'breadcrumb' na classe ou id
        trails = soup.find_all(['ul', 'ol', 'nav'], class_=lambda x: x and 'breadcrumb' in x)
        
        for trail in trails:
            links = trail.find_all('li') # Itens da lista
            if not links:
                links = trail.find_all('a') # Ou links diretos
                
            # Geralmente o programa está no penúltimo ou antepenúltimo item
            # Ex: Home > Teses > Programa X > Item
            if len(links) >= 2:
                # Itera de trás para frente, ignorando o último (que é o título do item)
                for i in range(len(links)-2, -1, -1):
                    txt = links[i].get_text(strip=True)
                    # Validação heurística para ver se parece um programa
                    if ("programa" in txt.lower() or "mestrado" in txt.lower() or 
                        "doutorado" in txt.lower() or "pós-graduação" in txt.lower() or 
                        "direito" in txt.lower()): # Adicionado 'direito' para o caso Mackenzie
                        return txt
        return None

    def _infer_sigla(self, univ_nome):
        """Deduz a sigla a partir do nome da universidade."""
        if not univ_nome or univ_nome == "Não identificada": return "-"
        
        nome = univ_nome.upper()
        
        # 1. Mapa manual (Prioridade Alta)
        mapa = {
            "UNIVERSIDADE DE SÃO PAULO": "USP",
            "UNIVERSIDADE ESTADUAL PAULISTA": "UNESP",
            "UNIVERSIDADE ESTADUAL DE CAMPINAS": "UNICAMP",
            "UNIVERSIDADE FEDERAL DE SANTA CATARINA": "UFSC",
            "UNIVERSIDADE FEDERAL DE GOIÁS": "UFG", # Adicionado
            "UNIVERSIDADE FEDERAL DE MINAS GERAIS": "UFMG",
            "UNIVERSIDADE FEDERAL DO RIO DE JANEIRO": "UFRJ",
            "UNIVERSIDADE FEDERAL DO RIO GRANDE DO SUL": "UFRGS",
            "UNIVERSIDADE DE BRASÍLIA": "UnB",
            "UNIVERSIDADE ESTADUAL DA PARAÍBA": "UEPB", # Adicionado
            "UNIVERSIDADE PRESBITERIANA MACKENZIE": "MACKENZIE", # Adicionado
            "PONTIFÍCIA UNIVERSIDADE CATÓLICA": "PUC", # Genérico
            "FUNDAÇÃO GETULIO VARGAS": "FGV"
        }

    def extract_univ_data(self):
        """Extrai Sigla, Univ e Programa delegando para a ParserFactory."""
        if not hasattr(self, 'selected_research'): 
            self._log("Selecione uma pesquisa na tabela primeiro.", "yellow")
            return
        
        title = self.selected_research["title"]
        author = self.selected_research["author"]
        
        # Busca o HTML salvo no banco
        url, html = self.db.get_ppr_full_content(title, author)
        
        if html and url:
            try:
                # Importa a Factory
                from services.parser_factory import ParserFactory
                
                factory = ParserFactory()
                
                # A Factory analisa o HTML e devolve DSpaceParser ou VufindParser
                parser = factory.get_parser(url, html_content=html)
                
                self._log(f"Parser identificado: {parser.__class__.__name__}", "yellow")

                # O Parser faz todo o trabalho sujo
                data = parser.extract(html, url)
                
                # Recupera os dados retornados (com valores padrão se vazio)
                sigla = data.get('sigla', '-')
                univ = data.get('universidade', 'Não identificada')
                programa = data.get('programa', 'Não identificado')

                # Atualiza no banco
                self.db.update_univ_data(title, author, sigla, univ, programa)
                
                self._log(f"Sucesso: {sigla} | {programa[:30]}...", "green")
                
                # Atualiza a UI
                self.initialize_data()
                
            except Exception as e:
                self._log(f"Erro na extração: {e}", "red")
                print(f"Erro detalhado: {e}") # Debug
        else:
            self._log("Erro: Conteúdo PPR não encontrado (execute o scrap primeiro).", "red")

    def _update_source_ui(self, url, success):
        """Atualiza a aba de Fontes na interface"""
        root = self._extract_root_url(url)
        self.view.update_source_status(root, success)

    def __init__(self, view):
        self.view = view
        self.db = DatabaseModel(db_name=config.DB_NAME)
        self.scraper = ScraperModel()
        self.current_history_id = None

    def initialize_data(self):
        """Carrega dados iniciais: PLBs, Pesquisas e agora as FONTES salvas."""
        self.load_history_list()
        
        # 1. Carrega Fontes salvas e atualiza a aba
        try:
            sources = self.db.get_all_sources()
            for root, status in sources.items():
                # Atualiza a UI sem salvar no banco novamente (pois já veio de lá)
                self.view.update_source_status(root, status)
        except Exception as e:
            self._log(f"Erro ao carregar fontes: {e}", "red")

        # 2. Carrega Resultados
        try:
            saved_data = self.db.get_all_pesquisas() 
            if saved_data:
                self.view.after_thread_safe(lambda: self.view.results_tab.display_results(saved_data))
        except Exception as e:
            self._log(f"Erro ao carregar dados salvos: {e}", "red")

    def _extract_root_url(self, url):
        try:
            parsed = urlparse(url)
            # Retorna netloc (ex: repositorio.ucs.br) e remove porta se houver
            return parsed.netloc.split(':')[0]
        except:
            return "url-invalida"

    def _update_source_ui_and_db(self, url, success):
        """Atualiza a UI e Persiste o status no Banco."""
        root = self._extract_root_url(url)
        
        # 1. Salva no Banco
        self.db.save_source_status(root, success)
        
        # 2. Atualiza a UI
        self.view.update_source_status(root, success)

    def scrape_pending_pprs(self):
        """Inicia o processo de raspagem em lote."""
        pending = self.db.get_pending_ppr_records()
        if not pending:
            self._log("Todas as PPRs listadas já possuem HTML salvo.", "green")
            return

        self._log(f"Iniciando download em lote de {len(pending)} PPRs pendentes...", "yellow")
        thread = threading.Thread(target=self._run_batch_ppr_scraping, args=(pending,))
        thread.start()

    def _run_batch_ppr_scraping(self, pending_list):
        """
        Executa o download sequencial.
        REGRA: Só baixa se a raiz não estiver marcada como Falha (unchecked) na guia Fontes.
        """
        total = len(pending_list)
        success_count = 0
        skipped_count = 0
        
        for index, (pid, url) in enumerate(pending_list):
            root = self._extract_root_url(url)
            
            # --- VERIFICAÇÃO DE PERMISSÃO ---
            # Verifica no banco se essa raiz está permitida (True) ou bloqueada (False)
            is_allowed = self.db.get_source_status(root)
            
            if not is_allowed:
                self._log(f"Pulando {root} (Marcada como inativa/falha na guia Fontes).", "yellow")
                skipped_count += 1
                continue
            # -------------------------------

            try:
                self._log(f"Baixando ({index + 1}/{total}): {url}", "yellow")
                html = self.scraper.fetch_html(url)
                
                if html:
                    self.db.save_ppr_content(url, html)
                    success_count += 1
                    # Sucesso: Garante que está marcado como True
                    self._update_source_ui_and_db(url, True)
                else:
                    raise Exception("HTML vazio retornado")
                
                time.sleep(1.0) # Crawling educado
                
            except Exception as e:
                # FALHA NO DOWNLOAD
                self._log(f"Falha ao baixar {url}: {e}", "red")
                
                # REQUISITO: Desmarcar a caixa na guia Fontes
                # Isso bloqueará futuras tentativas para este domínio nesta execução e nas próximas
                self._update_source_ui_and_db(url, False) 
                
                # "Reiniciar o processo" = O loop continua, mas agora o get_source_status(root)
                # retornará False para as próximas URLs desse mesmo domínio, efetivamente pulando-as.

        self._log(f"Lote concluído! {success_count} baixados, {skipped_count} pulados.", "green")
        
        # Recarrega a tabela de resultados para mostrar se houve novos dados (opcional)
        self.initialize_data()
    
    def _log(self, message, color="white"):
        try:
            self.db.save_log(message)
        except:
            pass
        self.view.update_status(message, color)
    
    def _run_specific_scraping_task(self, url, doc_type='buscador'):
        try:
            html = self.scraper.fetch_html(url)
            if doc_type == 'buscador':
                self.db.save_ppb_content(url, html)
            else:
                self.db.save_ppr_content(url, html)
            
            self._update_source_ui_and_db(url, True)
            self.view.after_thread_safe(self.load_history_list)
            self._log(f"{doc_type.upper()} capturado.", "green")
        except Exception as e:
            self._update_source_ui_and_db(url, False)
            self._log(f"Erro em {doc_type}: {e}", "red")

    def toggle_source_manually(self, root_url, new_status):
        self.db.save_source_status(root_url, new_status)
        self._log(f"Fonte {root_url} alterada manualmente para {new_status}", "white")

    def batch_extract_univ_data(self):
        """
        Dispara a extração de metadados (Sigla/Univ/Programa) para 
        TODAS as PPRs que já têm HTML salvo no banco.
        """
        records = self.db.get_all_ppr_with_html()
        
        if not records:
            self._log("Nenhum HTML de PPR encontrado no banco para processar.", "yellow")
            return
            
        self._log(f"Iniciando extração de dados em lote para {len(records)} registros...", "yellow")
        
        # Executa em thread para não travar a interface
        threading.Thread(target=self._run_batch_extraction, args=(records,)).start()

    def _run_batch_extraction(self, records):
        # Importação tardia para evitar ciclos, se necessário
        from services.parser_factory import ParserFactory
        factory = ParserFactory()
        
        count = 0
        total = len(records)
        
        for index, (title, author, url, html) in enumerate(records):
            try:
                # 1. Identifica o parser correto para este HTML/URL
                parser = factory.get_parser(url, html_content=html)
                
                # 2. Extrai os dados
                data = parser.extract(html, url)
                
                sigla = data.get('sigla', '-')
                univ = data.get('universidade', 'Não identificada')
                programa = data.get('programa', 'Não identificado')
                
                # 3. Salva no banco
                self.db.update_univ_data(title, author, sigla, univ, programa)
                count += 1
                
                # Log de progresso a cada 5 itens para não poluir demais
                if index % 5 == 0:
                    self._log(f"Processando {index+1}/{total}: {sigla} - {programa[:20]}...", "white")
                    
            except Exception as e:
                # Não interrompe o lote por erro em um item, apenas loga
                print(f"Erro ao extrair {url}: {e}")

        self._log(f"Processamento concluído! Dados atualizados em {count}/{total} pesquisas.", "green")
        
        # Atualiza a tabela na interface
        self.initialize_data()

    def load_history_list(self):
        """
        Carrega o histórico e prepara os dados estruturados para a Tabela (Treeview).
        Prioriza 'search_term' e 'search_year' do banco. Se não existirem, faz parse da URL.
        """
        # O método get_plb_list agora deve retornar: (id, url, created_at, search_term, search_year)
        raw_items = self.db.get_plb_list() 
        structured_items = []

        for item in raw_items:
            # Desempacotamento seguro (garanta que o DatabaseModel retornará 5 itens)
            # Se o banco antigo retornar só 3, isso daria erro, mas assumimos que o banco foi migrado.
            try:
                item_id = item[0]
                url = item[1]
                created_at = item[2]
                db_term = item[3] if len(item) > 3 else None
                db_year = item[4] if len(item) > 4 else None
            except IndexError:
                # Fallback para caso o DB não tenha retornado as colunas novas ainda
                item_id, url, created_at = item[0], item[1], item[2]
                db_term, db_year = None, None

            # Lógica Híbrida: Banco > URL
            if db_term and db_year:
                termo = db_term
                ano = db_year
                # A página geralmente não é salva como metadado fixo, extraímos da URL
                try:
                    parsed = urlparse(url)
                    pagina = parse_qs(parsed.query).get('page', ['1'])[0]
                except:
                    pagina = '1'
            else:
                # Fallback: Extrair tudo da URL (para registros antigos)
                try:
                    parsed = urlparse(url)
                    params = parse_qs(parsed.query)
                    
                    termo_raw = params.get('lookfor0[]', params.get('lookfor', ['-']))[0]
                    termo = unquote(termo_raw).replace('"', '')
                    
                    ano = params.get('publishDatefrom', ['-'])[0]
                    pagina = params.get('page', ['1'])[0]
                except Exception:
                    termo = "URL Personalizada"
                    ano = "-"
                    pagina = "1"

            # Formata a data
            data_fmt = created_at
            
            # Adiciona à lista estruturada para a View
            structured_items.append((item_id, termo, ano, pagina, data_fmt, url))

        # Envia para a View
        self.view.after_thread_safe(lambda: self.view.history_tab.update_table(structured_items))

    def start_scraping_command(self):
        url = self.view.get_url_input()
        if not url: return
        
        # NOVO: Obtém o termo e ano selecionados na interface
        # (O método get_current_selection deve ter sido criado na MainView)
        term, year = None, None
        if hasattr(self.view, 'get_current_selection'):
            term, year = self.view.get_current_selection()
        
        self.view.toggle_button(False)
        
        # Passa term e year para a thread
        thread = threading.Thread(target=self._run_task, args=(url, term, year))
        thread.start()

    def _run_task(self, url, term=None, year=None):
        try:
            html = self.scraper.fetch_html(url)
            
            # NOVO: Passa term e year para o método save_plb
            # (Certifique-se que db.save_plb aceita esses argumentos)
            self.db.save_plb(url, html, term, year)
            
            self.view.after_thread_safe(lambda: self.view.home_tab.display_html(html))
            self.view.after_thread_safe(self.load_history_list)
            
            self._update_source_ui_and_db(url, True)
            self._log("PLB capturada e salva com sucesso.", "green")
        except Exception as e:
            self._update_source_ui_and_db(url, False)
            self._log(str(e), "red")
        finally:
            self.view.toggle_button(True)

    def check_pagination_and_scrape(self, history_id):
        try:
            # Recupera registro original para manter consistência do Termo/Ano
            # get_plb_by_id deve retornar (id, url, html, term, year)
            record = self.db.get_plb_by_id(history_id)
            if not record: return
            
            current_url = record[1]
            # Índices baseados na query SELECT do database.py
            current_term = record[3] if len(record) > 3 else None
            current_year = record[4] if len(record) > 4 else None
            
            # Calcula próxima página
            parsed = urlparse(current_url)
            params = parse_qs(parsed.query)
            current_page = int(params.get('page', ['1'])[0])
            next_page = current_page + 1
            params['page'] = [str(next_page)]
            
            from urllib.parse import urlencode, urlunparse
            new_query = urlencode(params, doseq=True)
            next_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))
            
            self._log(f"Buscando página {next_page}...", "yellow")
            
            self.view.toggle_button(False)
            
            # NOVO: Inicia thread repassando o termo e ano originais
            thread = threading.Thread(target=self._run_task, args=(next_url, current_term, current_year))
            thread.start()
            
        except Exception as e:
            self._log(f"Erro ao calcular paginação: {e}", "red")