import asyncio
import aiohttp
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import urljoin, urlparse
import time
import logging
from typing import Dict, List, Optional, Any
import json

class WebScraper:
    def __init__(self):
        """Inicializar el web scraper"""
        self.session = None
        self.driver = None
        self.timeout = 30
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        
        # Configurar logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    async def _get_session(self):
        """Obtener sesión HTTP asíncrona"""
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers={'User-Agent': self.user_agent}
            )
        return self.session
    
    def _setup_selenium(self):
        """Configurar Selenium para casos complejos"""
        if self.driver is None:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument(f"--user-agent={self.user_agent}")
            chrome_options.add_argument("--window-size=1920,1080")
            
            try:
                self.driver = webdriver.Chrome(
                    service=webdriver.chrome.service.Service(ChromeDriverManager().install()),
                    options=chrome_options
                )
            except Exception as e:
                self.logger.error(f"Error configurando Selenium: {e}")
                return False
        
        return True
    
    async def scrape_url(self, url: str, use_selenium: bool = False) -> Dict[str, Any]:
        """
        Extraer contenido de una URL
        
        Args:
            url: URL a procesar
            use_selenium: Usar Selenium para JavaScript dinámico
            
        Returns:
            Diccionario con contenido extraído
        """
        try:
            self.logger.info(f"🔍 Extrayendo contenido de: {url}")
            
            if use_selenium:
                return await self._scrape_with_selenium(url)
            else:
                return await self._scrape_with_requests(url)
                
        except Exception as e:
            self.logger.error(f"❌ Error extrayendo {url}: {str(e)}")
            return {
                "url": url,
                "success": False,
                "error": str(e),
                "html": "",
                "text": "",
                "images": [],
                "metadata": {}
            }
    
    async def _scrape_with_requests(self, url: str) -> Dict[str, Any]:
        """Extraer contenido usando requests/aiohttp"""
        session = await self._get_session()
        
        try:
            async with session.get(url) as response:
                response.raise_for_status()
                html = await response.text()
                
                # Parsear HTML
                soup = BeautifulSoup(html, 'html.parser')
                
                # Extraer información
                result = {
                    "url": url,
                    "success": True,
                    "html": html,
                    "text": soup.get_text(separator=' ', strip=True),
                    "title": soup.title.string if soup.title else "",
                    "images": self._extract_images(soup, url),
                    "metadata": self._extract_metadata(soup),
                    "links": self._extract_links(soup, url),
                    "scripts": self._extract_scripts(soup),
                    "styles": self._extract_styles(soup)
                }
                
                self.logger.info(f"✅ Contenido extraído: {len(result['text'])} caracteres")
                return result
                
        except Exception as e:
            self.logger.error(f"Error con requests: {e}")
            # Intentar con Selenium como fallback
            return await self._scrape_with_selenium(url)
    
    async def _scrape_with_selenium(self, url: str) -> Dict[str, Any]:
        """Extraer contenido usando Selenium"""
        if not self._setup_selenium():
            raise Exception("No se pudo configurar Selenium")
        
        try:
            self.driver.get(url)
            
            # Esperar a que la página cargue
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Esperar un poco más para contenido dinámico
            time.sleep(3)
            
            # Obtener HTML
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extraer información
            result = {
                "url": url,
                "success": True,
                "html": html,
                "text": soup.get_text(separator=' ', strip=True),
                "title": soup.title.string if soup.title else "",
                "images": self._extract_images(soup, url),
                "metadata": self._extract_metadata(soup),
                "links": self._extract_links(soup, url),
                "scripts": self._extract_scripts(soup),
                "styles": self._extract_styles(soup),
                "selenium_used": True
            }
            
            self.logger.info(f"✅ Contenido extraído con Selenium: {len(result['text'])} caracteres")
            return result
            
        except Exception as e:
            self.logger.error(f"Error con Selenium: {e}")
            raise
    
    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """Extraer imágenes de la página"""
        images = []
        
        for img in soup.find_all('img'):
            src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
            if src:
                # Resolver URL relativa
                full_url = urljoin(base_url, src)
                
                images.append({
                    "src": full_url,
                    "alt": img.get('alt', ''),
                    "title": img.get('title', ''),
                    "width": img.get('width', ''),
                    "height": img.get('height', ''),
                    "class": ' '.join(img.get('class', []))
                })
        
        return images
    
    def _extract_metadata(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extraer metadatos de la página"""
        metadata = {}
        
        # Meta tags
        for meta in soup.find_all('meta'):
            name = meta.get('name') or meta.get('property')
            content = meta.get('content')
            if name and content:
                metadata[name] = content
        
        # Open Graph tags
        for og in soup.find_all('meta', property=lambda x: x and x.startswith('og:')):
            property_name = og.get('property')
            content = og.get('content')
            if property_name and content:
                metadata[property_name] = content
        
        return metadata
    
    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """Extraer enlaces de la página"""
        links = []
        
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if href:
                full_url = urljoin(base_url, href)
                
                links.append({
                    "url": full_url,
                    "text": link.get_text(strip=True),
                    "title": link.get('title', ''),
                    "rel": link.get('rel', [])
                })
        
        return links
    
    def _extract_scripts(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extraer scripts de la página"""
        scripts = []
        
        for script in soup.find_all('script'):
            src = script.get('src')
            if src:
                scripts.append({
                    "src": src,
                    "type": script.get('type', ''),
                    "content": script.get_text()[:200] + "..." if len(script.get_text()) > 200 else script.get_text()
                })
        
        return scripts
    
    def _extract_styles(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extraer estilos de la página"""
        styles = []
        
        for style in soup.find_all('link', rel='stylesheet'):
            href = style.get('href')
            if href:
                styles.append({
                    "href": href,
                    "media": style.get('media', ''),
                    "type": style.get('type', 'text/css')
                })
        
        return styles
    
    async def close(self):
        """Cerrar sesiones y drivers"""
        if self.session:
            await self.session.close()
            self.session = None
        
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def __del__(self):
        """Destructor para limpiar recursos"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass 