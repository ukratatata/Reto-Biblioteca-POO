"""
app_window.py

Punto de entrada de la aplicación Tkinter.
Inicializa la base de datos, el controlador y arranca el ciclo de login → ventana principal.

Ejecutar desde la raíz del proyecto:
    python -m biblioteca.ui.app_window
o bien:
    python biblioteca_POO/main.py
"""

import tkinter as tk
from tkinter import messagebox

from biblioteca.db import BibliotecaRepository
from biblioteca.controllers import BibliotecaController
from biblioteca.models import Socio, Empleado
from biblioteca.ui.theme import aplicar_tema, Colores as C
from biblioteca.ui.login_view import VentanaLogin
from biblioteca.ui.socio_view import VentanaSocio
from biblioteca.ui.empleado_view import VentanaEmpleado


class Aplicacion:
    """
    Orquestador de ciclo de vida de la app.
    Gestiona la ventana raíz invisible y la rotación login → ventana principal → logout.
    """

    def __init__(self):
        # Ventana raíz invisible: sirve de padre para todas las ventanas
        self._root = tk.Tk()
        self._root.withdraw()   # La ocultamos; el usuario solo ve las ventanas hijas
        self._root.title("Biblioteca")

        # Aplicamos el tema oscuro antes de crear ningún widget
        aplicar_tema(self._root)

        # Inicializamos el backend
        self._repo = BibliotecaRepository(ruta_db="data/biblioteca.db")
        self._ctrl = BibliotecaController(self._repo)

        # Arrancamos con la pantalla de login
        self._mostrar_login()

    def _mostrar_login(self):
        """Abre la ventana de login y espera a que el usuario se autentique."""
        VentanaLogin(self._root, self._ctrl, self._al_autenticarse)

    def _al_autenticarse(self, usuario):
        """
        Callback llamado por VentanaLogin cuando el login es correcto.
        Decide qué ventana principal abrir según el tipo de usuario.
        """
        if isinstance(usuario, Socio):
            VentanaSocio(
                self._root,
                self._ctrl,
                usuario,
                callback_logout=self._al_hacer_logout
            )
        elif isinstance(usuario, Empleado):
            VentanaEmpleado(
                self._root,
                self._ctrl,
                usuario,
                callback_logout=self._al_hacer_logout
            )
        else:
            messagebox.showerror("Error", "Tipo de usuario no reconocido.")
            self._mostrar_login()

    def _al_hacer_logout(self):
        """
        Callback llamado cuando el usuario cierra sesión.
        Detiene el temporizador del controlador actual antes de reemplazarlo,
        y vuelve al login con un controlador limpio.
        """
        # Paramos el temporizador del controlador que acaba de cerrar sesión
        # antes de crear uno nuevo, para no acumular hilos daemon sueltos
        self._ctrl.detener_temporizador()
        self._ctrl = BibliotecaController(self._repo)
        self._mostrar_login()

    def ejecutar(self):
        """Arranca el bucle principal de eventos de Tkinter."""
        self._root.mainloop()


def main():
    app = Aplicacion()
    app.ejecutar()


if __name__ == "__main__":
    main()
