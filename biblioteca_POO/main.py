"""
main.py

Punto de entrada principal de la aplicación.
Desde aquí iniciaremos la interfaz gráfica (Tkinter) y conectaremos el Controlador.
"""

from biblioteca.db import BibliotecaRepository
from biblioteca.controllers import BibliotecaController

def probar_controlador():
    print("Iniciando el sistema de biblioteca...")
    
    # Inicializamos el repositorio en la ruta definitiva
    repo = BibliotecaRepository(ruta_db="data/biblioteca.db")

    # 2. Encendemos el "Cerebro" (Controlador)
    controlador = BibliotecaController(repo)
    
    # 3. Probamos a buscar un libro que creamos en el script anterior (LIB-001)
    libro = controlador.buscar_material("LIB-001")
    if libro:
        print(f"\n✅ Libro encontrado: {libro.titulo}")
    else:
        print("\n❌ No se encontró el libro.")

    # 4. Probamos a hacer un préstamo a nuestro Socio 1 (S-001)
    print("\nIntentando realizar un préstamo...")
    exito, mensaje = controlador.realizar_prestamo(
        id_usuario="S-001", 
        codigo_material="LIB-001"
    )
    
    if exito:
        print(f"✅ {mensaje}")
    else:
        print(f"❌ {mensaje}")

if __name__ == "__main__":
    probar_controlador()