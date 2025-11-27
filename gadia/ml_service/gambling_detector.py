import os
import sys
import logging
from pathlib import Path
import numpy as np
from PIL import Image
import asyncio
from typing import List, Union
import io
import base64
import requests

# Importar Keras 3
import keras
from keras.models import load_model

# Configurar logger
logger = logging.getLogger("backend.detector")
logger.setLevel(logging.INFO)

class GamblingDetector:
    def __init__(self):
        self.model = None
        self.is_model_loaded = False
        self.BEST_THRESHOLD = 0.4931
        self.model_path = None
        
        # Cargar modelo al iniciar
        self._load_model()
    
    def _find_model(self) -> Path:
        """Busca el archivo del modelo subiendo niveles de carpetas."""
        cwd = Path.cwd()
        path_from_cwd = cwd / "ResNet" / "ResNet.keras"
        
        if path_from_cwd.exists():
            return path_from_cwd

        script_path = Path(__file__).resolve()
        path_from_script = script_path.parent.parent.parent / "ResNet" / "ResNet.keras"
        
        if path_from_script.exists():
            return path_from_script
            
        return None

    def _load_model(self):
        """Lógica interna de carga"""
        try:
            found_path = self._find_model()
            
            if not found_path:
                logger.error("❌ CRÍTICO: No se encontró 'ResNet/ResNet.keras'.")
                self.is_model_loaded = False
                return

            self.model_path = str(found_path)
            logger.info(f"📦 Cargando modelo desde: {self.model_path}")
            
            self.model = load_model(self.model_path)
            self.is_model_loaded = True
            logger.info("✅ GADIA: Modelo cargado y verificado en memoria.")
            
        except Exception as e:
            logger.error(f"❌ ERROR AL CARGAR MODELO: {e}")
            self.is_model_loaded = False

    def load(self):
        """Método público para reintentar carga."""
        if not self.is_loaded():
            self._load_model()
    
    def is_loaded(self) -> bool:
        return self.is_model_loaded and self.model is not None
    
    def preprocess_image(self, image: Union[str, bytes, np.ndarray, Image.Image], 
                         target_size: tuple = (224, 224)) -> np.ndarray:
        try:
            pil_image = None
            if isinstance(image, str): 
                if image.startswith(('http://', 'https://')):
                    response = requests.get(image, timeout=10)
                    response.raise_for_status()
                    pil_image = Image.open(io.BytesIO(response.content))
                elif ',' in image: 
                    image_data = base64.b64decode(image.split(',')[1])
                    pil_image = Image.open(io.BytesIO(image_data))
                else: 
                    image_data = base64.b64decode(image)
                    pil_image = Image.open(io.BytesIO(image_data))
            elif isinstance(image, bytes):
                pil_image = Image.open(io.BytesIO(image))
            elif isinstance(image, np.ndarray):
                pil_image = Image.fromarray(image)
            elif isinstance(image, Image.Image):
                pil_image = image
                
            if pil_image is None: raise ValueError("Formato no reconocido")
            if pil_image.mode != 'RGB': pil_image = pil_image.convert('RGB')
            
            pil_image = pil_image.resize(target_size)
            image_array = np.array(pil_image) / 255.0
            if len(image_array.shape) == 3: image_array = np.expand_dims(image_array, axis=0)
            return image_array
        except Exception as e:
            logger.error(f"Error preprocesando: {e}")
            raise

    def predict(self, image) -> float:
        """Predicción síncrona (usada internamente)"""
        if not self.is_loaded(): raise RuntimeError("Modelo no cargado")
        try:
            processed = self.preprocess_image(image)
            prediction = self.model.predict(processed, verbose=0)
            
            if isinstance(prediction, np.ndarray):
                return float(prediction.flatten()[0])
            return float(prediction[0])
            
        except Exception as e:
            logger.error(f"❌ Error predicción: {e}")
            return 0.0

    async def predict_async(self, image) -> float:
        """
        Predicción asíncrona (ESTA ES LA QUE FALTABA).
        Permite que FastAPI maneje otras peticiones mientras la IA piensa.
        """
        if not self.is_loaded():
            self.load()
            if not self.is_loaded(): return 0.0
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.predict, image)

    def get_model_info(self) -> dict:
        return {
            "status": "loaded" if self.is_loaded() else "failed", 
            "path": self.model_path
        }

# Instancia global
gambling_detector = GamblingDetector()