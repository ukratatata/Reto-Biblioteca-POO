"""
socio_view.py

Ventana principal para socios. Dos pestañas:
  · Buscar material  — catálogo filtrable + botón de reservar
  · Mis préstamos    — historial de préstamos y reservas activas
  · Mi cuenta        — cambiar email y contraseña
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable

from biblioteca.models import Socio, MaterialFisico, RecursoDigital, EstadoMaterial
from biblioteca.ui.theme import Colores as C, Fuentes as F
from biblioteca.ui.widgets import (
    BotonPrimario, BotonSecundario, BotonGhost,
    CampoTexto, ComboBox, TablaDatos,
    EtiquetaEstado, CabeceraPanel, Separador,
    confirmar, alerta, error_dialogo
)


TIPOS_MATERIAL = ["Todos", "Libro", "Revista", "Dispositivo", "JuegoDeMesa", "RecursoDigital"]
ESTADOS_MATERIAL = ["Todos"] + [e.value for e in EstadoMaterial]


class VentanaSocio(tk.Toplevel):
    """Ventana principal del socio tras el login."""

    def __init__(self, root: tk.Tk, controlador, socio: Socio, callback_logout: Callable):
        super().__init__(root)
        self._ctrl = controlador
        self._socio = socio
        self._callback_logout = callback_logout

        self.title(f"Biblioteca · {socio.nombre} {socio.apellidos}")
        self.configure(bg=C.FONDO_PRINCIPAL)
        self.protocol("WM_DELETE_WINDOW", self._al_cerrar)
        self._maximizar()
        self._construir_ui()

    # ==========================================
    # CONSTRUCCIÓN DE LA INTERFAZ
    # ==========================================

    def _construir_ui(self):
        # ---- Barra superior ----
        self._barra_superior()

        # ---- Notebook de pestañas ----
        self._notebook = ttk.Notebook(self)
        self._notebook.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        self._tab_catalogo  = self._crear_tab_catalogo()
        self._tab_prestamos = self._crear_tab_prestamos()
        self._tab_cuenta    = self._crear_tab_cuenta()

        self._notebook.add(self._tab_catalogo,  text="  📖  Catálogo  ")
        self._notebook.add(self._tab_prestamos, text="  📋  Mis Préstamos  ")
        self._notebook.add(self._tab_cuenta,    text="  👤  Mi Cuenta  ")

        # Cargamos datos iniciales
        self._buscar_materiales()
        self._cargar_prestamos()

        # Refrescamos cuando se cambia de pestaña
        self._notebook.bind("<<NotebookTabChanged>>", self._al_cambiar_tab)

    def _barra_superior(self):
        barra = tk.Frame(self, bg=C.FONDO_PANEL, height=56)
        barra.pack(fill="x")
        barra.pack_propagate(False)

        # Franja de acento
        tk.Frame(barra, bg=C.ACENTO, width=5).pack(side="left", fill="y")

        # Logo y nombre app
        tk.Label(
            barra,
            text="📚  BIBLIOTECA",
            font=F.TITULO_PEQUEÑO,
            bg=C.FONDO_PANEL,
            fg=C.ACENTO,
            padx=16
        ).pack(side="left")

        # Info del usuario
        estado_sancion = "  ⚠ SANCIONADO" if self._socio.sancionado else ""
        tk.Label(
            barra,
            text=f"Hola, {self._socio.nombre}{estado_sancion}",
            font=F.CUERPO,
            bg=C.FONDO_PANEL,
            fg=C.ERROR if self._socio.sancionado else C.TEXTO_SECUNDARIO
        ).pack(side="right", padx=(0, 8))

        tk.Label(
            barra,
            text=f"Socio · {self._socio.id_usuario}",
            font=F.PEQUEÑO,
            bg=C.FONDO_PANEL,
            fg=C.TEXTO_DESACTIVADO
        ).pack(side="right", padx=(16, 4))

        BotonGhost(barra, "Cerrar sesión", self._logout).pack(side="right", padx=(0, 12), pady=8)

    # ==========================================
    # TAB: CATÁLOGO
    # ==========================================

    def _crear_tab_catalogo(self) -> tk.Frame:
        tab = tk.Frame(self._notebook, bg=C.FONDO_PRINCIPAL)

        # Cabecera
        cab = CabeceraPanel(tab, "Catálogo de materiales")
        cab.pack(fill="x", padx=16, pady=(16, 8))

        # Panel de filtros
        panel_filtros = tk.Frame(tab, bg=C.FONDO_PANEL, padx=16, pady=12)
        panel_filtros.pack(fill="x", padx=16, pady=(0, 12))

        # Fila 1 de filtros
        fila1 = tk.Frame(panel_filtros, bg=C.FONDO_PANEL)
        fila1.pack(fill="x", pady=(0, 8))

        self._f_titulo = CampoTexto(fila1, "Título")
        self._f_titulo.pack(side="left", fill="x", expand=True, padx=(0, 12))
        self._f_titulo._entry.bind("<KeyRelease>", lambda e: self._buscar_materiales())

        self._f_autor = CampoTexto(fila1, "Autor / Editorial / Fabricante")
        self._f_autor.pack(side="left", fill="x", expand=True, padx=(0, 12))
        self._f_autor._entry.bind("<KeyRelease>", lambda e: self._buscar_materiales())

        self._f_tipo = ComboBox(fila1, "Tipo", TIPOS_MATERIAL)
        self._f_tipo.set("Todos")
        self._f_tipo.pack(side="left", fill="x", expand=False)
        self._f_tipo._combo.bind("<<ComboboxSelected>>", lambda e: self._buscar_materiales())

        # Fila 2 de filtros
        fila2 = tk.Frame(panel_filtros, bg=C.FONDO_PANEL)
        fila2.pack(fill="x")

        self._f_ubicacion = CampoTexto(fila2, "Ubicación")
        self._f_ubicacion.pack(side="left", fill="x", expand=True, padx=(0, 12))
        self._f_ubicacion._entry.bind("<KeyRelease>", lambda e: self._buscar_materiales())

        self._solo_disponibles = tk.BooleanVar(value=False)
        tk.Checkbutton(
            fila2,
            text="Solo disponibles",
            variable=self._solo_disponibles,
            font=F.CUERPO,
            bg=C.FONDO_PANEL,
            fg=C.TEXTO_PRINCIPAL,
            selectcolor=C.FONDO_WIDGET,
            activebackground=C.FONDO_PANEL,
            activeforeground=C.ACENTO,
            cursor="hand2",
            command=self._buscar_materiales
        ).pack(side="left", padx=(0, 16))

        BotonGhost(fila2, "Limpiar filtros", self._limpiar_filtros).pack(side="left")

        # Tabla de resultados
        columnas_cat = [
            ("codigo",    "Código",     100, "w"),
            ("tipo",      "Tipo",       110, "w"),
            ("titulo",    "Título",     280, "w"),
            ("detalle",   "Detalle",    200, "w"),
            ("ubicacion", "Ubicación",  160, "w"),
            ("estado",    "Estado",     140, "center"),
        ]
        self._tabla_catalogo = TablaDatos(tab, columnas_cat, altura_filas=18)
        self._tabla_catalogo.pack(fill="both", expand=True, padx=16, pady=(0, 8))
        self._tabla_catalogo.bind_seleccion(self._al_seleccionar_material)

        # Panel inferior: detalle + botón reservar
        pie = tk.Frame(tab, bg=C.FONDO_PANEL, padx=16, pady=10)
        pie.pack(fill="x", padx=16, pady=(0, 16))

        self._lbl_seleccion = tk.Label(
            pie,
            text="Selecciona un material para ver opciones",
            font=F.CUERPO,
            bg=C.FONDO_PANEL,
            fg=C.TEXTO_SECUNDARIO
        )
        self._lbl_seleccion.pack(side="left", fill="x", expand=True)

        self._btn_reservar = BotonPrimario(pie, "📌  Reservar", self._reservar_seleccionado)
        self._btn_reservar.pack(side="right", padx=(8, 0))
        self._btn_reservar.config(state="disabled")

        self._estado_catalogo = EtiquetaEstado(tab)
        self._estado_catalogo.pack(pady=(0, 8))

        return tab

    def _buscar_materiales(self):
        titulo    = self._f_titulo.get().strip()
        texto_aux = self._f_autor.get().strip()   # buscamos en autor, editorial y fabricante
        tipo      = self._f_tipo.get()
        ubicacion = self._f_ubicacion.get().strip()
        solo_disp = self._solo_disponibles.get()

        resultados = self._ctrl.buscar_materiales(
            titulo=titulo or None,
            tipo_material=None if tipo == "Todos" else tipo,
            autor=texto_aux or None,
            editorial=texto_aux or None,
            fabricante=texto_aux or None,
            ubicacion=ubicacion or None,
            solo_disponibles=solo_disp
        )

        filas = []
        for m in resultados:
            # Construimos la columna "detalle" según el tipo
            if hasattr(m, "autor") and m.autor:
                detalle = f"Autor: {m.autor}"
            elif hasattr(m, "editorial") and m.editorial:
                detalle = f"Editorial: {m.editorial}"
            elif hasattr(m, "fabricante") and m.fabricante:
                detalle = f"Fab: {m.fabricante}"
            elif hasattr(m, "url") and m.url:
                detalle = f"URL: {m.url}"
            else:
                detalle = "—"

            ubicacion_str = getattr(m, "ubicacion", None) or "Digital"

            filas.append((
                m.codigo_id,
                type(m).__name__,
                m.titulo,
                detalle,
                ubicacion_str,
                m.estado.value
            ))

        self._tabla_catalogo.cargar(filas)
        self._btn_reservar.config(state="disabled")
        self._lbl_seleccion.config(
            text=f"{len(filas)} resultado{'s' if len(filas) != 1 else ''} encontrado{'s' if len(filas) != 1 else ''}",
            fg=C.TEXTO_SECUNDARIO
        )

    def _al_seleccionar_material(self, fila):
        if not fila:
            return

        codigo, tipo, titulo, detalle, ubicacion, estado = fila
        self._lbl_seleccion.config(
            text=f"[{codigo}] {titulo}  ·  {estado}",
            fg=C.AZUL
        )

        # Solo habilitamos reservar si el material está disponible y es físico
        puede = (
            estado == EstadoMaterial.DISPONIBLE.value and
            not self._socio.sancionado and
            self._socio.puede_prestar and
            tipo != "RecursoDigital"
        )
        self._btn_reservar.config(state="normal" if puede else "disabled")

    def _reservar_seleccionado(self):
        fila = self._tabla_catalogo.seleccion()
        if not fila:
            return

        codigo = fila[0]
        titulo = fila[2]

        if not confirmar("Confirmar reserva", f"¿Reservar '{titulo}'?\n\nTendrás 48h para recogerlo en la biblioteca."):
            return

        exito, mensaje = self._ctrl.realizar_reserva(self._socio.id_usuario, codigo)

        if exito:
            self._estado_catalogo.exito(mensaje)
            # Refrescamos el socio desde la BD para tener el cupo actualizado
            self._socio = self._ctrl.buscar_usuario(self._socio.id_usuario)
            self._buscar_materiales()
            self._cargar_prestamos()
        else:
            self._estado_catalogo.error(mensaje)

    def _limpiar_filtros(self):
        self._f_titulo.limpiar()
        self._f_autor.limpiar()
        self._f_tipo.set("Todos")
        self._f_ubicacion.limpiar()
        self._solo_disponibles.set(False)
        self._buscar_materiales()

    # ==========================================
    # TAB: MIS PRÉSTAMOS Y RESERVAS
    # ==========================================

    def _crear_tab_prestamos(self) -> tk.Frame:
        tab = tk.Frame(self._notebook, bg=C.FONDO_PRINCIPAL)

        # Cabecera fija con label de cupo que actualizamos in-place
        cab_frame = tk.Frame(tab, bg=C.FONDO_PANEL)
        cab_frame.pack(fill="x", padx=16, pady=(16, 8))

        tk.Label(
            cab_frame, text="Mis préstamos y reservas",
            font=F.TITULO_MEDIO, bg=C.FONDO_PANEL, fg=C.ACENTO
        ).pack(side="left")

        # Label de cupo: lo guardamos como atributo para actualizarlo sin recrearlo
        self._lbl_cupo = tk.Label(
            cab_frame, text="",
            font=F.CUERPO_BOLD, bg=C.FONDO_PANEL, fg=C.AZUL
        )
        self._lbl_cupo.pack(side="right")

        # Sub-notebook: préstamos / reservas
        sub_nb = ttk.Notebook(tab)
        sub_nb.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        # --- Sub-tab: Préstamos ---
        frame_prest = tk.Frame(sub_nb, bg=C.FONDO_PRINCIPAL)
        sub_nb.add(frame_prest, text="  Préstamos  ")

        cols_prest = [
            ("id",        "ID Préstamo", 120, "w"),
            ("material",  "Material",    280, "w"),
            ("prestado",  "Prestado el", 120, "center"),
            ("devolver",  "Devolver antes de", 140, "center"),
            ("estado",    "Estado",      120, "center"),
        ]
        self._tabla_prestamos = TablaDatos(frame_prest, cols_prest, altura_filas=12)
        self._tabla_prestamos.pack(fill="both", expand=True, pady=(8, 0))

        self._estado_prestamos = EtiquetaEstado(frame_prest)
        self._estado_prestamos.pack(pady=8)

        # --- Sub-tab: Reservas ---
        frame_res = tk.Frame(sub_nb, bg=C.FONDO_PRINCIPAL)
        sub_nb.add(frame_res, text="  Reservas  ")

        cols_res = [
            ("id",       "ID Reserva", 120, "w"),
            ("material", "Material",   280, "w"),
            ("limite",   "Recoger antes de", 160, "center"),
            ("estado",   "Estado",     120, "center"),
        ]
        self._tabla_reservas = TablaDatos(frame_res, cols_res, altura_filas=12)
        self._tabla_reservas.pack(fill="both", expand=True, pady=(8, 0))

        self._estado_reservas = EtiquetaEstado(frame_res)
        self._estado_reservas.pack(pady=8)

        return tab

    def _cargar_prestamos(self):
        # Préstamos
        prestamos = self._ctrl.obtener_prestamos_de_usuario(self._socio.id_usuario)
        filas_p = []
        for p in prestamos:
            p.actualizar_estado()
            tag = "retrasado" if p.estado.value == "Retrasado" else ""
            filas_p.append(((
                p.id_prestamo,
                p.material.titulo,
                p.fecha_prestamo.strftime("%d/%m/%Y"),
                p.fecha_devolucion_prevista.strftime("%d/%m/%Y"),
                p.estado.value
            ), tag))
        self._tabla_prestamos.cargar_con_tags(filas_p)

        # Reservas
        reservas = self._ctrl.obtener_reservas_de_usuario(self._socio.id_usuario)
        filas_r = []
        for r in reservas:
            tag = "expirado" if r.ha_expirado() else ""
            filas_r.append(((
                r.id_reserva,
                r.material.titulo,
                r.fecha_limite_recogida.strftime("%d/%m/%Y %H:%M"),
                r.estado.value
            ), tag))
        self._tabla_reservas.cargar_con_tags(filas_r)

        # Actualizamos el label del cupo in-place (sin destruir ni recrear nada)
        activos = self._socio.prestamos_activos
        maximo  = self._socio.max_prestamos
        self._lbl_cupo.config(
            text=f"Cupo: {activos} / {maximo}",
            fg=C.AZUL if activos < maximo else C.ERROR
        )

    # ==========================================
    # TAB: MI CUENTA
    # ==========================================

    def _crear_tab_cuenta(self) -> tk.Frame:
        tab = tk.Frame(self._notebook, bg=C.FONDO_PRINCIPAL)

        contenido = tk.Frame(tab, bg=C.FONDO_PRINCIPAL, padx=40, pady=30)
        contenido.pack(fill="both", expand=True)

        tk.Label(
            contenido,
            text="Mi cuenta",
            font=F.TITULO_MEDIO,
            bg=C.FONDO_PRINCIPAL,
            fg=C.ACENTO
        ).pack(anchor="w", pady=(0, 4))

        tk.Label(
            contenido,
            text=f"{self._socio.nombre} {self._socio.apellidos}  ·  {self._socio.id_usuario}",
            font=F.CUERPO,
            bg=C.FONDO_PRINCIPAL,
            fg=C.TEXTO_SECUNDARIO
        ).pack(anchor="w", pady=(0, 20))

        Separador(contenido).pack(fill="x", pady=(0, 24))

        # --- Cambiar email ---
        tk.Label(
            contenido, text="Cambiar email",
            font=F.TITULO_PEQUEÑO, bg=C.FONDO_PRINCIPAL, fg=C.TEXTO_PRINCIPAL
        ).pack(anchor="w", pady=(0, 8))

        self._nuevo_email = CampoTexto(contenido, "Nuevo email")
        self._nuevo_email.pack(fill="x", pady=(0, 8))

        self._estado_email = EtiquetaEstado(contenido)

        BotonSecundario(contenido, "Guardar email", self._cambiar_email).pack(anchor="w")
        self._estado_email.pack(anchor="w", pady=(6, 20))

        Separador(contenido).pack(fill="x", pady=(0, 24))

        # --- Cambiar contraseña ---
        tk.Label(
            contenido, text="Cambiar contraseña",
            font=F.TITULO_PEQUEÑO, bg=C.FONDO_PRINCIPAL, fg=C.TEXTO_PRINCIPAL
        ).pack(anchor="w", pady=(0, 8))

        self._pass_actual  = CampoTexto(contenido, "Contraseña actual",  password=True)
        self._pass_actual.pack(fill="x", pady=(0, 8))

        self._pass_nueva   = CampoTexto(contenido, "Nueva contraseña",   password=True)
        self._pass_nueva.pack(fill="x", pady=(0, 8))

        self._pass_repite  = CampoTexto(contenido, "Repetir contraseña", password=True)
        self._pass_repite.pack(fill="x", pady=(0, 8))

        self._estado_pass = EtiquetaEstado(contenido)

        BotonSecundario(contenido, "Guardar contraseña", self._cambiar_password).pack(anchor="w")
        self._estado_pass.pack(anchor="w", pady=(6, 0))

        return tab

    def _cambiar_email(self):
        nuevo = self._nuevo_email.get().strip()
        if not nuevo:
            self._estado_email.error("Introduce el nuevo email.")
            return

        exito, msg = self._ctrl.cambiar_email_usuario(self._socio.id_usuario, nuevo)
        if exito:
            self._socio = self._ctrl.buscar_usuario(self._socio.id_usuario)
            self._nuevo_email.limpiar()
            self._estado_email.exito(msg)
        else:
            self._estado_email.error(msg)

    def _cambiar_password(self):
        actual  = self._pass_actual.get()
        nueva   = self._pass_nueva.get()
        repite  = self._pass_repite.get()

        if nueva != repite:
            self._estado_pass.error("Las contraseñas nuevas no coinciden.")
            return

        if len(nueva) < 6:
            self._estado_pass.error("La contraseña debe tener al menos 6 caracteres.")
            return

        exito, msg = self._ctrl.cambiar_password_usuario(
            self._socio.id_usuario, actual, nueva
        )
        if exito:
            self._pass_actual.limpiar()
            self._pass_nueva.limpiar()
            self._pass_repite.limpiar()
            self._estado_pass.exito(msg)
        else:
            self._estado_pass.error(msg)

    # ==========================================
    # UTILIDADES
    # ==========================================

    def _al_cambiar_tab(self, event):
        tab_idx = self._notebook.index("current")
        if tab_idx == 1:
            self._cargar_prestamos()

    def _logout(self):
        self._ctrl.detener_temporizador()
        self.destroy()
        self._callback_logout()

    def _al_cerrar(self):
        self._ctrl.detener_temporizador()
        self.master.destroy()

    def _maximizar(self):
        try:
            self.state("zoomed")        # Windows
        except Exception:
            self.attributes("-zoomed", True)   # Linux
        self.update_idletasks()
