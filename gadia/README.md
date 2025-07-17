# 🎰 GADIA - Gambling Advertisement Detection & Intelligence Analyzer

## 📋 Descripción
GADIA es una aplicación web que detecta automáticamente anuncios de gambling en sitios web. Los usuarios pueden ingresar un enlace y el sistema analizará el contenido para identificar y clasificar anuncios relacionados con apuestas.

## 🚀 Características
- **Detección automática de anuncios** en páginas web
- **Análisis de contenido** usando IA (ResNet)
- **Clasificación de gambling** con alta precisión
- **Interfaz web moderna** con Next.js
- **API REST** para integraciones
- **Procesamiento asíncrono** en segundo plano

## 🏗️ Arquitectura
```
gadia/
├── backend/           # FastAPI - API REST
├── frontend/          # Next.js - Interfaz web
├── ml_service/        # Servicio de ML con ResNet
├── utils/             # Utilidades compartidas
└── docs/              # Documentación
```

## 🛠️ Tecnologías
- **Backend**: FastAPI, Python, SQLAlchemy
- **Frontend**: Next.js 15, TypeScript, Tailwind CSS
- **ML**: TensorFlow, ResNet
- **Base de datos**: SQLite/PostgreSQL
- **Despliegue**: Docker (solo backend, opcional)

## 📦 Instalación

### Opción 1: Desarrollo Local (Recomendado)
```bash
# Clonar repositorio
git clone <repo-url>
cd gadia

# Backend
cd backend
pip install -r requirements.txt
python -m main
```

En otra terminal, para el frontend:
```bash
cd frontend
npm install
npm run dev
```

- El frontend estará disponible en http://localhost:3000
- El backend en http://localhost:8000

### Opción 2: Docker (solo backend)
```bash
# Usar docker-compose para el backend (opcional)
docker-compose up --build
```

## 🔧 Configuración
1. Copiar `env.example` a `.env` y configurar variables
2. Asegurar que el modelo ResNet esté en `ResNet/ResNet.keras`
3. Instalar dependencias de Python y Node.js
4. Configurar la variable `DATABASE_URL` para tu base de datos en la nube

## 📊 Uso
1. Abrir http://localhost:3000
2. Ingresar URL del sitio a analizar
3. Esperar el procesamiento automático
4. Revisar resultados y reportes

## 🌐 Endpoints API

### POST /analyze
Inicia análisis de una URL
```json
{
  "url": "https://ejemplo.com"
}
```

### GET /status/{task_id}
Obtiene estado y resultados del análisis

### GET /health
Verifica estado del servicio

## 🚀 Despliegue

### Producción con Docker (solo backend)
```bash
docker-compose up -d
```

### Vercel (Frontend)
```bash
cd frontend
vercel --prod
```

## 🤝 Contribución
1. Fork el proyecto
2. Crear rama feature (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

## 📄 Licencia
MIT License - ver `LICENSE` para detalles.

## 🆘 Soporte
- 📧 Email: contact@gadia.com
- 🐛 Issues: GitHub Issues
- 📖 Documentación: `/docs` 