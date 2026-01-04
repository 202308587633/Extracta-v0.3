import requests
import random
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

    def _iniciar_driver(self, headless=True):
        """Configura e inicia uma instância do Edge Driver com opção de visibilidade."""
        if not os.path.exists(self.driver_path):
            raise FileNotFoundError(f"Driver não encontrado em: {self.driver_path}")

        edge_options = Options()
        
        # Configurações de visibilidade
        if headless:
            edge_options.add_argument("--headless=new") # Modo headless moderno (menos detectável)
        else:
            edge_options.add_argument("--start-maximized")
            edge_options.add_argument("--disable-blink-features=AutomationControlled")
            edge_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            edge_options.add_experimental_option('useAutomationExtension', False)

        # Configurações comuns
        edge_options.add_argument("--guest")
        edge_options.add_argument("--disable-gpu")
        edge_options.add_argument("--no-sandbox")
        
        # User-Agent fixo ou rotativo (mantendo o robusto que você já tinha)
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0'
        edge_options.add_argument(f'user-agent={user_agent}')

        service = Service(self.driver_path)
        driver = webdriver.Edge(service=service, options=edge_options)

        # Script anti-detecção (aplica-se a ambos, mas essencial no modo visual)
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            """
        })

        return driver

    def _verificar_bloqueio(self, driver):
        """Verifica sinais comuns de WAF, Captcha ou bloqueios de IP."""
        try:
            page_source = driver.page_source.lower()
            title = driver.title.lower()
            
            termos_bloqueio = [
                "just a moment", "attention required", "security check", 
                "cloudflare", "human verification", "access denied", 
                "403 forbidden", "pardon our interruption", "too many requests"
            ]

            # Verifica título e conteúdo
            for termo in termos_bloqueio:
                if termo in title or (len(page_source) < 5000 and termo in page_source):
                    return True
            return False
        except:
            return False

    def _is_pdf(self, url):
        """
        Verifica se a URL aponta para um arquivo PDF.
        Tenta primeiro pelo cabeçalho HTTP (Content-Type) e depois pela extensão.
        """
        try:
            # Verifica pela extensão da URL primeiro (mais rápido)
            if url.lower().endswith('.pdf'):
                return True

            # Faz uma requisição HEAD (apenas cabeçalhos) para verificar o Content-Type
            # Timeout curto para não atrasar o processo
            response = requests.head(url, allow_redirects=True, timeout=5)
            content_type = response.headers.get('Content-Type', '').lower()
            
            if 'application/pdf' in content_type:
                return True
                
        except Exception:
            # Se a requisição falhar (ex: bloqueio), confia apenas na extensão
            pass
            
        return False

    def fetch_html(self, url):
        """
        Tenta obter o HTML. 
        1. Verifica se é PDF (se for, ignora).
        2. Tenta modo Headless (rápido).
        3. Se bloqueado, reinicia em modo Headed (simulação manual).
        """
        # --- VERIFICAÇÃO DE PDF ---
        if self._is_pdf(url):
            print(f"📄 URL identificada como PDF. Ignorando scrap: {url}")
            return None

        driver = None
        try:
            # --- TENTATIVA 1: Modo Automático/Silencioso ---
            driver = self._iniciar_driver(headless=True)
            print(f"🤖 Tentando acesso automático: {url}")
            driver.get(url)

            # Aguarda carregamento básico
            try:
                WebDriverWait(driver, 10).until(
                    lambda d: d.execute_script('return document.readyState') == 'complete'
                )
            except:
                pass

            # Verifica se foi bloqueado
            if self._verificar_bloqueio(driver):
                print("⚠️ Bloqueio detectado! Alternando para modo Simulação Manual...")
                driver.quit() # Fecha o navegador headless
                
                # --- TENTATIVA 2: Modo Simulação Manual ---
                driver = self._iniciar_driver(headless=False)
                print(f"👤 Tentando acesso manual (burlas ativas): {url}")
                driver.get(url)
                
                # Espera maior e aleatória para passar por desafios (Cloudflare Turnstile/JS)
                tempo_espera = random.uniform(5, 10)
                time.sleep(tempo_espera)

                # Opcional: Se houver captcha visual, o usuário pode intervir aqui
                try:
                    WebDriverWait(driver, 20).until(
                        lambda d: "just a moment" not in d.title.lower()
                    )
                except:
                    print("⚠️ Tempo limite aguardando resolução do desafio visual.")

            # Captura o HTML final
            html_content = driver.page_source
            return html_content

        except Exception as e:
            print(f"❌ Erro no Selenium: {e}")
            return None
            
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
