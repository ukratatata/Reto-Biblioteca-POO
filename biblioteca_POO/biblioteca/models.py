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
from datetime import datetime, timedelta # ¡Necesario para calcular fechas!


class ConfiguracionBiblioteca: 
    MAX_PRESTAMOS = 3
    TIEMPO_PRESTAMO_DEFECTO = 15        # En días
    TIEMPO_PRESTAMO_DISPOSITIVOS = 7    # En días
    TIEMPO_PRESTAMO_JUEGOS_MESA = 2     # En días


# 1. Definición de la Máquina de Estados (Enumerador): en vez de usar strings sueltos, definimos un Enum para los estados posibles de un material.
class EstadoMaterial(Enum):
    DISPONIBLE = "Disponible"                       # El material está en la biblioteca y se puede prestar
    PENDIENTE_RECOGIDA = "Pendiente de Recogida"    # El usuario tiene 2 días para venir a por él
    PRESTADO = "Prestado"                           # El usuario lo tiene en su casa (15 días...)
    NO_DISPONIBLE = "No Disponible"                 # Extra: Para materiales que no se pueden prestar (mantenimiento, extravio, retiro...)
    BLOQUEADO = "Bloqueado"                         # Extra: Para materiales que se quieren bloquear para parar prestamos

class EstadoPrestamo(Enum):
    ACTIVO = "Activo"
    DEVUELTO = "Devuelto"
    RETRASADO = "Retrasado"


class TipoDispositivo(Enum):
    ORDENADOR = "Ordenador"
    TABLET = "Tablet"
    E_READER = "E-Reader"
    CALCULADORA = "Calculadora"
    OTROS = "Otros"


class RolEmpleado(Enum):
    BIBLIOTECARIO = "Bibliotecario"
    AUXILIAR = "Auxiliar"
    ADMIN = "Administrador"


# 2. Clase Abstracta Base (El Contrato)
class Material(ABC):
    """
    Clase abstracta pura que define la estructura base de cualquier 
    elemento prestable en la biblioteca. No se puede instanciar directamente.
    """
    
    def __init__(self, codigo_id: str, titulo: str, estado: EstadoMaterial = EstadoMaterial.DISPONIBLE):
        # Atributos protegidos (Encapsulación básica)
        self._codigo_id = codigo_id
        self.titulo = titulo
        self._estado = estado # Estado inicial por defecto: Disponible

    # -- Getters básicos para acceder a la información de forma segura --
    @property
    def codigo_id(self) -> str:
        return self._codigo_id

    @property
    def titulo(self) -> str:
        return self._titulo
    
    @titulo.setter
    def titulo(self, nuevo_titulo):
        if not nuevo_titulo or type(nuevo_titulo) != str:
            raise ValueError("Introduce un título válido.")
        self._titulo = nuevo_titulo.strip()
        
    @property
    def estado(self) -> EstadoMaterial:
        return self._estado

    # -- MÉTODOS CONCRETOS (Todos heredan) --

    def bloquear(self) -> bool:
        """
        Cambia el estado a NO_DISPONIBLE, impidiendo cualquier préstamo.
        Útil para mantenimiento o extravío.
        """
        if self._estado != EstadoMaterial.BLOQUEADO:
            self._estado = EstadoMaterial.BLOQUEADO
            return True
        return False
    
    # -- MÉTODOS ABSTRACTOS (El Polimorfismo) --
    @abstractmethod
    def puede_prestarse(self) -> bool:
        """
        Verifica si el material se puede prestar según su estado actual.
        OBLIGATORIO: Cada subclase debe definir sus propias reglas de préstamo.
        (Ej. Un libro solo se presta si está DISPONIBLE, un recurso digital si tiene licencias libres...)
        """
        pass

    @abstractmethod
    def prestar(self) -> bool:
        """
        Intenta prestar el material a un socio.
        OBLIGATORIO: Cada subclase debe implementar su propia lógica.
        """
        pass

    @abstractmethod
    def puede_devolverse(self) -> bool:
        """Comprueba si el material está en un estado que permita su devolución."""
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
        self.ubicacion = ubicacion  # Ej: "Pasillo 4, Estante B"

    @property    
    def ubicacion(self) -> str:     
        return self._ubicacion
    
    @ubicacion.setter
    def ubicacion(self, nueva_ubicacion):
        if nueva_ubicacion is not None:
            if type(nueva_ubicacion) != str:
                raise ValueError("Formato no válido.")
            self._ubicacion = nueva_ubicacion.strip()
        else:
            self._ubicacion = None
    
    # --- BLOQUE RESERVAR ---
    def puede_reservarse(self) -> bool:
        return self._estado == EstadoMaterial.DISPONIBLE

    def reservar_recogida(self) -> bool:
        if self.puede_reservarse():
            self._estado = EstadoMaterial.PENDIENTE_RECOGIDA
            return True
        return False

    # --- BLOQUE PRESTAR ---
    def puede_prestarse(self) -> bool:
        return self._estado == EstadoMaterial.DISPONIBLE

    def prestar(self) -> bool:
        if self.puede_prestarse():
            self._estado = EstadoMaterial.PRESTADO
            return True
        return False
    
    # --- BLOQUE RECOGER ---
    def puede_recogerse(self) -> bool:
        return self._estado == EstadoMaterial.PENDIENTE_RECOGIDA

    def recoger(self) -> bool:
        """Simula que el usuario viene a recoger el material reservado."""
        if self.puede_recogerse():
            self._estado = EstadoMaterial.PRESTADO
            return True
        return False

    # --- BLOQUE DEVOLVER ---
    def puede_devolverse(self) -> bool:
        # Usamos el truco de 'in' para simplificar
        return self._estado in [EstadoMaterial.PRESTADO, EstadoMaterial.PENDIENTE_RECOGIDA]

    def devolver(self) -> bool:
        if self.puede_devolverse():
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
        self.autor = autor
        self.paginas = paginas
        self.isbn = isbn
    
    @property
    def autor(self):
        return self._autor
    
    @autor.setter
    def autor(self, nuevo_autor):
        if nuevo_autor != None:
            if type(nuevo_autor) != str:
                raise ValueError("Formato no válido.")
            self._autor = nuevo_autor.strip()
        else:
            self._autor = None
    
    @property
    def paginas(self):
        return self._paginas
    
    @paginas.setter
    def paginas(self, nuevas_paginas):
        if nuevas_paginas != None:
            if type(nuevas_paginas) != int:
                raise ValueError("Formato no válido.")
            elif nuevas_paginas <= 0:
                raise ValueError("El número de páginas debe ser un entero positivo.")   
            self._paginas = nuevas_paginas
        else:
            self._paginas = None
    
    @property
    def isbn(self):
        return self._isbn
    
    @isbn.setter
    def isbn(self, nuevo_isbn):
        # Permitimos None por si es un libro antiguo sin ISBN.
        if nuevo_isbn != None:
            if type(nuevo_isbn) != str:
                raise ValueError("Formato no válido.")
            self._isbn = nuevo_isbn.strip()
        else:
            self._isbn = None

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
        self.fabricante = fabricante
        self.so = so  # Sistema Operativo
        self.numero_serie = numero_serie

    @property
    def tipo_dispositivo(self):
        return self._tipo_dispositivo

    @property
    def fabricante(self):
        return self._fabricante
    
    @fabricante.setter
    def fabricante(self, nuevo_fabricante):
        if nuevo_fabricante != None:
            if type(nuevo_fabricante) != str:
                raise ValueError("Formato no válido.")
            self._fabricante = nuevo_fabricante.strip()
        else:
            self._fabricante = None

    @property
    def so(self):
        return self._so
    
    @so.setter
    def so(self, nuevo_so):
        if nuevo_so != None:
            if type(nuevo_so) != str:
                raise ValueError("Formato no válido.")
            self._so = nuevo_so.strip()
        else:
            self._so = None

    @property
    def numero_serie(self):
        return self._numero_serie

    @numero_serie.setter
    def numero_serie(self, nuevo_numero_serie):
        if nuevo_numero_serie != None:
            if type(nuevo_numero_serie) != str:
                raise ValueError("Formato no válido.")
            self._numero_serie = nuevo_numero_serie.strip()
        else:
            self._numero_serie = None

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
        self.editorial = editorial
        self._min_jugadores = None # Como los setters los comparan, se inicializan con None
        self._max_jugadores = None
        self.min_jugadores = min_jugadores
        self.max_jugadores = max_jugadores

    @property
    def editorial(self):
        return self._editorial 
    
    @editorial.setter
    def editorial(self, nueva_editorial):
        if nueva_editorial != None:
            if type(nueva_editorial) != str:
                raise ValueError("Formato no válido.")
            self._editorial = nueva_editorial.strip()
        else:
            self._editorial = None

    @property
    def min_jugadores(self):
        return self._min_jugadores 

    @min_jugadores.setter
    def min_jugadores(self, nuevos_min_jugadores):
        if nuevos_min_jugadores != None:
            if type(nuevos_min_jugadores) != int:
                raise ValueError("Formato no válido.")
            if nuevos_min_jugadores < 0:
                raise ValueError("El número mínimo de jugadores debe ser un entero positivo.")
            if (self._max_jugadores != None) and (nuevos_min_jugadores > self._max_jugadores):
                raise ValueError("El número mínimo de jugadores no puede ser mayor que el máximo.")  
            self._min_jugadores = nuevos_min_jugadores
        else:
            self._min_jugadores = None

    @property
    def max_jugadores(self):
        return self._max_jugadores 

    @max_jugadores.setter
    def max_jugadores(self, nuevos_max_jugadores):
        if nuevos_max_jugadores != None:
            if type(nuevos_max_jugadores) != int:
                raise ValueError("Formato no válido.")
            if nuevos_max_jugadores < 0:
                raise ValueError("El número máximo de jugadores debe ser un entero positivo.")
            if (self._min_jugadores != None) and (nuevos_max_jugadores < self._min_jugadores):
                raise ValueError("El número máximo de jugadores no puede ser menor que el mínimo.")
            self._max_jugadores = nuevos_max_jugadores
        else:
            self._max_jugadores = None

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
        self.url = url
        self._licencias_disponibles = 0
        self._licencias_totales = 0
        self.licencias_totales = licencias_totales

    @property
    def url(self):
        return self._url 
    
    @url.setter
    def url(self, nueva_url):
        if nueva_url != None:
            if type(nueva_url) != str:
                raise ValueError("Formato no válido.")
            self._url = nueva_url.strip()
        else:
            self._url = None

    @property
    def licencias_totales(self):
        return self._licencias_totales
    
    @licencias_totales.setter
    def licencias_totales(self, nuevas_licencias):
        if type(nuevas_licencias) != int or nuevas_licencias < 0:
            raise ValueError("El número total de licencias debe ser un número " \
            "entero mayor o igual a 0.")
        diferencia = nuevas_licencias - self._licencias_totales
        if diferencia < 0 and abs(diferencia) > self._licencias_disponibles: # No se permiten retirar más licencias de las que hay disponibles, para evitar que el número de licencias prestadas supere el total.
            raise ValueError("No se pueden retirar más licencias de las " \
            "disponibles, devuelve licencias prestadas. ") # Plantear anular las licencias prestadas automaticamente con un script en un futuro.
        self._licencias_totales = nuevas_licencias
        self._licencias_disponibles += diferencia
        self.actualizar_estado()
    
    @property
    def licencias_disponibles(self):
        return self._licencias_disponibles

    def actualizar_estado(self): # Método para actualizar el estado segun licencias
        if self._licencias_totales == 0:
            self._estado = EstadoMaterial.NO_DISPONIBLE
        elif self._licencias_disponibles <= 0:
            self._estado = EstadoMaterial.PRESTADO
        else:
            self._estado = EstadoMaterial.DISPONIBLE

    def puede_prestarse(self) -> bool:
        """Comprueba si el material se puede prestar."""
        return self._licencias_disponibles > 0 and self.estado != EstadoMaterial.BLOQUEADO

    def prestar(self) -> bool:
        if self.puede_prestarse():
            self._licencias_disponibles -= 1
            self.actualizar_estado()
            return True
        return False

    def puede_devolverse(self) -> bool:
        """Comprueba si hay licencias prestadas que puedan devolverse."""
        return self._licencias_disponibles < self._licencias_totales

    def devolver(self) -> bool:
        if self.puede_devolverse():
            self._licencias_disponibles += 1
            self.actualizar_estado()
            return True
        return False

    def anadir_licencias(self, cantidad: int) -> bool:
            if type(cantidad) != int or cantidad <= 0:
                raise ValueError("La cantidad de licencias a añadir debe ser un número entero positivo.")
            self.licencias_totales += cantidad
            return True
    
    def retirar_licencias(self, cantidad: int) -> bool:
        if type(cantidad) != int or cantidad <= 0:
            raise ValueError("La cantidad de licencias a retirar debe ser un número entero positivo.")
        self.licencias_totales -= cantidad
        return True
        

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
                 apellidos: str, 
                 email: str):
        self._id_usuario = id_usuario
        self.nombre = nombre
        self.apellidos = apellidos
        self.email = email

    @property
    def id_usuario(self): 
        return self._id_usuario
    
    @property
    def nombre(self): 
        return self._nombre
    
    @nombre.setter
    def nombre(self, nuevo_nombre):
        if not nuevo_nombre or type(nuevo_nombre) != str:
            raise ValueError("El nombre debe ser un texto válido.")
        self._nombre = nuevo_nombre.strip()
    
    @property
    def apellidos(self): 
        return self._apellidos
    
    @apellidos.setter
    def apellidos(self, nuevos_apellidos):
        if not nuevos_apellidos or type(nuevos_apellidos) != str:
            raise ValueError("Introduce apellidos válidos.")
        self._apellidos = nuevos_apellidos.strip()

    @property
    def email(self): 
        return self._email
    
    @email.setter
    def email(self, nuevo_email):
        #   Comprobamos que no esté vacío y sea un texto
        if not nuevo_email or type(nuevo_email) != str:
            raise ValueError("El email no puede estar vacío.")
            
        nuevo_email = nuevo_email.strip() # Quitamos espacios en blanco a los lados

        # Para verificar formato cortamos el email por la @
        trozos = nuevo_email.split("@")
        
        # Si no hay exactamente 2 trozos, es que no había '@' o había más de una
        if len(trozos) != 2:
            raise ValueError("Formato de email no válido.")
            
        # Guardamos la segunda parte (el dominio) en una variable
        dominio = trozos[1]
        
        # Comprobamos si hay un punto en el dominio
        if "." not in dominio:
            raise ValueError("Formato de email no válido.")
            
        # En caso de pasar todas las comprobaciones, asignamos el nuevo email al usuario
        self._email = nuevo_email

    @abstractmethod
    def descripcion_corta(self) -> str: 
        pass
    
class Socio(Usuario):

    def __init__(self, 
                 id_usuario: str,
                 nombre: str,
                 apellidos: str,
                 email: str,            
                 sancionado: bool = False,
                 prestamos_activos: int = 0,
                 max_prestamos: int = ConfiguracionBiblioteca.MAX_PRESTAMOS,
                 max_especial: bool = False):

        super().__init__(id_usuario, nombre, apellidos, email)

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

    def cambiar_sancionar(self):
        self._sancionado = not self._sancionado

    def descripcion_corta(self):

        if self.sancionado:
            estado = "sancionado"
        else:
            estado = "activo"
        if self.max_especial:
            estado += ". Max especial"
        else:
            estado += ". Max no especial"

        return (
            f"[{self.id_usuario}] {self.nombre} {self.apellidos} - "
            f"Max prestamos: {self.max_prestamos} - Socio {estado}"
        )


class Empleado(Usuario):

    def __init__(self, id_usuario: str,
                 nombre: str, apellidos: str,
                 email: str,
                 rol: RolEmpleado = RolEmpleado.AUXILIAR):

        super().__init__(id_usuario, nombre, apellidos, email)
        self._rol = rol
    
    @property
    def rol(self):
        return self._rol
    
    @rol.setter
    def rol(self, nuevo_rol: RolEmpleado):
        if type(nuevo_rol) != RolEmpleado:
            raise ValueError("Rol no válido.")
        self._rol = nuevo_rol

    def es_admin(self):
        return self._rol == RolEmpleado.ADMIN
    
    def es_bibliotecario_o_superior(self):
        return self._rol in [RolEmpleado.ADMIN, RolEmpleado.BIBLIOTECARIO]
        
    def descripcion_corta(self):

        return f"[{self.id_usuario}] {self.nombre} {self.apellidos} · {self.rol.value}"


class Prestamo:
    def __init__(self,
                 id_prestamo: str,
                 usuario: Usuario,
                 material: Material,
                 dias_prestamo: int = None):
        # Validaciones de los ID
        if not id_prestamo or type(id_prestamo) != str:
            raise ValueError("El ID del préstamo debe ser un texto válido.")
        
        # Guardamos las referencias sin setters públicos para que sean inmutables
        self._id_prestamo = id_prestamo.strip()
        self._usuario = usuario
        self._material = material
        
        # Fecha de prestamo se asigna en funcion de la configurada para cada tipo de material, o la por defecto si no se especifica.
        self._fecha_prestamo = datetime.now() # Fecha y hora actual exacta
        if dias_prestamo is None:
            if isinstance(material, Dispositivo):
                dias_prestamo = ConfiguracionBiblioteca.TIEMPO_PRESTAMO_DISPOSITIVOS
            elif isinstance(material, JuegoDeMesa):
                dias_prestamo = ConfiguracionBiblioteca.TIEMPO_PRESTAMO_JUEGOS_MESA
            else:
                dias_prestamo = ConfiguracionBiblioteca.TIEMPO_PRESTAMO_DEFECTO

        # Calculamos la fecha de devolución sumando los días (timedelta)
        if type(dias_prestamo) != int or dias_prestamo <= 0:
            raise ValueError("Los días de préstamo deben ser un número entero positivo.")

        # Sumamos a la fecha del prestamo el numero de dias    
        fecha_base = self._fecha_prestamo + timedelta(days=dias_prestamo)

        # Establecemos la hora de devolucion que la hora de entrega límite sea las 23:59:59
        self._fecha_devolucion_prevista = fecha_base.replace(
            hour=23, 
            minute=59, 
            second=59, 
            microsecond=0
        )
        
        # Al instanciarse, el prestamo esta activo
        self._fecha_devolucion_real = None
        self._estado = EstadoPrestamo.ACTIVO

    # ==========================================
    # GETTERS (Solo lectura, sin setters ya que tienen que ser inmutables después de crear el préstamo)
    # ==========================================
    @property
    def id_prestamo(self):
        return self._id_prestamo

    @property
    def usuario(self):
        return self._usuario

    @property
    def material(self):
        return self._material

    @property
    def fecha_prestamo(self):
        return self._fecha_prestamo

    @property
    def fecha_devolucion_prevista(self):
        return self._fecha_devolucion_prevista

    @property
    def fecha_devolucion_real(self):
        return self._fecha_devolucion_real

    @property
    def estado(self):
        return self._estado

    # MÉTODOS DE ACCIÓN 
    
    def actualizar_estado(self) -> bool:
        """Verifica si la fecha actual superó la fecha prevista y marca como retrasado."""
        if self._estado == EstadoPrestamo.ACTIVO:
            if datetime.now() > self._fecha_devolucion_prevista:
                self._estado = EstadoPrestamo.RETRASADO
                return True
        return False

    def puede_finalizarse(self) -> bool:
        """Un préstamo se puede finalizar si no ha sido devuelto ya."""
        return self._estado != EstadoPrestamo.DEVUELTO

    def finalizar_prestamo(self) -> bool:
        """Registra la devolución del material y cierra el préstamo."""
        if not self.puede_finalizarse():
            return False # Ya estaba devuelto, abortamos
            
        self._fecha_devolucion_real = datetime.now()
        
        # Aquí verificamos si se entregó tarde
        entregado_tarde = self._fecha_devolucion_real > self._fecha_devolucion_prevista
        if entregado_tarde and isinstance(self._usuario, Socio) and self._usuario.sancionado is False: 
            self._usuario.cambiar_sancionar() # Sancionamos al usuario por entregar tarde
            
        self._estado = EstadoPrestamo.DEVUELTO
        return True

    def extender_prestamo(self, dias_extra: int) -> bool:
        """Permite renovar el préstamo si no está retrasado ni devuelto."""
        self.actualizar_estado() # Comprobamos cómo está hoy
        
        if self._estado != EstadoPrestamo.ACTIVO:
            raise ValueError("No se puede renovar un préstamo que está devuelto o retrasado.")
            
        if type(dias_extra) != int or dias_extra <= 0:
            raise ValueError("Los días extra deben ser un número positivo.")
            
        self._fecha_devolucion_prevista += timedelta(days=dias_extra)
        return True

    def resumen(self) -> str:
        """Devuelve un texto para la interfaz de Tkinter."""
        self.actualizar_estado() # Aseguramos que el estado esté al día al imprimir
        
        # Formateamos las fechas en (DD/MM/YYYY)
        fecha_p = self._fecha_prestamo.strftime("%d/%m/%Y")
        fecha_d = self._fecha_devolucion_prevista.strftime("%d/%m/%Y")
        
        return (f"[{self._id_prestamo}] {self._material.titulo} prestado a "
                f"{self._usuario.nombre} ({fecha_p} -> {fecha_d}) | Estado: {self._estado.value}")

