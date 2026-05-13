"""
login_view.py

Ventana de login: email + contraseña.
Detecta si el usuario es Socio o Empleado y abre la ventana correspondiente.
"""

import tkinter as tk
from typing import Callable

from biblioteca.ui.theme import Colores as C, Fuentes as F
from biblioteca.ui.widgets import (
    BotonPrimario, BotonGhost, CampoTexto, EtiquetaEstado
)


class VentanaLogin(tk.Toplevel):
    """
    Ventana modal de autenticación. Se muestra sobre la ventana raíz invisible.
    Al autenticarse correctamente llama al callback con el objeto usuario.
    """

    def __init__(self, root: tk.Tk, controlador, callback_exito: Callable):
        super().__init__(root)
        self._controlador = controlador
        self._callback_exito = callback_exito

        self.title("Biblioteca · Acceso")
        self.resizable(False, False)
        self.configure(bg=C.FONDO_PRINCIPAL)
        self.protocol("WM_DELETE_WINDOW", self._al_cerrar)

        self._construir_ui()
        self._centrar()

        # Bloqueamos la interacción con la ventana raíz mientras el login esté abierto
        self.grab_set()
        self.focus_force()

    def _construir_ui(self):
        # ---- Franja de acento lateral izquierda ----
        tk.Frame(self, bg=C.ACENTO, width=6).pack(side="left", fill="y")

        # ---- Contenido principal ----
        contenido = tk.Frame(self, bg=C.FONDO_PRINCIPAL, padx=50, pady=50)
        contenido.pack(side="left", fill="both", expand=True)

        # Logo / título
        tk.Label(
            contenido,
            text="📚",
            font=("Georgia", 36),
            bg=C.FONDO_PRINCIPAL,
            fg=C.ACENTO
        ).pack(anchor="center", pady=(0, 4))

        tk.Label(
            contenido,
            text="BIBLIOTECA",
            font=F.TITULO_GRANDE,
            bg=C.FONDO_PRINCIPAL,
            fg=C.TEXTO_PRINCIPAL
        ).pack(anchor="center")

        tk.Label(
            contenido,
            text="Sistema de Gestión",
            font=F.PEQUEÑO,
            bg=C.FONDO_PRINCIPAL,
            fg=C.TEXTO_SECUNDARIO
        ).pack(anchor="center", pady=(2, 28))

        # Línea divisoria
        tk.Frame(contenido, bg=C.SEPARADOR, height=1).pack(fill="x", pady=(0, 28))

        # Campos
        self._campo_email = CampoTexto(contenido, "Correo electrónico")
        self._campo_email.pack(fill="x", pady=(0, 14))

        self._campo_pass = CampoTexto(contenido, "Contraseña", password=True)
        self._campo_pass.pack(fill="x", pady=(0, 24))

        # Vincular Enter a login
        for campo in (self._campo_email, self._campo_pass):
            campo._entry.bind("<Return>", lambda e: self._intentar_login())

        # Botón de acceso
        BotonPrimario(
            contenido,
            "Entrar →",
            self._intentar_login
        ).pack(fill="x", pady=(0, 12))

        # Etiqueta de estado
        self._estado = EtiquetaEstado(contenido)
        self._estado.pack(anchor="center", pady=(4, 0))

        # Footer
        tk.Label(
            contenido,
            text="Contacta con un administrador si olvidaste tu contraseña.",
            font=F.PEQUEÑO,
            bg=C.FONDO_PRINCIPAL,
            fg=C.TEXTO_DESACTIVADO,
            wraplength=280
        ).pack(anchor="center", pady=(20, 0))

        # Foco inicial en el campo de email
        self.after(100, self._campo_email.focus)

    def _intentar_login(self):
        email = self._campo_email.get().strip()
        password = self._campo_pass.get()

        exito, mensaje, usuario = self._controlador.login_por_email(email, password)

        if exito:
            self._estado.exito(mensaje)
            self.after(400, lambda: self._completar_login(usuario))
        else:
            self._estado.error(mensaje)
            self._campo_pass.limpiar()
            self._campo_pass.focus()

    def _completar_login(self, usuario):
        self.grab_release()
        self.destroy()
        self._callback_exito(usuario)

    def _al_cerrar(self):
        # Si el usuario cierra el login cerramos toda la aplicación
        self.master.destroy()

    def _centrar(self):
        ancho, alto = 400, 520
        self.geometry(f"{ancho}x{alto}")
        self.update_idletasks()
        x = (self.winfo_screenwidth()  - ancho) // 2
        y = (self.winfo_screenheight() - alto)  // 2
        self.geometry(f"{ancho}x{alto}+{x}+{y}")
