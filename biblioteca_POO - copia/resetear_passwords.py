"""
resetear_passwords.py

Script de emergencia para asignar contraseñas a usuarios que no tienen ninguna.
Ejecutar desde biblioteca_POO/:
    python resetear_passwords.py

Por defecto asigna '1234' a todos los usuarios sin contraseña.
Puedes cambiar PASSWORD_DEFECTO antes de ejecutar.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from biblioteca.db import BibliotecaRepository
from biblioteca.models import Socio, Empleado

PASSWORD_DEFECTO = "1234"   # <-- Cambia esto si quieres otra contraseña inicial

def main():
    repo = BibliotecaRepository(ruta_db="data/biblioteca.db")
    usuarios = repo.obtener_todos_los_usuarios()

    sin_pass = [u for u in usuarios if not u.password_hash]

    if not sin_pass:
        print("✅ Todos los usuarios ya tienen contraseña. No hay nada que hacer.")
        return

    print(f"Usuarios sin contraseña: {len(sin_pass)}\n")

    for u in sin_pass:
        u.establecer_password(PASSWORD_DEFECTO)
        repo.guardar_usuario(u)

        tipo = "Socio" if isinstance(u, Socio) else f"Empleado ({u.rol.value})"
        print(f"  ✔ [{u.id_usuario}] {u.nombre} {u.apellidos}  ({tipo})  →  email: {u.email}")

    print(f"\n✅ Contraseña '{PASSWORD_DEFECTO}' asignada a {len(sin_pass)} usuario(s).")
    print("Entra con el email del usuario y esa contraseña.")
    print("Recuerda cambiarla desde 'Mi Cuenta' una vez dentro.")

if __name__ == "__main__":
    main()
