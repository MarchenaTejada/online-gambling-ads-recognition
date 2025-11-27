import os
import sys

print("--- INICIO DIAGNÓSTICO (MODO KERAS 3) ---")
cwd = os.getcwd()
print(f"1. Directorio: {cwd}")

expected_path = os.path.join(cwd, "ResNet", "ResNet.keras")
print(f"2. Archivo esperado: {expected_path}")

if os.path.exists(expected_path):
    print("✅ EL ARCHIVO EXISTE.")
    try:
        print("3. Importando Keras (esto puede tardar)...")
        import keras
        print(f"   Versión de Keras detectada: {keras.__version__}")
        
        print("4. Cargando modelo...")
        from keras.models import load_model
        model = load_model(expected_path)
        
        print("✅✅ ¡MODELO CARGADO EXITOSAMENTE!")
        print("   Tu entorno está listo.")
    except Exception as e:
        print("\n❌ FALLO EN LA CARGA.")
        print(f"   Error: {e}")
else:
    print("❌ El archivo no está en la ruta.")

print("--- FIN ---")