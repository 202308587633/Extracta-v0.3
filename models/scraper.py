import os
import time
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support.ui import WebDriverWait
import config 

class ScraperModel:
    def __init__(self):
        self.timeout = getattr(config, 'REQUEST_TIMEOUT', 60) # Timeout maior para Selenium
        self.delay = getattr(config, 'DELAY_BETWEEN_REQUESTS', 1.0)
        
        # Caminho para o driver na raiz do projeto
        self.driver_path = os.path.join(os.getcwd(), "msedgedriver.exe")

    def _iniciar_driver(self):
        """Configura e inicia uma instância do Edge Driver."""
        if not os.path.exists(self.driver_path):
            raise FileNotFoundError(f"Driver não encontrado em: {self.driver_path}")

        edge_options = Options()
        
        # --- Configurações Anti-Detecção ---
        edge_options.add_argument("--disable-blink-features=AutomationControlled") 
        edge_options.add_argument("--start-maximized")
        edge_options.add_argument("--guest")
        
        # User-Agent robusto
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0'
        if hasattr(config, 'USER_AGENT') and config.USER_AGENT:
             user_agent = config.USER_AGENT
        edge_options.add_argument(f"user-agent={user_agent}")

        # Se quiser rodar escondido (sem interface), descomente a linha abaixo. 
        # NOTA: O Anubis pode detectar o modo headless antigo. Use =new para versões recentes.
        # edge_options.add_argument("--headless=new") 

        service = Service(executable_path=self.driver_path)
        driver = webdriver.Edge(service=service, options=edge_options)

        # CDP Command para remover a flag navigator.webdriver (CRUCIAL PARA ANUBIS)
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            """
        })

        return driver

    def fetch_html(self, url):
        """Abre o navegador, resolve o desafio e retorna o HTML."""
        driver = None
        try:
            driver = self._iniciar_driver()
            print(f"🕷️ Selenium (Edge) acessando: {url}")
            
            driver.get(url)

            # --- Estratégia de Espera Inteligente (Anubis) ---
            # Espera até que o título da página NÃO contenha "Making sure you're not a bot!"
            # Ou espera até 30 segundos
            try:
                WebDriverWait(driver, 30).until(
                    lambda d: "Making sure you're not a bot!" not in d.title
                )
                # Pequeno delay extra para garantir renderização de frameworks JS (Angular/React/Vue)
                time.sleep(2) 
            except:
                print("⚠️ Tempo limite excedido aguardando resolução do desafio.")

            # Captura o HTML final renderizado
            html_content = driver.page_source
            return html_content

        except Exception as e:
            print(f"❌ Erro no Selenium: {e}")
            return None
            
        finally:
            if driver:
                driver.quit() # Fecha o navegador para liberar memória