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

from biblioteca.models import (
    Empleado, Socio, RolEmpleado, EstadoMaterial,
    Libro, Revista, Dispositivo, JuegoDeMesa, RecursoDigital, TipoDispositivo
)
from biblioteca.ui.theme import Colores as C, Fuentes as F
from biblioteca.ui.widgets import (
    BotonPrimario, BotonSecundario, BotonPeligro, BotonGhost,
    CampoTexto, CampoNumero, ComboBox, TablaDatos,
    EtiquetaEstado, CabeceraPanel, Separador,
    confirmar, alerta, error_dialogo
)

TIPOS_MATERIAL  = ["Libro", "Revista", "Dispositivo", "JuegoDeMesa", "RecursoDigital"]
ROLES_EMPLEADO  = [r.value for r in RolEmpleado]
TIPOS_DISP      = [t.value for t in TipoDispositivo]


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

        # Siempre disponibles para todos los empleados
        self._notebook.add(self._crear_tab_reservas(),  text="  📌  Reservas Pendientes  ")
        self._tab_loaders[self._notebook.index("end") - 1] = self._cargar_reservas

        self._notebook.add(self._crear_tab_prestamos(), text="  📋  Préstamos Activos  ")
        self._tab_loaders[self._notebook.index("end") - 1] = self._cargar_prestamos_activos

        self._notebook.add(self._crear_tab_cuenta(),    text="  👤  Mi Cuenta  ")
        # Mi Cuenta no necesita carga de datos desde la BD

        # Bibliotecario y admin
        if self._empleado.es_bibliotecario_o_superior():
            self._notebook.add(self._crear_tab_catalogo(), text="  📚  Catálogo  ")
            self._tab_loaders[self._notebook.index("end") - 1] = self._cargar_catalogo

            self._notebook.add(self._crear_tab_socios(),   text="  👥  Socios  ")
            self._tab_loaders[self._notebook.index("end") - 1] = self._cargar_socios

        # Solo admin
        if self._empleado.es_admin():
            self._notebook.add(self._crear_tab_empleados(), text="  🔑  Empleados  ")
            self._tab_loaders[self._notebook.index("end") - 1] = self._cargar_empleados

        self._notebook.bind("<<NotebookTabChanged>>", self._al_cambiar_tab)

        # Carga inicial de las pestañas que arrancan visibles
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

        # Badge del rol con color según nivel
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
    # TAB: RESERVAS PENDIENTES (Auxiliar+)
    # ==========================================

    def _crear_tab_reservas(self) -> tk.Frame:
        tab = tk.Frame(self._notebook, bg=C.FONDO_PRINCIPAL)

        cab = CabeceraPanel(tab, "Reservas pendientes de recogida")
        cab.agregar_boton("↺  Actualizar", self._cargar_reservas, "ghost")
        cab.pack(fill="x", padx=16, pady=(16, 8))

        tk.Label(
            tab,
            text="El socio debe presentarse en el mostrador con su ID de reserva.",
            font=F.PEQUEÑO, bg=C.FONDO_PRINCIPAL, fg=C.TEXTO_DESACTIVADO
        ).pack(anchor="w", padx=16, pady=(0, 8))

        cols = [
            ("id_res",   "ID Reserva", 120, "w"),
            ("socio",    "Socio",      200, "w"),
            ("material", "Material",   260, "w"),
            ("limite",   "Límite recogida", 160, "center"),
            ("estado",   "Estado",     120, "center"),
        ]
        self._tabla_reservas = TablaDatos(tab, cols, altura_filas=16)
        self._tabla_reservas.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        # Panel inferior: campo ID reserva + botón formalizar
        pie = tk.Frame(tab, bg=C.FONDO_PANEL, padx=16, pady=12)
        pie.pack(fill="x", padx=16, pady=(0, 16))

        tk.Label(
            pie, text="ID de la reserva a formalizar:",
            font=F.CUERPO, bg=C.FONDO_PANEL, fg=C.TEXTO_SECUNDARIO
        ).pack(side="left", padx=(0, 8))

        self._campo_id_reserva = tk.Entry(
            pie, font=F.MONO, bg=C.FONDO_WIDGET, fg=C.ACENTO,
            insertbackground=C.ACENTO, relief="flat", bd=6, width=22
        )
        self._campo_id_reserva.pack(side="left", padx=(0, 12))

        BotonPrimario(pie, "✓  Formalizar recogida", self._formalizar_recogida).pack(side="left")

        self._estado_reservas = EtiquetaEstado(tab)
        self._estado_reservas.pack(pady=(0, 8))

        return tab

    def _cargar_reservas(self):
        reservas = self._ctrl.obtener_reservas_activas()
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

    # ==========================================
    # TAB: PRÉSTAMOS ACTIVOS (Auxiliar+)
    # ==========================================

    def _crear_tab_prestamos(self) -> tk.Frame:
        tab = tk.Frame(self._notebook, bg=C.FONDO_PRINCIPAL)

        cab = CabeceraPanel(tab, "Préstamos activos")
        cab.agregar_boton("↺  Actualizar", self._cargar_prestamos_activos, "ghost")
        cab.pack(fill="x", padx=16, pady=(16, 8))

        # Panel superior: crear reserva para un socio
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
            insertbackground=C.AZUL, relief="flat", bd=6, width=16,
        )
        self._res_id_socio.insert(0, "ID Socio")
        self._res_id_socio.config(fg=C.TEXTO_DESACTIVADO)
        self._res_id_socio.bind("<FocusIn>",  lambda e: self._placeholder_in(self._res_id_socio,  "ID Socio"))
        self._res_id_socio.bind("<FocusOut>", lambda e: self._placeholder_out(self._res_id_socio, "ID Socio"))
        self._res_id_socio.pack(side="left", padx=(0, 8))

        self._res_id_mat = tk.Entry(
            fila_r, font=F.MONO, bg=C.FONDO_WIDGET, fg=C.AZUL,
            insertbackground=C.AZUL, relief="flat", bd=6, width=20
        )
        self._res_id_mat.insert(0, "Código Material")
        self._res_id_mat.config(fg=C.TEXTO_DESACTIVADO)
        self._res_id_mat.bind("<FocusIn>",  lambda e: self._placeholder_in(self._res_id_mat,  "Código Material"))
        self._res_id_mat.bind("<FocusOut>", lambda e: self._placeholder_out(self._res_id_mat, "Código Material"))
        self._res_id_mat.pack(side="left", padx=(0, 12))

        BotonSecundario(fila_r, "📌  Crear reserva", self._crear_reserva_por_empleado).pack(side="left")

        # Botones para abrir los selectores visuales
        BotonGhost(fila_r, "🔍 Socio", self._seleccionar_socio_para_reserva).pack(side="left", padx=(8, 0))
        BotonGhost(fila_r, "🔍 Material", self._seleccionar_material_para_reserva).pack(side="left", padx=(4, 0))

        self._estado_crear_res = EtiquetaEstado(panel_reserva)
        self._estado_crear_res.pack(anchor="w", pady=(6, 0))

        # Tabla de préstamos activos
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

        # Panel inferior: devolver
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
        prestamos = self._ctrl.obtener_prestamos_activos()
        filas = []
        for p in prestamos:
            p.actualizar_estado()
            tag = "retrasado" if p.estado.value == "Retrasado" else ""
            filas.append(((
                p.id_prestamo,
                f"{p.usuario.nombre} {p.usuario.apellidos}",
                p.material.titulo,
                p.fecha_prestamo.strftime("%d/%m/%Y"),
                p.fecha_devolucion_prevista.strftime("%d/%m/%Y"),
                p.estado.value
            ), tag))
        self._tabla_prestamos.cargar_con_tags(filas)

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
        """Abre el selector visual de socios y rellena el campo de ID."""
        sel = SelectorSocio(self, self._ctrl)
        self.wait_window(sel)
        if sel.resultado:
            self._placeholder_in(self._res_id_socio, "ID Socio")
            self._res_id_socio.delete(0, tk.END)
            self._res_id_socio.insert(0, sel.resultado)
            self._res_id_socio.config(fg=C.TEXTO_PRINCIPAL)

    def _seleccionar_material_para_reserva(self):
        """Abre el selector visual de materiales y rellena el campo de código."""
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

        # Filtro rápido
        filtro_frame = tk.Frame(tab, bg=C.FONDO_PRINCIPAL)
        filtro_frame.pack(fill="x", padx=16, pady=(0, 8))

        self._cat_busqueda = tk.Entry(
            filtro_frame, font=F.CUERPO, bg=C.FONDO_WIDGET, fg=C.TEXTO_PRINCIPAL,
            insertbackground=C.ACENTO, relief="flat", bd=8
        )
        self._cat_busqueda.insert(0, "Buscar por título...")
        self._cat_busqueda.config(fg=C.TEXTO_DESACTIVADO)
        self._cat_busqueda.bind("<FocusIn>",   lambda e: self._placeholder_in(self._cat_busqueda, "Buscar por título..."))
        self._cat_busqueda.bind("<FocusOut>",  lambda e: self._placeholder_out(self._cat_busqueda, "Buscar por título..."))
        self._cat_busqueda.bind("<KeyRelease>", lambda e: self._cargar_catalogo())
        self._cat_busqueda.pack(side="left", fill="x", expand=True, padx=(0, 12))

        BotonGhost(filtro_frame, "↺  Refrescar", self._cargar_catalogo).pack(side="left")

        cols = [
            ("codigo",  "Código",    110, "w"),
            ("tipo",    "Tipo",      120, "w"),
            ("titulo",  "Título",    260, "w"),
            ("detalle", "Detalle",   200, "w"),
            ("estado",  "Estado",    130, "center"),
        ]
        self._tabla_catalogo = TablaDatos(tab, cols, altura_filas=16)
        self._tabla_catalogo.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        pie = tk.Frame(tab, bg=C.FONDO_PANEL, padx=16, pady=10)
        pie.pack(fill="x", padx=16, pady=(0, 16))

        BotonSecundario(pie, "✏  Editar seleccionado", self._editar_seleccionado).pack(side="left", padx=(0, 8))
        BotonPeligro(pie, "🗑  Eliminar seleccionado", self._eliminar_seleccionado).pack(side="left")

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

        # Barra de búsqueda en tiempo real
        barra = tk.Frame(tab, bg=C.FONDO_PRINCIPAL)
        barra.pack(fill="x", padx=16, pady=(0, 8))

        self._socios_busqueda = tk.Entry(
            barra, font=F.CUERPO, bg=C.FONDO_WIDGET, fg=C.TEXTO_PRINCIPAL,
            insertbackground=C.ACENTO, relief="flat", bd=8
        )
        self._socios_busqueda.insert(0, "Buscar por nombre, email o ID...")
        self._socios_busqueda.config(fg=C.TEXTO_DESACTIVADO)
        self._socios_busqueda.bind("<FocusIn>",   lambda e: self._placeholder_in(self._socios_busqueda, "Buscar por nombre, email o ID..."))
        self._socios_busqueda.bind("<FocusOut>",  lambda e: self._placeholder_out(self._socios_busqueda, "Buscar por nombre, email o ID..."))
        self._socios_busqueda.bind("<KeyRelease>", lambda e: self._filtrar_socios())
        self._socios_busqueda.pack(side="left", fill="x", expand=True, padx=(0, 12))

        BotonGhost(barra, "↺  Refrescar", self._cargar_socios).pack(side="left")

        cols = [
            ("id",        "ID",          100, "w"),
            ("nombre",    "Nombre",      200, "w"),
            ("email",     "Email",       220, "w"),
            ("activos",   "Préstamos",    90, "center"),
            ("maximo",    "Límite",       70, "center"),
            ("sancion",   "Sancionado",  100, "center"),
        ]
        self._tabla_socios = TablaDatos(tab, cols, altura_filas=16)
        self._tabla_socios.pack(fill="both", expand=True, padx=16, pady=(0, 8))
        # Doble clic abre la ventana de detalle del socio
        self._tabla_socios.bind_doble_click(self._abrir_detalle_socio)

        pie = tk.Frame(tab, bg=C.FONDO_PANEL, padx=16, pady=10)
        pie.pack(fill="x", padx=16, pady=(0, 16))

        BotonSecundario(pie, "↺  Refrescar", self._cargar_socios).pack(side="left", padx=(0, 8))
        BotonSecundario(pie, "📄  Ver detalle", lambda: self._abrir_detalle_socio(self._tabla_socios.seleccion())).pack(side="left", padx=(0, 8))
        BotonPeligro(pie, "⚖  Cambiar sanción", self._cambiar_sancion_socio).pack(side="left")

        self._estado_socios = EtiquetaEstado(tab)
        self._estado_socios.pack(pady=(0, 8))

        # Guardamos todos los socios para el filtro local
        self._socios_cache = []

        return tab

    def _cargar_socios(self):
        usuarios = self._ctrl.obtener_todos_los_usuarios()
        self._socios_cache = [u for u in usuarios if isinstance(u, Socio)]
        self._renderizar_socios(self._socios_cache)

    def _filtrar_socios(self):
        """Filtra la caché local sin ir a la BD en cada tecla."""
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

        id_s = fila[0]
        nombre = fila[1]
        accion = "levantar la sanción de" if fila[5].startswith("Sí") else "sancionar a"

        if not confirmar("Cambiar sanción", f"¿Deseas {accion} {nombre}?"):
            return

        exito, msg = self._ctrl.cambiar_sancion_socio(id_s)
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
            ("id",     "ID",          100, "w"),
            ("nombre", "Nombre",      220, "w"),
            ("email",  "Email",       220, "w"),
            ("rol",    "Rol",         140, "center"),
        ]
        self._tabla_empleados = TablaDatos(tab, cols, altura_filas=16)
        self._tabla_empleados.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        pie = tk.Frame(tab, bg=C.FONDO_PANEL, padx=16, pady=10)
        pie.pack(fill="x", padx=16, pady=(0, 16))

        BotonSecundario(pie, "↺  Refrescar", self._cargar_empleados).pack(side="left", padx=(0, 8))
        BotonSecundario(pie, "✏  Cambiar rol", self._cambiar_rol).pack(side="left")

        self._estado_empleados = EtiquetaEstado(tab)
        self._estado_empleados.pack(pady=(0, 8))

        return tab

    def _cargar_empleados(self):
        usuarios = self._ctrl.obtener_todos_los_usuarios()
        empleados = [u for u in usuarios if isinstance(u, Empleado)]
        filas = []
        for e in empleados:
            filas.append((e.id_usuario, f"{e.nombre} {e.apellidos}", e.email, e.rol.value))
        self._tabla_empleados.cargar(filas)

    def _cambiar_rol(self):
        fila = self._tabla_empleados.seleccion()
        if not fila:
            self._estado_empleados.error("Selecciona un empleado primero.")
            return

        id_e = fila[0]
        if id_e == self._empleado.id_usuario:
            self._estado_empleados.error("No puedes cambiar tu propio rol.")
            return

        dialogo = DialogoSeleccion(
            self,
            titulo="Cambiar rol",
            mensaje=f"Nuevo rol para {fila[1]}:",
            opciones=ROLES_EMPLEADO
        )
        self.wait_window(dialogo)
        rol_str = dialogo.resultado

        if not rol_str:
            return

        nuevo_rol = RolEmpleado(rol_str)
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

        # Cambiar email
        tk.Label(contenido, text="Cambiar email", font=F.TITULO_PEQUEÑO,
                 bg=C.FONDO_PRINCIPAL, fg=C.TEXTO_PRINCIPAL).pack(anchor="w", pady=(0, 8))

        self._emp_nuevo_email = CampoTexto(contenido, "Nuevo email")
        self._emp_nuevo_email.pack(fill="x", pady=(0, 8))
        self._emp_estado_email = EtiquetaEstado(contenido)

        BotonSecundario(contenido, "Guardar email", self._cambiar_email).pack(anchor="w")
        self._emp_estado_email.pack(anchor="w", pady=(6, 20))

        Separador(contenido).pack(fill="x", pady=(0, 24))

        # Cambiar contraseña
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
        exito, msg = self._ctrl.cambiar_password_usuario(
            self._empleado.id_usuario, actual, nueva
        )
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
        tab_idx = self._notebook.index("current")
        # Refrescamos la pestaña activa con datos frescos de la BD
        handlers = {
            0: self._cargar_reservas,
            1: self._cargar_prestamos_activos,
        }
        if self._empleado.es_bibliotecario_o_superior():
            handlers[3] = self._cargar_catalogo
            handlers[4] = self._cargar_socios
        if self._empleado.es_admin():
            handlers[5] = self._cargar_empleados

        if tab_idx in handlers:
            handlers[tab_idx]()

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


# ==========================================
# FORMULARIO: MATERIAL (ventana auxiliar)
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
        ).pack(anchor="w", pady=(0, 16))

        # Tipo (solo en creación)
        if not self._material:
            self._tipo_combo = ComboBox(contenido, "Tipo de material", TIPOS_MATERIAL)
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
            ).pack(anchor="w", pady=(0, 10))
            tk.Label(
                contenido, text=f"Código: {self._material.codigo_id}",
                font=F.CUERPO, bg=C.FONDO_PRINCIPAL, fg=C.TEXTO_SECUNDARIO
            ).pack(anchor="w", pady=(0, 10))

        self._f_titulo  = CampoTexto(contenido, "Título")
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
            self._f_autor   = CampoTexto(self._zona_extra, "Autor")
            self._f_autor.pack(fill="x", pady=(0, 8))
            self._f_paginas = CampoNumero(self._zona_extra, "Páginas")
            self._f_paginas.pack(fill="x", pady=(0, 8))
            self._f_isbn    = CampoTexto(self._zona_extra, "ISBN")
            self._f_isbn.pack(fill="x", pady=(0, 8))

        elif tipo == "Revista":
            self._f_editorial = CampoTexto(self._zona_extra, "Editorial")
            self._f_editorial.pack(fill="x", pady=(0, 8))
            self._f_edicion   = CampoNumero(self._zona_extra, "Número de edición")
            self._f_edicion.pack(fill="x", pady=(0, 8))
            self._f_issn      = CampoTexto(self._zona_extra, "ISSN")
            self._f_issn.pack(fill="x", pady=(0, 8))

        elif tipo == "Dispositivo":
            self._f_tipo_disp  = ComboBox(self._zona_extra, "Tipo de dispositivo", TIPOS_DISP)
            self._f_tipo_disp.pack(fill="x", pady=(0, 8))
            self._f_fabricante = CampoTexto(self._zona_extra, "Fabricante")
            self._f_fabricante.pack(fill="x", pady=(0, 8))
            self._f_so         = CampoTexto(self._zona_extra, "Sistema Operativo")
            self._f_so.pack(fill="x", pady=(0, 8))
            self._f_num_serie  = CampoTexto(self._zona_extra, "Número de serie")
            self._f_num_serie.pack(fill="x", pady=(0, 8))

        elif tipo == "JuegoDeMesa":
            self._f_editorial2  = CampoTexto(self._zona_extra, "Editorial")
            self._f_editorial2.pack(fill="x", pady=(0, 8))
            self._f_min_jug     = CampoNumero(self._zona_extra, "Mín. jugadores")
            self._f_min_jug.pack(fill="x", pady=(0, 8))
            self._f_max_jug     = CampoNumero(self._zona_extra, "Máx. jugadores")
            self._f_max_jug.pack(fill="x", pady=(0, 8))

        elif tipo == "RecursoDigital":
            self._f_url           = CampoTexto(self._zona_extra, "URL de acceso")
            self._f_url.pack(fill="x", pady=(0, 8))
            self._f_licencias     = CampoNumero(self._zona_extra, "Licencias totales")
            self._f_licencias.pack(fill="x", pady=(0, 8))

    def _precargar(self, m):
        """Rellena los campos con los datos del material a editar."""
        self._f_titulo.set(m.titulo)
        if hasattr(m, "ubicacion") and m.ubicacion:
            self._f_ubicacion.set(m.ubicacion)

        if isinstance(m, Libro):
            if m.autor:    self._f_autor.set(m.autor)
            if m.paginas:  self._f_paginas.set(str(m.paginas))
            if m.isbn:     self._f_isbn.set(m.isbn)
        elif isinstance(m, Revista):
            if m.editorial:     self._f_editorial.set(m.editorial)
            if m.numero_edicion: self._f_edicion.set(str(m.numero_edicion))
            if m.issn:          self._f_issn.set(m.issn)
        elif isinstance(m, Dispositivo):
            self._f_tipo_disp.set(m.tipo_dispositivo.value)
            if m.fabricante:   self._f_fabricante.set(m.fabricante)
            if m.so:           self._f_so.set(m.so)
            if m.numero_serie: self._f_num_serie.set(m.numero_serie)
        elif isinstance(m, JuegoDeMesa):
            if m.editorial:    self._f_editorial2.set(m.editorial)
            if m.min_jugadores: self._f_min_jug.set(str(m.min_jugadores))
            if m.max_jugadores: self._f_max_jug.set(str(m.max_jugadores))
        elif isinstance(m, RecursoDigital):
            if m.url:           self._f_url.set(m.url)
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
                pags = int(self._f_paginas.get()) if self._f_paginas.get() else None
                nuevo = Libro(
                    codigo_id=codigo, titulo=titulo, ubicacion=ubic,
                    autor=self._f_autor.get().strip() or None,
                    paginas=pags,
                    isbn=self._f_isbn.get().strip() or None
                )
            elif tipo == "Revista":
                edic = int(self._f_edicion.get()) if self._f_edicion.get() else None
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
                    min_jugadores=min_j,
                    max_jugadores=max_j
                )
            elif tipo == "RecursoDigital":
                lics = int(self._f_licencias.get()) if self._f_licencias.get() else 1
                nuevo = RecursoDigital(
                    codigo_id=codigo, titulo=titulo,
                    url=self._f_url.get().strip() or None,
                    licencias_totales=lics
                )
            else:
                self._estado.error("Tipo de material no reconocido.")
                return

        except ValueError as e:
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
# FORMULARIO: EMPLEADO (ventana auxiliar)
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
        ).pack(anchor="w", pady=(0, 16))

        # El ID se muestra como información, no como campo editable
        id_preview = self._ctrl.siguiente_id_empleado()
        tk.Label(
            contenido, text=f"ID asignado automáticamente: {id_preview}",
            font=F.CUERPO, bg=C.FONDO_PRINCIPAL, fg=C.TEXTO_SECUNDARIO
        ).pack(anchor="w", pady=(0, 12))

        self._f_nombre   = CampoTexto(contenido, "Nombre")
        self._f_nombre.pack(fill="x", pady=(0, 8))
        self._f_apellidos = CampoTexto(contenido, "Apellidos")
        self._f_apellidos.pack(fill="x", pady=(0, 8))
        self._f_email    = CampoTexto(contenido, "Email")
        self._f_email.pack(fill="x", pady=(0, 8))
        self._f_pass     = CampoTexto(contenido, "Contraseña inicial", password=True)
        self._f_pass.pack(fill="x", pady=(0, 8))
        self._f_rol      = ComboBox(contenido, "Rol", ROLES_EMPLEADO)
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

        exito, msg = self._ctrl.crear_empleado(nom, ape, email, pwd, rol)
        if exito:
            if self._callback:
                self._callback()
            self.destroy()
        else:
            self._estado.error(msg)

    def _centrar(self):
        self.update_idletasks()
        ancho, alto = 420, 520
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
            ("id",      "ID Préstamo", 130, "w"),
            ("titulo",  "Material",    260, "w"),
            ("devolver","Devolver",    120, "center"),
            ("estado",  "Estado",      110, "center"),
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

    def _centrar(self):
        self.update_idletasks()
        ancho, alto = 760, 680
        x = (self.winfo_screenwidth()  - ancho) // 2
        y = (self.winfo_screenheight() - alto)  // 2
        self.geometry(f"{ancho}x{alto}+{x}+{y}")


# ==========================================
# SELECTORES DE BÚSQLÉDA (Socio / Material)
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


class SelectorMaterial(tk.Toplevel):
    """
    Ventana de selección de material con búsqueda por título.
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
        filas = []
        for m in materiales:
            filas.append((m.codigo_id, type(m).__name__, m.titulo, m.estado.value))
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
