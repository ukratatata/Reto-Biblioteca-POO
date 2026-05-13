"""
main.py

Punto de entrada del sistema de biblioteca.
Ejecutar desde la carpeta biblioteca_POO/:
    python main.py
"""

import os
import sys

# Aseguramos que Python encuentra el paquete 'biblioteca' correctamente
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from biblioteca.ui.app_window import main

if __name__ == "__main__":
    main()
