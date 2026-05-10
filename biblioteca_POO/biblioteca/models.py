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

class ConfiguracionBiblioteca:
    MAX_PRESTAMOS = 3

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
    def __init__(self, codigo_id: str,
                 titulo: str,
                 ubicacion: str = None,
                 estado: EstadoMaterial = EstadoMaterial.DISPONIBLE):
        super().__init__(codigo_id, titulo, estado=estado)
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
                 autor: str = None, 
                 paginas: int = None,  
                 isbn:str = None,
                 ubicacion: str = None,
                 estado: EstadoMaterial = EstadoMaterial.DISPONIBLE):
        super().__init__(codigo_id, titulo, ubicacion=ubicacion, estado=estado)
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
                 tipo_dispositivo: TipoDispositivo, 
                 fabricante: str = None, 
                 so: str = None, 
                 numero_serie: str = None,
                 ubicacion: str = None,
                 estado: EstadoMaterial = EstadoMaterial.DISPONIBLE):
        super().__init__(codigo_id, titulo, ubicacion = ubicacion, estado = estado)
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
            f"[{self.codigo_id}] {self.tipo_dispositivo.value}: {self.titulo} "
            f"- Fabricante: {fabricante_str} - SO: ({so_str}) - Estado: {self.estado.value}"
        )


class JuegoDeMesa(MaterialFisico):  # Para juegos de mesa, rol, cartas, etc. que se prestan físicamente pero no son libros ni dispositivos tecnológicos
    def __init__(self, codigo_id: str,
                 titulo: str,
                 editorial: str = None,
                 min_jugadores: int = None,
                 max_jugadores: int = None,
                 ubicacion: str = None,
                 estado: EstadoMaterial = EstadoMaterial.DISPONIBLE): # Estaria bien tipear a int aunque se pueda none?
        
        super().__init__(codigo_id, titulo, ubicacion = ubicacion, estado = estado)
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
                 url: str = None,
                 licencias_totales: int = 1,
                 estado: EstadoMaterial = EstadoMaterial.DISPONIBLE):
        super().__init__(codigo_id, titulo, estado = estado)
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
    
    @licencias_totales.setter
    def licencias_totales(self, nuevas_licencias):
        if type(nuevas_licencias) != int or nuevas_licencias < 0:
            raise ValueError("El número total de licencias debe ser un número " \
            "entero mayor o igual a 0.")
        diferencia = nuevas_licencias - self._licencias_totales
        self._licencias_totales = nuevas_licencias
        self._licencias_disponibles += diferencia
        self.actualizar_estado()

    def actualizar_estado(self): # Método para actualizar el estado segun licencias
        if self._licencias_totales == 0:
            self._estado = EstadoMaterial.NO_DISPONIBLE
        elif self._licencias_disponibles <= 0:
            self._estado = EstadoMaterial.PRESTADO
        else:
            self._estado = EstadoMaterial.DISPONIBLE

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
            self.actualizar_estado()
            return True
        return False

    def anadir_licencias(self, cantidad: int) -> bool:
        if cantidad > 0:
            self.licencias_totales += cantidad
            return True
        return False
    
    def retirar_licencias(self, cantidad: int) -> bool:
        if type(cantidad) != int:
            raise ValueError("La cantidad de licencias a retirar debe ser un número entero.")
        if 0 < cantidad <= self._licencias_disponibles:
            self.licencias_totales -= cantidad
            return True     # Plantear la posibilidad de retirar licencias aunque no estén disponibles (hacer que el usuario pierda el acceso a ese recurso siendo notificado del motivo)
        else: 
            raise ValueError("No se pueden retirar más licencias de las " \
            "disponibles, retira licencias prestadas. ")

    def descripcion_corta(self) -> str:
        return (
            f"[{self.codigo_id}] Digital: '{self.titulo}' - "
            f"Licencias libres: {self._licencias_disponibles}/{self._licencias_totales} "
            f"- Estado: {self.estado.value}"
        )


class Usuario(ABC):

    def __init__(self, 
                 id_usuario: str, 
                 nombre: str, 
                 apellido: str, 
                 email: str, 
                 apellido2: str = None):
        self._id_usuario = id_usuario
        self._nombre = nombre
        self._apellido = apellido
        self._email = email
        self._apellido2 = apellido2

    @property
    def id_usuario(self): 
        return self._id_usuario
    
    @property
    def nombre(self): 
        return self._nombre
    
    @property
    def apellido(self): 
        return self._apellido

    @property
    def email(self): 
        return self._email
    
    @property
    def apellido2(self):
        return self._apellido2

    @abstractmethod
    def descripcion_corta(self) -> str: 
        pass
    
class Socio(Usuario):

    def __init__(self, 
                 id_usuario,
                 nombre,
                 apellido,
                 email,
                 apellido2 = None,
                 sancionado=False,
                 prestamos_activos= 0,
                 max_prestamos=ConfiguracionBiblioteca.MAX_PRESTAMOS,
                 max_especial = False):

        super().__init__(id_usuario, nombre, apellido, email, apellido2 = apellido2)

        self._sancionado = sancionado # determina si el socio puede prestar
        self._prestamos_activos = prestamos_activos # cuantos prestamos tiene el usuario
        self._max_prestamos = max_prestamos # maximo de prestamos, por defecto equivale al maximo global
        self._max_especial = max_especial # permite que el socio tenga un max diferente, por ejemplo socios con suscripcion

    @property
    def sancionado(self): 
        return self._sancionado
    
    @property
    def prestamos_activos(self):
        return self._prestamos_activos

    @property
    def max_prestamos(self):
        if self.max_especial:
            return self._max_prestamos
        else:
            return ConfiguracionBiblioteca.MAX_PRESTAMOS
    
    @max_prestamos.setter
    def max_prestamos(self, nuevo_max):
        if not self.max_especial:
            raise ValueError("Este usuario no puede tener un máximo distinto al global")
            
        if type(nuevo_max) != int:
            raise ValueError("Estableza el número máximo de préstamos permitidos para este usuario." \
            " No puede estar vacio.")
        else:
            self._max_prestamos = nuevo_max
    
    @property
    def max_especial(self):
        return self._max_especial
        
    @property
    def puede_prestar(self) -> bool:

        if self._sancionado or (self._prestamos_activos >= self.max_prestamos):
            return False
        return True

    def incrementar_prestamos(self):
        if self.puede_prestar:
            self._prestamos_activos += 1
            return True
        return False
    
    def reducir_prestamos(self):
        if self.prestamos_activos >0:
            self._prestamos_activos -= 1
            return True
        return False
    
    def permitir_cambio_max(self): # Permite que el bibliotecario le asigne un max diferente
        if self.max_especial:
            self._max_especial = False
            self._max_prestamos = ConfiguracionBiblioteca.MAX_PRESTAMOS 
        else:
            self._max_especial = True

    def sancionar(self):
        self._sancionado = False if self._sancionado else True

    def descripcion_corta(self):

        if self.sancionado:
            estado = "sancionado"
        else:
            estado = "activo"
        if self.max_especial:
            estado += ". Max especial"
        else:
            estado += ". Max no especial"

        return (f"[{self.id_usuario}] {self.nombre} {self.apellido} - "
            f"Max prestamos: {self.max_prestamos} - Socio {estado}")


class Bibliotecario(Usuario):

    def __init__(self, id_usuario, nombre, apellido, email, apellido2 = None):

        super().__init__(id_usuario, nombre, apellido, email, apellido2 = apellido2)
        
    def descripcion_corta(self):

        return f"[{self.id_usuario}] {self.nombre} {self.apellido} · Bibliotecario"










libro1 = Libro("L001", "El Quijote", "Miguel de Cervantes", 863, "978-3-16-148410-0", "Pasillo 4, Estante B", EstadoMaterial.NO_DISPONIBLE)
dispositivo1 = Dispositivo("D001", "iPad Pro", TipoDispositivo.TABLET, ubicacion = "Mostrador Principal", fabricante="Apple", so="iOS")
juego1 = JuegoDeMesa("J001", "Catan", "Devir", "Pasillo 2, Estante A", 3, 4)
juego2 = JuegoDeMesa("J001", "Catan", "Devir", "Pasillo 2, Estante A", 4)
juego3 = JuegoDeMesa("J001", "Catan", "Devir", "Pasillo 2, Estante A", max_jugadores = 3)
recurso1 = RecursoDigital("R001", "Guía de Python", "https://python.org", 5)

print(recurso1.descripcion_corta(), "inicio")
recurso1.licencias_totales = 10
print(recurso1.descripcion_corta(), "cambio licencias totales")
recurso1.prestar()
recurso1.prestar()
print(recurso1.descripcion_corta(), "dos licencias prestadas")
recurso1.prestar()
recurso1.prestar()
recurso1.prestar()
recurso1.prestar()
recurso1.prestar()
recurso1.prestar()
recurso1.prestar()
recurso1.prestar()
recurso1.prestar()
print(recurso1.descripcion_corta(), "10 licencias prestadas")
recurso1.devolver()
recurso1.devolver()
print(recurso1.descripcion_corta(), "devolucion de 2 licencias")
# recurso1.retirar_licencias(3)
# print(recurso1.descripcion_corta(), "retirada de 3 licencias")
recurso1.retirar_licencias(2)
print(recurso1.descripcion_corta(), "retirada de 2 licencias")
recurso1.devolver()
print(recurso1.descripcion_corta(), "devolucion de 1 licencia")
recurso1.anadir_licencias(4)
print(recurso1.descripcion_corta(), "añadir de 4 licencia")
# print(libro1.descripcion_corta())
# print(dispositivo1.descripcion_corta()) 
# print(juego1.descripcion_corta())
# print(juego2.descripcion_corta())
# print(juego3.descripcion_corta())
# print(recurso1.descripcion_corta())

# print(dispositivo1.estado)
# print(dispositivo1.tipo_dispositivo)


# socio1 = Socio("S0001", "Paola", "Santana", "Paola.Santana@gmail.com" )
# print(socio1.descripcion_corta())
# socio1._prestamos_activos = 3
# print(socio1.puede_prestar)
# socio1.permitir_cambio_max()
# print(socio1.descripcion_corta())
# socio1.max_prestamos = 4
# print(socio1.descripcion_corta())
# socio1.puede_prestar
# print(socio1.descripcion_corta())
# socio1._prestamos_activos = 4
# print(socio1.puede_prestar)
# socio1.sancionar()
# print(socio1.descripcion_corta())
# print(socio1.puede_prestar)


# print(libro1.__dict__)



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
