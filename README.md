# TechServ Backend

API de gestión de servicios técnicos con autenticación **JWT local**, usuarios/roles, tickets y equipos.

## Alcance actual

- FastAPI + PostgreSQL (Docker Compose) + Redis (configurado, aún sin uso en la app)
- Auth propia: **bcrypt** (contraseñas) + **python-jose** (JWT)
- Modelos: `companies`, `users`, `equipos`, `tickets`
- Endpoints de auth, usuarios, tickets y equipos
- CI con GitHub Actions
- Documentación OpenAPI en `/docs`

## Inicio rápido

```bash
cp .env.example .env
docker compose up -d db redis
python -m pip install -r requirements.txt
python -m alembic upgrade head
python -m scripts.seed_admin
python -m uvicorn app.main:app --reload
```

## Autenticación JWT (frontend)

### 1. Login

```http
POST /api/v1/auth/login
Content-Type: application/json

{"email": "admin@techserv.local", "password": "admin123"}
```

Respuesta:

```json
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

### 2. Usar el token

```typescript
const res = await fetch(`${API_URL}/api/v1/me`, {
  headers: { Authorization: `Bearer ${access_token}` },
})
```

### 3. Registro (cliente, técnico, etc. — no administrador)

```http
POST /api/v1/auth/register
{"email": "...", "password": "...", "full_name": "...", "role": "cliente"}
```

## Variables de entorno

| Variable | Descripción |
|----------|-------------|
| `JWT_SECRET_KEY` | Clave para firmar JWT (generar una larga y aleatoria) |
| `JWT_EXPIRE_MINUTES` | Duración del token (default **15**) |
| `DATABASE_URL` | PostgreSQL async (FastAPI) |
| `DATABASE_URL_SYNC` | PostgreSQL sync (Alembic) |
| `REDIS_URL` | Redis (reservado para uso futuro) |
| `CORS_ORIGINS` | Orígenes permitidos, separados por coma |

Generar secret:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Endpoints

Prefijo base: `/api/v1`

### Health

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| GET | `/health` | No | Health check (`status`, `timestamp`, `version`) |
| HEAD | `/health` | No | Igual que GET |

### Auth

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| POST | `/auth/register` | No | Registro (no permite rol `administrador`) |
| POST | `/auth/login` | No | Login → JWT |

### Usuarios

| Método | Ruta | Auth | Roles | Descripción |
|--------|------|------|-------|-------------|
| GET | `/me` | JWT | cualquiera | Perfil del usuario autenticado |
| GET | `/users/me` | JWT | cualquiera | Alias de `/me` |
| GET | `/users` | JWT | `administrador` | Listar todos los usuarios |
| GET | `/users/tecnicos` | JWT | `administrador`, `area_administrativa`, `supervisor` | Listar técnicos |
| GET | `/users/clientes` | JWT | `administrador`, `area_administrativa`, `supervisor` | Listar clientes |
| POST | `/users` | JWT | `administrador`, `area_administrativa` | Crear usuario (no permite `administrador`) |
| PATCH | `/users/{id}` | JWT | `administrador` | Actualizar usuario |

### Tickets

| Método | Ruta | Auth | Roles | Descripción |
|--------|------|------|-------|-------------|
| GET | `/tickets` | JWT | todos | Listar tickets (cliente: propios; técnico: asignados; resto: todos) |
| GET | `/tickets/{id}` | JWT | todos | Detalle de ticket (con scoping por rol) |
| POST | `/tickets` | JWT | `administrador`, `supervisor`, `cliente` | Crear ticket |
| PATCH | `/tickets/{id}` | JWT | `administrador`, `supervisor`, `tecnico` | Actualizar `estado` y/o `tecnico_id` |

Estados: `abierto`, `en_diagnostico`, `en_proceso`, `resuelto`  
Urgencias: `alta`, `media`, `baja`

### Equipos

| Método | Ruta | Auth | Roles | Descripción |
|--------|------|------|-------|-------------|
| GET | `/equipos` | JWT | todos | Listar equipos (cliente: solo los propios) |
| POST | `/equipos` | JWT | `administrador`, `supervisor`, `cliente` | Crear equipo |

## Crear el primer administrador

**Opción recomendada:** usar el script de seed después de migrar la base:

```bash
python -m scripts.seed_admin
```

Crea `admin@techserv.local` / `admin123` y la empresa demo **TechServ Demo**.

Alternativa manual vía Swagger:

1. `POST /auth/register` con rol `supervisor`
2. En DB: `UPDATE users SET role = 'administrador' WHERE email = '...';`
3. Login y usar `POST /users` para el resto

## Roles

`cliente`, `tecnico`, `supervisor`, `administrador`, `area_administrativa`

## Tests

```bash
python -m pytest
python -m pytest tests/test_api.py -v
python -m pytest tests/test_api.py::test_health -v
```

Suite actual: health, auth básica, `/me`, listado de usuarios y utilidades de seguridad (JWT, bcrypt).

## Documentación de diseño

- [Diagrama de clases](docs/diagrama-de-clases.md)
- [Diagrama E/R](docs/diagrama-er.md)
- [Diagrama de secuencias](docs/diagrama-secuencias.md)
- [Casos de uso](docs/diagrama-casos-de-uso.md)
- [Diagrama de actividades](docs/diagrama-actividades.md)

> **Nota:** Auth ya no usa Supabase. JWT y usuarios viven en PostgreSQL local.
