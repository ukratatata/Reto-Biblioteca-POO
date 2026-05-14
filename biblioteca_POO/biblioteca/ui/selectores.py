"""
selectores.py

Ventanas auxiliares de selección y detalle:
  - SelectorSocio          — búsqueda y selección de un socio
  - SelectorMaterial       — búsqueda y selección de un material disponible
  - VentanaDetalleSocio    — perfil completo de un socio con préstamos y reservas
  - VentanaDetalleEmpleado — perfil completo de un empleado, editable por el admin
  - DialogoSeleccion       — diálogo minimalista de elección entre opciones
"""

import tkinter as tk
from typing import Callable

from biblioteca.models import Socio, Empleado, RolEmpleado
from biblioteca.ui.theme import Colores as C, Fuentes as F
from biblioteca.ui.widgets import (
    BotonPrimario, BotonSecundario, BotonPeligro, BotonGhost,
    CampoTexto, ComboBox, TablaDatos,
    EtiquetaEstado, Separador, confirmar
)

ROLES_EMPLEADO = [r.value for r in RolEmpleado]


# ==========================================
# SELECTOR DE SOCIO
# ==========================================

class SelectorSocio(tk.Toplevel):
    """
    Ventana de selección de socio con búsqueda en tiempo real.
    Al aceptar, guarda el ID del socio seleccionado en self.resultado.
    """

    def __init__(self, parent, controlador):
        super().__init__(parent)
        self.resultado = None
        self._ctrl = controlador
        self.title("Seleccionar socio")
        self.configure(bg=C.FONDO_PRINCIPAL)
        self.grab_set()
        self._construir()
        self._centrar()
        self._cargar()

    def _construir(self):
        contenido = tk.Frame(self, bg=C.FONDO_PRINCIPAL, padx=16, pady=16)
        contenido.pack(fill="both", expand=True)

        tk.Label(
            contenido, text="Buscar socio",
            font=F.TITULO_MEDIO, bg=C.FONDO_PRINCIPAL, fg=C.ACENTO
        ).pack(anchor="w", pady=(0, 10))

        self._busqueda = tk.Entry(
            contenido, font=F.CUERPO, bg=C.FONDO_WIDGET, fg=C.TEXTO_PRINCIPAL,
            insertbackground=C.ACENTO, relief="flat", bd=8
        )
        self._busqueda.pack(fill="x", pady=(0, 10))
        self._busqueda.bind("<KeyRelease>", lambda e: self._filtrar())
        self._busqueda.focus()

        cols = [
            ("id",     "ID",     100, "w"),
            ("nombre", "Nombre", 220, "w"),
            ("email",  "Email",  220, "w"),
        ]
        self._tabla = TablaDatos(contenido, cols, altura_filas=14)
        self._tabla.pack(fill="both", expand=True, pady=(0, 12))
        self._tabla.bind_doble_click(lambda f: self._aceptar(f))

        pie = tk.Frame(contenido, bg=C.FONDO_PRINCIPAL)
        pie.pack(fill="x")
        BotonPrimario(pie, "Seleccionar", lambda: self._aceptar(self._tabla.seleccion())).pack(side="left", padx=(0, 8))
        BotonGhost(pie, "Cancelar", self.destroy).pack(side="left")

        self._socios_cache = []

    def _cargar(self):
        usuarios = self._ctrl.obtener_todos_los_usuarios()
        self._socios_cache = [u for u in usuarios if isinstance(u, Socio)]
        self._renderizar(self._socios_cache)

    def _filtrar(self):
        texto = self._busqueda.get().lower()
        if not texto:
            self._renderizar(self._socios_cache)
            return
        filtrados = [
            s for s in self._socios_cache
            if texto in s.nombre.lower() or texto in s.apellidos.lower()
            or texto in s.email.lower() or texto in s.id_usuario.lower()
        ]
        self._renderizar(filtrados)

    def _renderizar(self, socios):
        filas = [(s.id_usuario, f"{s.nombre} {s.apellidos}", s.email) for s in socios]
        self._tabla.cargar(filas)

    def _aceptar(self, fila):
        if fila:
            self.resultado = fila[0]    # ID del socio
            self.destroy()

    def _centrar(self):
        self.update_idletasks()
        ancho, alto = 580, 480
        x = (self.winfo_screenwidth()  - ancho) // 2
        y = (self.winfo_screenheight() - alto)  // 2
        self.geometry(f"{ancho}x{alto}+{x}+{y}")


# ==========================================
# SELECTOR DE MATERIAL
# ==========================================

class SelectorMaterial(tk.Toplevel):
    """
    Ventana de selección de material con búsqueda por título.
    Muestra solo los materiales disponibles para préstamo.
    Al aceptar, guarda el código del material en self.resultado.
    """

    def __init__(self, parent, controlador):
        super().__init__(parent)
        self.resultado = None
        self._ctrl = controlador
        self.title("Seleccionar material")
        self.configure(bg=C.FONDO_PRINCIPAL)
        self.grab_set()
        self._construir()
        self._centrar()
        self._cargar()

    def _construir(self):
        contenido = tk.Frame(self, bg=C.FONDO_PRINCIPAL, padx=16, pady=16)
        contenido.pack(fill="both", expand=True)

        tk.Label(
            contenido, text="Buscar material",
            font=F.TITULO_MEDIO, bg=C.FONDO_PRINCIPAL, fg=C.ACENTO
        ).pack(anchor="w", pady=(0, 10))

        self._busqueda = tk.Entry(
            contenido, font=F.CUERPO, bg=C.FONDO_WIDGET, fg=C.TEXTO_PRINCIPAL,
            insertbackground=C.ACENTO, relief="flat", bd=8
        )
        self._busqueda.pack(fill="x", pady=(0, 10))
        self._busqueda.bind("<KeyRelease>", lambda e: self._buscar())
        self._busqueda.focus()

        cols = [
            ("codigo", "Código",  100, "w"),
            ("tipo",   "Tipo",    110, "w"),
            ("titulo", "Título",  260, "w"),
            ("estado", "Estado",  120, "center"),
        ]
        self._tabla = TablaDatos(contenido, cols, altura_filas=14)
        self._tabla.pack(fill="both", expand=True, pady=(0, 12))
        self._tabla.bind_doble_click(lambda f: self._aceptar(f))

        pie = tk.Frame(contenido, bg=C.FONDO_PRINCIPAL)
        pie.pack(fill="x")
        BotonPrimario(pie, "Seleccionar", lambda: self._aceptar(self._tabla.seleccion())).pack(side="left", padx=(0, 8))
        BotonGhost(pie, "Cancelar", self.destroy).pack(side="left")

    def _cargar(self):
        # Carga inicial: todo el catálogo disponible
        self._buscar()

    def _buscar(self):
        titulo = self._busqueda.get().strip() or None
        materiales = self._ctrl.buscar_materiales(titulo=titulo, solo_disponibles=True)
        filas = [(m.codigo_id, type(m).__name__, m.titulo, m.estado.value) for m in materiales]
        self._tabla.cargar(filas)

    def _aceptar(self, fila):
        if fila:
            self.resultado = fila[0]    # Código del material
            self.destroy()

    def _centrar(self):
        self.update_idletasks()
        ancho, alto = 580, 480
        x = (self.winfo_screenwidth()  - ancho) // 2
        y = (self.winfo_screenheight() - alto)  // 2
        self.geometry(f"{ancho}x{alto}+{x}+{y}")


# ==========================================
# VENTANA DETALLE DE SOCIO
# ==========================================

class VentanaDetalleSocio(tk.Toplevel):
    """
    Ventana modal que muestra el perfil completo de un socio:
    sus datos, préstamos activos, historial de reservas
    y la posibilidad de asignarle un préstamo directo.
    """

    def __init__(self, parent, controlador, socio: Socio, callback_refrescar: Callable = None):
        super().__init__(parent)
        self._ctrl     = controlador
        self._socio    = socio
        self._callback = callback_refrescar

        self.title(f"Socio: {socio.nombre} {socio.apellidos}")
        self.configure(bg=C.FONDO_PRINCIPAL)
        self.grab_set()
        self._construir()
        self._centrar()
        self._cargar_datos()

    def _construir(self):
        # Cabecera con datos del socio
        cab = tk.Frame(self, bg=C.FONDO_PANEL, padx=20, pady=14)
        cab.pack(fill="x")
        tk.Frame(cab, bg=C.ACENTO, width=5).pack(side="left", fill="y")

        info = tk.Frame(cab, bg=C.FONDO_PANEL, padx=12)
        info.pack(side="left", fill="x", expand=True)

        sancion_txt = "  ⚠ SANCIONADO" if self._socio.sancionado else ""
        tk.Label(
            info,
            text=f"{self._socio.nombre} {self._socio.apellidos}{sancion_txt}",
            font=F.TITULO_MEDIO, bg=C.FONDO_PANEL,
            fg=C.ERROR if self._socio.sancionado else C.ACENTO
        ).pack(anchor="w")
        tk.Label(
            info,
            text=f"{self._socio.id_usuario}  ·  {self._socio.email}  ·  Cupo: {self._socio.prestamos_activos}/{self._socio.max_prestamos}",
            font=F.PEQUEÑO, bg=C.FONDO_PANEL, fg=C.TEXTO_SECUNDARIO
        ).pack(anchor="w")

        contenido = tk.Frame(self, bg=C.FONDO_PRINCIPAL, padx=20, pady=16)
        contenido.pack(fill="both", expand=True)

        # --- Asignar préstamo directo ---
        lf = tk.LabelFrame(
            contenido, text="  Asignar préstamo directo  ",
            font=F.LABEL_CAMPO, bg=C.FONDO_PANEL, fg=C.ACENTO,
            bd=1, relief="solid", padx=12, pady=10
        )
        lf.pack(fill="x", pady=(0, 14))

        fila = tk.Frame(lf, bg=C.FONDO_PANEL)
        fila.pack(fill="x")

        tk.Label(fila, text="Material:", font=F.CUERPO, bg=C.FONDO_PANEL, fg=C.TEXTO_SECUNDARIO).pack(side="left", padx=(0, 6))

        self._campo_mat = tk.Entry(
            fila, font=F.MONO, bg=C.FONDO_WIDGET, fg=C.AZUL,
            insertbackground=C.AZUL, relief="flat", bd=6, width=22
        )
        self._campo_mat.pack(side="left", padx=(0, 8))

        BotonGhost(fila, "🔍 Buscar", self._abrir_selector_material).pack(side="left", padx=(0, 12))
        BotonPrimario(fila, "✓  Prestar", self._asignar_prestamo).pack(side="left")

        self._estado_prestamo = EtiquetaEstado(lf)
        self._estado_prestamo.pack(anchor="w", pady=(8, 0))

        # --- Préstamos activos ---
        tk.Label(
            contenido, text="Préstamos activos",
            font=F.TITULO_PEQUEÑO, bg=C.FONDO_PRINCIPAL, fg=C.TEXTO_PRINCIPAL
        ).pack(anchor="w", pady=(0, 6))

        cols_p = [
            ("id",       "ID Préstamo", 130, "w"),
            ("titulo",   "Material",    260, "w"),
            ("devolver", "Devolver",    120, "center"),
            ("estado",   "Estado",      110, "center"),
        ]
        self._tabla_prestamos = TablaDatos(contenido, cols_p, altura_filas=6)
        self._tabla_prestamos.pack(fill="x", pady=(0, 14))

        # --- Historial de reservas ---
        tk.Label(
            contenido, text="Reservas recientes",
            font=F.TITULO_PEQUEÑO, bg=C.FONDO_PRINCIPAL, fg=C.TEXTO_PRINCIPAL
        ).pack(anchor="w", pady=(0, 6))

        cols_r = [
            ("id",     "ID Reserva", 130, "w"),
            ("titulo", "Material",   260, "w"),
            ("limite", "Límite",     140, "center"),
            ("estado", "Estado",     110, "center"),
        ]
        self._tabla_reservas = TablaDatos(contenido, cols_r, altura_filas=5)
        self._tabla_reservas.pack(fill="x", pady=(0, 14))

        # --- Resetear contraseña (privilegio de admin) ---
        Separador(contenido).pack(fill="x", pady=(0, 14))

        tk.Label(
            contenido, text="Resetear contraseña",
            font=F.TITULO_PEQUEÑO, bg=C.FONDO_PRINCIPAL, fg=C.TEXTO_PRINCIPAL
        ).pack(anchor="w", pady=(0, 8))

        self._f_nueva_pass  = CampoTexto(contenido, "Nueva contraseña *",   password=True)
        self._f_nueva_pass.pack(fill="x", pady=(0, 8))
        self._f_repite_pass = CampoTexto(contenido, "Repetir contraseña *", password=True)
        self._f_repite_pass.pack(fill="x", pady=(0, 8))

        self._estado_pass_socio = EtiquetaEstado(contenido)
        self._estado_pass_socio.pack(anchor="w", pady=(0, 6))
        BotonPeligro(contenido, "🔑 Resetear contraseña", self._resetear_password_socio).pack(anchor="w", pady=(0, 16))

        # Botones de cierre
        pie = tk.Frame(contenido, bg=C.FONDO_PRINCIPAL)
        pie.pack(fill="x")
        BotonGhost(pie, "Cerrar", self.destroy).pack(side="right")

    def _cargar_datos(self):
        # Refresca el socio desde la BD
        self._socio = self._ctrl.buscar_usuario(self._socio.id_usuario)

        prestamos = self._ctrl.obtener_prestamos_de_usuario(self._socio.id_usuario)
        filas_p = []
        for p in prestamos:
            p.actualizar_estado()
            if p.estado.value == "Devuelto":
                continue    # Solo mostramos los activos y retrasados
            tag = "retrasado" if p.estado.value == "Retrasado" else ""
            filas_p.append(((p.id_prestamo, p.material.titulo,
                             p.fecha_devolucion_prevista.strftime("%d/%m/%Y"),
                             p.estado.value), tag))
        self._tabla_prestamos.cargar_con_tags(filas_p)

        reservas = self._ctrl.obtener_reservas_de_usuario(self._socio.id_usuario)
        filas_r = []
        for r in reservas[:10]:   # Mostramos las 10 más recientes
            tag = "expirado" if r.ha_expirado() else ""
            filas_r.append(((r.id_reserva, r.material.titulo,
                             r.fecha_limite_recogida.strftime("%d/%m/%Y %H:%M"),
                             r.estado.value), tag))
        self._tabla_reservas.cargar_con_tags(filas_r)

    def _abrir_selector_material(self):
        sel = SelectorMaterial(self, self._ctrl)
        self.wait_window(sel)
        if sel.resultado:
            self._campo_mat.delete(0, tk.END)
            self._campo_mat.insert(0, sel.resultado)

    def _asignar_prestamo(self):
        codigo = self._campo_mat.get().strip()
        if not codigo:
            self._estado_prestamo.error("Introduce o selecciona un código de material.")
            return

        exito, msg = self._ctrl.realizar_prestamo(self._socio.id_usuario, codigo)
        if exito:
            self._estado_prestamo.exito(msg)
            self._campo_mat.delete(0, tk.END)
            self._cargar_datos()
            if self._callback:
                self._callback()
        else:
            self._estado_prestamo.error(msg)

    def _resetear_password_socio(self):
        """Resetea la contraseña del socio sin pedir la actual — privilegio de admin."""
        nueva  = self._f_nueva_pass.get()
        repite = self._f_repite_pass.get()

        if not nueva or not repite:
            self._estado_pass_socio.error("Introduce y repite la nueva contraseña.")
            return

        if nueva != repite:
            self._estado_pass_socio.error("Las contraseñas no coinciden.")
            return

        if not confirmar(
            "Resetear contraseña",
            f"¿Resetear la contraseña de {self._socio.nombre} {self._socio.apellidos}?\n\n"
            f"El socio no podrá recuperar su contraseña anterior."
        ):
            return

        exito, msg = self._ctrl.resetear_password_admin(self._socio.id_usuario, nueva)
        if exito:
            self._f_nueva_pass.limpiar()
            self._f_repite_pass.limpiar()
            self._estado_pass_socio.exito(msg)
        else:
            self._estado_pass_socio.error(msg)

    def _centrar(self):
        """Altura dinámica con tope de pantalla para que el contenido no quede cortado."""
        self.update_idletasks()
        ancho = 760
        alto  = min(self.winfo_reqheight() + 20, self.winfo_screenheight() - 80)
        x = (self.winfo_screenwidth()  - ancho) // 2
        y = (self.winfo_screenheight() - alto)  // 2
        self.geometry(f"{ancho}x{alto}+{x}+{y}")


# ==========================================
# VENTANA DETALLE DE EMPLEADO (Admin)
# ==========================================

class VentanaDetalleEmpleado(tk.Toplevel):
    """
    Ventana modal que permite al administrador editar todos los datos
    de un empleado: nombre, apellidos, email, rol y contraseña.
    Funciona igual que VentanaDetalleSocio pero orientada a empleados.
    La validación del email la delega en el setter de Usuario (models.py),
    capturando el ValueError que lanza si el formato no es correcto.
    """

    def __init__(self, parent, controlador, empleado: Empleado, callback_refrescar: Callable = None):
        super().__init__(parent)
        self._ctrl      = controlador
        self._empleado  = empleado
        self._callback  = callback_refrescar

        self.title(f"Empleado: {empleado.nombre} {empleado.apellidos}")
        self.configure(bg=C.FONDO_PRINCIPAL)
        self.grab_set()
        self._construir()
        self._centrar()

    def _construir(self):
        # Cabecera con datos del empleado
        cab = tk.Frame(self, bg=C.FONDO_PANEL, padx=20, pady=14)
        cab.pack(fill="x")
        tk.Frame(cab, bg=C.ACENTO, width=5).pack(side="left", fill="y")

        info = tk.Frame(cab, bg=C.FONDO_PANEL, padx=12)
        info.pack(side="left", fill="x", expand=True)

        tk.Label(
            info,
            text=f"{self._empleado.nombre} {self._empleado.apellidos}",
            font=F.TITULO_MEDIO, bg=C.FONDO_PANEL, fg=C.ACENTO
        ).pack(anchor="w")
        tk.Label(
            info,
            text=f"{self._empleado.id_usuario}  ·  {self._empleado.email}  ·  {self._empleado.rol.value}",
            font=F.PEQUEÑO, bg=C.FONDO_PANEL, fg=C.TEXTO_SECUNDARIO
        ).pack(anchor="w")

        contenido = tk.Frame(self, bg=C.FONDO_PRINCIPAL, padx=24, pady=20)
        contenido.pack(fill="both", expand=True)

        tk.Label(
            contenido,
            text="Los campos marcados con * son obligatorios",
            font=F.PEQUEÑO, bg=C.FONDO_PRINCIPAL, fg=C.TEXTO_DESACTIVADO
        ).pack(anchor="w", pady=(0, 14))

        # Campos editables — precargados con los datos actuales
        self._f_nombre    = CampoTexto(contenido, "Nombre *")
        self._f_nombre.pack(fill="x", pady=(0, 8))
        self._f_nombre.set(self._empleado.nombre)

        self._f_apellidos = CampoTexto(contenido, "Apellidos *")
        self._f_apellidos.pack(fill="x", pady=(0, 8))
        self._f_apellidos.set(self._empleado.apellidos)

        self._f_email     = CampoTexto(contenido, "Email *")
        self._f_email.pack(fill="x", pady=(0, 8))
        self._f_email.set(self._empleado.email)

        self._f_rol = ComboBox(contenido, "Rol *", ROLES_EMPLEADO)
        self._f_rol.set(self._empleado.rol.value)
        self._f_rol.pack(fill="x", pady=(0, 8))

        self._estado_datos = EtiquetaEstado(contenido)
        self._estado_datos.pack(anchor="w", pady=(0, 6))
        BotonSecundario(contenido, "💾 Guardar cambios", self._guardar_datos).pack(anchor="w", pady=(0, 20))

        Separador(contenido).pack(fill="x", pady=(0, 20))

        # Resetear contraseña — sin pedir la actual (privilegio de admin)
        tk.Label(
            contenido, text="Resetear contraseña",
            font=F.TITULO_PEQUEÑO, bg=C.FONDO_PRINCIPAL, fg=C.TEXTO_PRINCIPAL
        ).pack(anchor="w", pady=(0, 8))

        self._f_nueva_pass  = CampoTexto(contenido, "Nueva contraseña *",   password=True)
        self._f_nueva_pass.pack(fill="x", pady=(0, 8))
        self._f_repite_pass = CampoTexto(contenido, "Repetir contraseña *", password=True)
        self._f_repite_pass.pack(fill="x", pady=(0, 8))

        self._estado_pass = EtiquetaEstado(contenido)
        self._estado_pass.pack(anchor="w", pady=(0, 6))
        BotonPeligro(contenido, "🔑 Resetear contraseña", self._resetear_password).pack(anchor="w", pady=(0, 0))

        Separador(contenido).pack(fill="x", pady=(20, 0))

        pie = tk.Frame(contenido, bg=C.FONDO_PRINCIPAL)
        pie.pack(fill="x", pady=(16, 0))
        BotonGhost(pie, "Cerrar", self.destroy).pack(side="right")

    def _guardar_datos(self):
        nombre    = self._f_nombre.get().strip()
        apellidos = self._f_apellidos.get().strip()
        email     = self._f_email.get().strip()
        rol       = RolEmpleado(self._f_rol.get())

        if not all([nombre, apellidos, email]):
            self._estado_datos.error("Nombre, apellidos y email son obligatorios.")
            return

        # La validación del formato del email la hace el setter de Usuario en models.py;
        # si el formato es incorrecto lanza ValueError con el mensaje correspondiente
        try:
            exito, msg = self._ctrl.modificar_empleado(
                self._empleado.id_usuario, nombre, apellidos, email, rol
            )
        except ValueError as e:
            self._estado_datos.error(str(e))
            return

        if exito:
            # Refrescamos el objeto local para que la cabecera sea coherente
            self._empleado = self._ctrl.buscar_usuario(self._empleado.id_usuario)
            self._estado_datos.exito(msg)
            if self._callback:
                self._callback()
        else:
            self._estado_datos.error(msg)

    def _resetear_password(self):
        nueva  = self._f_nueva_pass.get()
        repite = self._f_repite_pass.get()

        if not nueva or not repite:
            self._estado_pass.error("Introduce y repite la nueva contraseña.")
            return

        if nueva != repite:
            self._estado_pass.error("Las contraseñas no coinciden.")
            return

        if not confirmar(
            "Resetear contraseña",
            f"¿Seguro que quieres resetear la contraseña de "
            f"{self._empleado.nombre} {self._empleado.apellidos}?\n\n"
            f"El empleado no podrá recuperar su contraseña anterior."
        ):
            return

        exito, msg = self._ctrl.resetear_password_admin(self._empleado.id_usuario, nueva)
        if exito:
            self._f_nueva_pass.limpiar()
            self._f_repite_pass.limpiar()
            self._estado_pass.exito(msg)
        else:
            self._estado_pass.error(msg)

    def _centrar(self):
        """Altura dinámica para que el contenido nunca quede cortado."""
        self.update_idletasks()
        ancho = 520
        alto  = self.winfo_reqheight() + 20
        x = (self.winfo_screenwidth()  - ancho) // 2
        y = (self.winfo_screenheight() - alto)  // 2
        self.geometry(f"{ancho}x{alto}+{x}+{y}")


# ==========================================
# DIÁLOGO DE SELECCIÓN
# ==========================================

class DialogoSeleccion(tk.Toplevel):
    """Ventana modal minimalista para que el usuario elija entre una lista de opciones."""

    def __init__(self, parent, titulo: str, mensaje: str, opciones: list):
        super().__init__(parent)
        self.resultado = None
        self.title(titulo)
        self.configure(bg=C.FONDO_PRINCIPAL)
        self.resizable(False, False)
        self.grab_set()

        contenido = tk.Frame(self, bg=C.FONDO_PRINCIPAL, padx=24, pady=20)
        contenido.pack()

        tk.Label(
            contenido, text=mensaje,
            font=F.CUERPO, bg=C.FONDO_PRINCIPAL, fg=C.TEXTO_PRINCIPAL
        ).pack(anchor="w", pady=(0, 12))

        self._var = tk.StringVar(value=opciones[0])
        for op in opciones:
            tk.Radiobutton(
                contenido, text=op, variable=self._var, value=op,
                font=F.CUERPO, bg=C.FONDO_PRINCIPAL, fg=C.TEXTO_PRINCIPAL,
                selectcolor=C.FONDO_WIDGET, activebackground=C.FONDO_PRINCIPAL,
                activeforeground=C.ACENTO, cursor="hand2"
            ).pack(anchor="w", pady=2)

        fila = tk.Frame(contenido, bg=C.FONDO_PRINCIPAL)
        fila.pack(fill="x", pady=(16, 0))

        BotonPrimario(fila, "Aceptar", self._aceptar).pack(side="left", padx=(0, 8))
        BotonGhost(fila, "Cancelar", self.destroy).pack(side="left")

        self.update_idletasks()
        x = (self.winfo_screenwidth()  - self.winfo_reqwidth())  // 2
        y = (self.winfo_screenheight() - self.winfo_reqheight()) // 2
        self.geometry(f"+{x}+{y}")

    def _aceptar(self):
        self.resultado = self._var.get()
        self.destroy()
