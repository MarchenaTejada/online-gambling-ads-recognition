from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
import uuid
from typing import List
from urllib.parse import urljoin, urlparse, urlunparse

# Importar los servicios de scraping, detección de anuncios y gambling
from ml_service.gambling_detector import GamblingDetector
from utils.web_scraper import WebScraper
from utils.ad_detector import AdDetector
import asyncio
from bs4 import BeautifulSoup

app = FastAPI(
    title="GADIA API",
    description="Gambling Advertisement Detection & Intelligence Analyzer",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Eliminar analyses_memory y el endpoint de historial
# analyses_memory = []  # Eliminar esta línea

# Instanciar servicios
web_scraper = WebScraper()
ad_detector = AdDetector()
gambling_detector = GamblingDetector()

class SimpleAnalysisRequest(BaseModel):
    url: HttpUrl

class FrameAnalysis(BaseModel):
    url: str
    is_gambling: bool
    probability: float

class SimpleAnalysisResult(BaseModel):
    id: str
    page_name: str
    favicon_url: str
    link: str
    has_gambling_ads: str  # "Sí" o "No"
    gambling_image_url: str | None = None
    frames_analysis: list[FrameAnalysis] = []

@app.get("/")
def root():
    return {
        "message": "🎰 GADIA API - Gambling Advertisement Detection",
        "version": "1.0.0",
        "status": "running"
    }

@app.post("/simple-analyze", response_model=SimpleAnalysisResult)
def simple_analyze(request: SimpleAnalysisRequest):
    try:
        url = str(request.url)
        # 1. Extraer contenido de la web (sincronía para compatibilidad)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        page_content = loop.run_until_complete(web_scraper.scrape_url(url))

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

        # 3. Detectar anuncios
        ads = loop.run_until_complete(ad_detector.detect_ads(page_content))

        # 4. Analizar imágenes de anuncios con el modelo de gambling
        gambling_detected = False
        found_ad_images = False
        gambling_image_url = None
        gambling_image_url_debug = None
        frames_analysis = []
        palabras_ignorar = ["logo", "icon", "favicon", "marca", "brand", "comercio", "perfil", "avatar", "user", "persona", "foto", "author", "team", "staff"]
        gambling_keywords = [
            "casino", "poker", "bet", "gambling", "slot", "roulette", "blackjack", "baccarat", "craps", "lottery", "bingo",
            "sports betting", "online casino", "real money", "casino online", "apuestas", "juegos de azar", "tragaperras", "ruleta", "póker", "bingo online",
            "jackpot", "premio", "ganador", "apuesta deportiva", "apuesta", "ganancias", "bono", "apuesta gratis", "apuesta en vivo"
        ]
        gambling_symbols = ["🎰", "💰", "🃏", "🎲", "🏆", "💵", "💸", "🎯"]
        # Cambiar el umbral a 0.5 (más sensible)
        gambling_strict_threshold = 0.5
        for ad in ads:
            ad_images = loop.run_until_complete(ad_detector.extract_ad_images(ad))
            ad_classes = ad.get('classes', [])
            ad_text = ad.get('text', '').lower()
            es_banner = any(word in ' '.join(ad_classes).lower() for word in ["banner", "ad", "promo"]) or "banner" in ad_text or "ad" in ad_text
            filtered_ad_images = []
            for img_url in ad_images:
                lower_url = img_url.lower()
                if any(word in lower_url for word in palabras_ignorar):
                    continue
                img_related = False
                # Buscar palabras clave en el texto del anuncio
                if any(kw in ad_text for kw in gambling_keywords):
                    img_related = True
                # Buscar palabras clave en la URL
                if any(kw in lower_url for kw in gambling_keywords):
                    img_related = True
                # Buscar palabras clave en las clases del anuncio
                if any(kw in ' '.join(ad_classes).lower() for kw in gambling_keywords):
                    img_related = True
                # Buscar símbolos/emojis en el texto del anuncio
                if any(sym in ad_text for sym in gambling_symbols):
                    img_related = True
                if not img_related:
                    continue
                try:
                    if lower_url.startswith("http"):
                        from PIL import Image
                        import requests
                        from io import BytesIO
                        resp = requests.get(img_url, timeout=5)
                        img = Image.open(BytesIO(resp.content))
                        width, height = img.size
                        # Ignorar imágenes pequeñas y redondas (perfil/avatar)
                        if width < 100 or height < 100:
                            continue
                        if abs(width - height) < 10 and width < 200:
                            continue
                        # Ignorar imágenes con fondo blanco predominante
                        img_np = None
                        try:
                            img_np = img.convert('RGB')
                            colors = img_np.getcolors(maxcolors=1000000)
                            if colors:
                                total = sum([c[0] for c in colors])
                                white = sum([c[0] for c in colors if c[1] == (255,255,255)])
                                if total > 0 and white / total > 0.5:
                                    continue
                        except Exception as e:
                            print(f"[WARN] No se pudo analizar fondo blanco de {img_url}: {e}")
                        alt = getattr(img, 'alt', '').lower() if hasattr(img, 'alt') else ''
                        title = getattr(img, 'title', '').lower() if hasattr(img, 'title') else ''
                        if any(word in alt for word in palabras_ignorar) or any(word in title for word in palabras_ignorar):
                            continue
                except Exception as e:
                    print(f"[WARN] No se pudo verificar tamaño o atributos de {img_url}: {e}")
                filtered_ad_images.append((img_url, es_banner))
            filtered_ad_images.sort(key=lambda x: not x[1])  # True (banner) primero
            if filtered_ad_images:
                found_ad_images = True
            for img_url, _ in filtered_ad_images:
                try:
                    prob = loop.run_until_complete(gambling_detector.predict_async(img_url))
                    # Mejorar el bonus de contexto: +0.1 por palabras clave, +0.1 por símbolos
                    context_bonus = 0.0
                    if any(kw in ad_text for kw in gambling_keywords) or any(kw in lower_url for kw in gambling_keywords) or any(kw in ' '.join(ad_classes).lower() for kw in gambling_keywords):
                        context_bonus += 0.1
                    if any(sym in ad_text for sym in gambling_symbols):
                        context_bonus += 0.1
                    prob_with_context = min(prob + context_bonus, 1.0)
                    is_gambling = prob_with_context > gambling_strict_threshold
                    frames_analysis.append({
                        "url": img_url,
                        "is_gambling": is_gambling,
                        "probability": round(prob_with_context, 3)  # Mostrar probabilidad real con 3 decimales
                    })
                    print(f"[DEBUG] Probabilidad gambling para {img_url}: {prob:.4f} (con contexto: {prob_with_context:.4f})")
                    if is_gambling:
                        gambling_detected = True
                        gambling_image_url = img_url
                        gambling_image_url_debug = img_url
                        print(f"[RESULTADO] Imagen/frame detectado como gambling: {img_url}")
                        break
                except Exception as e:
                    print(f"[ERROR] No se pudo analizar la imagen {img_url}: {e}")
            if gambling_detected:
                break

        if not found_ad_images:
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
        # Eliminar la línea que agrega el resultado a analyses_memory
        # analyses_memory.append(result)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al analizar la página: {str(e)}")

# Eliminar el endpoint de historial
# @app.get("/simple-analyses", response_model=List[SimpleAnalysisResult])
# def list_simple_analyses():
#     return analyses_memory