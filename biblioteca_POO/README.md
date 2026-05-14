# 📚 Sistema de Gestión de Biblioteca

Aplicación de escritorio para la gestión integral de una biblioteca: socios, empleados, catálogo de materiales, préstamos y reservas. Desarrollada en Python con interfaz gráfica Tkinter y base de datos SQLite.

---

## Requisitos

- Python 3.10 o superior
- No requiere librerías externas — solo módulos de la biblioteca estándar de Python (`tkinter`, `sqlite3`, `hashlib`, `threading`)

---

## Instalación y primer arranque

**1. Clona o descarga el proyecto** y asegúrate de que la estructura de carpetas es la correcta (ver más abajo).

**2. Abre una terminal en la carpeta `biblioteca_POO/`**
Puedes hacer doble clic en `abrir_terminal.bat` o abrir cmd manualmente.

**3. Ejecuta la aplicación:**
```bash
python main.py
```

La base de datos `data/biblioteca.db` se crea automáticamente en el primer arranque.

---


## Acceso al sistema

El login se realiza con **email + contraseña**. La pantalla de inicio detecta automáticamente si el usuario es un socio o un empleado y abre la ventana correspondiente.

### Usuarios de prueba (si usaste `init_db.py`)

| Tipo                          | Email de ejemplo        | Contraseña  |
|-------------------------------|-------------------------|-------------|
| Socio                         | `socio1@biblioteca.com` | `123456`    |
| Empleado (Auxiliar)           | `staff1@biblioteca.com` | `1234`      |
| Empleado (Bibliotecario)      | `staff2@biblioteca.com` | `1234`      |
| Empleado (Admin)              | `staff3@biblioteca.com` | `1234`      |

---

## Guía de uso por perfil

### 👤 Socio

| Pestaña       | Qué puedes hacer 
| **Catálogo**  | Buscar materiales por título, autor, editorial, tipo o ubicación. Filtrar solo los disponibles. Reservar un material disponible (tendrás 48h para recogerlo). 
| **Mis Préstamos** | Ver tus préstamos activos, retrasados e histórico. Ver tus reservas y su estado. 
| **Mi Cuenta** | Cambiar tu email o contraseña. 

### 🔧 Empleado — Auxiliar

| Pestaña | Qué puedes hacer    
| **Reservas Pendientes**       | Ver todas las reservas activas. Formalizar la recogida cuando el socio llega al mostrador introduciendo el ID de la reserva. 
| **Préstamos Activos**         | Ver todos los préstamos en curso. Registrar devoluciones por ID de préstamo. Crear una reserva para un socio usando los botones 🔍 para buscar socio y material visualmente.
| **Mi Cuenta**                 | Cambiar email o contraseña. 

### 📚 Empleado — Bibliotecario

Todo lo del Auxiliar, más:

| Pestaña       | Qué puedes hacer |

| **Catálogo**  | Añadir, editar y eliminar materiales. El ID se genera automáticamente según el tipo (MFL- para libros, MFR- para revistas, etc.). |
| **Socios**    | Buscar socios por nombre, email o ID en tiempo real. Ver el detalle completo de un socio (doble clic o botón "Ver detalle"): sus préstamos activos, reservas recientes y asignarle un préstamo directo desde esa ventana. Sancionar o levantar la sanción de un socio. |

### 🔑 Empleado — Administrador

Todo lo del Bibliotecario, más:

| Pestaña       | Qué puedes hacer |
| **Empleados** | Ver la lista de empleados. Crear nuevos empleados (ID automático UE-XXXX). Cambiar el rol de cualquier empleado (excepto el propio). |

---

## Sistema de IDs automáticos

Los IDs se generan solos al crear cualquier registro. No es necesario introducirlos manualmente.

| Prefijo| Tipo            |
| `US-`  | Socio           |
| `UE-`  | Empleado        |
| `MFL-` | Libro           |
| `MFR-` | Revista         |
| `MFD-` | Dispositivo     |
| `MFJ-` | Juego de Mesa   |
| `MFG-` | Recurso Digital |
| `P-`   | Préstamo        |
| `R-`   | Reserva         |

---

## Reservas: cómo funciona el ciclo completo

```
Socio reserva en catálogo (o empleado reserva en mostrador)
            ↓
  Material pasa a "Pendiente de Recogida"
            ↓
    El socio tiene 48 horas para presentarse
            ↓
    ┌───────────────────────────────────┐
    │  Llega a tiempo                   │  No llega
    │  Auxiliar formaliza la recogida   │  El sistema libera el material
    │  → Se crea el préstamo            │  → El cupo del socio se devuelve
    └───────────────────────────────────┘  sin sanción
```

El temporizador de expiración de reservas se ejecuta automáticamente cada 5 minutos mientras la aplicación está abierta, y también al arrancar (para cubrir el tiempo que la app ha estado cerrada).

---

## Estructura del proyecto

```
biblioteca_POO/
├── main.py                     ← Punto de entrada
├── abrir_terminal.bat          ← Abre cmd aquí
├── README.md
├── Bilioteca.txt
│
├── assets/                     ← Contraseñas y recursos
├── data/
│   └── biblioteca.db           ← Base de datos SQLite
├── docs/                       ← Documentación y memoria del proyecto
│
└── biblioteca/                 ← Paquete principal
    ├── models.py               ← Clases del dominio (materiales, usuarios, transacciones)
    ├── db.py                   ← Acceso a datos SQLite (Repository)
    ├── controllers.py          ← Lógica de negocio y reglas del sistema (MVC)
    │
    └── ui/
        ├── theme.py            ← Paleta de colores y fuentes
        ├── widgets.py          ← Componentes reutilizables (botones, tablas, campos)
        ├── app_window.py       ← Orquestador: ciclo login → sesión → logout
        ├── login_view.py       ← Pantalla de acceso
        ├── socio_view.py       ← Interfaz del socio
        ├── empleado_view.py    ← Interfaz del empleado (pestañas según rol)
        ├── formularios.py      ← Formularios de creación y edición
        └── selectores.py       ← Ventanas de búsqueda y detalle de usuarios
```

