"""
empleado_view.py

Ventana principal para empleados. Las pestañas visibles dependen del rol:
  Auxiliar:       Reservas pendientes · Préstamos activos · Mi cuenta
  Bibliotecario+: + Catálogo (añadir/editar/borrar) · Socios
  Admin:          + Empleados
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable

from biblioteca.models import Empleado, Socio, RolEmpleado
from biblioteca.ui.theme import Colores as C, Fuentes as F
from biblioteca.ui.widgets import (
    BotonPrimario, BotonSecundario, BotonPeligro, BotonGhost,
    CampoTexto, TablaDatos, EtiquetaEstado, CabeceraPanel, Separador,
    confirmar
)
from biblioteca.ui.formularios import FormularioMaterial, FormularioSocio, FormularioEmpleado
from biblioteca.ui.selectores import (
    SelectorSocio, SelectorMaterial,
    VentanaDetalleSocio, VentanaDetalleEmpleado, DialogoSeleccion
)

ROLES_EMPLEADO = [r.value for r in RolEmpleado]


class VentanaEmpleado(tk.Toplevel):
    """Ventana principal del empleado. Las pestañas se montan según el rol."""

    def __init__(self, root: tk.Tk, controlador, empleado: Empleado, callback_logout: Callable):
        super().__init__(root)
        self._ctrl     = controlador
        self._empleado = empleado
        self._callback_logout = callback_logout

        self.title(f"Biblioteca · Personal · {empleado.nombre} ({empleado.rol.value})")
        self.configure(bg=C.FONDO_PRINCIPAL)
        self.protocol("WM_DELETE_WINDOW", self._al_cerrar)
        self._maximizar()
        self._construir_ui()

    # ==========================================
    # CONSTRUCCIÓN DE LA INTERFAZ
    # ==========================================

    def _construir_ui(self):
        self._barra_superior()

        self._notebook = ttk.Notebook(self)
        self._notebook.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        # Mapeamos cada pestaña con su función de carga para no depender de índices fijos
        self._tab_loaders = {}

        self._notebook.add(self._crear_tab_reservas(),  text="  📌  Reservas Pendientes  ")
        self._tab_loaders[self._notebook.index("end") - 1] = self._cargar_reservas

        self._notebook.add(self._crear_tab_prestamos(), text="  📋  Préstamos Activos  ")
        self._tab_loaders[self._notebook.index("end") - 1] = self._cargar_prestamos_activos

        self._notebook.add(self._crear_tab_cuenta(),    text="  👤  Mi Cuenta  ")

        if self._empleado.es_bibliotecario_o_superior():
            self._notebook.add(self._crear_tab_catalogo(), text="  📚  Catálogo  ")
            self._tab_loaders[self._notebook.index("end") - 1] = self._cargar_catalogo

            self._notebook.add(self._crear_tab_socios(),   text="  👥  Socios  ")
            self._tab_loaders[self._notebook.index("end") - 1] = self._cargar_socios

        if self._empleado.es_admin():
            self._notebook.add(self._crear_tab_empleados(), text="  🔑  Empleados  ")
            self._tab_loaders[self._notebook.index("end") - 1] = self._cargar_empleados

        self._notebook.bind("<<NotebookTabChanged>>", self._al_cambiar_tab)

        self._cargar_reservas()
        self._cargar_prestamos_activos()

    def _barra_superior(self):
        barra = tk.Frame(self, bg=C.FONDO_PANEL, height=56)
        barra.pack(fill="x")
        barra.pack_propagate(False)

        tk.Frame(barra, bg=C.ACENTO, width=5).pack(side="left", fill="y")

        tk.Label(
            barra, text="📚  BIBLIOTECA · PERSONAL",
            font=F.TITULO_PEQUEÑO, bg=C.FONDO_PANEL, fg=C.ACENTO, padx=16
        ).pack(side="left")

        colores_rol = {
            RolEmpleado.AUXILIAR:      C.AZUL,
            RolEmpleado.BIBLIOTECARIO: C.ACENTO,
            RolEmpleado.ADMIN:         C.ERROR
        }
        color_rol = colores_rol.get(self._empleado.rol, C.TEXTO_SECUNDARIO)

        tk.Label(
            barra, text=f"  {self._empleado.rol.value.upper()}  ",
            font=F.LABEL_CAMPO, bg=color_rol, fg=C.FONDO_PRINCIPAL
        ).pack(side="right", pady=16, padx=(0, 16))

        tk.Label(
            barra, text=f"Hola, {self._empleado.nombre}",
            font=F.CUERPO, bg=C.FONDO_PANEL, fg=C.TEXTO_SECUNDARIO
        ).pack(side="right", padx=(16, 8))

        BotonGhost(barra, "Cerrar sesión", self._logout).pack(side="right", padx=(0, 12), pady=8)

    # ==========================================
    # TAB: RESERVAS PENDIENTES
    # ==========================================

    def _crear_tab_reservas(self) -> tk.Frame:
        tab = tk.Frame(self._notebook, bg=C.FONDO_PRINCIPAL)

        cab = CabeceraPanel(tab, "Reservas pendientes de recogida")
        cab.agregar_boton("↺  Actualizar", self._cargar_reservas, "ghost")
        cab.pack(fill="x", padx=16, pady=(16, 8))

        tk.Label(
            tab,
            text="Doble clic sobre una reserva para rellenar el ID automáticamente.",
            font=F.PEQUEÑO, bg=C.FONDO_PRINCIPAL, fg=C.TEXTO_DESACTIVADO
        ).pack(anchor="w", padx=16, pady=(0, 6))

        # Barra de búsqueda
        barra = tk.Frame(tab, bg=C.FONDO_PRINCIPAL)
        barra.pack(fill="x", padx=16, pady=(0, 8))

        self._res_busqueda = tk.Entry(
            barra, font=F.CUERPO, bg=C.FONDO_WIDGET, fg=C.TEXTO_PRINCIPAL,
            insertbackground=C.ACENTO, relief="flat", bd=8
        )
        self._res_busqueda.insert(0, "Buscar por socio o material...")
        self._res_busqueda.config(fg=C.TEXTO_DESACTIVADO)
        self._res_busqueda.bind("<FocusIn>",    lambda e: self._placeholder_in(self._res_busqueda, "Buscar por socio o material..."))
        self._res_busqueda.bind("<FocusOut>",   lambda e: self._placeholder_out(self._res_busqueda, "Buscar por socio o material..."))
        self._res_busqueda.bind("<KeyRelease>", lambda e: self._filtrar_reservas())
        self._res_busqueda.pack(side="left", fill="x", expand=True, padx=(0, 12))

        BotonGhost(barra, "✕ Limpiar", lambda: (
            self._res_busqueda.delete(0, tk.END),
            self._res_busqueda.insert(0, "Buscar por socio o material..."),
            self._res_busqueda.config(fg=C.TEXTO_DESACTIVADO),
            self._filtrar_reservas()
        )).pack(side="left")

        cols = [
            ("id_res",   "ID Reserva",      120, "w"),
            ("socio",    "Socio",           200, "w"),
            ("material", "Material",        260, "w"),
            ("limite",   "Límite recogida", 160, "center"),
            ("estado",   "Estado",          120, "center"),
        ]
        self._tabla_reservas = TablaDatos(tab, cols, altura_filas=14)
        self._tabla_reservas.pack(fill="both", expand=True, padx=16, pady=(0, 8))
        self._tabla_reservas.bind_doble_click(self._al_doble_click_reserva)

        pie = tk.Frame(tab, bg=C.FONDO_PANEL, padx=16, pady=10)
        pie.pack(fill="x", padx=16, pady=(0, 16))

        tk.Label(pie, text="ID Reserva:", font=F.CUERPO,
                 bg=C.FONDO_PANEL, fg=C.TEXTO_SECUNDARIO).pack(side="left", padx=(0, 6))

        self._campo_id_reserva = tk.Entry(
            pie, font=F.MONO, bg=C.FONDO_WIDGET, fg=C.ACENTO,
            insertbackground=C.ACENTO, relief="flat", bd=6, width=20
        )
        self._campo_id_reserva.pack(side="left", padx=(0, 10))

        BotonPrimario(pie, "✓ Formalizar", self._formalizar_recogida).pack(side="left", padx=(0, 6))
        BotonPeligro(pie, "✕ Cancelar reserva", self._cancelar_reserva).pack(side="left")

        self._estado_reservas = EtiquetaEstado(tab)
        self._estado_reservas.pack(pady=(0, 8))

        self._reservas_cache = []

        return tab

    def _cargar_reservas(self):
        reservas = self._ctrl.obtener_reservas_activas()
        self._reservas_cache = reservas
        self._renderizar_reservas(reservas)

    def _filtrar_reservas(self):
        texto = self._res_busqueda.get().lower()
        placeholder = "buscar por socio o material..."
        if not texto or texto == placeholder:
            self._renderizar_reservas(self._reservas_cache)
            return
        filtradas = [
            r for r in self._reservas_cache
            if texto in r.usuario.nombre.lower()
            or texto in r.usuario.apellidos.lower()
            or texto in r.usuario.id_usuario.lower()
            or texto in r.material.titulo.lower()
        ]
        self._renderizar_reservas(filtradas)

    def _renderizar_reservas(self, reservas: list):
        filas = []
        for r in reservas:
            tag = "expirado" if r.ha_expirado() else ""
            filas.append(((
                r.id_reserva,
                f"{r.usuario.nombre} {r.usuario.apellidos} [{r.usuario.id_usuario}]",
                r.material.titulo,
                r.fecha_limite_recogida.strftime("%d/%m/%Y %H:%M"),
                r.estado.value
            ), tag))
        self._tabla_reservas.cargar_con_tags(filas)

    def _al_doble_click_reserva(self, fila):
        if not fila:
            return
        self._campo_id_reserva.delete(0, tk.END)
        self._campo_id_reserva.insert(0, fila[0])

    def _formalizar_recogida(self):
        id_res = self._campo_id_reserva.get().strip()
        if not id_res:
            self._estado_reservas.error("Introduce el ID de la reserva.")
            return

        exito, msg = self._ctrl.procesar_recogida(id_res)
        if exito:
            self._estado_reservas.exito(msg)
            self._campo_id_reserva.delete(0, tk.END)
            self._cargar_reservas()
            self._cargar_prestamos_activos()
        else:
            self._estado_reservas.error(msg)

    def _cancelar_reserva(self):
        id_res = self._campo_id_reserva.get().strip()
        if not id_res:
            self._estado_reservas.error("Introduce o selecciona el ID de la reserva.")
            return

        reserva = self._ctrl.repo.obtener_reserva(id_res.upper())
        if not reserva:
            self._estado_reservas.error("Reserva no encontrada.")
            return

        if not confirmar(
            "Cancelar reserva",
            f"¿Cancelar la reserva '{id_res}' de '{reserva.material.titulo}' "
            f"para {reserva.usuario.nombre} {reserva.usuario.apellidos}?\n\n"
            f"El material volverá a estar disponible y se liberará el cupo del socio."
        ):
            return

        self._ctrl._expirar_reserva(reserva)
        self._estado_reservas.exito(f"Reserva '{id_res}' cancelada. Material liberado.")
        self._campo_id_reserva.delete(0, tk.END)
        self._cargar_reservas()

    # ==========================================
    # TAB: PRÉSTAMOS ACTIVOS
    # ==========================================

    def _crear_tab_prestamos(self) -> tk.Frame:
        tab = tk.Frame(self._notebook, bg=C.FONDO_PRINCIPAL)

        # Estado del toggle: False = solo activos, True = incluye devueltos
        self._mostrar_historial = False

        cab = CabeceraPanel(tab, "Préstamos activos")
        cab.agregar_boton("↺  Actualizar", self._cargar_prestamos_activos, "ghost")
        cab.pack(fill="x", padx=16, pady=(16, 8))

        # Barra de toggle para el historial
        barra_hist = tk.Frame(tab, bg=C.FONDO_PRINCIPAL)
        barra_hist.pack(fill="x", padx=16, pady=(0, 8))

        self._btn_historial = BotonGhost(
            barra_hist, "🕑 Mostrar historial (devueltos)", self._toggle_historial
        )
        self._btn_historial.pack(side="left")

        self._lbl_historial = tk.Label(
            barra_hist, text="Mostrando solo préstamos activos y retrasados",
            font=F.PEQUEÑO, bg=C.FONDO_PRINCIPAL, fg=C.TEXTO_DESACTIVADO
        )
        self._lbl_historial.pack(side="left", padx=(12, 0))

        # Panel crear reserva para un socio
        panel_reserva = tk.LabelFrame(
            tab, text="  Crear reserva para un socio  ",
            font=F.LABEL_CAMPO, bg=C.FONDO_PANEL, fg=C.ACENTO,
            bd=1, relief="solid", padx=12, pady=10
        )
        panel_reserva.pack(fill="x", padx=16, pady=(0, 12))

        fila_r = tk.Frame(panel_reserva, bg=C.FONDO_PANEL)
        fila_r.pack(fill="x")

        self._res_id_socio = tk.Entry(
            fila_r, font=F.MONO, bg=C.FONDO_WIDGET, fg=C.AZUL,
            insertbackground=C.AZUL, relief="flat", bd=6, width=16
        )
        self._res_id_socio.insert(0, "ID Socio")
        self._res_id_socio.config(fg=C.TEXTO_DESACTIVADO)
        self._res_id_socio.bind("<FocusIn>",  lambda e: self._placeholder_in(self._res_id_socio, "ID Socio"))
        self._res_id_socio.bind("<FocusOut>", lambda e: self._placeholder_out(self._res_id_socio, "ID Socio"))
        self._res_id_socio.pack(side="left", padx=(0, 8))

        self._res_id_mat = tk.Entry(
            fila_r, font=F.MONO, bg=C.FONDO_WIDGET, fg=C.AZUL,
            insertbackground=C.AZUL, relief="flat", bd=6, width=20
        )
        self._res_id_mat.insert(0, "Código Material")
        self._res_id_mat.config(fg=C.TEXTO_DESACTIVADO)
        self._res_id_mat.bind("<FocusIn>",  lambda e: self._placeholder_in(self._res_id_mat, "Código Material"))
        self._res_id_mat.bind("<FocusOut>", lambda e: self._placeholder_out(self._res_id_mat, "Código Material"))
        self._res_id_mat.pack(side="left", padx=(0, 12))

        BotonSecundario(fila_r, "📌  Crear reserva", self._crear_reserva_por_empleado).pack(side="left")
        BotonGhost(fila_r, "🔍 Socio",    self._seleccionar_socio_para_reserva).pack(side="left", padx=(8, 0))
        BotonGhost(fila_r, "🔍 Material", self._seleccionar_material_para_reserva).pack(side="left", padx=(4, 0))

        self._estado_crear_res = EtiquetaEstado(panel_reserva)
        self._estado_crear_res.pack(anchor="w", pady=(6, 0))

        cols = [
            ("id",       "ID Préstamo", 120, "w"),
            ("socio",    "Socio",       200, "w"),
            ("material", "Material",    240, "w"),
            ("prestado", "Prestado",    110, "center"),
            ("devolver", "Devolver",    110, "center"),
            ("estado",   "Estado",      110, "center"),
        ]
        self._tabla_prestamos = TablaDatos(tab, cols, altura_filas=14)
        self._tabla_prestamos.pack(fill="both", expand=True, padx=16, pady=(0, 8))
        self._tabla_prestamos.bind_doble_click(self._al_doble_click_prestamo)

        pie = tk.Frame(tab, bg=C.FONDO_PANEL, padx=16, pady=12)
        pie.pack(fill="x", padx=16, pady=(0, 16))

        tk.Label(
            pie, text="ID del préstamo a devolver:",
            font=F.CUERPO, bg=C.FONDO_PANEL, fg=C.TEXTO_SECUNDARIO
        ).pack(side="left", padx=(0, 8))

        self._campo_id_prestamo = tk.Entry(
            pie, font=F.MONO, bg=C.FONDO_WIDGET, fg=C.ACENTO,
            insertbackground=C.ACENTO, relief="flat", bd=6, width=22
        )
        self._campo_id_prestamo.pack(side="left", padx=(0, 12))

        BotonPrimario(pie, "↩  Registrar devolución", self._registrar_devolucion).pack(side="left")

        self._estado_prestamos = EtiquetaEstado(tab)
        self._estado_prestamos.pack(pady=(0, 8))

        return tab

    def _cargar_prestamos_activos(self):
        """
        Carga la tabla de préstamos respetando el estado del toggle de historial.
        Si el historial está activo devuelve todos (incluidos devueltos);
        si no, solo los pendientes de devolución.
        """
        if self._mostrar_historial:
            prestamos = self._ctrl.obtener_todos_los_prestamos()
        else:
            prestamos = self._ctrl.obtener_prestamos_activos()

        filas = []
        for p in prestamos:
            p.actualizar_estado()
            if p.estado.value == "Retrasado":
                tag = "retrasado"
            elif p.estado.value == "Devuelto":
                tag = "devuelto"
            else:
                tag = ""
            filas.append(((
                p.id_prestamo,
                f"{p.usuario.nombre} {p.usuario.apellidos}",
                p.material.titulo,
                p.fecha_prestamo.strftime("%d/%m/%Y"),
                p.fecha_devolucion_prevista.strftime("%d/%m/%Y"),
                p.estado.value
            ), tag))
        self._tabla_prestamos.cargar_con_tags(filas)

    def _toggle_historial(self):
        """Alterna entre mostrar solo los préstamos activos y mostrar el historial completo."""
        self._mostrar_historial = not self._mostrar_historial

        if self._mostrar_historial:
            self._btn_historial.config(text="🕑 Ocultar devueltos")
            self._lbl_historial.config(
                text="Mostrando historial completo (incluye devueltos)",
                fg=C.AZUL
            )
        else:
            self._btn_historial.config(text="🕑 Mostrar historial (devueltos)")
            self._lbl_historial.config(
                text="Mostrando solo préstamos activos y retrasados",
                fg=C.TEXTO_DESACTIVADO
            )

        self._cargar_prestamos_activos()

    def _al_doble_click_prestamo(self, fila):
        if not fila:
            return
        self._campo_id_prestamo.delete(0, tk.END)
        self._campo_id_prestamo.insert(0, fila[0])

    def _registrar_devolucion(self):
        id_p = self._campo_id_prestamo.get().strip()
        if not id_p:
            self._estado_prestamos.error("Introduce el ID del préstamo.")
            return

        exito, msg = self._ctrl.procesar_devolucion(id_p)
        if exito:
            self._estado_prestamos.exito(msg)
            self._campo_id_prestamo.delete(0, tk.END)
            self._cargar_prestamos_activos()
        else:
            self._estado_prestamos.error(msg)

    def _crear_reserva_por_empleado(self):
        id_socio = self._res_id_socio.get().strip()
        id_mat   = self._res_id_mat.get().strip()

        if not id_socio or id_socio == "ID Socio":
            self._estado_crear_res.error("Introduce el ID del socio.")
            return
        if not id_mat or id_mat == "Código Material":
            self._estado_crear_res.error("Introduce el código del material.")
            return

        exito, msg = self._ctrl.realizar_reserva(id_socio, id_mat)
        if exito:
            self._estado_crear_res.exito(msg)
            self._cargar_reservas()
        else:
            self._estado_crear_res.error(msg)

    def _seleccionar_socio_para_reserva(self):
        sel = SelectorSocio(self, self._ctrl)
        self.wait_window(sel)
        if sel.resultado:
            self._placeholder_in(self._res_id_socio, "ID Socio")
            self._res_id_socio.delete(0, tk.END)
            self._res_id_socio.insert(0, sel.resultado)
            self._res_id_socio.config(fg=C.TEXTO_PRINCIPAL)

    def _seleccionar_material_para_reserva(self):
        sel = SelectorMaterial(self, self._ctrl)
        self.wait_window(sel)
        if sel.resultado:
            self._placeholder_in(self._res_id_mat, "Código Material")
            self._res_id_mat.delete(0, tk.END)
            self._res_id_mat.insert(0, sel.resultado)
            self._res_id_mat.config(fg=C.TEXTO_PRINCIPAL)

    # ==========================================
    # TAB: CATÁLOGO (Bibliotecario+)
    # ==========================================

    def _crear_tab_catalogo(self) -> tk.Frame:
        tab = tk.Frame(self._notebook, bg=C.FONDO_PRINCIPAL)

        cab = CabeceraPanel(tab, "Gestión del catálogo")
        cab.agregar_boton("+ Añadir material", self._abrir_formulario_material, "primario")
        cab.pack(fill="x", padx=16, pady=(16, 8))

        filtro_frame = tk.Frame(tab, bg=C.FONDO_PRINCIPAL)
        filtro_frame.pack(fill="x", padx=16, pady=(0, 8))

        self._cat_busqueda = tk.Entry(
            filtro_frame, font=F.CUERPO, bg=C.FONDO_WIDGET, fg=C.TEXTO_PRINCIPAL,
            insertbackground=C.ACENTO, relief="flat", bd=8
        )
        self._cat_busqueda.insert(0, "Buscar por título...")
        self._cat_busqueda.config(fg=C.TEXTO_DESACTIVADO)
        self._cat_busqueda.bind("<FocusIn>",    lambda e: self._placeholder_in(self._cat_busqueda, "Buscar por título..."))
        self._cat_busqueda.bind("<FocusOut>",   lambda e: self._placeholder_out(self._cat_busqueda, "Buscar por título..."))
        self._cat_busqueda.bind("<KeyRelease>", lambda e: self._cargar_catalogo())
        self._cat_busqueda.pack(side="left", fill="x", expand=True, padx=(0, 12))

        BotonGhost(filtro_frame, "↺  Refrescar", self._cargar_catalogo).pack(side="left")

        cols = [
            ("codigo",  "Código",  110, "w"),
            ("tipo",    "Tipo",    120, "w"),
            ("titulo",  "Título",  260, "w"),
            ("detalle", "Detalle", 200, "w"),
            ("estado",  "Estado",  130, "center"),
        ]
        self._tabla_catalogo = TablaDatos(tab, cols, altura_filas=16)
        self._tabla_catalogo.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        pie = tk.Frame(tab, bg=C.FONDO_PANEL, padx=16, pady=10)
        pie.pack(fill="x", padx=16, pady=(0, 16))

        BotonSecundario(pie, "✏  Editar seleccionado",  self._editar_seleccionado).pack(side="left", padx=(0, 8))
        BotonPeligro(pie,   "🗑  Eliminar seleccionado", self._eliminar_seleccionado).pack(side="left")

        self._estado_catalogo = EtiquetaEstado(tab)
        self._estado_catalogo.pack(pady=(0, 8))

        return tab

    def _cargar_catalogo(self):
        titulo = ""
        if hasattr(self, "_cat_busqueda"):
            v = self._cat_busqueda.get()
            titulo = "" if v == "Buscar por título..." else v

        materiales = self._ctrl.buscar_materiales(titulo=titulo or None)
        filas = []
        for m in materiales:
            if hasattr(m, "autor") and m.autor:
                det = f"Autor: {m.autor}"
            elif hasattr(m, "editorial") and m.editorial:
                det = f"Editorial: {m.editorial}"
            elif hasattr(m, "fabricante") and m.fabricante:
                det = f"Fab: {m.fabricante}"
            elif hasattr(m, "licencias_totales"):
                det = f"Licencias: {m.licencias_disponibles}/{m.licencias_totales}"
            else:
                det = "—"
            filas.append((m.codigo_id, type(m).__name__, m.titulo, det, m.estado.value))
        self._tabla_catalogo.cargar(filas)

    def _editar_seleccionado(self):
        fila = self._tabla_catalogo.seleccion()
        if not fila:
            self._estado_catalogo.error("Selecciona un material primero.")
            return
        material = self._ctrl.buscar_material(fila[0])
        if material:
            self._abrir_formulario_material(material)

    def _eliminar_seleccionado(self):
        fila = self._tabla_catalogo.seleccion()
        if not fila:
            self._estado_catalogo.error("Selecciona un material primero.")
            return

        if not confirmar("Eliminar material", f"¿Eliminar '{fila[2]}' permanentemente? Esta acción no se puede deshacer."):
            return

        exito, msg = self._ctrl.eliminar_material(fila[0])
        if exito:
            self._estado_catalogo.exito(msg)
            self._cargar_catalogo()
        else:
            self._estado_catalogo.error(msg)

    def _abrir_formulario_material(self, material=None):
        FormularioMaterial(self, self._ctrl, material, self._cargar_catalogo)

    # ==========================================
    # TAB: SOCIOS (Bibliotecario+)
    # ==========================================

    def _crear_tab_socios(self) -> tk.Frame:
        tab = tk.Frame(self._notebook, bg=C.FONDO_PRINCIPAL)

        cab = CabeceraPanel(tab, "Gestión de socios")
        cab.pack(fill="x", padx=16, pady=(16, 8))

        barra = tk.Frame(tab, bg=C.FONDO_PRINCIPAL)
        barra.pack(fill="x", padx=16, pady=(0, 8))

        self._socios_busqueda = tk.Entry(
            barra, font=F.CUERPO, bg=C.FONDO_WIDGET, fg=C.TEXTO_PRINCIPAL,
            insertbackground=C.ACENTO, relief="flat", bd=8
        )
        self._socios_busqueda.insert(0, "Buscar por nombre, email o ID...")
        self._socios_busqueda.config(fg=C.TEXTO_DESACTIVADO)
        self._socios_busqueda.bind("<FocusIn>",    lambda e: self._placeholder_in(self._socios_busqueda, "Buscar por nombre, email o ID..."))
        self._socios_busqueda.bind("<FocusOut>",   lambda e: self._placeholder_out(self._socios_busqueda, "Buscar por nombre, email o ID..."))
        self._socios_busqueda.bind("<KeyRelease>", lambda e: self._filtrar_socios())
        self._socios_busqueda.pack(side="left", fill="x", expand=True, padx=(0, 12))

        BotonGhost(barra, "↺  Refrescar", self._cargar_socios).pack(side="left")

        cols = [
            ("id",      "ID",         100, "w"),
            ("nombre",  "Nombre",     200, "w"),
            ("email",   "Email",      220, "w"),
            ("activos", "Préstamos",   90, "center"),
            ("maximo",  "Límite",      70, "center"),
            ("sancion", "Sancionado", 100, "center"),
        ]
        self._tabla_socios = TablaDatos(tab, cols, altura_filas=16)
        self._tabla_socios.pack(fill="both", expand=True, padx=16, pady=(0, 8))
        self._tabla_socios.bind_doble_click(self._abrir_detalle_socio)

        pie = tk.Frame(tab, bg=C.FONDO_PANEL, padx=16, pady=10)
        pie.pack(fill="x", padx=16, pady=(0, 16))

        BotonPrimario(pie,   "+ Nuevo socio",    self._abrir_formulario_socio).pack(side="left", padx=(0, 8))
        BotonSecundario(pie, "✏ Editar",         lambda: self._abrir_formulario_socio(self._tabla_socios.seleccion())).pack(side="left", padx=(0, 8))
        BotonSecundario(pie, "📄 Ver detalle",   lambda: self._abrir_detalle_socio(self._tabla_socios.seleccion())).pack(side="left", padx=(0, 8))
        BotonPeligro(pie,   "🗑 Eliminar",        self._eliminar_socio).pack(side="left", padx=(0, 8))
        BotonPeligro(pie,   "⚖ Cambiar sanción", self._cambiar_sancion_socio).pack(side="left")

        self._estado_socios = EtiquetaEstado(tab)
        self._estado_socios.pack(pady=(0, 8))

        self._socios_cache = []

        return tab

    def _cargar_socios(self):
        usuarios = self._ctrl.obtener_todos_los_usuarios()
        self._socios_cache = [u for u in usuarios if isinstance(u, Socio)]
        self._renderizar_socios(self._socios_cache)

    def _filtrar_socios(self):
        texto = self._socios_busqueda.get().lower()
        placeholder = "buscar por nombre, email o id..."
        if not texto or texto == placeholder:
            self._renderizar_socios(self._socios_cache)
            return
        filtrados = [
            s for s in self._socios_cache
            if texto in s.nombre.lower()
            or texto in s.apellidos.lower()
            or texto in s.email.lower()
            or texto in s.id_usuario.lower()
        ]
        self._renderizar_socios(filtrados)

    def _renderizar_socios(self, socios: list):
        filas = []
        for s in socios:
            filas.append((
                s.id_usuario, f"{s.nombre} {s.apellidos}", s.email,
                s.prestamos_activos, s.max_prestamos,
                "Sí ⚠" if s.sancionado else "No"
            ))
        self._tabla_socios.cargar(filas)

    def _abrir_detalle_socio(self, fila):
        if not fila:
            self._estado_socios.error("Selecciona un socio primero.")
            return
        socio = self._ctrl.buscar_usuario(fila[0])
        if socio and isinstance(socio, Socio):
            VentanaDetalleSocio(self, self._ctrl, socio, self._cargar_socios)

    def _cambiar_sancion_socio(self):
        fila = self._tabla_socios.seleccion()
        if not fila:
            self._estado_socios.error("Selecciona un socio primero.")
            return

        accion = "levantar la sanción de" if fila[5].startswith("Sí") else "sancionar a"
        if not confirmar("Cambiar sanción", f"¿Deseas {accion} {fila[1]}?"):
            return

        exito, msg = self._ctrl.cambiar_sancion_socio(fila[0])
        if exito:
            self._estado_socios.exito(msg)
            self._cargar_socios()
        else:
            self._estado_socios.error(msg)

    def _abrir_formulario_socio(self, fila=None):
        socio = None
        if fila:
            socio = self._ctrl.buscar_usuario(fila[0])
            if not isinstance(socio, Socio):
                socio = None
        FormularioSocio(self, self._ctrl, socio, self._cargar_socios)

    def _eliminar_socio(self):
        fila = self._tabla_socios.seleccion()
        if not fila:
            self._estado_socios.error("Selecciona un socio primero.")
            return

        if not confirmar("Eliminar socio", f"¿Eliminar a '{fila[1]}' permanentemente?\nEsta acción no se puede deshacer."):
            return

        exito, msg = self._ctrl.eliminar_socio(fila[0])
        if exito:
            self._estado_socios.exito(msg)
            self._cargar_socios()
        else:
            self._estado_socios.error(msg)

    # ==========================================
    # TAB: EMPLEADOS (Solo Admin)
    # ==========================================

    def _crear_tab_empleados(self) -> tk.Frame:
        tab = tk.Frame(self._notebook, bg=C.FONDO_PRINCIPAL)

        cab = CabeceraPanel(tab, "Gestión de empleados")
        cab.agregar_boton("+ Añadir empleado", self._abrir_formulario_empleado, "primario")
        cab.pack(fill="x", padx=16, pady=(16, 8))

        cols = [
            ("id",     "ID",     100, "w"),
            ("nombre", "Nombre", 220, "w"),
            ("email",  "Email",  220, "w"),
            ("rol",    "Rol",    140, "center"),
        ]
        self._tabla_empleados = TablaDatos(tab, cols, altura_filas=16)
        self._tabla_empleados.pack(fill="both", expand=True, padx=16, pady=(0, 8))
        # Doble clic abre el detalle de empleado editable
        self._tabla_empleados.bind_doble_click(self._abrir_detalle_empleado)

        pie = tk.Frame(tab, bg=C.FONDO_PANEL, padx=16, pady=10)
        pie.pack(fill="x", padx=16, pady=(0, 16))

        BotonSecundario(pie, "↺  Refrescar",    self._cargar_empleados).pack(side="left", padx=(0, 8))
        BotonSecundario(pie, "✏  Editar",        lambda: self._abrir_detalle_empleado(self._tabla_empleados.seleccion())).pack(side="left", padx=(0, 8))
        BotonSecundario(pie, "🔄  Cambiar rol",  self._cambiar_rol).pack(side="left")

        self._estado_empleados = EtiquetaEstado(tab)
        self._estado_empleados.pack(pady=(0, 8))

        return tab

    def _cargar_empleados(self):
        usuarios = self._ctrl.obtener_todos_los_usuarios()
        empleados = [u for u in usuarios if isinstance(u, Empleado)]
        filas = [(e.id_usuario, f"{e.nombre} {e.apellidos}", e.email, e.rol.value) for e in empleados]
        self._tabla_empleados.cargar(filas)

    def _abrir_detalle_empleado(self, fila):
        """Abre la ventana de edición completa del empleado seleccionado."""
        if not fila:
            self._estado_empleados.error("Selecciona un empleado primero.")
            return

        id_e = fila[0]
        if id_e == self._empleado.id_usuario:
            self._estado_empleados.error("Para editar tu propio perfil usa 'Mi Cuenta'.")
            return

        empleado = self._ctrl.buscar_usuario(id_e)
        if empleado and isinstance(empleado, Empleado):
            VentanaDetalleEmpleado(self, self._ctrl, empleado, self._cargar_empleados)

    def _cambiar_rol(self):
        fila = self._tabla_empleados.seleccion()
        if not fila:
            self._estado_empleados.error("Selecciona un empleado primero.")
            return

        id_e = fila[0]
        if id_e == self._empleado.id_usuario:
            self._estado_empleados.error("No puedes cambiar tu propio rol.")
            return

        dialogo = DialogoSeleccion(self, "Cambiar rol", f"Nuevo rol para {fila[1]}:", ROLES_EMPLEADO)
        self.wait_window(dialogo)

        if not dialogo.resultado:
            return

        nuevo_rol = RolEmpleado(dialogo.resultado)
        exito, msg = self._ctrl.cambiar_rol_empleado(id_e, nuevo_rol)
        if exito:
            self._estado_empleados.exito(msg)
            self._cargar_empleados()
        else:
            self._estado_empleados.error(msg)

    def _abrir_formulario_empleado(self):
        FormularioEmpleado(self, self._ctrl, self._cargar_empleados)

    # ==========================================
    # TAB: MI CUENTA
    # ==========================================

    def _crear_tab_cuenta(self) -> tk.Frame:
        tab = tk.Frame(self._notebook, bg=C.FONDO_PRINCIPAL)

        contenido = tk.Frame(tab, bg=C.FONDO_PRINCIPAL, padx=40, pady=30)
        contenido.pack(fill="both", expand=True)

        tk.Label(
            contenido, text="Mi cuenta",
            font=F.TITULO_MEDIO, bg=C.FONDO_PRINCIPAL, fg=C.ACENTO
        ).pack(anchor="w", pady=(0, 4))

        tk.Label(
            contenido,
            text=f"{self._empleado.nombre} {self._empleado.apellidos}  ·  {self._empleado.id_usuario}  ·  {self._empleado.rol.value}",
            font=F.CUERPO, bg=C.FONDO_PRINCIPAL, fg=C.TEXTO_SECUNDARIO
        ).pack(anchor="w", pady=(0, 20))

        Separador(contenido).pack(fill="x", pady=(0, 24))

        tk.Label(contenido, text="Cambiar email", font=F.TITULO_PEQUEÑO,
                 bg=C.FONDO_PRINCIPAL, fg=C.TEXTO_PRINCIPAL).pack(anchor="w", pady=(0, 8))

        self._emp_nuevo_email = CampoTexto(contenido, "Nuevo email")
        self._emp_nuevo_email.pack(fill="x", pady=(0, 8))
        self._emp_estado_email = EtiquetaEstado(contenido)

        BotonSecundario(contenido, "Guardar email", self._cambiar_email).pack(anchor="w")
        self._emp_estado_email.pack(anchor="w", pady=(6, 20))

        Separador(contenido).pack(fill="x", pady=(0, 24))

        tk.Label(contenido, text="Cambiar contraseña", font=F.TITULO_PEQUEÑO,
                 bg=C.FONDO_PRINCIPAL, fg=C.TEXTO_PRINCIPAL).pack(anchor="w", pady=(0, 8))

        self._emp_pass_actual = CampoTexto(contenido, "Contraseña actual",  password=True)
        self._emp_pass_actual.pack(fill="x", pady=(0, 8))
        self._emp_pass_nueva  = CampoTexto(contenido, "Nueva contraseña",   password=True)
        self._emp_pass_nueva.pack(fill="x", pady=(0, 8))
        self._emp_pass_repite = CampoTexto(contenido, "Repetir contraseña", password=True)
        self._emp_pass_repite.pack(fill="x", pady=(0, 8))
        self._emp_estado_pass = EtiquetaEstado(contenido)

        BotonSecundario(contenido, "Guardar contraseña", self._cambiar_password).pack(anchor="w")
        self._emp_estado_pass.pack(anchor="w", pady=(6, 0))

        return tab

    def _cambiar_email(self):
        nuevo = self._emp_nuevo_email.get().strip()
        if not nuevo:
            self._emp_estado_email.error("Introduce el nuevo email.")
            return
        if "@" not in nuevo or "." not in nuevo.split("@")[-1]:
            self._emp_estado_email.error("El email no tiene un formato válido.")
            return
        exito, msg = self._ctrl.cambiar_email_usuario(self._empleado.id_usuario, nuevo)
        if exito:
            self._empleado = self._ctrl.buscar_usuario(self._empleado.id_usuario)
            self._emp_nuevo_email.limpiar()
            self._emp_estado_email.exito(msg)
        else:
            self._emp_estado_email.error(msg)

    def _cambiar_password(self):
        actual = self._emp_pass_actual.get()
        nueva  = self._emp_pass_nueva.get()
        repite = self._emp_pass_repite.get()
        if nueva != repite:
            self._emp_estado_pass.error("Las contraseñas no coinciden.")
            return
        if len(nueva) < 6:
            self._emp_estado_pass.error("Mínimo 6 caracteres.")
            return
        exito, msg = self._ctrl.cambiar_password_usuario(self._empleado.id_usuario, actual, nueva)
        if exito:
            self._emp_pass_actual.limpiar()
            self._emp_pass_nueva.limpiar()
            self._emp_pass_repite.limpiar()
            self._emp_estado_pass.exito(msg)
        else:
            self._emp_estado_pass.error(msg)

    # ==========================================
    # UTILIDADES
    # ==========================================

    def _placeholder_in(self, entry: tk.Entry, placeholder: str):
        if entry.get() == placeholder:
            entry.delete(0, tk.END)
            entry.config(fg=C.TEXTO_PRINCIPAL)

    def _placeholder_out(self, entry: tk.Entry, placeholder: str):
        if not entry.get():
            entry.insert(0, placeholder)
            entry.config(fg=C.TEXTO_DESACTIVADO)

    def _al_cambiar_tab(self, event):
        """Refresca los datos de la pestaña activa usando el mapa de loaders."""
        tab_idx = self._notebook.index("current")
        loader = self._tab_loaders.get(tab_idx)
        if loader:
            loader()

    def _logout(self):
        self._ctrl.detener_temporizador()
        self.destroy()
        self._callback_logout()

    def _al_cerrar(self):
        self._ctrl.detener_temporizador()
        self.master.destroy()

    def _maximizar(self):
        try:
            self.state("zoomed")
        except Exception:
            self.attributes("-zoomed", True)
        self.update_idletasks()
