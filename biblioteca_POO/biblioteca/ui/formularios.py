"""
formularios.py

Formularios modales para crear y editar entidades del sistema:
  - FormularioMaterial  — crear o editar cualquier tipo de material del catálogo
  - FormularioSocio     — crear o editar un socio
  - FormularioEmpleado  — crear un nuevo empleado (el admin lo usa desde el panel)
"""

import tkinter as tk
from typing import Callable

from biblioteca.models import (
    Socio, RolEmpleado,
    Libro, Revista, Dispositivo, JuegoDeMesa, RecursoDigital, TipoDispositivo
)
from biblioteca.ui.theme import Colores as C, Fuentes as F
from biblioteca.ui.widgets import (
    BotonPrimario, BotonGhost,
    CampoTexto, CampoNumero, ComboBox,
    EtiquetaEstado, Separador
)

TIPOS_MATERIAL = ["Libro", "Revista", "Dispositivo", "JuegoDeMesa", "RecursoDigital"]
ROLES_EMPLEADO = [r.value for r in RolEmpleado]
TIPOS_DISP     = [t.value for t in TipoDispositivo]


# ==========================================
# FORMULARIO: MATERIAL
# ==========================================

class FormularioMaterial(tk.Toplevel):
    """Formulario modal para crear o editar un material del catálogo."""

    def __init__(self, parent, controlador, material=None, callback_ok: Callable = None):
        super().__init__(parent)
        self._ctrl      = controlador
        self._material  = material      # None = crear, objeto = editar
        self._callback  = callback_ok
        self._modo      = "Editar" if material else "Añadir"

        self.title(f"{self._modo} material")
        self.configure(bg=C.FONDO_PRINCIPAL)
        self.resizable(False, False)
        self.grab_set()
        self._construir()
        self._centrar()

        if material:
            self._precargar(material)

    def _construir(self):
        contenido = tk.Frame(self, bg=C.FONDO_PRINCIPAL, padx=30, pady=24)
        contenido.pack(fill="both", expand=True)

        tk.Label(
            contenido, text=f"{self._modo} material",
            font=F.TITULO_MEDIO, bg=C.FONDO_PRINCIPAL, fg=C.ACENTO
        ).pack(anchor="w", pady=(0, 8))

        tk.Label(
            contenido,
            text="Los campos marcados con * son obligatorios",
            font=F.PEQUEÑO, bg=C.FONDO_PRINCIPAL, fg=C.TEXTO_DESACTIVADO
        ).pack(anchor="w", pady=(0, 12))

        # Tipo (solo en creación)
        if not self._material:
            self._tipo_combo = ComboBox(contenido, "Tipo de material *", TIPOS_MATERIAL)
            self._tipo_combo.set("Libro")
            self._tipo_combo.pack(fill="x", pady=(0, 10))

            # ID autogenerado: lo calculamos y guardamos al abrir el formulario
            # y lo recalculamos solo si el usuario cambia el tipo
            self._id_reservado = None

            self._lbl_id_preview = tk.Label(
                contenido, text="",
                font=F.CUERPO, bg=C.FONDO_PRINCIPAL, fg=C.TEXTO_SECUNDARIO
            )
            self._lbl_id_preview.pack(anchor="w", pady=(0, 8))

            # Al cambiar el tipo recalculamos el ID reservado para ese tipo
            self._tipo_combo._combo.bind("<<ComboboxSelected>>", lambda e: (
                self._actualizar_campos_extra(),
                self._reservar_id()
            ))
            self._reservar_id()    # Calculamos el ID inicial al abrir
        else:
            self._tipo_fijo = type(self._material).__name__
            tk.Label(
                contenido, text=f"Tipo: {self._tipo_fijo}",
                font=F.CUERPO_BOLD, bg=C.FONDO_PRINCIPAL, fg=C.AZUL
            ).pack(anchor="w", pady=(0, 6))
            tk.Label(
                contenido, text=f"Código: {self._material.codigo_id}",
                font=F.CUERPO, bg=C.FONDO_PRINCIPAL, fg=C.TEXTO_SECUNDARIO
            ).pack(anchor="w", pady=(0, 10))

        self._f_titulo    = CampoTexto(contenido, "Título *")
        self._f_titulo.pack(fill="x", pady=(0, 8))

        self._f_ubicacion = CampoTexto(contenido, "Ubicación (opcional)")
        self._f_ubicacion.pack(fill="x", pady=(0, 8))

        Separador(contenido).pack(fill="x", pady=(4, 12))

        # Zona de campos extra (depende del tipo)
        self._zona_extra = tk.Frame(contenido, bg=C.FONDO_PRINCIPAL)
        self._zona_extra.pack(fill="x")

        self._actualizar_campos_extra()

        Separador(contenido).pack(fill="x", pady=(12, 12))

        # Botones
        fila_btns = tk.Frame(contenido, bg=C.FONDO_PRINCIPAL)
        fila_btns.pack(fill="x")

        BotonPrimario(fila_btns, "Guardar", self._guardar).pack(side="left", padx=(0, 8))
        BotonGhost(fila_btns, "Cancelar", self.destroy).pack(side="left")

        self._estado = EtiquetaEstado(contenido)
        self._estado.pack(anchor="w", pady=(10, 0))

    def _reservar_id(self):
        """
        Calcula el siguiente ID para el tipo seleccionado, lo guarda en self._id_reservado
        y actualiza el label de preview. Al llamarse una sola vez por tipo elegido,
        garantizamos que el ID mostrado y el usado al guardar son siempre el mismo.
        """
        tipo = self._tipo_combo.get()
        try:
            self._id_reservado = self._ctrl.siguiente_id_material(tipo)
            self._lbl_id_preview.config(text=f"ID asignado automáticamente: {self._id_reservado}")
        except Exception:
            self._id_reservado = None

    def _actualizar_campos_extra(self):
        """Destruye y recrea los campos específicos del tipo seleccionado."""
        for widget in self._zona_extra.winfo_children():
            widget.destroy()

        tipo = self._tipo_fijo if self._material else self._tipo_combo.get()

        if tipo == "Libro":
            self._f_autor   = CampoTexto(self._zona_extra, "Autor (opcional)")
            self._f_autor.pack(fill="x", pady=(0, 8))
            self._f_paginas = CampoNumero(self._zona_extra, "Páginas (opcional)")
            self._f_paginas.pack(fill="x", pady=(0, 8))
            self._f_isbn    = CampoTexto(self._zona_extra, "ISBN (opcional)")
            self._f_isbn.pack(fill="x", pady=(0, 8))

        elif tipo == "Revista":
            self._f_editorial = CampoTexto(self._zona_extra, "Editorial (opcional)")
            self._f_editorial.pack(fill="x", pady=(0, 8))
            self._f_edicion   = CampoNumero(self._zona_extra, "Número de edición (opcional)")
            self._f_edicion.pack(fill="x", pady=(0, 8))
            self._f_issn      = CampoTexto(self._zona_extra, "ISSN (opcional)")
            self._f_issn.pack(fill="x", pady=(0, 8))

        elif tipo == "Dispositivo":
            self._f_tipo_disp  = ComboBox(self._zona_extra, "Tipo de dispositivo *", TIPOS_DISP)
            self._f_tipo_disp.pack(fill="x", pady=(0, 8))
            self._f_fabricante = CampoTexto(self._zona_extra, "Fabricante (opcional)")
            self._f_fabricante.pack(fill="x", pady=(0, 8))
            self._f_so         = CampoTexto(self._zona_extra, "Sistema Operativo (opcional)")
            self._f_so.pack(fill="x", pady=(0, 8))
            self._f_num_serie  = CampoTexto(self._zona_extra, "Número de serie (opcional)")
            self._f_num_serie.pack(fill="x", pady=(0, 8))

        elif tipo == "JuegoDeMesa":
            self._f_editorial2 = CampoTexto(self._zona_extra, "Editorial (opcional)")
            self._f_editorial2.pack(fill="x", pady=(0, 8))
            self._f_min_jug    = CampoNumero(self._zona_extra, "Mín. jugadores (opcional)")
            self._f_min_jug.pack(fill="x", pady=(0, 8))
            self._f_max_jug    = CampoNumero(self._zona_extra, "Máx. jugadores (opcional)")
            self._f_max_jug.pack(fill="x", pady=(0, 8))

        elif tipo == "RecursoDigital":
            self._f_url       = CampoTexto(self._zona_extra, "URL de acceso (opcional)")
            self._f_url.pack(fill="x", pady=(0, 8))
            self._f_licencias = CampoNumero(self._zona_extra, "Licencias totales *")
            self._f_licencias.pack(fill="x", pady=(0, 8))

    def _precargar(self, m):
        """Rellena los campos con los datos del material a editar."""
        self._f_titulo.set(m.titulo)
        if hasattr(m, "ubicacion") and m.ubicacion:
            self._f_ubicacion.set(m.ubicacion)

        if isinstance(m, Libro):
            if m.autor:          self._f_autor.set(m.autor)
            if m.paginas:        self._f_paginas.set(str(m.paginas))
            if m.isbn:           self._f_isbn.set(m.isbn)
        elif isinstance(m, Revista):
            if m.editorial:      self._f_editorial.set(m.editorial)
            if m.numero_edicion: self._f_edicion.set(str(m.numero_edicion))
            if m.issn:           self._f_issn.set(m.issn)
        elif isinstance(m, Dispositivo):
            self._f_tipo_disp.set(m.tipo_dispositivo.value)
            if m.fabricante:     self._f_fabricante.set(m.fabricante)
            if m.so:             self._f_so.set(m.so)
            if m.numero_serie:   self._f_num_serie.set(m.numero_serie)
        elif isinstance(m, JuegoDeMesa):
            if m.editorial:      self._f_editorial2.set(m.editorial)
            if m.min_jugadores:  self._f_min_jug.set(str(m.min_jugadores))
            if m.max_jugadores:  self._f_max_jug.set(str(m.max_jugadores))
        elif isinstance(m, RecursoDigital):
            if m.url:            self._f_url.set(m.url)
            self._f_licencias.set(str(m.licencias_totales))

    def _guardar(self):
        tipo   = self._tipo_fijo if self._material else self._tipo_combo.get()
        titulo = self._f_titulo.get().strip()
        ubic   = self._f_ubicacion.get().strip() or None

        if not titulo:
            self._estado.error("El título es obligatorio.")
            return

        # En creación el ID fue calculado al abrir el formulario; en edición conservamos el original
        if self._material:
            codigo = self._material.codigo_id
        else:
            if not self._id_reservado:
                self._estado.error("Error al generar el ID. Cierra y vuelve a abrir el formulario.")
                return
            codigo = self._id_reservado

        try:
            if tipo == "Libro":
                pags  = int(self._f_paginas.get()) if self._f_paginas.get() else None
                nuevo = Libro(
                    codigo_id=codigo, titulo=titulo, ubicacion=ubic,
                    autor=self._f_autor.get().strip() or None,
                    paginas=pags,
                    isbn=self._f_isbn.get().strip() or None
                )
            elif tipo == "Revista":
                edic  = int(self._f_edicion.get()) if self._f_edicion.get() else None
                nuevo = Revista(
                    codigo_id=codigo, titulo=titulo, ubicacion=ubic,
                    editorial=self._f_editorial.get().strip() or None,
                    numero_edicion=edic,
                    issn=self._f_issn.get().strip() or None
                )
            elif tipo == "Dispositivo":
                tipo_disp = TipoDispositivo(self._f_tipo_disp.get())
                nuevo = Dispositivo(
                    codigo_id=codigo, titulo=titulo, ubicacion=ubic,
                    tipo_dispositivo=tipo_disp,
                    fabricante=self._f_fabricante.get().strip() or None,
                    so=self._f_so.get().strip() or None,
                    numero_serie=self._f_num_serie.get().strip() or None
                )
            elif tipo == "JuegoDeMesa":
                min_j = int(self._f_min_jug.get()) if self._f_min_jug.get() else None
                max_j = int(self._f_max_jug.get()) if self._f_max_jug.get() else None
                nuevo = JuegoDeMesa(
                    codigo_id=codigo, titulo=titulo, ubicacion=ubic,
                    editorial=self._f_editorial2.get().strip() or None,
                    min_jugadores=min_j, max_jugadores=max_j
                )
            elif tipo == "RecursoDigital":
                lics  = int(self._f_licencias.get()) if self._f_licencias.get() else 1
                nuevo = RecursoDigital(
                    codigo_id=codigo, titulo=titulo,
                    url=self._f_url.get().strip() or None,
                    licencias_totales=lics
                )
            else:
                self._estado.error("Tipo de material no reconocido.")
                return

        except ValueError as e:
            # Los setters de los modelos lanzan ValueError con mensajes descriptivos
            self._estado.error(f"Error en los datos: {e}")
            return

        if self._material:
            # Conservamos el estado actual del material al editar
            nuevo._estado = self._material.estado
            exito, msg = self._ctrl.modificar_material(nuevo)
        else:
            exito, msg = self._ctrl.crear_material(nuevo)

        if exito:
            if self._callback:
                self._callback()
            self.destroy()
        else:
            self._estado.error(msg)

    def _centrar(self):
        self.update_idletasks()
        ancho, alto = 480, self.winfo_reqheight() + 40
        x = (self.winfo_screenwidth()  - ancho) // 2
        y = (self.winfo_screenheight() - alto)  // 2
        self.geometry(f"{ancho}x{alto}+{x}+{y}")


# ==========================================
# FORMULARIO: SOCIO
# ==========================================

class FormularioSocio(tk.Toplevel):
    """Formulario modal para crear o editar un socio."""

    def __init__(self, parent, controlador, socio: Socio = None, callback_ok: Callable = None):
        super().__init__(parent)
        self._ctrl     = controlador
        self._socio    = socio
        self._callback = callback_ok
        self._modo     = "Editar socio" if socio else "Nuevo socio"

        self.title(self._modo)
        self.configure(bg=C.FONDO_PRINCIPAL)
        self.resizable(False, False)
        self.grab_set()
        self._construir()
        self._centrar()

        if socio:
            self._precargar()

    def _construir(self):
        contenido = tk.Frame(self, bg=C.FONDO_PRINCIPAL, padx=30, pady=24)
        contenido.pack(fill="both", expand=True)

        tk.Label(
            contenido, text=self._modo,
            font=F.TITULO_MEDIO, bg=C.FONDO_PRINCIPAL, fg=C.ACENTO
        ).pack(anchor="w", pady=(0, 8))

        if self._socio:
            tk.Label(
                contenido, text=f"ID: {self._socio.id_usuario}",
                font=F.CUERPO, bg=C.FONDO_PRINCIPAL, fg=C.TEXTO_SECUNDARIO
            ).pack(anchor="w", pady=(0, 4))
        else:
            id_preview = self._ctrl.siguiente_id_socio()
            tk.Label(
                contenido, text=f"ID asignado automáticamente: {id_preview}",
                font=F.CUERPO, bg=C.FONDO_PRINCIPAL, fg=C.TEXTO_SECUNDARIO
            ).pack(anchor="w", pady=(0, 4))

        tk.Label(
            contenido,
            text="Los campos marcados con * son obligatorios",
            font=F.PEQUEÑO, bg=C.FONDO_PRINCIPAL, fg=C.TEXTO_DESACTIVADO
        ).pack(anchor="w", pady=(0, 12))

        self._f_nombre    = CampoTexto(contenido, "Nombre *")
        self._f_nombre.pack(fill="x", pady=(0, 8))
        self._f_apellidos = CampoTexto(contenido, "Apellidos *")
        self._f_apellidos.pack(fill="x", pady=(0, 8))
        self._f_email     = CampoTexto(contenido, "Email *")
        self._f_email.pack(fill="x", pady=(0, 8))

        if not self._socio:
            # Solo pedimos contraseña al crear; para cambiarla está Mi Cuenta
            self._f_pass = CampoTexto(contenido, "Contraseña inicial *", password=True)
            self._f_pass.pack(fill="x", pady=(0, 8))

        Separador(contenido).pack(fill="x", pady=(8, 16))

        fila_btns = tk.Frame(contenido, bg=C.FONDO_PRINCIPAL)
        fila_btns.pack(fill="x")
        BotonPrimario(fila_btns, "Guardar", self._guardar).pack(side="left", padx=(0, 8))
        BotonGhost(fila_btns, "Cancelar", self.destroy).pack(side="left")

        self._estado = EtiquetaEstado(contenido)
        self._estado.pack(anchor="w", pady=(10, 0))

    def _precargar(self):
        self._f_nombre.set(self._socio.nombre)
        self._f_apellidos.set(self._socio.apellidos)
        self._f_email.set(self._socio.email)

    def _guardar(self):
        nombre    = self._f_nombre.get().strip()
        apellidos = self._f_apellidos.get().strip()
        email     = self._f_email.get().strip()

        if not all([nombre, apellidos, email]):
            self._estado.error("Nombre, apellidos y email son obligatorios.")
            return

        # No validamos el email aquí — el setter de Usuario en models.py
        # lanza ValueError con el mensaje adecuado si el formato no es correcto
        if self._socio:
            try:
                exito, msg = self._ctrl.modificar_socio(
                    self._socio.id_usuario, nombre, apellidos, email
                )
            except ValueError as e:
                self._estado.error(str(e))
                return
        else:
            pwd = self._f_pass.get()
            if not pwd or len(pwd) < 6:
                self._estado.error("La contraseña debe tener al menos 6 caracteres.")
                return
            try:
                exito, msg = self._ctrl.crear_socio(nombre, apellidos, email, pwd)
            except ValueError as e:
                self._estado.error(str(e))
                return

        if exito:
            if self._callback:
                self._callback()
            self.destroy()
        else:
            self._estado.error(msg)

    def _centrar(self):
        self.update_idletasks()
        ancho, alto = 420, self.winfo_reqheight() + 40
        x = (self.winfo_screenwidth()  - ancho) // 2
        y = (self.winfo_screenheight() - alto)  // 2
        self.geometry(f"{ancho}x{alto}+{x}+{y}")


# ==========================================
# FORMULARIO: EMPLEADO
# ==========================================

class FormularioEmpleado(tk.Toplevel):
    """Formulario modal para registrar un nuevo empleado."""

    def __init__(self, parent, controlador, callback_ok: Callable = None):
        super().__init__(parent)
        self._ctrl     = controlador
        self._callback = callback_ok

        self.title("Añadir empleado")
        self.configure(bg=C.FONDO_PRINCIPAL)
        self.resizable(False, False)
        self.grab_set()
        self._construir()
        self._centrar()

    def _construir(self):
        contenido = tk.Frame(self, bg=C.FONDO_PRINCIPAL, padx=30, pady=24)
        contenido.pack(fill="both", expand=True)

        tk.Label(
            contenido, text="Nuevo empleado",
            font=F.TITULO_MEDIO, bg=C.FONDO_PRINCIPAL, fg=C.ACENTO
        ).pack(anchor="w", pady=(0, 8))

        # El ID se muestra como información, no como campo editable
        id_preview = self._ctrl.siguiente_id_empleado()
        tk.Label(
            contenido, text=f"ID asignado automáticamente: {id_preview}",
            font=F.CUERPO, bg=C.FONDO_PRINCIPAL, fg=C.TEXTO_SECUNDARIO
        ).pack(anchor="w", pady=(0, 4))

        tk.Label(
            contenido,
            text="Los campos marcados con * son obligatorios",
            font=F.PEQUEÑO, bg=C.FONDO_PRINCIPAL, fg=C.TEXTO_DESACTIVADO
        ).pack(anchor="w", pady=(0, 12))

        self._f_nombre    = CampoTexto(contenido, "Nombre *")
        self._f_nombre.pack(fill="x", pady=(0, 8))
        self._f_apellidos = CampoTexto(contenido, "Apellidos *")
        self._f_apellidos.pack(fill="x", pady=(0, 8))
        self._f_email     = CampoTexto(contenido, "Email *")
        self._f_email.pack(fill="x", pady=(0, 8))
        self._f_pass      = CampoTexto(contenido, "Contraseña inicial *", password=True)
        self._f_pass.pack(fill="x", pady=(0, 8))
        self._f_rol       = ComboBox(contenido, "Rol *", ROLES_EMPLEADO)
        self._f_rol.set(RolEmpleado.AUXILIAR.value)
        self._f_rol.pack(fill="x", pady=(0, 16))

        fila_btns = tk.Frame(contenido, bg=C.FONDO_PRINCIPAL)
        fila_btns.pack(fill="x")
        BotonPrimario(fila_btns, "Crear empleado", self._guardar).pack(side="left", padx=(0, 8))
        BotonGhost(fila_btns, "Cancelar", self.destroy).pack(side="left")

        self._estado = EtiquetaEstado(contenido)
        self._estado.pack(anchor="w", pady=(10, 0))

    def _guardar(self):
        nom   = self._f_nombre.get().strip()
        ape   = self._f_apellidos.get().strip()
        email = self._f_email.get().strip()
        pwd   = self._f_pass.get()
        rol   = RolEmpleado(self._f_rol.get())

        if not all([nom, ape, email, pwd]):
            self._estado.error("Todos los campos son obligatorios.")
            return

        if len(pwd) < 6:
            self._estado.error("La contraseña debe tener al menos 6 caracteres.")
            return

        # El setter de email en Usuario lanza ValueError si el formato no es correcto;
        # lo capturamos aquí para mostrárselo al usuario en lugar de explotar
        try:
            exito, msg = self._ctrl.crear_empleado(nom, ape, email, pwd, rol)
        except ValueError as e:
            self._estado.error(str(e))
            return

        if exito:
            if self._callback:
                self._callback()
            self.destroy()
        else:
            self._estado.error(msg)

    def _centrar(self):
        self.update_idletasks()
        ancho, alto = 420, self.winfo_reqheight() + 40
        x = (self.winfo_screenwidth()  - ancho) // 2
        y = (self.winfo_screenheight() - alto)  // 2
        self.geometry(f"{ancho}x{alto}+{x}+{y}")
