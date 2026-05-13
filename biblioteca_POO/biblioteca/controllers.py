"""
controllers.py

Capa de Control (Controlador) según el patrón MVC.
Actúa como intermediario entre la Interfaz Gráfica (Tkinter) y la Base de Datos.
Aplica las reglas de negocio asegurando que todo se actualice de forma coherente.
"""

import uuid
from typing import Tuple

from biblioteca.models import Usuario, Material, Prestamo, Socio
from biblioteca.db import BibliotecaRepository


class BibliotecaController:
    """
    Controlador central del sistema.
    Expone las operaciones de alto nivel que la interfaz gráfica necesitará ejecutar.
    """
    
    def __init__(self, repositorio: BibliotecaRepository):
        # Inyectamos el repositorio para que el controlador pueda hablar con SQLite
        self.repo = repositorio

    # ==========================================
    # 1. BÚSQUEDA Y LECTURA
    # ==========================================

    def buscar_usuario(self, id_usuario: str) -> Usuario:
        """
        Busca un usuario por su identificador exacto.
        Devuelve el objeto Usuario o None si no existe.
        """
        if not id_usuario:
            return None
            
        return self.repo.obtener_usuario(id_usuario.strip())

    def buscar_material(self, codigo_material: str) -> Material:
        """
        Busca un material en el catálogo por su código único.
        Devuelve el objeto Material o None si no existe.
        """
        if not codigo_material:
            return None
            
        return self.repo.obtener_material(codigo_material.strip())

    # ==========================================
    # 2. OPERACIONES TRANSACCIONALES
    # ==========================================

    def realizar_prestamo(
        self, 
        id_usuario: str, 
        codigo_material: str, 
        dias_prestamo: int = None
    ) -> Tuple[bool, str]:
        """
        Orquesta todo el proceso de prestar un material a un usuario.
        Comprueba las reglas de negocio, actualiza los estados y guarda en base de datos.
        
        Retorna:
            - (True, "Mensaje de éxito") si todo salió bien.
            - (False, "Mensaje de error") si alguna regla de negocio lo impidió.
        """
        # 1. Recuperamos los objetos vivos desde la base de datos
        usuario = self.buscar_usuario(id_usuario)
        material = self.buscar_material(codigo_material)
        
        # 2. Comprobaciones de seguridad básicas
        if usuario is None:
            return False, "Error: El usuario indicado no existe en el sistema."
            
        if material is None:
            return False, "Error: El material indicado no existe en el catálogo."
            
        # 3. Aplicamos las Preguntas CQS de nuestros Modelos
        # Solo los Socios tienen la restricción de cupos y sanciones
        if isinstance(usuario, Socio):
            if not usuario.puede_prestar:
                return False, "Error: El usuario ha superado su límite de préstamos o está sancionado."
                
        if not material.puede_prestarse():
            return False, f"Error: El material '{material.titulo}' no está disponible para préstamo."

        # 4. Si pasamos los controles, ejecutamos las Acciones CQS
        material.prestar()
        
        if isinstance(usuario, Socio):
            usuario.incrementar_prestamos()
            
        # Generamos un ID corto y seguro mediante un bucle anti-colisiones
        while True:
            nuevo_id_prestamo = f"P-{uuid.uuid4().hex[:8].upper()}"     # Al ser prestamo, empieza por P
            
            # Comprobamos si este id ya existe en la base de datos
            # (Si el repositorio nos devuelve None, significa que está libre)
            if self.repo.obtener_prestamo(nuevo_id_prestamo) is None:
                break # ¡Está libre! Rompemos el bucle y seguimos
        
        nuevo_prestamo = Prestamo(
            id_prestamo=nuevo_id_prestamo,
            usuario=usuario,
            material=material,
            dias_prestamo=dias_prestamo
        )
        
        # 5. Guardamos absolutamente todo en la base de datos para no perder coherencia
        self.repo.guardar_material(material)
        self.repo.guardar_usuario(usuario)
        self.repo.guardar_prestamo(nuevo_prestamo)
        
        return True, f"¡Éxito! Préstamo '{nuevo_id_prestamo}' registrado correctamente."

    def procesar_devolucion(
        self, 
        id_prestamo: str
    ) -> Tuple[bool, str]:
        """
        Registra el retorno de un material al catálogo, cierra el préstamo
        y libera el cupo del usuario, aplicando sanciones si corresponde.
        """
        if not id_prestamo:
            return False, "Error: Debe proporcionar un ID de préstamo válido."
            
        # 1. Recuperamos el préstamo (que por dentro ya trae a su Usuario y Material)
        prestamo = self.repo.obtener_prestamo(id_prestamo.strip())
        
        if prestamo is None:
            return False, "Error: No se ha encontrado el registro del préstamo."
            
        # 2. Comprobamos si ya estaba devuelto usando CQS
        if not prestamo.puede_finalizarse():
            return False, "Aviso: Este préstamo ya consta como devuelto en el sistema."
            
        # 3. Extraemos al usuario y al material implicados
        usuario = prestamo.usuario
        material = prestamo.material
        
        # 4. Ejecutamos las Acciones CQS
        # Finalizar el préstamo comprueba automáticamente si hay retrasos y sanciona si es necesario
        prestamo.finalizar_prestamo() 
        material.devolver()
        
        if isinstance(usuario, Socio):
            usuario.reducir_prestamos()
            
        # 5. Guardamos todos los cambios sincronizados en SQLite
        self.repo.guardar_prestamo(prestamo)
        self.repo.guardar_material(material)
        self.repo.guardar_usuario(usuario)
        
        # Comprobamos si hubo sanción para avisar al bibliotecario por pantalla
        if isinstance(usuario, Socio) and usuario.sancionado:
            return True, "Devolución registrada. ATENCIÓN: El socio ha sido sancionado por retraso."
            
        return True, "Devolución registrada correctamente. Material libre."