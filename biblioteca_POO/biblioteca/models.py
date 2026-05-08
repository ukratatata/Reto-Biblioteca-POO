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


from abc import ABC, abstractmethod
from enum import Enum

# 1. Definición de la Máquina de Estados (Enumerador): en vez de usar strings sueltos, definimos un Enum para los estados posibles de un material.
class EstadoMaterial(Enum):
    DISPONIBLE = "Disponible"                       # El material está en la biblioteca y se puede prestar
    PENDIENTE_RECOGIDA = "Pendiente de Recogida"    # El usuario tiene 2 días para venir a por él
    PRESTADO = "Prestado"                           # El usuario lo tiene en su casa (15 días...)
    NO_DISPONIBLE = "No Disponible"                # Extra: Para materiales que no se pueden prestar (mantenimiento, extravio, retiro...)


class TipoDispositivo(Enum):
    ORDENADOR = "Ordenador"
    TABLET = "Tablet"
    E_READER = "E-Reader"
    CALCULADORA = "Calculadora"
    OTROS = "Otros"

# 2. Clase Abstracta Base (El Contrato)
class Material(ABC):
    """
    Clase abstracta pura que define la estructura base de cualquier 
    elemento prestable en la biblioteca. No se puede instanciar directamente.
    """
    
    def __init__(self, codigo_id: str, titulo: str, estado: EstadoMaterial = EstadoMaterial.DISPONIBLE):
        # Atributos protegidos (Encapsulación básica)
        self._codigo_id = codigo_id
        self._titulo = titulo
        self._estado = estado # Estado inicial por defecto: Disponible

    # -- Getters básicos para acceder a la información de forma segura --
    @property
    def codigo_id(self) -> str:
        return self._codigo_id

    @property
    def titulo(self) -> str:
        return self._titulo
        
    @property
    def estado(self) -> EstadoMaterial:
        return self._estado

    # -- MÉTODOS CONCRETOS (Todos heredan) --

    def bloquear(self) -> bool:
        """
        Cambia el estado a NO_DISPONIBLE, impidiendo cualquier préstamo.
        Útil para mantenimiento o extravío.
        """
        if self._estado != EstadoMaterial.NO_DISPONIBLE:
            self._estado = EstadoMaterial.NO_DISPONIBLE
            return True
        return False
    
    # -- MÉTODOS ABSTRACTOS (El Polimorfismo) --
    
    @abstractmethod
    def prestar(self) -> bool:
        """
        Intenta prestar el material a un socio.
        OBLIGATORIO: Cada subclase debe implementar su propia lógica.
        (Ej. Físico = cambiar estado; Digital = restar licencia)
        """
        pass

    @abstractmethod
    def devolver(self) -> bool:
        """
        Procesa la devolución del material.
        OBLIGATORIO: Cada subclase debe implementar su propia lógica.
        """
        pass

    @abstractmethod
    def descripcion_corta(self) -> str:
        """
        Devuelve un string formateado con los datos del material.
        OBLIGATORIO: Cada subclase debe definir cómo se muestra por consola.
        """
        pass
     

class MaterialFisico(Material):
    """Clase intermedia para todo lo que ocupa espacio en la biblioteca."""
    def __init__(self, codigo_id: str, titulo: str, ubicacion: str = None):
        super().__init__(codigo_id, titulo)
        self._ubicacion = ubicacion  # Ej: "Pasillo 4, Estante B"

    @property   # Por ver como hacer para cuando este pendiente de recogida, para que el bibliotecario 
    def ubicacion(self) -> str: # pueda ver ubicacion pero no el usuario que veria "recoger en mostrador".     
        return self._ubicacion
    
    # Implementamos la lógica común de préstamo físico para no repetirla
    def reservar_recogida(self) -> bool:
        if self._estado == EstadoMaterial.DISPONIBLE:
            self._estado = EstadoMaterial.PENDIENTE_RECOGIDA
            return True
        return False

    def prestar(self) -> bool:
        if self._estado == EstadoMaterial.DISPONIBLE:
            self._estado = EstadoMaterial.PRESTADO
            return True
        elif self._estado == EstadoMaterial.PENDIENTE_RECOGIDA:
            self._estado = EstadoMaterial.PRESTADO
            return True
        return False

    def devolver(self) -> bool:
        if self._estado == EstadoMaterial.PRESTADO:
            self._estado = EstadoMaterial.DISPONIBLE
            return True
        elif self._estado == EstadoMaterial.PENDIENTE_RECOGIDA:
            self._estado = EstadoMaterial.DISPONIBLE
            return True
        return False


# 4. Clases Concretas Nivel 3 (Las que realmente se instancian)

class Libro(MaterialFisico):
    def __init__(self, 
                 codigo_id: str, 
                 titulo: str, 
                 ubicacion: str, 
                 autor: str = None, 
                 paginas: int = None,  
                 isbn = None):
        super().__init__(codigo_id, titulo, ubicacion)
        self._autor = autor
        self._paginas = paginas
        self._isbn = isbn

    @property
    def isbn(self):
        return self._isbn
    
    @property
    def autor(self):
        return self._autor
    
    @property
    def paginas(self):
        return self._paginas

    def descripcion_corta(self) -> str:
        autor_str = self._autor if self._autor else "desconocido"
        paginas_str = f"{self._paginas}" if self._paginas else "desconocido"
        isbn_str = self._isbn if self._isbn else "no disponible"
        return (
            f"[{self.codigo_id}] Libro: '{self.titulo}' - Autor: {autor_str} - Pags: {paginas_str}"
            f"- ISBN: {isbn_str} - Estado: {self.estado.value}"
        )

class Dispositivo(MaterialFisico):  # Para ordenadores, tablets, e-readers, calculadoras y demás dispositivos tecnológicos
    def __init__(self, 
                 codigo_id: str, 
                 titulo: str, 
                 ubicacion: str, 
                 tipo_dispositivo: TipoDispositivo, 
                 fabricante: str = None, 
                 so: str = None, 
                 numero_serie: str = None):
        super().__init__(codigo_id, titulo, ubicacion)
        self._tipo_dispositivo = tipo_dispositivo
        self._fabricante = fabricante
        self._so = so  # Sistema Operativo
        self._numero_serie = numero_serie

    @property
    def fabricante(self):
        return self._fabricante

    @property
    def so(self):
        return self._so

    @property
    def tipo_dispositivo(self):
        return self._tipo_dispositivo
    
    @property
    def numero_serie(self):
        return self._numero_serie

    def descripcion_corta(self) -> str:
        fabricante_str = self._fabricante if self._fabricante else "desconocido"
        so_str = self._so if self._so else "desconocido"
        return (
            f"[{self.codigo_id}] {self.tipo_dispositivo.value}: {self.titulo} ",
            f"- Fabricante: {fabricante_str} - SO: ({so_str}) - Estado: {self.estado.value}"
        )


class JuegoDeMesa(MaterialFisico):  # Para juegos de mesa, rol, cartas, etc. que se prestan físicamente pero no son libros ni dispositivos tecnológicos
    def __init__(self, codigo_id: str, 
                 titulo: str, 
                 ubicacion: str, 
                 editorial: str = None, 
                 min_jugadores: int = None, 
                 max_jugadores: int = None): # Estaria bien tipear a int aunque se pueda none?
        
        super().__init__(codigo_id, titulo, ubicacion)
        self._editorial = editorial
        self._min_jugadores = min_jugadores
        self._max_jugadores = max_jugadores

    @property
    def editorial(self):
        return self._editorial 
    
    @property
    def min_jugadores(self):
        return self._min_jugadores 
    
    @property
    def max_jugadores(self):
        return self._max_jugadores 
    
    def descripcion_corta(self) -> str:
        editorial_str = self._editorial if self._editorial else "Editorial desconocida"
        jugadores_str = (
            f"{self._min_jugadores}-{self._max_jugadores}" 
            if self._min_jugadores and self._max_jugadores 
            else "deconocido"
        )
        return (
            f"[{self.codigo_id}] Juego: '{self.titulo}', de {editorial_str} "
            f"- Jugadores: {jugadores_str}) - Estado: {self.estado.value}"
        )


class RecursoDigital(Material):
    """Hereda directamente de Material, porque no tiene ubicación física."""
    def __init__(self,
                 codigo_id: str,
                 titulo: str,
                 url: str,
                 licencias_totales: int):
        super().__init__(codigo_id, titulo)
        self._url = url
        self._licencias_totales = licencias_totales
        self._licencias_disponibles = licencias_totales

    @property
    def url(self):
        return self._url   

    @property
    def licencias_totales(self):
        return self._licencias_totales

    @property
    def licencias_disponibles(self):
        return self._licencias_disponibles

    # POLIMORFISMO: El préstamo digital funciona restando licencias
    def prestar(self) -> bool:
        if self._licencias_disponibles > 0: # Si hay licencias disponibles, se puede prestar
            self._licencias_disponibles -= 1
            if self._licencias_disponibles == 0:
                self._estado = EstadoMaterial.PRESTADO
            return True
        return False

    def devolver(self) -> bool:
        if self._licencias_disponibles < self._licencias_totales:
            self._licencias_disponibles += 1
            self._estado = EstadoMaterial.DISPONIBLE
            return True
        return False

    def añadir_licencias(self, cantidad: int) -> bool:
        if cantidad > 0:
            self._licencias_totales += cantidad
            self._licencias_disponibles += cantidad
            self._estado = EstadoMaterial.DISPONIBLE
            return True
        return False
    
    def retirar_licencias(self, cantidad: int) -> bool:
        if 0 < cantidad <= self._licencias_disponibles:
            self._licencias_totales -= cantidad
            self._licencias_disponibles -= cantidad
            if self._licencias_totales == 0:
                self._estado = EstadoMaterial.NO_DISPONIBLE
            if self._licencias_disponibles == 0:
                self._estado = EstadoMaterial.PRESTADO
            return True     # Plantear la posibilidad de retirar licencias aunque no estén disponibles (hacer que el usuario pierda el acceso a ese recurso siendo notificado del motivo)
        return False

    def descripcion_corta(self) -> str:
        return (
            f"[{self.codigo_id}] Digital: '{self.titulo}' - "
                f"Licencias libres: {self._licencias_disponibles}/{self._licencias_totales}"
        )


class Usuario:

    def __init__(self, id, nombre, apellido):
        self.id = id
        self.nombre = nombre
        self.apellido = apellido

    def datos_usuario(self):
        return f"[{self.id}] {self.nombre} {self.apellido}"
    
class Socio(Usuario):

    def __init__(self, id, nombre, apellido, sancionado=False, max_prestamos=3):

        super().__init__(id, nombre, apellido)

        self.sancionado = bool(sancionado)
        self.max_prestamos = int(max_prestamos)

    def puede_prestar(self, numero_prestamos_activos):

        if self.sancionado:
            estado = "sancionado"
        else:
            estado = "activo" 

        if self.sancionado:
            return False
        if numero_prestamos_activos >= self.max_prestamos:
            return False
            
        return True
        
        return f"[{self.id} {self.nombre} {self.apellido} - Socio {(estado)}]"
        
    def descripcion_corta(self):

        if self.sancionado:
            estado = "sancionado"
        else:
            estado = "activo"

        return f"[{self.id}] {self.nombre} {self.apellido} · Socio {estado}"


class Bibliotecario(Usuario):

    def __init__(self, id, nombre, apellido, sancionado=False, max_prestamos=3):

        super().__init__(id, nombre, apellido)

        self.sancionado = bool(sancionado)
        self.max_prestamos = int(max_prestamos)

    def puede_prestar(self, numero_prestamos_activos):

        if self.sancionado:
            estado = "sancionado"
        else:
            estado = "activo" 

        if self.sancionado:
            return False
        if numero_prestamos_activos >= self.max_prestamos:
            return False
            
        return True
        
        return f"[{self.id} {self.nombre} {self.apellido} - Socio {(estado)}]"
        
    def descripcion_corta(self):

        if self.sancionado:
            estado = "sancionado"
        else:
            estado = "activo"

        return f"[{self.id}] {self.nombre} {self.apellido} · Socio {estado}"
    
    def añadir_libro(self, biblioteca, libro):

        biblioteca.catalogo.append(libro)

        return f"Libro '{libro.titulo}' añadido."
    
    def quitar_libro(self, biblioteca, codigo):

        for libro in biblioteca.catalogo:
            if libro.codigo == codigo:
                biblioteca.catalogo.remove(libro)
                return f"Libro {codigo} eliminado."
            
        return "Libro no encontrado."










# libro1 = Libro("L001", "El Quijote", "Pasillo 4, Estante B", "Miguel de Cervantes", 863, "978-3-16-148410-0")
# dispositivo1 = Dispositivo("D001", "iPad Pro", "Mostrador Principal", TipoDispositivo.TABLET, fabricante="Apple", so="iOS")
# juego1 = JuegoDeMesa("J001", "Catan", "Pasillo 2, Estante A", "Devir", 3, 4)
# juego2 = JuegoDeMesa("J001", "Catan", "Pasillo 2, Estante A", "Devir", 4)
# juego3 = JuegoDeMesa("J001", "Catan", "Pasillo 2, Estante A", "Devir", max_jugadores = 3)
# recurso1 = RecursoDigital("R001", "Guía de Python", "https://python.org", 5)


# print(libro1.descripcion_corta())
# print(dispositivo1.descripcion_corta()) 
# print(juego1.descripcion_corta())
# print(juego2.descripcion_corta())
# print(juego3.descripcion_corta())
# print(recurso1.descripcion_corta())

# print(dispositivo1.estado)
# print(dispositivo1.tipo_dispositivo)







""""
    Mirar de aqui para cuando se muestre por pantalla.

    @property   # Por ver como hacer para cuando este pendiente de recogida, para que el bibliotecario 
    def ubicacion(self) -> str: # pueda ver ubicacion pero no el usuario que veria "recoger en mostrador".     
        if self._estado == EstadoMaterial.NO_DISPONIBLE:
            return "Ubicación no disponible"
        if self._estado == EstadoMaterial.PRESTADO:
            return "En préstamo"
        return self._ubicacion if self._ubicacion else "Ubicación no disponible"





"""




# class Libro(Material):
#     """
#     Clase que representa un libro.

#     Hereda de Material porque un libro ES un material.
#     """

#     def __init__(self, codigo, titulo, autor, paginas, disponible=True):
#         """
#         Constructor de Libro.

#         Usa super() para reutilizar el constructor de Material.
#         """

#         super().__init__(codigo, titulo, )
#         self.paginas = int(paginas)

#     def descripcion_corta(self):
#         """
#         TODO 1

#         Completa este método para que devuelva una descripción de un libro.

#         Ejemplo esperado:

#         [L001] El Quijote - Miguel de Cervantes · Libro de 863 páginas (disponible)
#         """
#         if self.disponible:
#             estado = "disponible"
#         else:
#             estado = "prestado"

#         return f"[{self.codigo}] {self.titulo}  - {self.autor} · Libro de {self.paginas} páginas ({estado})"


# class RecursoDigital(Material):
#     """
#     Clase que representa un recurso digital.

#     Hereda de Material porque un recurso digital ES un material.
#     """

#     def __init__(self, codigo, titulo, autor, url, disponible=True):
#         """
#         Constructor de RecursoDigital.
#         """

#         super().__init__(codigo, titulo, autor, disponible)
#         self.url = url

#     def descripcion_corta(self):
#         """
#         Devuelve una descripción de un recurso digital.
#         """

#         if self.disponible:
#             estado = "disponible"
#         else:
#             estado = "prestado"

#         return f"[{self.codigo}] {self.titulo} - {self.autor} · Recurso digital ({estado})"


# class Usuario:
#     """
#     Clase base para usuarios del sistema.
#     """

#     def __init__(self, identificador, nombre):
#         """
#         Constructor de Usuario.
#         """

#         self.identificador = identificador
#         self.nombre = nombre

#     def descripcion_corta(self):
#         """
#         Devuelve una descripción sencilla.
#         """

#         return f"[{self.identificador}] {self.nombre}"


# class Socio(Usuario):
#     """
#     Clase que representa un socio de la biblioteca.

#     Hereda de Usuario porque un socio ES un usuario.
#     """

#     def __init__(self, identificador, nombre, sancionado=False, max_prestamos=3):
#         """
#         Constructor de Socio.
#         """

#         super().__init__(identificador, nombre)

#         self.sancionado = bool(sancionado)
#         self.max_prestamos = int(max_prestamos)

#     def puede_prestar(self, numero_prestamos_activos):
#         """
#         TODO 2

#         Completa este método.

#         Reglas:
#         - Si el socio está sancionado, devuelve False.
#         - Si numero_prestamos_activos es mayor o igual que max_prestamos, devuelve False.
#         - En caso contrario, devuelve True.
#         """
#         if numero_prestamos_activos >= 3 or self.sancionado == True:
#             return False
#         else:
#             return True
  

#     def descripcion_corta(self):
#         """
#         Devuelve una descripción del socio.
#         """

#         if self.sancionado:
#             estado = "sancionado"
#         else:
#             estado = "activo"

#         return f"[{self.identificador}] {self.nombre} · Socio {estado}"


# class Prestamo:
#     """
#     Clase que representa un préstamo.

#     Esta clase muestra una asociación:
#     - tiene un socio;
#     - tiene un material.

#     No hereda de Socio ni de Material.
#     """

#     def __init__(self, id_prestamo, socio, material, fecha_prestamo, fecha_devolucion=None):
#         """
#         Constructor de Prestamo.
#         """

#         self.id_prestamo = id_prestamo
#         self.socio = socio
#         self.material = material
#         self.fecha_prestamo = fecha_prestamo
#         self.fecha_devolucion = fecha_devolucion

#     def esta_activo(self):
#         """
#         Devuelve True si el préstamo sigue activo.
#         """

#         return self.fecha_devolucion is None

#     def resumen(self):
#         """
#         Devuelve una frase resumen.
#         """

#         if self.esta_activo():
#             estado = "activo"
#         else:
#             estado = f"devuelto el {self.fecha_devolucion}"

#         return f"Préstamo {self.id_prestamo}: {self.socio.nombre} tiene '{self.material.titulo}' ({estado})"
