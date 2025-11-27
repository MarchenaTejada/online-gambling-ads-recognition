from ml_service.gambling_detector import GamblingDetector, gambling_detector
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("test_load_model")

if __name__ == "__main__":
    logger.info("Test local: intentar cargar modelo mediante instancia global")
    try:
        gambling_detector.load()
        logger.info("Resultado: model_loaded=%s", gambling_detector.is_loaded())
    except Exception as e:
        logger.exception("Fallo en test_load_model: %s", e)