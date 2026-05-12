"""
models.py

Contiene la lógica de negocio y las clases del dominio de la biblioteca.
Este módulo es independiente de la interfaz gráfica y de la base de datos.
"""

from abc import ABC, abstractmethod
from enum import Enum
from datetime import datetime, timedelta

class ConfiguracionBiblioteca:
    """Configuraciones globales por defecto para el sistema de la biblioteca."""
    MAX_PRESTAMOS = 3
    TIEMPO_PRESTAMO_DEFECTO = 15        # En días
    TIEMPO_PRESTAMO_DISPOSITIVOS = 7    # En días
    TIEMPO_PRESTAMO_JUEGOS_MESA = 2     # En días


class EstadoMaterial(Enum):
    """Posibles estados del ciclo de vida de un material físico o digital."""
    DISPONIBLE = "Disponible"
    PENDIENTE_RECOGIDA = "Pendiente de Recogida"    # Valorar meter temporizador para liberar si no se recoge en plazo
    PRESTADO = "Prestado"
    NO_DISPONIBLE = "No Disponible"                 # hay 0 disponibles o esta retirado
    BLOQUEADO = "Bloqueado"                         # No se quiere dejar prestar mas


class EstadoPrestamo(Enum):
    """Estados por los que pasa un registro de préstamo."""
    ACTIVO = "Activo"
    DEVUELTO = "Devuelto"
    RETRASADO = "Retrasado"


class TipoDispositivo(Enum):
    """Clasificación de los dispositivos tecnológicos prestables."""
    ORDENADOR = "Ordenador"
    TABLET = "Tablet"
    E_READER = "E-Reader"
    CALCULADORA = "Calculadora"
    OTROS = "Otros"


class RolEmpleado(Enum):
    """Niveles de acceso y permisos para el personal del sistema."""
    BIBLIOTECARIO = "Bibliotecario"
    AUXILIAR = "Auxiliar"
    ADMIN = "Administrador"


# ==========================================
# MATERIALES
# ==========================================

class Material(ABC):
    """
    Clase abstracta base para todos los elementos prestables.
    Define el contrato común que deben cumplir los materiales físicos y digitales.
    """
    
    def __init__(
        self, 
        codigo_id: str, 
        titulo: str, 
        estado: EstadoMaterial = EstadoMaterial.DISPONIBLE
    ):
        self._codigo_id = codigo_id
        self.titulo = titulo
        self._estado = estado 

    @property
    def codigo_id(self) -> str:
        """Devuelve el identificador único del material."""
        return self._codigo_id

    @property
    def titulo(self) -> str:
        """Devuelve el título del material."""
        return self._titulo
    
    @titulo.setter
    def titulo(self, nuevo_titulo: str):
        """Establece y valida el título del material asegurando que no esté vacío."""
        if not nuevo_titulo or type(nuevo_titulo) != str:
            raise ValueError("Introduce un título válido.")
        
        self._titulo = nuevo_titulo.strip()
        
    @property
    def estado(self) -> EstadoMaterial:
        """Devuelve el estado actual en el que se encuentra el material."""
        return self._estado

    def bloquear(self) -> bool:
        """Retira el material de circulación manualmente (ej. pérdida o mantenimiento)."""
        if self._estado != EstadoMaterial.BLOQUEADO:
            self._estado = EstadoMaterial.BLOQUEADO
            return True
        
        return False
    
    @abstractmethod
    def prestar(self) -> bool:
        """Lógica abstracta para ceder el material a un usuario."""
        pass

    @abstractmethod
    def puede_devolverse(self) -> bool:
        """Verifica de forma abstracta si el material puede ser devuelto."""
        pass

    @abstractmethod
    def devolver(self) -> bool:
        """Lógica abstracta para retornar el material al catálogo activo."""
        pass

    @abstractmethod
    def descripcion_corta(self) -> str:
        """Genera un resumen en texto del material para la interfaz."""
        pass
     

class MaterialFisico(Material):
    """
    Representa materiales tangibles que ocupan espacio físico en la biblioteca.
    Gestiona el ciclo de estados (Disponible -> Reservado -> Prestado).
    """
    def __init__(
        self, 
        codigo_id: str, 
        titulo: str, 
        ubicacion: str = None, 
        estado: EstadoMaterial = EstadoMaterial.DISPONIBLE
    ):
        super().__init__(codigo_id, titulo, estado=estado)
        self.ubicacion = ubicacion 

    @property    
    def ubicacion(self) -> str:
        """Devuelve la ubicación física (estante, pasillo, etc.) del material."""
        return self._ubicacion
    
    @ubicacion.setter
    def ubicacion(self, nueva_ubicacion: str):
        """Establece la ubicación física, permitiendo que sea nula si no se conoce."""
        if nueva_ubicacion != None:
            if type(nueva_ubicacion) != str:
                raise ValueError("Formato no válido.")
            
            self._ubicacion = nueva_ubicacion.strip()
        else:
            self._ubicacion = None
    
    def puede_reservarse(self) -> bool:
        """Verifica si el material está libre para ser apartado por un usuario."""
        return self._estado == EstadoMaterial.DISPONIBLE

    def reservar_recogida(self) -> bool:
        """Aparta el material temporalmente para que el usuario venga a por él."""
        if self.puede_reservarse():
            self._estado = EstadoMaterial.PENDIENTE_RECOGIDA
            return True
        
        return False

    def puede_prestarse(self) -> bool:
        """Verifica si el material puede ser prestado directamente en el mostrador."""
        return self._estado == EstadoMaterial.DISPONIBLE

    def prestar(self) -> bool:
        """Formaliza el préstamo directo desde la estantería al usuario."""
        if self.puede_prestarse():
            self._estado = EstadoMaterial.PRESTADO
            return True
        
        return False
    
    def puede_recogerse(self) -> bool:
        """Verifica si el material está esperando a ser recogido por quien lo reservó."""
        return self._estado == EstadoMaterial.PENDIENTE_RECOGIDA

    def recoger(self) -> bool:
        """Convierte una reserva previa en un préstamo activo cuando el usuario llega."""
        if self.puede_recogerse():
            self._estado = EstadoMaterial.PRESTADO
            return True
        
        return False

    def puede_devolverse(self) -> bool:
        """Comprueba si el material estaba fuera de la estantería (prestado o reservado)."""
        return self._estado in [EstadoMaterial.PRESTADO, EstadoMaterial.PENDIENTE_RECOGIDA]

    def devolver(self) -> bool:
        """Devuelve el material a la estantería, dejándolo disponible de nuevo."""
        if self.puede_devolverse():
            self._estado = EstadoMaterial.DISPONIBLE
            return True
        
        return False


class Libro(MaterialFisico):
    """Clase para libros impresos tradicionales y revistas."""
    def __init__(
        self, 
        codigo_id: str, 
        titulo: str, 
        autor: str = None, 
        paginas: int = None, 
        isbn: str = None, 
        ubicacion: str = None, 
        estado: EstadoMaterial = EstadoMaterial.DISPONIBLE
    ):
        super().__init__(codigo_id, titulo, ubicacion=ubicacion, estado=estado)
        self.autor = autor
        self.paginas = paginas
        self.isbn = isbn
    
    @property
    def autor(self) -> str:
        """Devuelve el autor principal del libro."""
        return self._autor
    
    @autor.setter
    def autor(self, nuevo_autor: str):
        """Establece el autor, asegurando el formato correcto."""
        if nuevo_autor != None:
            if type(nuevo_autor) != str:
                raise ValueError("Formato no válido.")
            
            self._autor = nuevo_autor.strip()
        else:
            self._autor = None
    
    @property
    def paginas(self) -> int:
        """Devuelve el conteo de páginas del libro."""
        return self._paginas
    
    @paginas.setter
    def paginas(self, nuevas_paginas: int):
        """Establece el conteo de páginas asegurando que sea lógico."""
        if nuevas_paginas != None:
            if type(nuevas_paginas) != int:
                raise ValueError("Formato no válido.")
            
            if nuevas_paginas <= 0:
                raise ValueError("El número de páginas debe ser un entero positivo.")
            
            self._paginas = nuevas_paginas
        else:
            self._paginas = None
    
    @property
    def isbn(self) -> str:
        """Devuelve el identificador comercial del libro (ISBN)."""
        return self._isbn
    
    @isbn.setter
    def isbn(self, nuevo_isbn: str):
        """Establece el ISBN del libro."""
        if nuevo_isbn != None:
            if type(nuevo_isbn) != str:
                raise ValueError("Formato no válido.")
            
            self._isbn = nuevo_isbn.strip()
        else:
            self._isbn = None

    def descripcion_corta(self) -> str:
        """Retorna una cadena con la información clave del libro para listados."""
        autor_str = self._autor if self._autor else "desconocido"
        paginas_str = f"{self._paginas}" if self._paginas else "desconocido"
        isbn_str = self._isbn if self._isbn else "no disponible"
        
        return (
            f"[{self.codigo_id}] Libro: '{self.titulo}' - Autor: {autor_str} - "
            f"Pags: {paginas_str} - ISBN: {isbn_str} - Estado: {self.estado.value}"
        )


class Dispositivo(MaterialFisico):  
    """Hardware disponible para préstamo en las instalaciones (ordenadores, tablets...)."""
    def __init__(
        self, 
        codigo_id: str, 
        titulo: str, 
        tipo_dispositivo: TipoDispositivo, 
        fabricante: str = None, 
        so: str = None, 
        numero_serie: str = None, 
        ubicacion: str = None, 
        estado: EstadoMaterial = EstadoMaterial.DISPONIBLE
    ):
        super().__init__(codigo_id, titulo, ubicacion=ubicacion, estado=estado)
        self._tipo_dispositivo = tipo_dispositivo
        self.fabricante = fabricante
        self.so = so
        self.numero_serie = numero_serie

    @property
    def tipo_dispositivo(self) -> TipoDispositivo:
        """Devuelve la categoría del equipo informático."""
        return self._tipo_dispositivo

    @property
    def fabricante(self) -> str:
        """Devuelve la marca o creador del dispositivo."""
        return self._fabricante
    
    @fabricante.setter
    def fabricante(self, nuevo_fabricante: str):
        """Asigna el fabricante validando que sea una cadena de texto."""
        if nuevo_fabricante != None:
            if type(nuevo_fabricante) != str:
                raise ValueError("Formato no válido.")
            
            self._fabricante = nuevo_fabricante.strip()
        else:
            self._fabricante = None

    @property
    def so(self) -> str:
        """Devuelve el Sistema Operativo del dispositivo (ej. Windows 11)."""
        return self._so
    
    @so.setter
    def so(self, nuevo_so: str):
        """Asigna el Sistema Operativo validando que sea un texto."""
        if nuevo_so != None:
            if type(nuevo_so) != str:
                raise ValueError("Formato no válido.")
            
            self._so = nuevo_so.strip()
        else:
            self._so = None

    @property
    def numero_serie(self) -> str:
        """Devuelve el número de serie físico del fabricante."""
        return self._numero_serie

    @numero_serie.setter
    def numero_serie(self, nuevo_numero_serie: str):
        """Establece el número de serie para auditorías físicas."""
        if nuevo_numero_serie != None:
            if type(nuevo_numero_serie) != str:
                raise ValueError("Formato no válido.")
            
            self._numero_serie = nuevo_numero_serie.strip()
        else:
            self._numero_serie = None

    def descripcion_corta(self) -> str:
        """Genera el resumen de información técnica para interfaces gráficas."""
        fabricante_str = self._fabricante if self._fabricante else "desconocido"
        so_str = self._so if self._so else "desconocido"
        
        return (
            f"[{self.codigo_id}] {self.tipo_dispositivo.value}: {self.titulo} - "
            f"Fabricante: {fabricante_str} - SO: ({so_str}) - Estado: {self.estado.value}"
        )


class JuegoDeMesa(MaterialFisico):  
    """Materiales de ocio que no se consideran componentes tecnológicos ni lectura tradicional."""
    def __init__(
        self, 
        codigo_id: str, 
        titulo: str, 
        editorial: str = None, 
        min_jugadores: int = None, 
        max_jugadores: int = None, 
        ubicacion: str = None, 
        estado: EstadoMaterial = EstadoMaterial.DISPONIBLE
    ): 
        super().__init__(codigo_id, titulo, ubicacion=ubicacion, estado=estado)
        self.editorial = editorial
        self._min_jugadores = None 
        self._max_jugadores = None
        self.min_jugadores = min_jugadores
        self.max_jugadores = max_jugadores

    @property
    def editorial(self) -> str:
        """Devuelve la editorial responsable de publicar el juego."""
        return self._editorial 
    
    @editorial.setter
    def editorial(self, nueva_editorial: str):
        """Establece y valida el nombre de la editorial."""
        if nueva_editorial != None:
            if type(nueva_editorial) != str:
                raise ValueError("Formato no válido.")
            
            self._editorial = nueva_editorial.strip()
        else:
            self._editorial = None

    @property
    def min_jugadores(self) -> int:
        """Devuelve la cantidad mínima de personas requeridas para jugar."""
        return self._min_jugadores 

    @min_jugadores.setter
    def min_jugadores(self, nuevos_min_jugadores: int):
        """Valida que el número de jugadores mínimo sea lógico y no choque con el máximo."""
        if nuevos_min_jugadores != None:
            if type(nuevos_min_jugadores) != int:
                raise ValueError("Formato no válido.")
            
            if nuevos_min_jugadores < 0:
                raise ValueError("Debe ser un entero positivo.")
            
            if self._max_jugadores != None:
                if nuevos_min_jugadores > self._max_jugadores:
                    raise ValueError("Mínimo no puede ser mayor que el máximo.")  
                
            self._min_jugadores = nuevos_min_jugadores
        else:
            self._min_jugadores = None

    @property
    def max_jugadores(self) -> int:
        """Devuelve el límite máximo de jugadores que admite el juego."""
        return self._max_jugadores 

    @max_jugadores.setter
    def max_jugadores(self, nuevos_max_jugadores: int):
        """Valida que el máximo de jugadores no sea inferior al mínimo estipulado."""
        if nuevos_max_jugadores != None:
            if type(nuevos_max_jugadores) != int:
                raise ValueError("Formato no válido.")
            
            if nuevos_max_jugadores < 0:
                raise ValueError("Debe ser un entero positivo.")
            
            if self._min_jugadores != None:
                if nuevos_max_jugadores < self._min_jugadores:
                    raise ValueError("Máximo no puede ser menor que el mínimo.")
                
            self._max_jugadores = nuevos_max_jugadores
        else:
            self._max_jugadores = None

    def descripcion_corta(self) -> str:
        """Crea el resumen del juego mostrando su rango de jugadores posibles."""
        editorial_str = self._editorial if self._editorial else "Editorial desconocida"
        jugadores_str = "desconocido"
        
        if self._min_jugadores and self._max_jugadores:
            jugadores_str = f"{self._min_jugadores}-{self._max_jugadores}"
        elif self._min_jugadores:
            jugadores_str = f"mín {self._min_jugadores}"
        elif self._max_jugadores:
            jugadores_str = f"máx {self._max_jugadores}"
            
        return (
            f"[{self.codigo_id}] Juego: '{self.titulo}', de {editorial_str} - "
            f"Jugadores: {jugadores_str} - Estado: {self.estado.value}"
        )


class RecursoDigital(Material):
    """
    Elementos virtuales accesibles mediante licencias concurrentes.
    Su estado general depende de la disponibilidad matemática de sus licencias.
    """
    def __init__(
        self, 
        codigo_id: str, 
        titulo: str, 
        url: str = None, 
        licencias_totales: int = 1, 
        estado: EstadoMaterial = EstadoMaterial.DISPONIBLE
    ):
        super().__init__(codigo_id, titulo, estado=estado)
        self.url = url
        self._licencias_disponibles = 0
        self._licencias_totales = 0
        self.licencias_totales = licencias_totales

    @property
    def url(self) -> str:
        """Devuelve el enlace web de acceso al recurso digital."""
        return self._url 
    
    @url.setter
    def url(self, nueva_url: str):
        """Establece la dirección web del recurso."""
        if nueva_url != None:
            if type(nueva_url) != str:
                raise ValueError("Formato no válido.")
            
            self._url = nueva_url.strip()
        else:
            self._url = None

    @property
    def licencias_totales(self) -> int:
        """Devuelve el número total de copias digitales adquiridas por la biblioteca."""
        return self._licencias_totales
    
    @licencias_totales.setter
    def licencias_totales(self, nuevas_licencias: int):
        """
        Ajusta el total de licencias disponibles protegiendo matemáticamente 
        las que ya están prestadas para evitar conteos negativos.
        """
        if type(nuevas_licencias) != int or nuevas_licencias < 0:
            raise ValueError("Debe ser un entero mayor o igual a 0.")
        
        diferencia = nuevas_licencias - self._licencias_totales
        
        if diferencia < 0 and abs(diferencia) > self._licencias_disponibles: 
            raise ValueError("No puedes retirar licencias en uso.") 
        
        self._licencias_totales = nuevas_licencias
        self._licencias_disponibles += diferencia
        self.actualizar_estado()
    
    @property
    def licencias_disponibles(self) -> int:
        """Devuelve las licencias libres para ser prestadas en este momento."""
        return self._licencias_disponibles

    def actualizar_estado(self):
        """Recalcula el estado general respetando si un bibliotecario lo ha bloqueado."""
        if self._estado == EstadoMaterial.BLOQUEADO:
            return  # Cortamos la función para no machacar la decisión del bibliotecario

        if self._licencias_totales == 0:
            self._estado = EstadoMaterial.NO_DISPONIBLE
        elif self._licencias_disponibles <= 0:
            self._estado = EstadoMaterial.PRESTADO
        else:
            self._estado = EstadoMaterial.DISPONIBLE

    def puede_prestarse(self) -> bool:
        """Comprueba que queden copias libres y que no haya sido bloqueado manualmente."""
        if self._estado == EstadoMaterial.BLOQUEADO:
            return False
            
        if self._licencias_disponibles > 0 and self._estado != EstadoMaterial.NO_DISPONIBLE:
            return True
        return False

    def prestar(self) -> bool:
        """Resta una licencia de disponibilidad y recalcula el estado general."""
        if self.puede_prestarse():
            self._licencias_disponibles -= 1
            self.actualizar_estado()
            return True
        return False

    def puede_devolverse(self) -> bool:
        """Verifica que el sistema no intente devolver copias que nunca se prestaron."""
        return self._licencias_disponibles < self._licencias_totales

    def devolver(self) -> bool:
        """Suma una licencia al pool de disponibilidad y recalcula el estado general."""
        if self.puede_devolverse():
            self._licencias_disponibles += 1
            self.actualizar_estado()
            return True
        return False

    def anadir_licencias(self, cantidad: int) -> bool:
        """Wrapper matemático que delega en el setter de licencias totales para incrementar."""
        if type(cantidad) != int or cantidad <= 0:
            raise ValueError("Debe ser un entero positivo.")
        self.licencias_totales += cantidad
        return True
    
    def retirar_licencias(self, cantidad: int) -> bool:
        """Wrapper matemático que delega en el setter para reducir licencias de forma segura."""
        if type(cantidad) != int or cantidad <= 0:
            raise ValueError("Debe ser un entero positivo.")
        
        self.licencias_totales -= cantidad
        return True

    def descripcion_corta(self) -> str:
        """Resumen textual orientado a control de stocks de licencias."""
        return (
            f"[{self.codigo_id}] Digital: '{self.titulo}' - "
            f"Licencias libres: {self._licencias_disponibles}/{self._licencias_totales} "
            f"- Estado: {self.estado.value}"
        )


# ==========================================
# USUARIOS
# ==========================================

class Usuario(ABC):
    """
    Representación general de cualquier persona registrada en la biblioteca.
    Obliga a implementar un resumen corto para listados.
    """
    def __init__(
        self, 
        id_usuario: str, 
        nombre: str, 
        apellidos: str, 
        email: str
    ):
        self._id_usuario = id_usuario
        self.nombre = nombre
        self.apellidos = apellidos
        self.email = email

    @property
    def id_usuario(self) -> str:
        """Devuelve la clave primaria inmutable del usuario."""
        return self._id_usuario
    
    @property
    def nombre(self) -> str:
        """Devuelve el nombre de pila del usuario."""
        return self._nombre
    
    @nombre.setter
    def nombre(self, nuevo_nombre: str):
        """Establece el nombre asegurando que el texto no esté vacío."""
        if not nuevo_nombre or type(nuevo_nombre) != str:
            raise ValueError("El nombre debe ser un texto válido.")
        
        self._nombre = nuevo_nombre.strip()
    
    @property
    def apellidos(self) -> str:
        """Devuelve los apellidos familiares del usuario."""
        return self._apellidos
    
    @apellidos.setter
    def apellidos(self, nuevos_apellidos: str):
        """Valida que los apellidos tengan contenido y formato correcto."""
        if not nuevos_apellidos or type(nuevos_apellidos) != str:
            raise ValueError("Introduce apellidos válidos.")
        
        self._apellidos = nuevos_apellidos.strip()

    @property
    def email(self) -> str:
        """Devuelve el correo de contacto para avisos de la biblioteca."""
        return self._email
    
    @email.setter
    def email(self, nuevo_email: str):
        """Valida rigurosamente la presencia de arroba y un dominio en el correo."""
        if not nuevo_email or type(nuevo_email) != str:
            raise ValueError("El email no puede estar vacío.")
        
        nuevo_email = nuevo_email.strip()
        trozos = nuevo_email.split("@")
        
        if len(trozos) != 2 or "." not in trozos[1]:
            raise ValueError("Formato de email no válido.")
        
        self._email = nuevo_email

    @abstractmethod
    def descripcion_corta(self) -> str: 
        """Genera el identificador textual para componentes visuales."""
        pass
    
class Socio(Usuario):
    """
    Cliente habitual de la biblioteca con capacidad de efectuar préstamos.
    Sujeto a límites de préstamos simultáneos y sistema de sanciones.
    """
    def __init__(
        self, 
        id_usuario: str, 
        nombre: str, 
        apellidos: str, 
        email: str, 
        sancionado: bool = False, 
        prestamos_activos: int = 0, 
        max_prestamos: int = ConfiguracionBiblioteca.MAX_PRESTAMOS, 
        max_especial: bool = False
    ):
        super().__init__(id_usuario, nombre, apellidos, email)
        self._sancionado = sancionado
        self._prestamos_activos = prestamos_activos 
        self._max_prestamos = max_prestamos 
        self._max_especial = max_especial 

    @property
    def sancionado(self) -> bool:
        """Indica si el usuario tiene prohibido realizar retiros por multas pendientes."""
        return self._sancionado
    
    @property
    def prestamos_activos(self) -> int:
        """Devuelve el recuento de materiales que el usuario tiene físicamente ahora mismo."""
        return self._prestamos_activos

    @property
    def max_prestamos(self) -> int:
        """Devuelve el cupo total, ya sea el configurado por la biblioteca o uno personalizado."""
        if self.max_especial:
            return self._max_prestamos
        
        return ConfiguracionBiblioteca.MAX_PRESTAMOS
    
    @max_prestamos.setter
    def max_prestamos(self, nuevo_max: int):
        """Modifica el cupo siempre y cuando se haya activado el permiso especial del socio."""
        if not self.max_especial:
            raise ValueError("Este usuario no tiene un máximo personalizado habilitado.")
        
        if type(nuevo_max) != int:
            raise ValueError("El máximo debe ser un entero.")
        
        self._max_prestamos = nuevo_max
    
    @property
    def max_especial(self) -> bool:
        """Indica si el socio goza de privilegios VIP/Investigador en cuanto a límites."""
        return self._max_especial
        
    @property
    def puede_prestar(self) -> bool:
        """Verifica si el historial disciplinario y el cupo permiten darle más libros."""
        if self._sancionado or (self._prestamos_activos >= self.max_prestamos):
            return False
        
        return True

    def incrementar_prestamos(self) -> bool:
        """Registra internamente que el socio se ha llevado un material más."""
        if self.puede_prestar:
            self._prestamos_activos += 1
            return True
        
        return False
    
    def reducir_prestamos(self) -> bool:
        """Registra internamente la liberación del cupo del socio al devolver algo."""
        if self._prestamos_activos > 0:
            self._prestamos_activos -= 1
            return True
        
        return False
    
    def permitir_cambio_max(self): 
        """Concede o revoca la capacidad de ignorar el límite general de la biblioteca."""
        if self.max_especial:
            self._max_especial = False
            self._max_prestamos = ConfiguracionBiblioteca.MAX_PRESTAMOS 
        else:
            self._max_especial = True

    def cambiar_sancionar(self):
        """Inmuta el estado del usuario bloqueándolo o indultándolo de sus faltas."""
        self._sancionado = not self._sancionado

    def descripcion_corta(self) -> str:
        """Genera una tarjeta rápida con el estatus administrativo del socio."""
        estado = "sancionado" if self.sancionado else "activo"
        return (
            f"[{self.id_usuario}] {self.nombre} {self.apellidos} - "
            f"Socio {estado}"
        )


class Empleado(Usuario):
    """
    Personal del sistema encargado de gestionar materiales e interacciones.
    Posee niveles de acceso en función de su rol contractual.
    """
    def __init__(
        self, 
        id_usuario: str, 
        nombre: str, 
        apellidos: str, 
        email: str, 
        rol: RolEmpleado = RolEmpleado.AUXILIAR
    ):
        super().__init__(id_usuario, nombre, apellidos, email)
        self._rol = rol
    
    @property
    def rol(self) -> RolEmpleado:
        """Devuelve el cargo administrativo de este trabajador."""
        return self._rol
    
    @rol.setter
    def rol(self, nuevo_rol: RolEmpleado):
        """Asigna el cargo obligando a que provenga del enumerador de roles validos."""
        if type(nuevo_rol) != RolEmpleado:
            raise ValueError("Rol no válido.")
        
        self._rol = nuevo_rol

    def es_admin(self) -> bool:
        """Verifica el permiso más alto, para operaciones destructivas del sistema."""
        return self._rol == RolEmpleado.ADMIN
    
    def es_bibliotecario_o_superior(self) -> bool:
        """Verifica permisos de gestión media, como bloquear libros o editar usuarios."""
        return self._rol in [RolEmpleado.ADMIN, RolEmpleado.BIBLIOTECARIO]
        
    def descripcion_corta(self) -> str:
        """Retorna los datos clave del empleado y su categoría profesional."""
        return f"[{self.id_usuario}] {self.nombre} {self.apellidos} · {self.rol.value}"


# ==========================================
# TRANSACCIONES
# ==========================================

class Prestamo:
    """
    Representa el contrato vinculante e inmutable entre un socio y el catálogo en el tiempo.
    Calcula fechas automáticamente y aplica sanciones en devoluciones tardías.
    """
    def __init__(
        self, 
        id_prestamo: str, 
        usuario: Usuario, 
        material: Material, 
        dias_prestamo: int = None
    ):
        if not id_prestamo or type(id_prestamo) != str:
            raise ValueError("El ID del préstamo debe ser un texto válido.")
        
        self._id_prestamo = id_prestamo.strip()
        self._usuario = usuario
        self._material = material
        self._fecha_prestamo = datetime.now() 
        
        if dias_prestamo is None:
            if isinstance(material, Dispositivo):
                dias_prestamo = ConfiguracionBiblioteca.TIEMPO_PRESTAMO_DISPOSITIVOS
            elif isinstance(material, JuegoDeMesa):
                dias_prestamo = ConfiguracionBiblioteca.TIEMPO_PRESTAMO_JUEGOS_MESA
            else:
                dias_prestamo = ConfiguracionBiblioteca.TIEMPO_PRESTAMO_DEFECTO

        if type(dias_prestamo) != int or dias_prestamo <= 0:
            raise ValueError("Debe ser un número entero positivo.")

        fecha_base = self._fecha_prestamo + timedelta(days=dias_prestamo)
        self._fecha_devolucion_prevista = fecha_base.replace(
            hour=23, 
            minute=59, 
            second=59, 
            microsecond=0
        )
        
        self._fecha_devolucion_real = None
        self._estado = EstadoPrestamo.ACTIVO

    @property
    def id_prestamo(self) -> str:
        """Devuelve el ticket de registro inmutable que identifica este préstamo en BBDD."""
        return self._id_prestamo

    @property
    def usuario(self) -> Usuario:
        """Devuelve la referencia al objeto del usuario responsable de este contrato."""
        return self._usuario

    @property
    def material(self) -> Material:
        """Devuelve la referencia al objeto del libro/dispositivo adjudicado en esta sesión."""
        return self._material

    @property
    def fecha_prestamo(self) -> datetime:
        """Devuelve la fecha y el instante exacto en el que se firmó la retirada del material."""
        return self._fecha_prestamo

    @property
    def fecha_devolucion_prevista(self) -> datetime:
        """Devuelve la frontera temporal de gracia (hasta fin de día) que se acordó al inicio."""
        return self._fecha_devolucion_prevista

    @property
    def fecha_devolucion_real(self) -> datetime:
        """Devuelve la estampa temporal en la que el usuario físico retorna el objeto al mostrador."""
        return self._fecha_devolucion_real

    @property
    def estado(self) -> EstadoPrestamo:
        """Indica si el contrato sigue vivo, expiró en tiempo, o fue saldado correctamente."""
        return self._estado

    def actualizar_estado(self) -> bool:
        """Analiza proactivamente si se ha agotado el tiempo para rotar el ticket a RETRASADO."""
        if self._estado == EstadoPrestamo.ACTIVO:
            if datetime.now() > self._fecha_devolucion_prevista:
                self._estado = EstadoPrestamo.RETRASADO
                return True
            
        return False

    def puede_finalizarse(self) -> bool:
        """Previene que un préstamo previamente cerrado intente ejecutarse por duplicado."""
        return self._estado != EstadoPrestamo.DEVUELTO

    def finalizar_prestamo(self) -> bool:
        """
        Registra la recepción física del objeto prestado. 
        Manda la orden de multa si la línea de tiempo excede el margen previsto.
        """
        if not self.puede_finalizarse():
            return False 
            
        self._fecha_devolucion_real = datetime.now()
        entregado_tarde = self._fecha_devolucion_real > self._fecha_devolucion_prevista
        
        if entregado_tarde and isinstance(self._usuario, Socio):
            if self._usuario.sancionado is False: 
                self._usuario.cambiar_sancionar() 
            
        self._estado = EstadoPrestamo.DEVUELTO
        return True

    def extender_prestamo(self, dias_extra: int) -> bool:
        """
        Desplaza la fecha acordada de entrega para renovar el ticket.
        El sistema exige que el usuario esté al día de las reglas para admitir esto.
        """
        self.actualizar_estado() 
        
        if self._estado != EstadoPrestamo.ACTIVO:
            raise ValueError("No se puede renovar un préstamo cerrado o con retraso.")
        
        if type(dias_extra) != int or dias_extra <= 0:
            raise ValueError("Debe ser un número positivo.")
        
        self._fecha_devolucion_prevista += timedelta(days=dias_extra)
        return True

    def resumen(self) -> str:
        """Crea una vista simplificada en modo texto orientada al usuario y bibliotecario."""
        self.actualizar_estado() 
        fecha_p = self._fecha_prestamo.strftime("%d/%m/%Y")
        fecha_d = self._fecha_devolucion_prevista.strftime("%d/%m/%Y")
        
        return (
            f"[{self._id_prestamo}] {self._material.titulo} prestado a "
            f"{self._usuario.nombre} ({fecha_p} -> {fecha_d}) | Estado: {self._estado.value}"
        )
