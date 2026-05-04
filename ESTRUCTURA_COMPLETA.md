# ESTRUCTURA COMPLETA DE LA APLICACIÓN CiudadIA

## 1. TEMPLATES HTML

### Ubicación: `/frontend/templates/` (12 archivos)

```
frontend/templates/
├── admin_dashboard.html          # Panel principal del administrador
├── admin_login.html              # Pantalla de login para administradores
├── admin_ticket_edit.html        # Edición de tickets por admin
├── base.html                     # Template base (herencia)
├── citizen_dashboard.html        # Panel principal del ciudadano
├── citizen_report.html           # Formulario para reportar incidencia
├── dashboard.html                # Dashboard genérico (heredado)
├── home.html                     # Página de inicio
├── items.html                    # Listado de items (heredado)
├── login.html                    # Pantalla de login genérica
├── register.html                 # Registro de nuevos usuarios
└── ticket_success.html           # Confirmación de ticket enviado
```

### Templates Clave:

**admin_dashboard.html**
- Muestra información del usuario admin
- Badge de rol
- Estadísticas: total, pending_review, resolved
- Tabla de tickets recientes con: ID, Categoría, Estado, Urgencia, Ubicación, Descripción, Fecha
- Botón "Editar" para cada ticket
- Variables esperadas:
  - `current_user` (username, role)
  - `admin_data` (content.title, content.description)
  - `admin_stats` (total, pending_review, resolved)
  - `admin_tickets` (lista de tickets)

**citizen_dashboard.html**
- Formulario para reportar incidencias
- Campo "Categoría" (select: movilidad, limpieza, alumbrado_publico, parques_y_jardines, mobiliario_urbano, otros)
- Campo "Descripción" (textarea max 300 caracteres)
- Campo "Ubicación de la incidencia" (text input max 255)
- Listado de mis reportes con estado (Pendiente/Resuelto)
- Variables esperadas:
  - `current_user` (username, role)
  - `citizen_tickets` (lista de tickets del usuario)
  - `form_error` (mensaje de error si existe)

---

## 2. ESTRUCTURA DE DIRECTORIOS COMPLETA

```
CiudadIA/
├── backend/
│   ├── src/
│   │   ├── routers/
│   │   │   ├── admin_router.py          # Endpoints admin
│   │   │   ├── auth_router.py           # Login/auth
│   │   │   ├── citizen_router.py        # Endpoints ciudadano
│   │   │   ├── health_router.py         # Health checks
│   │   │   ├── items_router.py          # Items CRUD
│   │   │   ├── tickets_router.py        # Tickets CRUD
│   │   │   └── user_router.py           # User registration/login
│   │   ├── services/
│   │   │   ├── auth_service.py          # Lógica autenticación
│   │   │   ├── ticket_service.py        # Lógica de tickets
│   │   │   ├── user_service.py          # Lógica de usuarios
│   │   │   └── anonymizer.py            # Anonimización de datos
│   │   ├── models/
│   │   │   ├── auth.py                  # Modelos de auth
│   │   │   ├── tickets.py               # Modelos de tickets
│   │   │   ├── errors.py                # Modelos de errores
│   │   │   └── health.py                # Modelos de health
│   │   ├── db/
│   │   │   ├── models.py                # ORM models
│   │   │   ├── session.py               # Database session
│   │   │   └── init_db.py               # Database initialization
│   │   ├── clients/
│   │   │   ├── ml_client.py             # Cliente ML service
│   │   │   └── __init__.py
│   │   ├── common/
│   │   │   ├── responses.py             # Response templates
│   │   │   └── __init__.py
│   │   ├── app.py                       # Aplicación principal
│   │   ├── config.py                    # Configuración
│   │   ├── deps.py                      # Dependencias (auth)
│   │   ├── middleware.py                # Middlewares HTTP
│   │   ├── constants.py                 # Constantes
│   │   ├── spec.py                      # OpenAPI spec
│   │   └── __init__.py
│   ├── tests/
│   │   ├── test_admin_endpoints.py
│   │   ├── test_auth.py
│   │   ├── test_health.py
│   │   ├── test_ticket_service.py
│   │   ├── test_tickets_contract.py
│   │   ├── test_tickets_router.py
│   │   ├── test_anonymizer.py
│   │   ├── conftest.py
│   │   └── __init__.py
│   ├── requirements.txt
│   ├── pyproject.toml
│   └── .env.example
│
├── frontend/
│   ├── routes/
│   │   ├── pages.py                     # Rutas principales (SSR)
│   │   ├── auth.py                      # Rutas de autenticación
│   │   └── __init__.py
│   ├── services/
│   │   ├── api_client.py                # Cliente HTTP al backend
│   │   └── __init__.py
│   ├── schemas/
│   │   ├── api.py                       # Schemas de API
│   │   └── __init__.py
│   ├── templates/
│   │   └── [12 archivos HTML]
│   ├── static/
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   ├── app.py                           # Aplicación FastAPI
│   ├── config.py                        # Configuración frontend
│   ├── requirements.txt
│   ├── tests/
│   │   └── test_smoke.py
│   └── .env.example
│
├── docker-compose.yml
├── .env
├── .gitignore
└── README.md
```

---

## 3. ENDPOINTS BACKEND - ESTRUCTURA DE RUTAS

### URL Base: `http://localhost:8000/api/v1`

### **Auth Router** (`/api/v1/auth`)
```
POST   /api/v1/auth/login
       └─ Params: {username, password}
       └─ Returns: {access_token, token_type, user_id, username, role}

POST   /api/v1/auth/admin/login
       └─ Params: {username, password}
       └─ Returns: {access_token, token_type, user_id, username, role}

GET    /api/v1/auth/me
       └─ Headers: Authorization: Bearer {token}
       └─ Returns: {id, username, role, email}
```

### **User Router** (`/api/v1/user`)
```
POST   /api/v1/user/register
       └─ Params: {nombre, apellidos, nif, telefono, email, domicilio, password}
       └─ Returns: {message, user_id, email}

POST   /api/v1/user/login
       └─ Params: {email, password}
       └─ Returns: {access_token, token_type, user_id, username, role}
```

### **Admin Router** (`/api/v1/admin`)
```
GET    /api/v1/admin/dashboard
       └─ Auth: Requiere rol admin
       └─ Returns: {message, username, role, content}

GET    /api/v1/admin/stats
       └─ Auth: Requiere rol admin
       └─ Returns: {total, pending_review, resolved, by_category, by_urgency}

GET    /api/v1/admin/tickets
       └─ Auth: Requiere rol admin
       └─ Query: status?, skip=0, limit=50
       └─ Returns: [{id, categoria, status, prediccion_urgencia, ubicacion_incidencia, description, fecha}]

GET    /api/v1/admin/tickets/{ticket_id}
       └─ Auth: Requiere rol admin
       └─ Returns: {id, categoria, status, description, ubicacion_incidencia, fecha, admin_notes}

PATCH  /api/v1/admin/tickets/{ticket_id}/review
       └─ Auth: Requiere rol admin
       └─ Body: {status, notes}
       └─ Returns: ticket actualizado
```

### **Citizen Router** (`/api/v1/citizen`)
```
POST   /api/v1/citizen/tickets
       └─ Auth: Requiere usuario registrado (token)
       └─ Body: {categoria, description, ubicacion_incidencia}
       └─ Returns: {id, categoria, description, ubicacion_incidencia, status, fecha}

GET    /api/v1/citizen/tickets
       └─ Auth: Requiere usuario registrado (token)
       └─ Returns: [{id, categoria, status, description, ubicacion_incidencia, fecha}]

GET    /api/v1/citizen/dashboard
       └─ Auth: Público
       └─ Returns: {message, content}

GET    /api/v1/citizen/tickets/{ticket_id}/status
       └─ Auth: Público
       └─ Returns: {id, estado, categoria, fecha_creacion, description, ubicacion_incidencia}
```

### **Tickets Router** (`/api/v1/tickets`)
```
GET    /api/v1/tickets/spec
       └─ Auth: Público
       └─ Returns: {input_fields, persisted_fields, anonymized_fields, urgency_scale, categories, statuses}

POST   /api/v1/tickets
       └─ Auth: Público (sin autenticación)
       └─ Body: {nombre, apellidos, nif, telefono, email, categoria, description, ubicacion_incidencia}
       └─ Returns: {id, categoria, status, prediccion_urgencia, fecha}

GET    /api/v1/tickets
       └─ Auth: Requiere admin
       └─ Query: status?, skip=0, limit=50
       └─ Returns: [{ticket_summary}]

GET    /api/v1/tickets/{ticket_id}
       └─ Auth: Requiere admin
       └─ Returns: {ticket_detail}

PATCH  /api/v1/tickets/{ticket_id}/review
       └─ Auth: Requiere admin
       └─ Body: {status, notes}
       └─ Returns: {ticket_updated}
```

### **Items Router** (`/api/v1/items`)
```
GET    /api/v1/items
       └─ Auth: Requiere token
       └─ Returns: {items: []}
```

### **Health Router** (`/api/v1/health`)
```
GET    /api/v1/health
       └─ Auth: Público
       └─ Returns: {status, timestamp}
```

---

## 4. MÉTODOS EN `api_client.py` (Frontend)

### Ubicación: `/frontend/services/api_client.py`

```python
class BackendApiClient:
    def __init__(self, base_url: str)
        # Inicializa el cliente con URL base del backend
    
    # ============ AUTENTICACIÓN ============
    async def login(token: str) -> TokenResponse
        # POST /api/v1/auth/login
        # Parámetros: {username, password}
        # Retorna: TokenResponse (access_token, token_type, etc)
    
    async def admin_login(username: str, password: str) -> TokenResponse
        # POST /api/v1/auth/admin/login
        # Login especial para administradores
        # Retorna: TokenResponse
    
    async def login_user(email: str, password: str) -> TokenResponse
        # POST /api/v1/user/login
        # Login para usuarios registrados
        # Retorna: TokenResponse
    
    async def me(token: str) -> CurrentUser
        # GET /api/v1/auth/me
        # Obtiene información del usuario autenticado
        # Retorna: CurrentUser {id, username, role, email}
    
    async def register_user(
        nombre: str, apellidos: str, nif: str, 
        telefono: str, email: str, domicilio: str, 
        password: str
    ) -> dict
        # POST /api/v1/user/register
        # Registra un nuevo usuario
        # Retorna: {message, user_id}
    
    # ============ ITEMS ============
    async def items(token: str) -> ItemsResponse
        # GET /api/v1/items
        # Obtiene lista de items
        # Retorna: ItemsResponse {items: []}
    
    # ============ TICKETS ============
    async def create_ticket(payload: dict) -> dict
        # POST /api/v1/citizen/tickets
        # Crea ticket sin autenticación
        # Retorna: {id, categoria, status, fecha}
    
    async def create_ticket_authenticated(
        token: str, 
        payload: dict
    ) -> dict
        # POST /api/v1/citizen/tickets (con auth)
        # Crea ticket con usuario autenticado
        # Retorna: {id, categoria, status, fecha}
    
    async def get_user_tickets(token: str) -> list[dict]
        # GET /api/v1/citizen/tickets
        # Obtiene tickets del usuario autenticado
        # Retorna: [{id, categoria, status, description, fecha}]
```

### Esquemas de Respuesta (en `schemas/api.py`):

```python
class TokenResponse:
    access_token: str
    token_type: str
    user_id: Optional[int]
    username: Optional[str]
    role: Optional[str]

class CurrentUser:
    id: int
    username: str
    role: str
    email: Optional[str]

class ItemsResponse:
    items: list[dict]
```

---

## 5. RUTAS FRONTEND - ESTRUCTURA SSR

### Ubicación: `/frontend/routes/pages.py`

```
GET  /                    # Home (redirige a dashboard según rol)
GET  /register            # Página de registro
GET  /admin/login         # Página de login admin

POST /auth/login          # Procesa login (ciudadano/admin dual)
POST /auth/register       # Procesa registro
POST /auth/admin/login    # Procesa login admin

GET  /dashboard           # Dashboard genérico (heredado)

GET  /admin/dashboard     # Dashboard administrador
GET  /admin/tickets/{id}  # Detalle de ticket (admin)
POST /admin/tickets/{id}/review  # Revisar ticket (admin)

GET  /citizen/dashboard   # Dashboard ciudadano
GET  /citizen/report      # Formulario de reporte (redirige a /)
POST /citizen/report      # Procesa nuevo reporte

POST /logout              # Cierra sesión
```

---

## 6. ESTRUCTURA ANTERIOR (git history)

### Cambios Recientes:
- **f3a305e**: "Cambiar el login como usuario" - Modificó flujo de login
- **62fa291**: "Modificar ext. tlfno, anadir mejoras en panel administrativo"
- **5793385**: "Conectar frontend y backend, y corregir errores"
- **290c7ab**: "Cambiar atributos del ticket y tests"
- **c6ecf9a**: "Implementar la primera versión del backend de la aplicación"
- **8bbd653**: "Cambiar frontend: usuario + administrador"

### Cambio Anterior (páginas.py):
```python
# VERSIÓN ANTERIOR (sin admin/login dual):
@router.post("/auth/login")
async def login(request: Request, email: str = Form(...), password: str = Form(...)):
    # Solo intenta login_user (usuario registrado)
    # No intenta admin_login primero
    try:
        token_response = await api_client.login_user(email, password)
        request.session["access_token"] = token_response.access_token
        request.session["role"] = "citizen"  # Siempre citizen
        return RedirectResponse(url="/citizen/dashboard", status_code=303)
    except HTTPStatusError as exc:
        error_msg = _translate_api_error(exc, "Credenciales inválidas")
        return templates.TemplateResponse("home.html", {"request": request, "error": error_msg})

# VERSIÓN ACTUAL (intenta admin primero, luego user):
@router.post("/auth/login")
async def login(request: Request, email: str = Form(...), password: str = Form(...)):
    credential = email.strip()
    try:
        # 1) Attempt admin login first
        admin_token = await api_client.admin_login(credential, password)
        return await _set_session_and_redirect_by_role(request, admin_token.access_token)
    except (HTTPStatusError, RequestError) as exc:
        # Si no es error de auth, saca el error inmediatamente
        if exc.response is not None and exc.response.status_code != 401:
            error_msg = _translate_api_error(exc, "Credenciales inválidas")
            return templates.TemplateResponse("home.html", {"request": request, "error": error_msg})
    
    try:
        # 2) Fallback to registered user login
        user_token = await api_client.login_user(credential, password)
        return await _set_session_and_redirect_by_role(request, user_token.access_token)
    except (HTTPStatusError, RequestError) as exc:
        error_msg = _translate_api_error(exc, "Credenciales inválidas")
        return templates.TemplateResponse("home.html", {"request": request, "error": error_msg})
```

---

## 7. VARIABLES DE ENTORNO CONFIGURABLES

### Backend (.env):
```
APP_NAME=CiudadIA
APP_VERSION=0.1.0
APP_ENV=dev
APP_HOST=0.0.0.0
APP_PORT=8000
API_PREFIX=/api/v1

DB_HOST=localhost
DB_PORT=5432
DB_NAME=ciudadia
DB_USER=ciudadia_user
DB_PASSWORD=your_password

ML_SERVICE_URL=http://ml_service:8001
ML_SERVICE_TIMEOUT=10.0

SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Frontend (.env):
```
FRONTEND_APP_NAME=CiudadIA Frontend
FRONTEND_APP_ENV=dev
FRONTEND_APP_HOST=0.0.0.0
FRONTEND_APP_PORT=8500
BACKEND_BASE_URL=http://127.0.0.1:8000
FRONTEND_SECRET_KEY=your-frontend-secret
```

---

## 8. RESUMEN DE DATOS/CONTEXTO TEMPLATES

### admin_dashboard.html
Necesita en contexto:
- `current_user`: CurrentUser (username, role)
- `admin_data`: dict con content.title y content.description
- `admin_stats`: dict con total, pending_review, resolved
- `admin_tickets`: list[dict] con tickets recientes

### citizen_dashboard.html
Necesita en contexto:
- `current_user`: CurrentUser (username)
- `citizen_tickets`: list[dict] con tickets del usuario
- `form_error`: str (opcional, mensaje de error)

---

## 9. CATEGORÍAS DE TICKETS (Enumeraciones)

```
"movilidad"
"limpieza"
"alumbrado_publico"
"parques_y_jardines"
"mobiliario_urbano"
"otros"
```

## 10. ESTADOS DE TICKETS (TicketStatus)

```
"pending_classification"
"pending_review"
"resolved"
"rejected"
```

