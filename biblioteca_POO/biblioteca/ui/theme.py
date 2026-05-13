"""
theme.py

Paleta de colores, fuentes y estilos centralizados para toda la interfaz.
Cambiar aquí afecta al aspecto de toda la aplicación de una sola vez.
"""

import tkinter as tk
from tkinter import ttk


# ==========================================
# PALETA DE COLORES
# ==========================================

class Colores:
    # Fondos
    FONDO_PRINCIPAL    = "#2e2e2e"   # Fondo de ventanas principales
    FONDO_PANEL        = "#373737"   # Fondo de paneles y frames
    FONDO_WIDGET       = "#404040"   # Fondo de entradas y listas
    FONDO_HOVER        = "#4a4a4a"   # Hover sobre elementos interactivos
    FONDO_SELECCION    = "#1e3a4a"   # Fila seleccionada en tabla

    # Texto
    TEXTO_PRINCIPAL    = "#e8e8e8"   # Texto general
    TEXTO_SECUNDARIO   = "#a0a0a0"   # Labels, placeholders, info menor
    TEXTO_DESACTIVADO  = "#606060"   # Texto inactivo

    # Acento principal — amarillo dorado
    ACENTO             = "#cfa959"   # Botones primarios, bordes activos, iconos clave
    ACENTO_HOVER       = "#dfc070"   # Hover del acento
    ACENTO_DARK        = "#a07830"   # Sombra / estado presionado

    # Acento secundario — azul
    AZUL               = "#7eb9df"   # Info, enlaces, detalles secundarios
    AZUL_HOVER         = "#9fcfef"   # Hover del azul
    AZUL_DARK          = "#5a8faf"   # Estado presionado del azul

    # Estados semánticos
    EXITO              = "#6ab87a"   # Verde éxito
    ERROR              = "#e06060"   # Rojo error
    ADVERTENCIA        = "#e0a040"   # Naranja aviso
    RETRASADO          = "#d06050"   # Rojo suave para préstamos retrasados

    # Bordes
    BORDE              = "#505050"   # Borde general
    BORDE_ACTIVO       = "#cfa959"   # Borde de campo enfocado
    SEPARADOR          = "#454545"   # Líneas separadoras


# ==========================================
# FUENTES
# ==========================================

class Fuentes:
    # Tkinter no carga Google Fonts — usamos fuentes del sistema con carácter
    FAMILIA_DISPLAY    = "Georgia"         # Títulos principales
    FAMILIA_CUERPO     = "Helvetica"       # Texto general
    FAMILIA_MONO       = "Courier New"     # IDs, códigos

    TITULO_GRANDE      = (FAMILIA_DISPLAY, 22, "bold")
    TITULO_MEDIO       = (FAMILIA_DISPLAY, 15, "bold")
    TITULO_PEQUEÑO     = (FAMILIA_CUERPO,  12, "bold")
    CUERPO             = (FAMILIA_CUERPO,  11)
    CUERPO_BOLD        = (FAMILIA_CUERPO,  11, "bold")
    PEQUEÑO            = (FAMILIA_CUERPO,   9)
    MONO               = (FAMILIA_MONO,    10)
    BOTON              = (FAMILIA_CUERPO,  10, "bold")
    LABEL_CAMPO        = (FAMILIA_CUERPO,   9, "bold")


# ==========================================
# ESTILOS ttk GLOBALES
# ==========================================

def aplicar_tema(root: tk.Tk):
    """
    Configura el tema ttk global. Llamar una sola vez desde app_window.py
    antes de crear ningún widget.
    """
    style = ttk.Style(root)
    style.theme_use("clam")     # 'clam' es el más moldeable sin necesitar ttkthemes

    C = Colores
    F = Fuentes

    # --- Treeview (tablas) ---
    style.configure(
        "Treeview",
        background=C.FONDO_WIDGET,
        foreground=C.TEXTO_PRINCIPAL,
        fieldbackground=C.FONDO_WIDGET,
        rowheight=28,
        font=F.CUERPO,
        borderwidth=0,
        relief="flat"
    )
    style.configure(
        "Treeview.Heading",
        background=C.FONDO_PANEL,
        foreground=C.ACENTO,
        font=F.BOTON,
        relief="flat",
        borderwidth=0
    )
    style.map(
        "Treeview",
        background=[("selected", C.FONDO_SELECCION)],
        foreground=[("selected", C.AZUL)]
    )
    style.map(
        "Treeview.Heading",
        background=[("active", C.FONDO_HOVER)]
    )

    # --- Scrollbar ---
    style.configure(
        "Vertical.TScrollbar",
        background=C.FONDO_PANEL,
        troughcolor=C.FONDO_WIDGET,
        arrowcolor=C.ACENTO,
        borderwidth=0,
        relief="flat"
    )
    style.configure(
        "Horizontal.TScrollbar",
        background=C.FONDO_PANEL,
        troughcolor=C.FONDO_WIDGET,
        arrowcolor=C.ACENTO,
        borderwidth=0,
        relief="flat"
    )

    # --- Notebook (pestañas) ---
    style.configure(
        "TNotebook",
        background=C.FONDO_PRINCIPAL,
        borderwidth=0
    )
    style.configure(
        "TNotebook.Tab",
        background=C.FONDO_PANEL,
        foreground=C.TEXTO_SECUNDARIO,
        font=F.BOTON,
        padding=(16, 6),
        borderwidth=0
    )
    style.map(
        "TNotebook.Tab",
        background=[("selected", C.FONDO_PRINCIPAL)],
        foreground=[("selected", C.ACENTO)]
    )

    # --- Separator ---
    style.configure(
        "TSeparator",
        background=C.SEPARADOR
    )

    # --- Progressbar (por si se usa en el futuro) ---
    style.configure(
        "TProgressbar",
        troughcolor=C.FONDO_WIDGET,
        background=C.ACENTO,
        borderwidth=0
    )
