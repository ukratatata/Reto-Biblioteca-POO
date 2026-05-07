"""
models.py

Este archivo contiene las clases principales del dominio de biblioteca.

Dominio significa "la parte del mundo real que estamos modelando".
En nuestro caso:
- materiales;
- libros;
- recursos digitales;
- usuarios;
- socios;
- préstamos.

IMPORTANTE:
Este archivo NO sabe nada de terminal.
Este archivo NO sabe nada de SQLite.

Solo define objetos y comportamientos propios del problema.
"""


class Material:
    """
    Clase base para cualquier material de la biblioteca.

    Un Material tiene datos comunes:
    - codigo
    - titulo
    - autor
    - disponible
    """

    def __init__(self, codigo, titulo, autor, disponible=True):
        """
        Constructor de Material.

        disponible será True si el material se puede prestar.
        disponible será False si el material ya está prestado.
        """

        self.codigo = codigo
        self.titulo = titulo
        self.autor = autor
        self.disponible = bool(disponible)

    def prestar(self):
        """
        Intenta prestar el material.

        Devuelve True si se ha podido prestar.
        Devuelve False si ya estaba prestado.
        """

        if self.disponible:
            self.disponible = False
            return True

        return False

    def devolver(self):
        """
        Marca el material como disponible.
        """

        self.disponible = True

    def descripcion_corta(self):
        """
        Devuelve un texto sencillo para mostrar por pantalla.
        """

        if self.disponible:
            estado = "disponible"
        else:
            estado = "prestado"

        return f"[{self.codigo}] {self.titulo} - {self.autor} ({estado})"


class Libro(Material):
    """
    Clase que representa un libro.

    Hereda de Material porque un libro ES un material.
    """

    def __init__(self, codigo, titulo, autor, paginas, disponible=True):
        """
        Constructor de Libro.

        Usa super() para reutilizar el constructor de Material.
        """

        super().__init__(codigo, titulo, autor, disponible)
        self.paginas = int(paginas)

    def descripcion_corta(self):
        """
        TODO 1

        Completa este método para que devuelva una descripción de un libro.

        Ejemplo esperado:

        [L001] El Quijote - Miguel de Cervantes · Libro de 863 páginas (disponible)
        """
        if self.disponible:
            estado = "disponible"
        else:
            estado = "prestado"

        return f"[{self.codigo}] {self.titulo}  - {self.autor} · Libro de {self.paginas} páginas ({estado})"


class RecursoDigital(Material):
    """
    Clase que representa un recurso digital.

    Hereda de Material porque un recurso digital ES un material.
    """

    def __init__(self, codigo, titulo, autor, url, disponible=True):
        """
        Constructor de RecursoDigital.
        """

        super().__init__(codigo, titulo, autor, disponible)
        self.url = url

    def descripcion_corta(self):
        """
        Devuelve una descripción de un recurso digital.
        """

        if self.disponible:
            estado = "disponible"
        else:
            estado = "prestado"

        return f"[{self.codigo}] {self.titulo} - {self.autor} · Recurso digital ({estado})"


class Usuario:
    """
    Clase base para usuarios del sistema.
    """

    def __init__(self, identificador, nombre):
        """
        Constructor de Usuario.
        """

        self.identificador = identificador
        self.nombre = nombre

    def descripcion_corta(self):
        """
        Devuelve una descripción sencilla.
        """

        return f"[{self.identificador}] {self.nombre}"


class Socio(Usuario):
    """
    Clase que representa un socio de la biblioteca.

    Hereda de Usuario porque un socio ES un usuario.
    """

    def __init__(self, identificador, nombre, sancionado=False, max_prestamos=3):
        """
        Constructor de Socio.
        """

        super().__init__(identificador, nombre)

        self.sancionado = bool(sancionado)
        self.max_prestamos = int(max_prestamos)

    def puede_prestar(self, numero_prestamos_activos):
        """
        TODO 2

        Completa este método.

        Reglas:
        - Si el socio está sancionado, devuelve False.
        - Si numero_prestamos_activos es mayor o igual que max_prestamos, devuelve False.
        - En caso contrario, devuelve True.
        """

        raise NotImplementedError("Completa Socio.puede_prestar()")

    def descripcion_corta(self):
        """
        Devuelve una descripción del socio.
        """

        if self.sancionado:
            estado = "sancionado"
        else:
            estado = "activo"

        return f"[{self.identificador}] {self.nombre} · Socio {estado}"


class Prestamo:
    """
    Clase que representa un préstamo.

    Esta clase muestra una asociación:
    - tiene un socio;
    - tiene un material.

    No hereda de Socio ni de Material.
    """

    def __init__(self, id_prestamo, socio, material, fecha_prestamo, fecha_devolucion=None):
        """
        Constructor de Prestamo.
        """

        self.id_prestamo = id_prestamo
        self.socio = socio
        self.material = material
        self.fecha_prestamo = fecha_prestamo
        self.fecha_devolucion = fecha_devolucion

    def esta_activo(self):
        """
        Devuelve True si el préstamo sigue activo.
        """

        return self.fecha_devolucion is None

    def resumen(self):
        """
        Devuelve una frase resumen.
        """

        if self.esta_activo():
            estado = "activo"
        else:
            estado = f"devuelto el {self.fecha_devolucion}"

        return f"Préstamo {self.id_prestamo}: {self.socio.nombre} tiene '{self.material.titulo}' ({estado})"
