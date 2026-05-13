"""
init_db.py

Script de inicialización para el producto final.
Crea el entorno de carpetas y puebla la base de datos con datos de prueba realistas.
"""

# Como init_db.py está justo al lado de la carpeta "biblioteca", 
# solo tenemos que decirle que entre en ella directamente.
import os
from biblioteca.db import BibliotecaRepository
from biblioteca.models import (
    Socio, Empleado, RolEmpleado, Libro, Revista, 
    Dispositivo, TipoDispositivo, JuegoDeMesa, RecursoDigital
)

def inicializar_sistema():
    """
    Prepara la estructura de carpetas y genera la carga inicial de datos.
    """
    # 1. Aseguramos que la carpeta data existe para el producto final
    if not os.path.exists("data"):
        os.makedirs("data")
    
    # 2. Inicializamos el repositorio en la ruta definitiva
    repo = BibliotecaRepository(ruta_db="data/biblioteca.db")
    
    print("Carpeta 'data/' verificada y base de datos conectada.")
    
    # --- GENERACIÓN DE 20 PERSONAS (15 Socios y 5 Empleados) ---
    print("Generando usuarios de prueba...")
    
    # Creamos 15 socios con perfiles variados
    for i in range(1, 16):
        nuevo_socio = Socio(
            id_usuario=f"S-{i:03d}",
            nombre=f"Socio{i}",
            apellidos=f"Apellido{i}",
            email=f"socio{i}@biblioteca.com"
        )
        repo.guardar_usuario(nuevo_socio)
    
    # Creamos 5 empleados con diferentes roles
    roles = [RolEmpleado.ADMIN, RolEmpleado.BIBLIOTECARIO, RolEmpleado.AUXILIAR]
    for i in range(1, 6):
        rol_asignado = roles[i % len(roles)]
        nuevo_empleado = Empleado(
            id_usuario=f"E-{i:03d}",
            nombre=f"Empleado{i}",
            apellidos=f"Staff",
            email=f"staff{i}@biblioteca.com",
            rol=rol_asignado
        )
        repo.guardar_usuario(nuevo_empleado)

    # --- GENERACIÓN DE 30 MATERIALES ---
    print("Generando catálogo de materiales...")

    # 10 Libros
    for i in range(1, 11):
        libro = Libro(
            codigo_id=f"LIB-{i:03d}",
            titulo=f"Libro de Prueba {i}",
            autor=f"Autor Famoso {i}",
            paginas=100 + (i * 20),
            isbn=f"978-84-{i:05d}",
            ubicacion=f"Pasillo {i%5 + 1}, Estante {i}"
        )
        repo.guardar_material(libro)

    # 5 Revistas
    for i in range(1, 6):
        revista = Revista(
            codigo_id=f"REV-{i:03d}",
            titulo=f"Revista Científica Vol. {i}",
            editorial="Science Press",
            numero_edicion=i * 10,
            issn=f"1234-567{i}",
            ubicacion="Hemeroteca, Planta 1"
        )
        repo.guardar_material(revista)

    # 5 Dispositivos
    tipos = [TipoDispositivo.ORDENADOR, TipoDispositivo.TABLET, TipoDispositivo.E_READER]
    for i in range(1, 6):
        dispositivo = Dispositivo(
            codigo_id=f"DIS-{i:03d}",
            titulo=f"Equipo Multimedia {i}",
            tipo_dispositivo=tipos[i % len(tipos)],
            fabricante="TechCorp",
            so="SystemOS v2",
            numero_serie=f"SN-{i}XYZ",
            ubicacion="Sala de Informática"
        )
        repo.guardar_material(dispositivo)

    # 5 Juegos de Mesa
    for i in range(1, 6):
        juego = JuegoDeMesa(
            codigo_id=f"JUE-{i:03d}",
            titulo=f"Juego Estratégico {i}",
            editorial="BoardGames SL",
            min_jugadores=2,
            max_jugadores=4 + i,
            ubicacion="Ludoteca, Estante Infantil"
        )
        repo.guardar_material(juego)

    # 5 Recursos Digitales
    for i in range(1, 6):
        digital = RecursoDigital(
            codigo_id=f"DIG-{i:03d}",
            titulo=f"E-book Premium {i}",
            url=f"https://biblioteca.digital/book/{i}",
            licencias_totales=5 + i
        )
        repo.guardar_material(digital)

    print("\n¡Éxito! Se ha creado 'data/biblioteca.db' con 20 personas y 30 materiales.")

if __name__ == "__main__":
    inicializar_sistema()