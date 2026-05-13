"""
widgets.py

Componentes reutilizables de la interfaz: botones, campos, tablas, diálogos.
Todos los widgets heredan la paleta de theme.py para mantener coherencia visual.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, List, Tuple

from biblioteca.ui.theme import Colores as C, Fuentes as F


# ==========================================
# BOTONES
# ==========================================

class BotonPrimario(tk.Button):
    """Botón amarillo dorado — acción principal de cada pantalla."""

    def __init__(self, parent, texto: str, comando: Callable = None, **kwargs):
        super().__init__(
            parent,
            text=texto,
            command=comando,
            font=F.BOTON,
            bg=C.ACENTO,
            fg=C.FONDO_PRINCIPAL,
            activebackground=C.ACENTO_HOVER,
            activeforeground=C.FONDO_PRINCIPAL,
            relief="flat",
            cursor="hand2",
            padx=18,
            pady=8,
            borderwidth=0,
            **kwargs
        )
        self.bind("<Enter>", lambda e: self.config(bg=C.ACENTO_HOVER))
        self.bind("<Leave>", lambda e: self.config(bg=C.ACENTO))


class BotonSecundario(tk.Button):
    """Botón azul — acción secundaria o informativa."""

    def __init__(self, parent, texto: str, comando: Callable = None, **kwargs):
        super().__init__(
            parent,
            text=texto,
            command=comando,
            font=F.BOTON,
            bg=C.AZUL,
            fg=C.FONDO_PRINCIPAL,
            activebackground=C.AZUL_HOVER,
            activeforeground=C.FONDO_PRINCIPAL,
            relief="flat",
            cursor="hand2",
            padx=18,
            pady=8,
            borderwidth=0,
            **kwargs
        )
        self.bind("<Enter>", lambda e: self.config(bg=C.AZUL_HOVER))
        self.bind("<Leave>", lambda e: self.config(bg=C.AZUL))


class BotonPeligro(tk.Button):
    """Botón rojo — acciones destructivas (borrar, sancionar)."""

    def __init__(self, parent, texto: str, comando: Callable = None, **kwargs):
        super().__init__(
            parent,
            text=texto,
            command=comando,
            font=F.BOTON,
            bg=C.ERROR,
            fg=C.TEXTO_PRINCIPAL,
            activebackground="#f07070",
            activeforeground=C.TEXTO_PRINCIPAL,
            relief="flat",
            cursor="hand2",
            padx=18,
            pady=8,
            borderwidth=0,
            **kwargs
        )
        self.bind("<Enter>", lambda e: self.config(bg="#f07070"))
        self.bind("<Leave>", lambda e: self.config(bg=C.ERROR))


class BotonGhost(tk.Button):
    """Botón sin relleno — acción terciaria, cancelar, volver."""

    def __init__(self, parent, texto: str, comando: Callable = None, **kwargs):
        super().__init__(
            parent,
            text=texto,
            command=comando,
            font=F.BOTON,
            bg=C.FONDO_PANEL,
            fg=C.TEXTO_SECUNDARIO,
            activebackground=C.FONDO_HOVER,
            activeforeground=C.TEXTO_PRINCIPAL,
            relief="flat",
            cursor="hand2",
            padx=18,
            pady=8,
            borderwidth=0,
            **kwargs
        )
        self.bind("<Enter>", lambda e: self.config(bg=C.FONDO_HOVER, fg=C.TEXTO_PRINCIPAL))
        self.bind("<Leave>", lambda e: self.config(bg=C.FONDO_PANEL, fg=C.TEXTO_SECUNDARIO))


# ==========================================
# CAMPOS DE TEXTO
# ==========================================

class CampoTexto(tk.Frame):
    """
    Campo de entrada con label flotante encima y borde que cambia al enfocar.
    Uso: campo.get() para leer el valor, campo.set("texto") para escribirlo.
    """

    def __init__(self, parent, label: str, password: bool = False, **kwargs):
        super().__init__(parent, bg=C.FONDO_PANEL, **kwargs)

        tk.Label(
            self,
            text=label.upper(),
            font=F.LABEL_CAMPO,
            bg=C.FONDO_PANEL,
            fg=C.ACENTO
        ).pack(anchor="w", pady=(0, 3))

        self._borde = tk.Frame(self, bg=C.BORDE, padx=1, pady=1)
        self._borde.pack(fill="x")

        self._entry = tk.Entry(
            self._borde,
            font=F.CUERPO,
            bg=C.FONDO_WIDGET,
            fg=C.TEXTO_PRINCIPAL,
            insertbackground=C.ACENTO,     # cursor de escritura en color acento
            relief="flat",
            show="•" if password else "",
            bd=6
        )
        self._entry.pack(fill="x")

        # El borde se ilumina al enfocar
        self._entry.bind("<FocusIn>",  lambda e: self._borde.config(bg=C.BORDE_ACTIVO))
        self._entry.bind("<FocusOut>", lambda e: self._borde.config(bg=C.BORDE))

    def get(self) -> str:
        return self._entry.get()

    def set(self, valor: str):
        self._entry.delete(0, tk.END)
        self._entry.insert(0, valor)

    def limpiar(self):
        self._entry.delete(0, tk.END)

    def focus(self):
        self._entry.focus()


class CampoNumero(CampoTexto):
    """Campo de texto que solo acepta dígitos."""

    def __init__(self, parent, label: str, **kwargs):
        super().__init__(parent, label, **kwargs)
        validar = self._entry.register(lambda v: v.isdigit() or v == "")
        self._entry.config(validate="key", validatecommand=(validar, "%P"))


class ComboBox(tk.Frame):
    """Selector desplegable estilizado."""

    def __init__(self, parent, label: str, opciones: List[str], **kwargs):
        super().__init__(parent, bg=C.FONDO_PANEL, **kwargs)

        tk.Label(
            self,
            text=label.upper(),
            font=F.LABEL_CAMPO,
            bg=C.FONDO_PANEL,
            fg=C.ACENTO
        ).pack(anchor="w", pady=(0, 3))

        self._var = tk.StringVar()
        self._combo = ttk.Combobox(
            self,
            textvariable=self._var,
            values=opciones,
            state="readonly",
            font=F.CUERPO
        )
        # Estilo inline porque ttk.Combobox no toma bg/fg directamente
        self._combo.configure(style="Dark.TCombobox")
        self._combo.pack(fill="x")

        # Aplicamos estilo al combobox
        style = ttk.Style()
        style.configure(
            "Dark.TCombobox",
            fieldbackground=C.FONDO_WIDGET,
            background=C.FONDO_WIDGET,
            foreground=C.TEXTO_PRINCIPAL,
            selectbackground=C.FONDO_SELECCION,
            selectforeground=C.AZUL,
            arrowcolor=C.ACENTO,
            borderwidth=1,
            relief="flat"
        )
        # Sin esto, el fondo del dropdown antes de seleccionar sale blanco en Windows
        style.map(
            "Dark.TCombobox",
            fieldbackground=[("readonly", C.FONDO_WIDGET)],
            foreground=[("readonly", C.TEXTO_PRINCIPAL)],
            background=[("readonly", C.FONDO_WIDGET), ("active", C.FONDO_HOVER)],
            selectbackground=[("readonly", C.FONDO_SELECCION)],
            selectforeground=[("readonly", C.AZUL)]
        )

    def get(self) -> str:
        return self._var.get()

    def set(self, valor: str):
        self._var.set(valor)


# ==========================================
# TABLA DE DATOS
# ==========================================

class TablaDatos(tk.Frame):
    """
    Treeview con scrollbars integradas y zebra-striping.
    Columnas: lista de (id_col, texto_header, ancho_px, anchor)
    """

    def __init__(
        self,
        parent,
        columnas: List[Tuple[str, str, int, str]],
        altura_filas: int = 15,
        **kwargs
    ):
        super().__init__(parent, bg=C.FONDO_PANEL, **kwargs)

        # Scrollbar vertical
        scroll_v = ttk.Scrollbar(self, orient="vertical")
        scroll_v.pack(side="right", fill="y")

        # Scrollbar horizontal
        scroll_h = ttk.Scrollbar(self, orient="horizontal")
        scroll_h.pack(side="bottom", fill="x")

        ids_col = [c[0] for c in columnas]
        self._tree = ttk.Treeview(
            self,
            columns=ids_col,
            show="headings",
            height=altura_filas,
            yscrollcommand=scroll_v.set,
            xscrollcommand=scroll_h.set
        )

        scroll_v.config(command=self._tree.yview)
        scroll_h.config(command=self._tree.xview)

        # Configuramos cabeceras y anchos — con click para ordenar
        for col_id, col_texto, col_ancho, col_anchor in columnas:
            self._tree.heading(
                col_id,
                text=col_texto,
                anchor="w",
                command=lambda c=col_id: self._ordenar_por(c)
            )
            self._tree.column(col_id, width=col_ancho, anchor=col_anchor, minwidth=60)

        # Rastreamos la columna y dirección del último orden aplicado
        self._orden_col = None
        self._orden_asc = True

        # Zebra striping: filas alternas con fondo ligeramente diferente
        self._tree.tag_configure("par",      background=C.FONDO_WIDGET)
        self._tree.tag_configure("impar",    background="#3a3a3a")
        self._tree.tag_configure("retrasado", background="#4a2828", foreground=C.RETRASADO)
        self._tree.tag_configure("expirado",  background="#3a3020", foreground=C.ADVERTENCIA)
        # Préstamos devueltos: texto atenuado para distinguirlos visualmente de los activos
        self._tree.tag_configure("devuelto",  background="#323232", foreground=C.TEXTO_DESACTIVADO)

        self._tree.pack(side="left", fill="both", expand=True)

    def _ordenar_por(self, col_id: str):
        """
        Ordena las filas de la tabla por la columna pulsada.
        Alterna ascendente/descendente si se pulsa la misma columna dos veces.
        Muestra una flecha ↑↓ en la cabecera activa.
        """
        # Intentamos ordenar numéricamente primero; si falla, como texto
        datos = [
            (self._tree.set(item, col_id), item)
            for item in self._tree.get_children("")
        ]

        def clave(par):
            val = par[0]
            try:
                return (0, float(val.replace("/", "").replace("-", "")))
            except ValueError:
                return (1, val.lower())

        # Alternamos dirección si se repite la misma columna
        if self._orden_col == col_id:
            self._orden_asc = not self._orden_asc
        else:
            self._orden_asc = True
            self._orden_col = col_id

        datos.sort(key=clave, reverse=not self._orden_asc)

        for posicion, (_, item) in enumerate(datos):
            self._tree.move(item, "", posicion)

        # Actualizamos el zebra-striping tras reordenar
        for i, item in enumerate(self._tree.get_children("")):
            tags_actuales = list(self._tree.item(item, "tags"))
            # Quitamos tags de zebra anteriores y ponemos el nuevo
            tags_sin_zebra = [t for t in tags_actuales if t not in ("par", "impar")]
            nuevo_tag = "par" if i % 2 == 0 else "impar"
            # Conservamos tags semánticos (retrasado, expirado) si los hay
            if tags_sin_zebra:
                self._tree.item(item, tags=tags_sin_zebra)
            else:
                self._tree.item(item, tags=(nuevo_tag,))

        # Marcamos la cabecera activa con una flecha
        flecha = " ↑" if self._orden_asc else " ↓"
        for col in self._tree["columns"]:
            texto_actual = self._tree.heading(col, "text")
            # Quitamos flecha previa si la había
            texto_limpio = texto_actual.rstrip(" ↑↓")
            self._tree.heading(col, text=texto_limpio + (flecha if col == col_id else ""))

    def cargar(self, filas: List[tuple]):
        """Limpia la tabla y carga una nueva lista de tuplas de datos."""
        self._tree.delete(*self._tree.get_children())

        # Ordenamos por la primera columna (ID) por defecto al cargar
        filas_ordenadas = sorted(filas, key=lambda f: str(f[0]).upper())

        for i, fila in enumerate(filas):
            tag = "par" if i % 2 == 0 else "impar"
            self._tree.insert("", "end", values=fila, tags=(tag,))

    def cargar_con_tags(self, filas: List[Tuple[tuple, str]]):
        """
        Versión avanzada: cada elemento es (tupla_datos, nombre_tag).
        Permite colorear filas individualmente (ej: retrasado, expirado).
        """
        self._tree.delete(*self._tree.get_children())

        # Ordenamos por la primera columna (ID) por defecto al cargar
        filas_ordenadas = sorted(filas, key=lambda f: str(f[0][0]).upper())
        
        for i, (datos, tag_extra) in enumerate(filas):
            tag_zebra = "par" if i % 2 == 0 else "impar"
            # El tag_extra sobreescribe el color zebra si es relevante
            tag_final = tag_extra if tag_extra else tag_zebra
            self._tree.insert("", "end", values=datos, tags=(tag_final,))

    def seleccion(self):
        """Devuelve los valores de la fila seleccionada o None si no hay ninguna."""
        sel = self._tree.selection()
        if not sel:
            return None
        return self._tree.item(sel[0], "values")

    def bind_doble_click(self, callback: Callable):
        """Registra un callback para cuando el usuario hace doble clic en una fila."""
        self._tree.bind("<Double-1>", lambda e: callback(self.seleccion()))

    def bind_seleccion(self, callback: Callable):
        """Registra un callback para cuando cambia la fila seleccionada."""
        self._tree.bind("<<TreeviewSelect>>", lambda e: callback(self.seleccion()))


# ==========================================
# PANEL DE BÚSQUEDA
# ==========================================

class PanelBusqueda(tk.Frame):
    """
    Barra de búsqueda rápida con campo de texto y botón integrado.
    Al pulsar Enter o el botón se dispara el callback con el texto introducido.
    """

    def __init__(self, parent, placeholder: str, callback: Callable, **kwargs):
        super().__init__(parent, bg=C.FONDO_PANEL, **kwargs)

        self._callback = callback

        # Borde contenedor que se ilumina al enfocar
        contenedor = tk.Frame(self, bg=C.BORDE, padx=1, pady=1)
        contenedor.pack(side="left", fill="x", expand=True)

        self._entry = tk.Entry(
            contenedor,
            font=F.CUERPO,
            bg=C.FONDO_WIDGET,
            fg=C.TEXTO_PRINCIPAL,
            insertbackground=C.ACENTO,
            relief="flat",
            bd=8
        )
        self._entry.insert(0, placeholder)
        self._entry.config(fg=C.TEXTO_DESACTIVADO)
        self._entry.pack(fill="x")

        # Comportamiento de placeholder
        self._entry.bind("<FocusIn>",  self._al_enfocar)
        self._entry.bind("<FocusOut>", self._al_desenfocar)
        self._entry.bind("<Return>",   lambda e: self._buscar())
        self._entry.bind("<KeyRelease>", lambda e: self._buscar())   # búsqueda en tiempo real

        self._entry.bind("<FocusIn>",  lambda e: contenedor.config(bg=C.BORDE_ACTIVO), add="+")
        self._entry.bind("<FocusOut>", lambda e: contenedor.config(bg=C.BORDE), add="+")

        self._placeholder = placeholder

        BotonPrimario(self, "Buscar", self._buscar).pack(side="left", padx=(8, 0))

    def _al_enfocar(self, event):
        if self._entry.get() == self._placeholder:
            self._entry.delete(0, tk.END)
            self._entry.config(fg=C.TEXTO_PRINCIPAL)

    def _al_desenfocar(self, event):
        if not self._entry.get():
            self._entry.insert(0, self._placeholder)
            self._entry.config(fg=C.TEXTO_DESACTIVADO)

    def _buscar(self):
        texto = self._entry.get()
        if texto == self._placeholder:
            texto = ""
        self._callback(texto)

    def get(self) -> str:
        v = self._entry.get()
        return "" if v == self._placeholder else v

    def limpiar(self):
        self._entry.delete(0, tk.END)
        self._entry.insert(0, self._placeholder)
        self._entry.config(fg=C.TEXTO_DESACTIVADO)


# ==========================================
# ETIQUETA DE ESTADO
# ==========================================

class EtiquetaEstado(tk.Label):
    """
    Muestra mensajes de éxito, error o advertencia con color automático.
    Desaparece solo después de N segundos si se indica.
    El fondo se hereda del padre automáticamente para no romper el layout.
    """

    def __init__(self, parent, **kwargs):
        # Intentamos leer el fondo del padre para que el label encaje sin cuadrado visible
        try:
            bg_padre = parent.cget("bg")
        except Exception:
            bg_padre = C.FONDO_PANEL

        super().__init__(
            parent,
            text="",
            font=F.PEQUEÑO,
            bg=bg_padre,
            fg=C.TEXTO_SECUNDARIO,
            **kwargs
        )
        self._job = None

    def exito(self, mensaje: str, auto_limpiar: int = 4000):
        self._mostrar(mensaje, C.EXITO, auto_limpiar)

    def error(self, mensaje: str, auto_limpiar: int = 5000):
        self._mostrar(mensaje, C.ERROR, auto_limpiar)

    def info(self, mensaje: str, auto_limpiar: int = 0):
        self._mostrar(mensaje, C.AZUL, auto_limpiar)

    def advertencia(self, mensaje: str, auto_limpiar: int = 5000):
        self._mostrar(mensaje, C.ADVERTENCIA, auto_limpiar)

    def _mostrar(self, mensaje: str, color: str, auto_limpiar: int):
        if self._job:
            self.after_cancel(self._job)
            self._job = None

        self.config(text=mensaje, fg=color)

        if auto_limpiar > 0:
            self._job = self.after(auto_limpiar, self.limpiar)

    def limpiar(self):
        self.config(text="", fg=C.TEXTO_SECUNDARIO)
        self._job = None


# ==========================================
# SEPARADOR DECORATIVO
# ==========================================

class Separador(tk.Frame):
    """Línea horizontal decorativa con padding vertical."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=C.SEPARADOR, height=1, **kwargs)


# ==========================================
# DIÁLOGOS AUXILIARES
# ==========================================

def confirmar(titulo: str, mensaje: str) -> bool:
    """Diálogo de confirmación estándar. Devuelve True si el usuario confirma."""
    return messagebox.askyesno(titulo, mensaje)


def alerta(titulo: str, mensaje: str):
    """Diálogo de aviso informativo."""
    messagebox.showinfo(titulo, mensaje)


def error_dialogo(titulo: str, mensaje: str):
    """Diálogo de error."""
    messagebox.showerror(titulo, mensaje)


# ==========================================
# PANEL DE CABECERA (HEADER)
# ==========================================

class CabeceraPanel(tk.Frame):
    """
    Cabecera interior de cada panel: título a la izquierda,
    botones de acción opcionales a la derecha.
    """

    def __init__(self, parent, titulo: str, **kwargs):
        super().__init__(parent, bg=C.FONDO_PANEL, **kwargs)

        tk.Label(
            self,
            text=titulo,
            font=F.TITULO_MEDIO,
            bg=C.FONDO_PANEL,
            fg=C.ACENTO
        ).pack(side="left")

        # Los botones se añaden llamando a agregar_boton()
        self._zona_botones = tk.Frame(self, bg=C.FONDO_PANEL)
        self._zona_botones.pack(side="right")

    def agregar_boton(self, texto: str, comando: Callable, tipo: str = "primario"):
        """Añade un botón a la derecha de la cabecera. tipo: primario|secundario|peligro|ghost"""
        clases = {
            "primario":   BotonPrimario,
            "secundario": BotonSecundario,
            "peligro":    BotonPeligro,
            "ghost":      BotonGhost
        }
        cls = clases.get(tipo, BotonGhost)
        cls(self._zona_botones, texto, comando).pack(side="left", padx=(6, 0))
