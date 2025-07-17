import re
import json
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup, Tag
from urllib.parse import urljoin, urlparse
import logging

class AdDetector:
    def __init__(self):
        """Inicializar detector de anuncios"""
        self.logger = logging.getLogger(__name__)
        
        # Patrones para detectar anuncios
        self.ad_patterns = {
            # Selectores CSS comunes para anuncios
            'selectors': [
                '[class*="ad"]',
                '[class*="advertisement"]',
                '[class*="banner"]',
                '[id*="ad"]',
                '[id*="banner"]',
                '[class*="sponsored"]',
                '[class*="promo"]',
                '[class*="commercial"]',
                '[data-ad]',
                '[data-advertisement]',
                '[data-sponsor]',
                '.adsbygoogle',
                '.advertisement',
                '.ad-banner',
                '.ad-container',
                '.ad-wrapper',
                '.advertisement-container',
                '.sponsored-content',
                '.promotional-content',
                '.commercial-content'
            ],
            
            # Palabras clave relacionadas con anuncios
            'keywords': [
                'advertisement', 'ad', 'sponsored', 'promoted', 'banner',
                'commercial', 'promo', 'sponsor', 'advert', 'marketing',
                'publicidad', 'anuncio', 'patrocinado', 'promocionado'
            ],
            
            # Servicios de anuncios conocidos
            'ad_services': [
                'googleadservices.com',
                'googlesyndication.com',
                'doubleclick.net',
                'facebook.com/tr',
                'amazon-adsystem.com',
                'adnxs.com',
                'adsystem.com',
                'adtech.com',
                'advertising.com',
                'adform.net',
                'criteo.com',
                'taboola.com',
                'outbrain.com',
                'adroll.com',
                'adsrvr.org'
            ]
        }
        
        # Patrones específicos para gambling
        self.gambling_patterns = {
            'keywords': [
                'casino', 'poker', 'bet', 'gambling', 'slot', 'roulette',
                'blackjack', 'baccarat', 'craps', 'lottery', 'bingo',
                'sports betting', 'online casino', 'real money',
                'casino online', 'apuestas', 'juegos de azar',
                'tragaperras', 'ruleta', 'póker', 'bingo online'
            ],
            
            'domains': [
                'casino', 'poker', 'bet', 'gambling', 'slot',
                'roulette', 'blackjack', 'baccarat', 'lottery',
                'bingo', 'apuestas', 'azar', 'casino'
            ]
        }
    
    async def detect_ads(self, page_content: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detectar anuncios en el contenido de la página
        
        Args:
            page_content: Contenido extraído de la página
            
        Returns:
            Lista de anuncios detectados
        """
        try:
            if not page_content.get('success', False):
                self.logger.warning("Contenido de página no válido")
                return []
            
            html = page_content.get('html', '')
            if not html:
                return []
            
            soup = BeautifulSoup(html, 'html.parser')
            ads = []
            
            # 1. Detectar por selectores CSS
            ads.extend(self._detect_by_selectors(soup))
            
            # 2. Detectar por patrones de texto
            ads.extend(self._detect_by_text_patterns(soup))
            
            # 3. Detectar por scripts de anuncios
            ads.extend(self._detect_by_scripts(page_content.get('scripts', [])))
            
            # 4. Detectar por imágenes con patrones de anuncios
            ads.extend(self._detect_by_images(page_content.get('images', [])))
            
            # 5. Filtrar duplicados y validar
            ads = self._filter_and_validate_ads(ads)
            
            self.logger.info(f"✅ Detectados {len(ads)} anuncios")
            return ads
            
        except Exception as e:
            self.logger.error(f"❌ Error detectando anuncios: {str(e)}")
            return []
    
    def _detect_by_selectors(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Detectar anuncios usando selectores CSS"""
        ads = []
        
        for selector in self.ad_patterns['selectors']:
            try:
                elements = soup.select(selector)
                for element in elements:
                    ad_info = self._extract_ad_info(element)
                    if ad_info:
                        ads.append(ad_info)
            except Exception as e:
                self.logger.debug(f"Error con selector {selector}: {e}")
        
        return ads
    
    def _detect_by_text_patterns(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Detectar anuncios por patrones de texto"""
        ads = []

        # Buscar elementos con texto que contenga palabras clave en atributos relevantes
        for keyword in self.ad_patterns['keywords']:
            elements = soup.find_all(
                lambda tag: any(
                    keyword.lower() in (str(tag.get(attr, '')).lower())
                    for attr in ['class', 'id', 'title', 'alt']
                )
            )

            for element in elements:
                ad_info = self._extract_ad_info(element)
                if ad_info:
                    ads.append(ad_info)

        return ads
    
    def _detect_by_scripts(self, scripts: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """Detectar anuncios por scripts de servicios de anuncios"""
        ads = []
        
        for script in scripts:
            src = script.get('src', '')
            content = script.get('content', '')
            
            # Verificar si es un script de anuncios
            if any(service in src.lower() for service in self.ad_patterns['ad_services']):
                ads.append({
                    "type": "script_ad",
                    "source": "script",
                    "src": src,
                    "content": content[:200] + "..." if len(content) > 200 else content,
                    "confidence": "high"
                })
            
            # Verificar contenido del script
            elif any(keyword in content.lower() for keyword in self.ad_patterns['keywords']):
                ads.append({
                    "type": "script_ad",
                    "source": "script_content",
                    "src": src,
                    "content": content[:200] + "..." if len(content) > 200 else content,
                    "confidence": "medium"
                })
        
        return ads
    
    def _detect_by_images(self, images: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """Detectar anuncios por patrones en imágenes"""
        ads = []
        
        for img in images:
            src = img.get('src', '')
            alt = img.get('alt', '').lower()
            title = img.get('title', '').lower()
            classes = img.get('class', '').lower()
            
            # Verificar patrones de anuncios en atributos
            ad_indicators = []
            
            if any(keyword in alt for keyword in self.ad_patterns['keywords']):
                ad_indicators.append('alt_text')
            
            if any(keyword in title for keyword in self.ad_patterns['keywords']):
                ad_indicators.append('title')
            
            if any(keyword in classes for keyword in self.ad_patterns['keywords']):
                ad_indicators.append('class')
            
            if any(service in src.lower() for service in self.ad_patterns['ad_services']):
                ad_indicators.append('src_url')
            
            if ad_indicators:
                ads.append({
                    "type": "image_ad",
                    "source": "image",
                    "src": src,
                    "alt": img.get('alt', ''),
                    "title": img.get('title', ''),
                    "indicators": ad_indicators,
                    "confidence": "medium" if len(ad_indicators) >= 2 else "low"
                })
        
        return ads
    
    def _extract_ad_info(self, element: Tag) -> Optional[Dict[str, Any]]:
        """Extraer información de un elemento de anuncio"""
        try:
            # Obtener texto del elemento
            text = element.get_text(strip=True)
            if not text or len(text) < 10:  # Ignorar elementos muy cortos
                return None
            
            # Obtener imágenes del elemento
            images = []
            for img in element.find_all('img'):
                src = img.get('src') or img.get('data-src')
                if src:
                    images.append({
                        "src": src,
                        "alt": img.get('alt', ''),
                        "title": img.get('title', '')
                    })
            
            # Obtener enlaces del elemento
            links = []
            for link in element.find_all('a', href=True):
                links.append({
                    "url": link.get('href'),
                    "text": link.get_text(strip=True),
                    "title": link.get('title', '')
                })
            
            # Calcular confianza basada en indicadores
            confidence_indicators = []
            
            # Verificar clases
            classes = element.get('class', [])
            if any('ad' in cls.lower() for cls in classes):
                confidence_indicators.append('class')
            
            # Verificar ID
            element_id = element.get('id', '')
            if 'ad' in element_id.lower():
                confidence_indicators.append('id')
            
            # Verificar atributos data
            for attr, value in element.attrs.items():
                if 'ad' in attr.lower() or 'ad' in str(value).lower():
                    confidence_indicators.append('data_attr')
            
            # Determinar nivel de confianza
            if len(confidence_indicators) >= 2:
                confidence = "high"
            elif len(confidence_indicators) == 1:
                confidence = "medium"
            else:
                confidence = "low"
            
            return {
                "type": "html_ad",
                "source": "html_element",
                "text": text[:500] + "..." if len(text) > 500 else text,
                "images": images,
                "links": links,
                "classes": classes,
                "element_id": element_id,
                "confidence": confidence,
                "indicators": confidence_indicators,
                "position": self._get_element_position(element)
            }
            
        except Exception as e:
            self.logger.debug(f"Error extrayendo info de elemento: {e}")
            return None
    
    def _get_element_position(self, element: Tag) -> Dict[str, Any]:
        """Obtener posición aproximada del elemento"""
        try:
            # Intentar obtener posición del elemento
            parent = element.parent
            siblings = list(parent.children) if parent else []
            index = siblings.index(element) if element in siblings else 0
            
            return {
                "tag": element.name,
                "parent_tag": parent.name if parent else None,
                "sibling_index": index,
                "depth": len(list(element.parents)) if element.parent else 0
            }
        except:
            return {"tag": element.name if element else "unknown"}
    
    def _filter_and_validate_ads(self, ads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filtrar y validar anuncios detectados"""
        filtered_ads = []
        seen_content = set()
        
        for ad in ads:
            # Generar clave única para evitar duplicados
            content_key = f"{ad.get('text', '')[:100]}_{ad.get('src', '')}"
            
            if content_key not in seen_content:
                seen_content.add(content_key)
                
                # Solo incluir anuncios con confianza mínima
                if ad.get('confidence') in ['high', 'medium']:
                    filtered_ads.append(ad)
        
        return filtered_ads
    
    async def extract_ad_images(self, ad: Dict[str, Any]) -> List[str]:
        """
        Extraer URLs de imágenes de un anuncio
        
        Args:
            ad: Información del anuncio
            
        Returns:
            Lista de URLs de imágenes
        """
        images = []
        
        try:
            # Extraer imágenes del anuncio
            ad_images = ad.get('images', [])
            for img in ad_images:
                src = img.get('src')
                if src and src.startswith(('http://', 'https://')):
                    images.append(src)
            
            # Si no hay imágenes, intentar extraer del texto
            if not images and ad.get('text'):
                # Buscar URLs de imágenes en el texto
                img_urls = re.findall(r'https?://[^\s<>"]+\.(?:jpg|jpeg|png|gif|webp)', ad['text'])
                images.extend(img_urls)
            
        except Exception as e:
            self.logger.error(f"Error extrayendo imágenes del anuncio: {e}")
        
        return images
    
    def analyze_gambling_content(self, ad: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analizar si un anuncio contiene contenido de gambling
        
        Args:
            ad: Información del anuncio
            
        Returns:
            Análisis de contenido de gambling
        """
        gambling_score = 0
        indicators = []
        
        try:
            # Analizar texto
            text = ad.get('text', '').lower()
            for keyword in self.gambling_patterns['keywords']:
                if keyword.lower() in text:
                    gambling_score += 0.3
                    indicators.append(f"keyword: {keyword}")
            
            # Analizar enlaces
            links = ad.get('links', [])
            for link in links:
                url = link.get('url', '').lower()
                text = link.get('text', '').lower()
                
                for domain in self.gambling_patterns['domains']:
                    if domain in url or domain in text:
                        gambling_score += 0.4
                        indicators.append(f"domain: {domain}")
            
            # Analizar imágenes
            images = ad.get('images', [])
            for img in images:
                alt = img.get('alt', '').lower()
                title = img.get('title', '').lower()
                
                for keyword in self.gambling_patterns['keywords']:
                    if keyword.lower() in alt or keyword.lower() in title:
                        gambling_score += 0.2
                        indicators.append(f"image: {keyword}")
            
            # Normalizar score
            gambling_score = min(gambling_score, 1.0)
            
            return {
                "gambling_score": gambling_score,
                "indicators": indicators,
                "is_likely_gambling": gambling_score > 0.5
            }
            
        except Exception as e:
            self.logger.error(f"Error analizando contenido de gambling: {e}")
            return {
                "gambling_score": 0.0,
                "indicators": [],
                "is_likely_gambling": False
            } 