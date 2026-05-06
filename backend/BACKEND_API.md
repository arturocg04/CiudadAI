# Backend API - Documentación de Endpoints

## Descripción General

API REST para la plataforma CiudadAI que gestiona reportes de incidencias ciudadanas y su asignación a trabajadores.

## Endpoints de Incidencias (Ciudadanos)

### 1. Crear Incidencia (POST)
- **URL**: `/api/v1/citizen/incidents`
- **Método**: `POST`
- **Descripción**: Recibe una nueva incidencia de un ciudadano
- **Body (JSON)**:
```json
{
  "nombre": "Elena",
  "apellidos": "Pérez Garrido",
  "nif": "66608986C",
  "telefono": "656964241",
  "email": "elenaperez847@example.com",
  "categoria": "Movilidad",
  "description": "En la Avenida de los Maestros hay un bache en la acera",
  "canal": "App",
  "direccion_persona": "Calle Obispo Hu...",
  "ubicacion_incid": "37.185, -3.596 - Junto a..."
}
```

- **Response (201 Created)**:
```json
{
  "id": 1001,
  "nombre": "Elena",
  "apellidos": "Pérez Garrido",
  "nif": "66608986C",
  "telefono": "656964241",
  "email": "elenaperez847@example.com",
  "categoria": "Movilidad",
  "description": "En la Avenida de los Maestros hay un bache en la acera",
  "urgencia": 3,
  "fecha": "2026-01-01T07:45:00",
  "estado": "nuevo",
  "canal": "App",
  "direccion_persona": "Calle Obispo Hu...",
  "ubicacion_incid": "37.185, -3.596 - Junto a..."
}
```

**Validaciones**:
- NIF: exactamente 9 caracteres alfanuméricos
- Teléfono: exactamente 9 dígitos
- Descripción: mínimo 10 caracteres
- Description es enviada al servicio ML para predecir urgencia (1-5)

### 2. Obtener Estado de Incidencia (GET)
- **URL**: `/api/v1/citizen/incidents/{incident_id}`
- **Método**: `GET`
- **Descripción**: Consulta el estado de una incidencia existente
- **Response (200 OK)**:
```json
{
  "id": 1001,
  "nombre": "Elena",
  "apellidos": "Pérez Garrido",
  "nif": "66608986C",
  "telefono": "656964241",
  "email": "elenaperez847@example.com",
  "categoria": "Movilidad",
  "description": "En la Avenida de los Maestros hay un bache en la acera",
  "urgencia": 3,
  "fecha": "2026-01-01T07:45:00",
  "estado": "nuevo",
  "canal": "App",
  "direccion_persona": "Calle Obispo Hu...",
  "ubicacion_incid": "37.185, -3.596 - Junto a..."
}
```

## Endpoints del Panel del Trabajador

### 1. Listar Incidencias (GET)
- **URL**: `/api/v1/items`
- **Método**: `GET`
- **Descripción**: Lista todas las incidencias ordenadas por urgencia (5→1) y fecha
- **Autenticación**: Requerida (solo admin/worker)
- **Response (200 OK)**:
```json
[
  {
    "id": 1002,
    "nombre": "Carlos",
    "apellidos": "López García",
    "nif": "12345678A",
    "telefono": "666555444",
    "email": "carlos@example.com",
    "categoria": "Seguridad",
    "description": "Acto vandálico en la plaza central",
    "urgencia": 5,
    "fecha": "2026-01-02T10:30:00",
    "estado": "nuevo",
    "canal": "App",
    "direccion_persona": "Plaza Central",
    "ubicacion_incid": "37.190, -3.595"
  },
  {
    "id": 1001,
    "nombre": "Elena",
    "apellidos": "Pérez Garrido",
    "nif": "66608986C",
    "telefono": "656964241",
    "email": "elenaperez847@example.com",
    "categoria": "Movilidad",
    "description": "En la Avenida de los Maestros hay un bache en la acera",
    "urgencia": 3,
    "fecha": "2026-01-01T07:45:00",
    "estado": "nuevo",
    "canal": "App",
    "direccion_persona": "Calle Obispo Hu...",
    "ubicacion_incid": "37.185, -3.596"
  }
]
```

### 2. Obtener Detalle de Incidencia (GET)
- **URL**: `/api/v1/items/{item_id}`
- **Método**: `GET`
- **Descripción**: Obtiene detalles completos de una incidencia
- **Autenticación**: Requerida (solo admin/worker)
- **Response (200 OK)**: (mismo formato que listado)

### 3. Cambiar Estado de Incidencia (PATCH)
- **URL**: `/api/v1/items/{item_id}/status`
- **Método**: `PATCH`
- **Descripción**: Actualiza el estado de una incidencia
- **Autenticación**: Requerida (solo admin/worker)
- **Body (JSON)**:
```json
{
  "estado": "pendiente"
}
```

**Estados válidos**:
- `nuevo`: Recién reportada
- `pendiente`: En proceso
- `cerrado`: Resuelta

- **Response (200 OK)**:
```json
{
  "id": 1001,
  "nombre": "Elena",
  "apellidos": "Pérez Garrido",
  "nif": "66608986C",
  "telefono": "656964241",
  "email": "elenaperez847@example.com",
  "categoria": "Movilidad",
  "description": "En la Avenida de los Maestros hay un bache en la acera",
  "urgencia": 3,
  "fecha": "2026-01-01T07:45:00",
  "estado": "pendiente",
  "canal": "App",
  "direccion_persona": "Calle Obispo Hu...",
  "ubicacion_incid": "37.185, -3.596"
}
```

## Autenticación

Para acceder a endpoints protegidos, incluir header `Authorization`:
```
Authorization: Bearer {access_token}
```

**Trabajadores de ejemplo**:
- Email: `worker@ciudadai.com` / Contraseña: `SecurePass123`
- Email: `admin@ciudadai.com` / Contraseña: `AdminPass456`

## Documentación Interactiva

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Flujo ML (Machine Learning)

1. Ciudadano envía incidencia con **description**
2. `MLService.predict_urgency()` analiza el texto y predice urgencia (1-5)
3. `MLService.validate_category()` confirma o ajusta la categoría
4. Incidencia se almacena con urgencia y categoría predichas
5. Trabajador ve incidencias ordenadas por urgencia

## Base de Datos

Ejecutar migraciones:
```bash
psql -U postgres -d ciudadai < backend/migrations.sql
```

Esto crea:
- Tabla `workers`: Datos de trabajadores con contraseñas hasheadas (bcrypt)
- Tabla `incidents`: Todas las incidencias ciudadanas

## Instalación de Dependencias

```bash
cd backend
pip install -r requirements.txt
```

Dependencias clave:
- `fastapi`: Framework web
- `uvicorn`: Servidor ASGI
- `pydantic`: Validación de datos
- `passlib[bcrypt]`: Hash seguro de contraseñas

## Ejecución

```bash
cd backend
uvicorn src.app:app --reload --host 0.0.0.0 --port 8000
```

## Ejemplos de uso (curl)

### Crear incidencia
```bash
curl -X POST "http://localhost:8000/api/v1/citizen/incidents" \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Elena",
    "apellidos": "Pérez Garrido",
    "nif": "66608986C",
    "telefono": "656964241",
    "email": "elenaperez847@example.com",
    "categoria": "Movilidad",
    "description": "En la Avenida de los Maestros hay un bache en la acera",
    "canal": "App",
    "direccion_persona": "Calle Obispo Hu",
    "ubicacion_incid": "37.185, -3.596"
  }'
```

### Listar incidencias (requiere autenticación)
```bash
curl -X GET "http://localhost:8000/api/v1/items" \
  -H "Authorization: Bearer bootstrap-token"
```

### Cambiar estado
```bash
curl -X PATCH "http://localhost:8000/api/v1/items/1001/status" \
  -H "Authorization: Bearer bootstrap-token" \
  -H "Content-Type: application/json" \
  -d '{"estado": "pendiente"}'
```
