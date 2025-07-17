import os
import numpy as np
from PIL import Image
import tensorflow as tf
from tensorflow.keras.models import load_model
import asyncio
from typing import List, Union
import io
import base64
import requests
from urllib.parse import urlparse

class GamblingDetector:
    def __init__(self, model_path: str = "../ResNet/ResNet.keras"):
        """
        Inicializar el detector de gambling con el modelo ResNet
        
        Args:
            model_path: Ruta al modelo ResNet entrenado
        """
        self.model = None
        self.model_path = model_path
        self.is_model_loaded = False
        self.BEST_THRESHOLD = 0.4931  # Umbral optimizado del notebook original
        
        # Cargar modelo al inicializar
        self._load_model()
    
    def _load_model(self):
        """Cargar el modelo ResNet"""
        try:
            # Verificar si el archivo existe
            if not os.path.exists(self.model_path):
                print(f"⚠️ Modelo no encontrado en: {self.model_path}")
                print("🔍 Buscando modelo en ubicaciones alternativas...")
                
                # Buscar en ubicaciones alternativas
                alternative_paths = [
                    "ResNet/ResNet.keras",
                    "./ResNet/ResNet.keras",
                    "../ResNet/ResNet.keras"
                ]
                
                for alt_path in alternative_paths:
                    if os.path.exists(alt_path):
                        self.model_path = alt_path
                        break
                else:
                    raise FileNotFoundError("Modelo ResNet no encontrado")
            
            print(f"📦 Cargando modelo desde: {self.model_path}")
            self.model = load_model(self.model_path)
            self.is_model_loaded = True
            print("✅ Modelo ResNet cargado exitosamente")
            
        except Exception as e:
            print(f"❌ Error al cargar modelo: {str(e)}")
            self.is_model_loaded = False
    
    def is_loaded(self) -> bool:
        """Verificar si el modelo está cargado"""
        return self.is_model_loaded and self.model is not None
    
    def preprocess_image(self, image: Union[str, bytes, np.ndarray, Image.Image], 
                        target_size: tuple = (224, 224)) -> np.ndarray:
        """
        Preprocesar imagen para el modelo
        
        Args:
            image: Imagen en formato string (URL/base64), bytes, numpy array o PIL Image
            target_size: Tamaño objetivo para redimensionar
            
        Returns:
            Imagen preprocesada como numpy array
        """
        try:
            # Convertir diferentes formatos de entrada a PIL Image
            if isinstance(image, str):
                # URL o base64
                if image.startswith(('http://', 'https://')):
                    # Es una URL
                    response = requests.get(image, timeout=10)
                    response.raise_for_status()
                    pil_image = Image.open(io.BytesIO(response.content))
                else:
                    # Es base64
                    if ',' in image:
                        image = image.split(',')[1]
                    image_data = base64.b64decode(image)
                    pil_image = Image.open(io.BytesIO(image_data))
            
            elif isinstance(image, bytes):
                pil_image = Image.open(io.BytesIO(image))
            
            elif isinstance(image, np.ndarray):
                pil_image = Image.fromarray(image)
            
            elif isinstance(image, Image.Image):
                pil_image = image
            
            else:
                raise ValueError("Formato de imagen no soportado")
            
            # Convertir a RGB si es necesario
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')
            
            # Redimensionar
            pil_image = pil_image.resize(target_size)
            
            # Convertir a numpy array y normalizar
            image_array = np.array(pil_image) / 255.0
            
            # Agregar dimensión de batch si es necesario
            if len(image_array.shape) == 3:
                image_array = np.expand_dims(image_array, axis=0)
            
            return image_array
            
        except Exception as e:
            print(f"❌ Error en preprocesamiento: {str(e)}")
            raise
    
    def predict(self, image: Union[str, bytes, np.ndarray, Image.Image]) -> float:
        """
        Predecir si una imagen contiene contenido de gambling
        
        Args:
            image: Imagen a analizar
            
        Returns:
            Probabilidad de que sea gambling (0.0 - 1.0)
        """
        if not self.is_loaded():
            raise RuntimeError("Modelo no está cargado")
        
        try:
            # Preprocesar imagen
            processed_image = self.preprocess_image(image)
            
            # Realizar predicción
            predictions = self.model.predict(processed_image, verbose=0)
            
            # Obtener probabilidad promedio (para múltiples frames)
            if len(predictions.shape) > 1:
                probability = np.mean(predictions.ravel())
            else:
                probability = float(predictions[0])
            
            return probability
            
        except Exception as e:
            print(f"❌ Error en predicción: {str(e)}")
            return 0.0
    
    async def predict_async(self, image: Union[str, bytes, np.ndarray, Image.Image]) -> float:
        """
        Versión asíncrona de predict para uso en FastAPI
        """
        # Ejecutar predicción en thread pool para no bloquear
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.predict, image)
    
    def predict_batch(self, images: List[Union[str, bytes, np.ndarray, Image.Image]]) -> List[float]:
        """
        Predecir múltiples imágenes de forma eficiente
        
        Args:
            images: Lista de imágenes a analizar
            
        Returns:
            Lista de probabilidades
        """
        if not self.is_loaded():
            raise RuntimeError("Modelo no está cargado")
        
        try:
            # Preprocesar todas las imágenes
            processed_images = []
            for img in images:
                processed = self.preprocess_image(img)
                processed_images.append(processed)
            
            # Concatenar en un batch
            batch = np.vstack(processed_images)
            
            # Realizar predicción en batch
            predictions = self.model.predict(batch, verbose=0)
            
            # Convertir a lista de probabilidades
            probabilities = predictions.ravel().tolist()
            
            return probabilities
            
        except Exception as e:
            print(f"❌ Error en predicción batch: {str(e)}")
            return [0.0] * len(images)
    
    def classify_gambling(self, probability: float, threshold: float = None) -> dict:
        """
        Clasificar resultado basado en probabilidad
        
        Args:
            probability: Probabilidad de gambling
            threshold: Umbral personalizado (usa BEST_THRESHOLD por defecto)
            
        Returns:
            Diccionario con clasificación y detalles
        """
        if threshold is None:
            threshold = self.BEST_THRESHOLD
        
        is_gambling = probability > threshold
        
        return {
            "probability": probability,
            "threshold": threshold,
            "is_gambling": is_gambling,
            "confidence": "high" if abs(probability - threshold) > 0.2 else "medium",
            "classification": "Gambling" if is_gambling else "No Gambling"
        }
    
    def get_model_info(self) -> dict:
        """Obtener información del modelo"""
        if not self.is_loaded():
            return {"status": "not_loaded"}
        
        return {
            "status": "loaded",
            "model_path": self.model_path,
            "input_shape": self.model.input_shape,
            "output_shape": self.model.output_shape,
            "threshold": self.BEST_THRESHOLD,
            "total_params": self.model.count_params()
        }

# Instancia global para uso en la aplicación
gambling_detector = GamblingDetector() 