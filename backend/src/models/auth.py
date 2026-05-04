from pydantic import BaseModel, EmailStr, Field


class LoginInput(BaseModel):
    """Credenciales básicas para el login de ejemplo."""

    username: str = Field(example="api_user")
    password: str = Field(example="change_me")


class TokenResponse(BaseModel):
    """Respuesta mock que simula un access token OAuth2/JWT."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int


class CurrentUser(BaseModel):
    """Usuario autenticado disponible dentro de endpoints protegidos."""

    id: int | None = None
    username: str
    role: str = "citizen"  # "citizen" o "admin"
    nombre: str | None = None
    apellidos: str | None = None
    email: str | None = None
    nif: str | None = None
    telefono: str | None = None
    domicilio: str | None = None


class UserCreate(BaseModel):
    """Datos para crear un nuevo usuario."""

    nombre: str = Field(..., min_length=1, max_length=120)
    apellidos: str = Field(..., min_length=1, max_length=180)
    nif: str = Field(..., min_length=1, max_length=32)
    telefono: str = Field(..., min_length=1, max_length=24)
    email: EmailStr
    domicilio: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=8)


class UserLogin(BaseModel):
    """Credenciales para login de usuario registrado."""

    email: EmailStr
    password: str
