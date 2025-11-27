import logging
import asyncio
import uuid
from typing import List
from urllib.parse import urljoin, urlparse, urlunparse

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, HttpUrl
from bs4 import BeautifulSoup

# --- IMPORTS DE TUS MÓDULOS ---
# Asegúrate de que estos archivos existen en las rutas correctas
from ml_service.gambling_detector import gambling_detector
from utils.web_scraper import WebScraper
from utils.ad_detector import AdDetector

# Configuración de Logs
logger = logging.getLogger("backend")
if not logging.getLogger().handlers:
    logging.basicConfig(level=logging.DEBUG)

app = FastAPI(
    title="GADIA API",
    description="Gambling Advertisement Detection & Intelligence Analyzer",
    version="1.0.0"
)

# --- CORRECCIÓN CRÍTICA: CORS ---
# Esto permite que tu frontend (React/Vite) se comunique con el backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permitir cualquier origen (localhost:3000, 5173, etc.)
    allow_credentials=True,
    allow_methods=["*"],  # Permitir todos los métodos (GET, POST, OPTIONS, etc.)
    allow_headers=["*"],  # Permitir todos los headers
)

# Instanciar servicios auxiliares
web_scraper = WebScraper()
ad_detector = AdDetector()
# gambling_detector ya viene instanciado desde el import, no lo re-creamos aquí

@app.on_event("startup")
async def startup_event():
    logger.info("Startup: Verificando carga del detector de gambling...")
    try:
        # Usamos el método .load() (que añadimos para compatibilidad) o is_loaded()
        if not gambling_detector.is_loaded():
            logger.info("Modelo no detectado en memoria, forzando carga...")
            if hasattr(gambling_detector, 'load'):
                gambling_detector.load()
            else:
                # Fallback si por alguna razón no se actualizó el archivo
                gambling_detector._load_model()
        logger.info("Startup: Estado final del modelo cargado=%s", gambling_detector.is_loaded())
    except Exception as exc:
        logger.exception("Error al cargar el detector durante startup: %s", exc)

# --- MODELOS PYDANTIC ---

class SimpleAnalysisRequest(BaseModel):
    url: HttpUrl

class FrameAnalysis(BaseModel):
    url: str
    is_gambling: bool
    probability: float

class SimpleAnalysisResult(BaseModel):
    id: str
    page_name: str
    favicon_url: str | None = None
    link: str
    has_gambling_ads: str  # "Sí" o "No"
    gambling_image_url: str | None = None
    frames_analysis: list[FrameAnalysis] = Field(default_factory=list)

class ImageAnalysisRequest(BaseModel):
    urls: List[HttpUrl] = Field(default_factory=list)
    threshold: float | None = None

# --- ENDPOINTS ---

@app.get("/")
def root():
    return {
        "message": "🎰 GADIA API - Gambling Advertisement Detection",
        "version": "1.0.0",
        "status": "running",
        "cors_enabled": True
    }

@app.get("/health")
def health_check():
    """Verificar el estado del servicio y del modelo"""
    model_status = gambling_detector.is_loaded()
    model_info = gambling_detector.get_model_info()
    
    return {
        "status": "healthy" if model_status else "degraded",
        "model_loaded": model_status,
        "model_info": model_info,
        "services": {
            "web_scraper": True,
            "ad_detector": True,
            "gambling_detector": model_status
        }
    }

async def _analyze_images_with_resnet(urls: List[str], threshold: float | None = None) -> List[FrameAnalysis]:
    """Analizar una lista de URLs de imágenes con el modelo ResNet."""
    results: List[FrameAnalysis] = []
    if not urls:
        return results

    final_threshold = threshold if threshold is not None else gambling_detector.BEST_THRESHOLD

    for img_url in urls:
        try:
            # Convertimos HttpUrl a str por si acaso
            str_url = str(img_url)
            prob = await gambling_detector.predict_async(str_url)
            results.append(FrameAnalysis(
                url=str_url,
                is_gambling=prob > final_threshold,
                probability=round(prob, 3)
            ))
        except Exception as exc:
            logger.error(f"No se pudo analizar la imagen {img_url}: {exc}")
            results.append(FrameAnalysis(
                url=str(img_url),
                is_gambling=False,
                probability=0.0
            ))
    return results


@app.post("/simple-analyze", response_model=SimpleAnalysisResult)
def simple_analyze(request: SimpleAnalysisRequest):
    # Verificar que el modelo esté cargado
    if not gambling_detector.is_loaded():
        # Intentar carga de emergencia
        if hasattr(gambling_detector, 'load'):
            gambling_detector.load()
        
        if not gambling_detector.is_loaded():
            raise HTTPException(
                status_code=503,
                detail="El modelo de detección de gambling no está disponible. Revisa los logs del servidor."
            )
    
    try:
        url = str(request.url)
        
        # 1. Extraer contenido de la web (sincronía para compatibilidad con BeautifulSoup)
        # Nota: Idealmente web_scraper debería ser async totalmente, pero usamos el loop para compatibilidad
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            page_content = loop.run_until_complete(web_scraper.scrape_url(url))
        except Exception as e:
            logger.error(f"Fallo scraping: {e}")
            page_content = {"success": False, "html": ""}

        # 2. Extraer nombre y favicon
        page_name = page_content.get('title') or url
        favicon_url = None
        soup = BeautifulSoup(page_content.get('html', ''), 'html.parser')
        
        icon_link = soup.find('link', rel=lambda x: x and 'icon' in x.lower())
        if icon_link and icon_link.get('href'):
            favicon_url = icon_link['href']
            if not favicon_url.startswith('http'):
                favicon_url = urljoin(url, favicon_url)
        else:
            parsed = urlparse(url)
            favicon_url = urlunparse((parsed.scheme, parsed.netloc, '/favicon.ico', '', '', ''))

        # 3. Detectar anuncios (Heurística clásica)
        try:
            ads = loop.run_until_complete(ad_detector.detect_ads(page_content))
        except Exception as e:
            logger.error(f"Fallo detección anuncios: {e}")
            ads = []

        # 4. Preparación para análisis de imágenes
        gambling_detected = False
        found_ad_images = False
        gambling_image_url = None
        frames_analysis = []
        
        palabras_ignorar = ["logo", "icon", "favicon", "marca", "brand", "comercio", "perfil", "avatar", "user", "persona", "foto", "author", "team", "staff"]
        gambling_keywords = [
            "casino", "poker", "bet", "gambling", "slot", "roulette", "blackjack", "baccarat", "craps", "lottery", "bingo",
            "sports betting", "online casino", "real money", "casino online", "apuestas", "juegos de azar", "tragaperras", "ruleta", "póker", "bingo online",
            "jackpot", "premio", "ganador", "apuesta deportiva", "apuesta", "ganancias", "bono", "apuesta gratis", "apuesta en vivo"
        ]
        gambling_symbols = ["🎰", "💰", "🃏", "🎲", "🏆", "💵", "💸", "🎯"]
        gambling_strict_threshold = 0.5
        
        # Obtener TODAS las imágenes de la página
        all_images = page_content.get('images', [])
        
        # Recolectar imágenes de anuncios detectados
        filtered_ad_images = []
        for ad in ads:
            ad_images_urls = loop.run_until_complete(ad_detector.extract_ad_images(ad))
            ad_classes = ad.get('classes', [])
            ad_text = ad.get('text', '').lower()
            es_banner = any(word in ' '.join(ad_classes).lower() for word in ["banner", "ad", "promo"]) or "banner" in ad_text or "ad" in ad_text
            
            for img_url in ad_images_urls:
                lower_url = img_url.lower()
                if any(word in lower_url for word in palabras_ignorar):
                    continue
                
                # Contexto del anuncio
                img_related = False
                if any(kw in ad_text for kw in gambling_keywords): img_related = True
                if any(kw in lower_url for kw in gambling_keywords): img_related = True
                if any(kw in ' '.join(ad_classes).lower() for kw in gambling_keywords): img_related = True
                if any(sym in ad_text for sym in gambling_symbols): img_related = True
                
                if img_related:
                    # Aquí podrías añadir lógica de tamaño (width/height) si tienes esos datos
                    filtered_ad_images.append((img_url, es_banner, ad_text, ad_classes))

        # Ordenar: banners primero
        filtered_ad_images.sort(key=lambda x: not x[1])
        
        if filtered_ad_images:
            found_ad_images = True

        # Analizar imágenes de anuncios
        for img_url, _, ad_text, ad_classes in filtered_ad_images:
            try:
                prob = loop.run_until_complete(gambling_detector.predict_async(img_url))
                
                # Bonus de contexto
                context_bonus = 0.0
                if any(kw in ad_text for kw in gambling_keywords) or any(kw in img_url.lower() for kw in gambling_keywords):
                    context_bonus += 0.1
                if any(sym in ad_text for sym in gambling_symbols):
                    context_bonus += 0.1
                
                prob_with_context = min(prob + context_bonus, 1.0)
                is_gambling = prob_with_context > gambling_strict_threshold
                
                frames_analysis.append({
                    "url": img_url,
                    "is_gambling": is_gambling,
                    "probability": round(prob_with_context, 3)
                })
                
                if is_gambling:
                    gambling_detected = True
                    if not gambling_image_url:
                        gambling_image_url = img_url
                        
            except Exception as e:
                logger.error(f"Error analizando imagen anuncio {img_url}: {e}")

        # 5. Analizar el resto de imágenes de la página (Deep Scan)
        logger.info(f"Analizando {len(all_images)} imágenes totales de la página...")
        processed_urls = set([f['url'] for f in frames_analysis]) # Evitar re-analizar las de anuncios
        
        for img_data in all_images:
            img_url = img_data.get('src', '')
            if not img_url or not img_url.startswith(('http://', 'https://')):
                continue
            if img_url in processed_urls:
                continue
            
            processed_urls.add(img_url)
            lower_url = img_url.lower()
            
            if any(word in lower_url for word in palabras_ignorar):
                continue
            
            # Filtro básico de tamaño (si el scraper devolvió width/height)
            w_str = img_data.get('width', '0')
            h_str = img_data.get('height', '0')
            try:
                w = int(w_str) if w_str and w_str.isdigit() else 0
                h = int(h_str) if h_str and h_str.isdigit() else 0
                # Ignorar muy pequeñas si tenemos datos
                if 0 < w < 50 or 0 < h < 50: 
                    continue
            except:
                pass

            try:
                prob = loop.run_until_complete(gambling_detector.predict_async(img_url))
                is_gambling = prob > gambling_strict_threshold
                
                frames_analysis.append({
                    "url": img_url,
                    "is_gambling": is_gambling,
                    "probability": round(prob, 3)
                })
                
                if is_gambling:
                    gambling_detected = True
                    if not gambling_image_url:
                        gambling_image_url = img_url
                        
            except Exception as e:
                logger.error(f"Error analizando imagen general {img_url}: {e}")
        
        loop.close()

        # Determinar resultado final
        if not found_ad_images and len(frames_analysis) == 0:
            gambling_result = "No"
        else:
            gambling_result = "Sí" if gambling_detected else "No"

        result = {
            "id": str(uuid.uuid4()),
            "page_name": page_name,
            "favicon_url": favicon_url,
            "link": url,
            "has_gambling_ads": gambling_result,
            "gambling_image_url": gambling_image_url,
            "frames_analysis": frames_analysis
        }
        
        return result

    except Exception as e:
        logger.exception("Error crítico en simple_analyze")
        raise HTTPException(status_code=400, detail=f"Error al analizar la página: {str(e)}")

@app.post("/analyze-images", response_model=List[FrameAnalysis])
async def analyze_images_endpoint(request: ImageAnalysisRequest):
    if not gambling_detector.is_loaded():
        raise HTTPException(status_code=503, detail="Modelo de gambling no está disponible")
    if not request.urls:
        return []
    # Convertimos HttpUrl a str
    urls_as_strings = [str(u) for u in request.urls]
    return await _analyze_images_with_resnet(urls_as_strings, request.threshold)