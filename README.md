# 🐟 Fish Inventory API

API REST para sistema de inventario de negocio de compra y venta de pescado al por mayor.

## Stack Tecnológico

| Capa | Tecnología |
|------|-----------|
| Framework | FastAPI |
| ORM | SQLAlchemy 2.0 |
| Migraciones | Alembic |
| Base de datos | MySQL 8.x |
| Validación | Pydantic v2 |
| Auth | JWT (python-jose) + Refresh Tokens |
| Hashing | bcrypt (passlib) |
| Servidor | Uvicorn |

---

## Estructura del Proyecto

```
fish_inventory_api/
├── app/
│   ├── domain/                     # Entidades y contratos de negocio
│   │   ├── entities/               # User, Category, Product, Order, Delivery
│   │   ├── repositories/           # Interfaces abstractas (ABCs)
│   │   └── services/               # auth_service.py
│   │
│   ├── application/                # Lógica de aplicación
│   │   ├── dto/                    # Pydantic v2 schemas (request / response)
│   │   └── use_cases/              # Un archivo por entidad con todos sus casos de uso
│   │
│   ├── infrastructure/
│   │   ├── config/settings.py      # Variables de entorno (BaseSettings)
│   │   ├── database/
│   │   │   ├── session.py          # Motor SQLAlchemy + get_db()
│   │   │   ├── models/             # ORM models (mapean a tablas MySQL)
│   │   │   └── repositories/       # Implementaciones concretas de los repos
│   │   └── security/
│   │       ├── jwt_handler.py      # Creación y decodificación de JWT
│   │       └── password_handler.py # Hash bcrypt
│   │
│   ├── presentation/
│   │   └── api/
│   │       ├── routers/            # Un router por entidad
│   │       ├── dependencies/       # get_current_user, require_roles, etc.
│   │       └── middleware/         # Global error handler
│   │
│   └── shared/
│       ├── constants/roles.py      # Enums: UserRole, OrderStatus, DeliveryType, WeightUnit
│       ├── exceptions/             # AppException, NotFoundException, etc.
│       ├── responses/              # ApiResponse, PaginatedResponse
│       └── utils/weight_converter.py  # kg ↔ lb ↔ ton ↔ oz
│
├── migrations/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/001_initial.py
│
├── main.py
├── seed.py
├── requirements.txt
├── alembic.ini
├── .env.example
└── README.md
```

---

## Instalación y Configuración

### 1. Prerrequisitos

- Python 3.12+
- MySQL 8.x en ejecución

### 2. Clonar y crear entorno virtual

```bash
cd fish_inventory_api
python -m venv venv 

ad.-

# Linux / Mac
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

```bash
cp .env.example .env
```

Editar `.env`:

```env
APP_NAME=FishInventoryAPI
APP_VERSION=1.0.0
DEBUG=True

DB_HOST=localhost
DB_PORT=3306
DB_NAME=fish_inventory_db
DB_USER=root
DB_PASSWORD=tu_password_real

JWT_SECRET=un_secreto_muy_largo_y_aleatorio_de_al_menos_32_caracteres
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60
JWT_REFRESH_EXPIRE_DAYS=7
```

### 5. Crear la base de datos en MySQL

```sql
CREATE DATABASE fish_inventory_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 6. Ejecutar migraciones

```bash
alembic upgrade head
```

### 7. Crear el usuario administrador inicial

```bash
python seed.py
```

Salida esperada:
```
✅ Usuario administrador creado exitosamente:
   Usuario:    admin
   Contraseña: Admin1234!
   Rol:        admin
   ID:         1
⚠️  CAMBIA LA CONTRASEÑA inmediatamente después del primer inicio de sesión.
```

### 8. Iniciar el servidor

```bash
uvicorn main:app --reload --port 8000
```

O directamente:
```bash
python main.py
```

### 9. Abrir documentación interactiva

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health check: http://localhost:8000/health

---

## Autenticación

Todos los endpoints (excepto `/health`) requieren un **Bearer Token JWT**.

### Flujo de autenticación

```
POST /api/v1/auth/login
Body: { "username": "admin", "password": "Admin1234!" }

Respuesta:
{
  "success": true,
  "data": {
    "access_token": "eyJ...",
    "refresh_token": "eyJ...",
    "token_type": "bearer",
    "expires_in": 3600
  }
}
```

Usar el `access_token` en el header:
```
Authorization: Bearer eyJ...
```

---

## Endpoints

### 🔐 Autenticación (`/api/v1/auth`)

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/auth/login` | Iniciar sesión |
| POST | `/auth/refresh` | Renovar access token |
| POST | `/auth/logout` | Revocar refresh token |

### 👤 Usuarios (`/api/v1/usuarios`) — Solo Admin

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/usuarios` | Crear usuario |
| GET | `/usuarios` | Listar usuarios (paginado + filtros) |
| GET | `/usuarios/{id}` | Obtener usuario por ID |
| PUT | `/usuarios/{id}` | Editar usuario |
| DELETE | `/usuarios/{id}` | Eliminar usuario (soft delete) |

### 📦 Categorías (`/api/v1/categorias`) — Solo Admin

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/categorias` | Crear categoría |
| GET | `/categorias` | Listar categorías |
| GET | `/categorias/{id}` | Obtener categoría |
| PUT | `/categorias/{id}` | Editar categoría |
| DELETE | `/categorias/{id}` | Eliminar categoría |

### 🐠 Productos (`/api/v1/productos`)

| Método | Ruta | Rol | Descripción |
|--------|------|-----|-------------|
| POST | `/productos` | Admin | Crear producto |
| GET | `/productos` | Admin | Listar productos |
| GET | `/productos/{id}` | Admin / Empleado | Admin: info completa. Empleado: solo stock |
| PUT | `/productos/{id}` | Admin / Empleado | Admin: editar todo. Empleado: solo editar stock |
| PATCH | `/productos/{id}/stock` | Admin / Empleado | Actualizar únicamente el stock |
| DELETE | `/productos/{id}` | Admin | Eliminar producto |

### 🛒 Pedidos (`/api/v1/pedidos`)

| Método | Ruta | Roles | Descripción |
|--------|------|-------|-------------|
| POST | `/pedidos` | Admin, Empleado | Crear pedido |
| GET | `/pedidos` | Admin, Repartidor, Empleado | Listar pedidos (filtrado por rol) |
| GET | `/pedidos/{id}` | Admin, Repartidor, Empleado | Ver pedido (filtrado por rol) |
| PUT | `/pedidos/{id}` | Admin, Repartidor, Empleado | Editar pedido |
| DELETE | `/pedidos/{id}` | Admin, Empleado | Cancelar pedido |

**Restricciones por rol:**
- **Repartidor**: solo ve y edita los pedidos que le están asignados
- **Empleado**: solo cancela pedidos que él mismo creó

### 🚚 Entregas (`/api/v1/entregas`)

| Método | Ruta | Roles | Descripción |
|--------|------|-------|-------------|
| POST | `/entregas` | Admin, Repartidor, Empleado | Registrar entrega |
| GET | `/entregas` | Admin, Repartidor | Listar entregas |
| GET | `/entregas/{id}` | Admin, Repartidor | Ver entrega |
| PUT | `/entregas/{id}` | Admin, Repartidor | Editar entrega |
| DELETE | `/entregas/{id}` | Admin | Eliminar entrega |

**Lógica de stock automática:**
- `tipo=compra` → **incrementa** el stock de los productos en la entrega
- `tipo=venta` → **descuenta** el stock de los productos (valida disponibilidad)
- Al editar ítems, el sistema revierte el stock anterior antes de aplicar los nuevos valores

---

## Conversión de Pesos

Todos los pedidos, entregas e inventario se almacenan en **kilogramos (kg)**.  
Cada respuesta incluye el campo `stock` / `cantidad` / `total` con conversión automática:

```json
{
  "stock_kg": "500.000000",
  "stock": {
    "kg": 500.0,
    "lb": 1102.31,
    "ton": 0.5,
    "oz": 17636.98
  }
}
```

---

## Formato de Respuestas

### Éxito
```json
{
  "success": true,
  "message": "Operación exitosa",
  "data": { ... }
}
```

### Listado paginado
```json
{
  "success": true,
  "message": "Operación exitosa",
  "data": [ ... ],
  "total": 45,
  "page": 1,
  "page_size": 20,
  "total_pages": 3
}
```

### Error
```json
{
  "success": false,
  "message": "Descripción del error",
  "errors": [
    { "field": "username", "message": "El campo es requerido", "type": "missing" }
  ]
}
```

---

## Roles y Permisos

| Acción | Admin | Repartidor | Empleado |
|--------|:-----:|:----------:|:--------:|
| Login | ✅ | ✅ | ✅ |
| CRUD Usuarios | ✅ | ❌ | ❌ |
| CRUD Categorías | ✅ | ❌ | ❌ |
| Crear Producto | ✅ | ❌ | ❌ |
| Ver Producto (completo) | ✅ | ❌ | ❌ |
| Ver Producto (solo stock) | ✅ | ❌ | ✅ |
| Editar Producto (completo) | ✅ | ❌ | ❌ |
| Actualizar solo stock | ✅ | ❌ | ✅ |
| Eliminar Producto | ✅ | ❌ | ❌ |
| Crear Pedido | ✅ | ❌ | ✅ |
| Ver Pedido | ✅ | ✅ (solo asignados) | ✅ (solo propios) |
| Editar Pedido | ✅ | ✅ (solo asignados) | ✅ |
| Cancelar Pedido | ✅ | ❌ | ✅ (solo propios) |
| Crear Entrega | ✅ | ✅ | ✅ |
| Ver Entrega | ✅ | ✅ (solo propias) | ❌ |
| Editar Entrega | ✅ | ✅ (solo propias) | ❌ |
| Eliminar Entrega | ✅ | ❌ | ❌ |

---

## Modelo de Base de Datos

```
users (id, username, password_hash, role, nombre, correo, telefono, documento, is_active, ...)
  ├── refresh_tokens (id, user_id, token, expires_at, is_revoked)
  ├── categories (id, nombre, descripcion, activa, ...)
  │     └── products (id, categoria_id, nombre, precio, stock_kg, imagen, activo, ...)
  │           ├── order_items (id, pedido_id, producto_id, cantidad_kg, precio_unitario_kg)
  │           └── delivery_items (id, entrega_id, producto_id, cantidad_kg)
  ├── orders (id, nombre_cliente, documento_cliente, id_domiciliario→users, lugar, fecha, precio_total, estado, ...)
  │     └── order_items
  └── deliveries (id, tipo[compra/venta], fecha_hora, observaciones, ...)
        └── delivery_items
```

Todos los campos principales incluyen: `created_at`, `updated_at`, `deleted_at`, `created_by`, `updated_by`.

---

## Crear una nueva migración

```bash
# Después de modificar un ORM model:
alembic revision --autogenerate -m "descripcion_del_cambio"
alembic upgrade head
```

## Revertir migración

```bash
alembic downgrade -1   # Revertir la última
alembic downgrade base # Revertir todo
```
#   F R E S C O P E Z  
 