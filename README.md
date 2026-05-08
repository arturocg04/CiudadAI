# Sistema CiudadIA: Gestión Inteligente de Incidencias

Sistema completo para la gestión de incidencias ciudadanas con clasificación automática, predicción de urgencia y flujos de trabajo aprobados. Combina una API backend robusta, interfaz web intuitiva y servicios de aprendizaje automático para optimizar la atención de solicitudes municipales.

## Arquitectura del Sistema

CiudadIA es un sistema completo compuesto por:

- **Backend API** (`/backend`): Servicio RESTful desarrollado con FastAPI que maneja la lógica de negocio, autenticación y persistencia
- **Frontend Web** (`/frontend`): Interfaz de usuario desarrollada con Jinja2/HTML/CSS para ciudadanos y administradores
- **Servicio de ML** (`/ml_service`): Microservicio que proporciona predicciones de urgencia y clasificación de tickets usando modelos de aprendizaje automático
- **Entrenamiento de Modelos** (`/ML`): Notebooks y scripts para entrenar y mejorar los modelos de ML

## Qué incluye

- Sistema completo backend-frontend-ML integrado
- API RESTful con FastAPI y documentación OpenAPI automática
- Interfaz web para ciudadanos (reportar incidencias) y administradores (gestionar tickets)
- Servicio de ML para predicción de urgencia y clasificación automática
- Autenticación JWT segura con roles de usuario
- Base de datos PostgreSQL con modelos ORM
- Tests unitarios y de integración
- Containerización con Docker y Docker Compose
- Configuración por entorno mediante variables
- Manejo global de errores y validación de datos
- Arquitectura modular y escalable

## Estructura del repositorio

```text
CiudadIA/
├── backend/                 # API RESTful con FastAPI
│   ├── src/                 # Código fuente
│   │   ├── app.py           # Punto de entrada
│   │   ├── routers/         # Endpoints agrupados por dominio
│   │   ├── services/        # Lógica de negocio
│   │   ├── models/          # Modelos Pydantic y ORM
│   │   ├── db/              # Configuración de base de datos
│   │   └── clients/         # Clientes para servicios externos
│   ├── tests/               # Tests unitarios e integración
│   ├── Dockerfile           # Configuración de contenedor
│   └── requirements.txt     # Dependencias de Python
├── frontend/                # Interfaz web
│   ├── app.py               # Aplicación web (Jinja2)
│   ├── templates/           # Páginas HTML
│   ├── static/              # Assets estáticos
│   ├── config.py            # Configuración
│   ├── Dockerfile           # Configuración de contenedor
│   └── requirements.txt     # Dependencias
├── ml_service/              # Servicio de aprendizaje automático
│   ├── app.py               # API de predicciones
│   ├── model/               # Modelos entrenados
│   ├── Dockerfile           # Configuración de contenedor
│   └── requirements.txt     # Dependencias
├── ML/                      # Entrenamiento y experimentación
│   ├── ModelTraining.ipynb  # Notebook principal de entrenamiento
│   ├── incidencias.csv      # Dataset de entrenamiento
│   ├── requirements.txt     # Dependencias de ML
│   └── IMPLEMENTATION_SUMMARY.md  # Resumen de implementación
├── docker-compose.yaml      # Orquestación de todos los servicios
├── .env.example             # Variables de entorno de ejemplo
└── README.md                # Este archivo
```

## Librerías mínimas

### Backend:
- fastapi
- uvicorn
- pydantic-settings
- psycopg2-binary
- sqlalchemy
- python-jose[cryptography]
- passlib[bcrypt]

### Frontend:
- fastapi (para servir templates)
- jinja2

### ML Service:
- tensorflow
- scikit-learn
- pandas
- numpy
- fastapi
- uvicorn

### Dependencias de desarrollo (para todos los servicios):
- pytest
- httpx
- ruff

## Qué es pyproject.toml

Nota: Cada servicio tiene su propio requirements.txt para gestionar dependencias específicas. Los servicios usan configuraciones individuales apropiadas para su funcionalidad.

## Ejecución completa del sistema

1. Clonar el repositorio y entrar al directorio
2. Copiar `.env.example` a `.env` en cada servicio (backend, frontend, ml_service) y ajustar valores
3. Construir y levantar todos los servicios con Docker Compose:
   ```bash
   docker compose up --build
   ```
4. Acceder a los diferentes servicios:
   - API Backend: http://localhost:8000/docs
   - Frontend Web: http://localhost:8080
   - Servicio ML: http://localhost:8001/docs
   - Base de datos: disponible en puerto 5432 (PostgreSQL)

### Ejecución individual (para desarrollo)

#### Backend:
```bash
cd backend
python -m pip install -r requirements.txt
uvicorn src.app:app --reload
```

#### Frontend:
```bash
cd frontend
python -m pip install -r requirements.txt
python app.py
```

#### ML Service:
```bash
cd ml_service
python -m pip install -r requirements.txt
uvicorn app:app --reload
```

## Servicio de Machine Learning

El proyecto incluye un servicio dedicado a ML que proporciona:

- Predicción de urgencia para nuevos tickets (baja, media, alta)
- Clasificación automática de categorías (alumbrado, baches, limpieza, etc.)
- Reentrenamiento periódico con nuevos datos
- API RESTful para integración con el backend

Detalles técnicos:
- Ubicado en `/ml_service`
- Usa TensorFlow/Keras para redes neuronales
- Entrenado con datos históricos de incidencias
- Endpoints: `/predict` (predicción), `/health` (estado)
- Documentación en `/ML/IMPLEMENTATION_SUMMARY.md`

## Cómo adaptar el sistema a necesidades específicas

Este sistema está listo para producción pero puede extenderse:

- **Backend**: Añadir nuevos routers en `backend/src/routers/` y servicios en `backend/src/services/`
- **Frontend**: Crear nuevas plantillas en `frontend/templates/` y rutas en `frontend/app.py`
- **ML**: Mejorar modelos en `ML/ModelTraining.ipynb` y actualizar `/ml_service/app.py`
- **Integraciones**: Añadir clientes en `backend/src/clients/` para servicios externos
- **Monitoring**: Implementar logging avanzado y métricas
- **Multi-tenancy**: Adaptar para múltiples municipios o departamentos

## Tecnologías Utilizadas

- **Backend**: FastAPI, PostgreSQL, SQLAlchemy, Pydantic, JWT
- **Frontend**: Jinja2, HTML5, CSS3, Bootstrap
- **ML**: TensorFlow, Keras, Pandas, Scikit-learn
- **Infraestructura**: Docker, Docker Compose, NGINX (implícito en composición)
- **Testing**: Pytest, HTTPX
- **Calidad**: Ruff, MyPy
- **ORM**: SQLAlchemy con modelos declarativos
- **Autenticación**: JWT con refresh tokens y roles

## Decisiones de diseño

- Arquitectura basada en microservicios ligados por Docker Compose
- Separación clara de responsabilidades: API, presentación y ML
- Seguridad por diseño con autenticación JWT y autorización por roles
- Escalabilidad horizontal mediante contenedores independientes
- Manejo de errores centralizado y respuestas consistentes
- Documentación automática de APIs mediante OpenAPI/Swagger
- Configuración por entorno para desarrollo, staging y producción
- Tests que verifican tanto funcionalidad como seguridad


## Comandos de trabajo útiles

```bash
# Ejecutar tests
pytest -q

# Ejecutar lint
ruff check .

# Formatear
ruff format .
```

### Sistema completo:
```bash
# Ver estado de todos los servicios
docker compose ps

# Ver logs de todos los servicios
docker compose logs -f

# Detener todos los servicios
docker compose down

# Reconstruir y reiniciar
docker compose up --build -d
```

## Limitaciones 

- El servicio de ML usa un modelo simple para demostración
- La autenticación está diseñada para ser reemplazada por proveedores externos
- No incluye monitoreo avanzado (Prometheus/Grafana)
- Los tests de carga no están incluidos pero pueden añadirse con herramientas como Locust

Este sistema representa una base sólida para aplicaciones gubernamentales inteligentes que pueden evolucionar según las necesidades específicas de cada entidad municipal o departamento público.