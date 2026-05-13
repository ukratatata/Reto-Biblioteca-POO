"""
controllers.py

Capa de Control (Controlador) según el patrón MVC.
Actúa como intermediario entre la Interfaz Gráfica (Tkinter) y la Base de Datos.
Aplica las reglas de negocio asegurando que todo se actualice de forma coherente.
"""

import uuid
import threading
from typing import Callable, List, Tuple

from biblioteca.models import Usuario, Material, Prestamo, Reserva, Socio, MaterialFisico
from biblioteca.db import BibliotecaRepository


class BibliotecaController:
    """
    Controlador central del sistema.
    Expone las operaciones de alto nivel que la interfaz gráfica necesitará ejecutar.
    """
    
    def __init__(self, repositorio: BibliotecaRepository, callback_expiracion: Callable = None):
        """
        callback_expiracion: función opcional que la UI puede pasar para recibir aviso
        cuando el temporizador expire reservas en segundo plano. Se llama con la lista
        de IDs expirados, por ejemplo para refrescar la tabla de reservas en pantalla.
        """
        self.repo = repositorio
        self._callback_expiracion = callback_expiracion
        self._temporizador = None   # Guardamos referencia para poder pararlo limpiamente

        # Primera pasada inmediata al arrancar (cubre reservas que expiraron con la app cerrada)
        self.liberar_reservas_expiradas()

        # Arrancamos el ciclo de comprobación periódica en segundo plano
        self._iniciar_temporizador()

    # ==========================================
    # 0. TEMPORIZADOR DE RESERVAS
    # ==========================================

    def _iniciar_temporizador(self):
        """
        Programa la siguiente comprobación de reservas expiradas.
        Usa threading.Timer para no bloquear el hilo principal de la UI.
        El intervalo de revisión es de 5 minutos; suficiente precisión sin sobrecargar.
        """
        INTERVALO_SEGUNDOS = 5 * 60     # Revisamos cada 5 minutos

        # daemon=True hace que el hilo muera solo si se cierra la aplicación principal
        self._temporizador = threading.Timer(INTERVALO_SEGUNDOS, self._ciclo_temporizador)
        self._temporizador.daemon = True
        self._temporizador.start()

    def _ciclo_temporizador(self):
        """
        Función que ejecuta el Timer: libera lo que haya expirado y se reprograma a sí mismo.
        Al ser llamada desde un hilo secundario, no toca la UI directamente;
        si hay callback, la UI decide qué hacer con los IDs expirados de forma segura.
        """
        expiradas = self.liberar_reservas_expiradas()

        # Si la UI registró un callback y realmente hubo expiraciones, la avisamos
        if self._callback_expiracion and expiradas:
            self._callback_expiracion(expiradas)

        # Nos reprogramamos para la siguiente vuelta
        self._iniciar_temporizador()

    def detener_temporizador(self):
        """
        Para el temporizador de fondo de forma limpia.
        Llamar desde la ventana principal al cerrar la aplicación (evento on_close / destroy).
        """
        if self._temporizador is not None:
            self._temporizador.cancel()
            self._temporizador = None

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

    # ==========================================
    # 3. RESERVAS Y RECOGIDAS
    # ==========================================

    def realizar_reserva(
        self,
        id_usuario: str,
        codigo_material: str
    ) -> Tuple[bool, str]:
        """
        Aparta un material físico para que el socio venga a recogerlo.
        El material queda bloqueado con estado PENDIENTE_RECOGIDA hasta que el socio llegue
        o hasta que expire el plazo configurado en ConfiguracionBiblioteca.

        Retorna:
            - (True, "Mensaje de éxito") si el apartado se creó correctamente.
            - (False, "Mensaje de error") si algo lo impidió.
        """
        usuario = self.buscar_usuario(id_usuario)
        material = self.buscar_material(codigo_material)

        if usuario is None:
            return False, "Error: El usuario indicado no existe en el sistema."

        if material is None:
            return False, "Error: El material indicado no existe en el catálogo."

        # Las reservas solo tienen sentido para materiales físicos;
        # los recursos digitales no necesitan recogida presencial
        if not isinstance(material, MaterialFisico):
            return False, "Error: Las reservas solo aplican a materiales físicos."

        if not isinstance(usuario, Socio):
            return False, "Error: Solo los socios pueden realizar reservas."

        if not usuario.puede_prestar:
            return False, "Error: El socio tiene el cupo lleno o está sancionado."

        if not material.puede_reservarse():
            return False, f"Error: '{material.titulo}' no está disponible para reservar."

        # Apartamos el material y contabilizamos el cupo del socio
        material.reservar_recogida()
        usuario.incrementar_prestamos()

        # Generamos un ID único para la reserva con prefijo R (de Reserva)
        while True:
            nuevo_id_reserva = f"R-{uuid.uuid4().hex[:8].upper()}"
            if self.repo.obtener_reserva(nuevo_id_reserva) is None:
                break

        nueva_reserva = Reserva(
            id_reserva=nuevo_id_reserva,
            usuario=usuario,
            material=material
        )

        self.repo.guardar_material(material)
        self.repo.guardar_usuario(usuario)
        self.repo.guardar_reserva(nueva_reserva)

        return True, f"¡Éxito! Reserva '{nuevo_id_reserva}' creada. El socio tiene 48h para recoger."

    def procesar_recogida(
        self,
        id_reserva: str,
        dias_prestamo: int = None
    ) -> Tuple[bool, str]:
        """
        Formaliza la llegada del socio al mostrador para recoger su material apartado.
        Cierra la reserva y genera el Préstamo definitivo con su fecha de devolución.

        Retorna:
            - (True, "Mensaje de éxito") con el ID del préstamo creado.
            - (False, "Mensaje de error") si el plazo expiró o la reserva no es válida.
        """
        if not id_reserva:
            return False, "Error: Debe proporcionar un ID de reserva válido."

        reserva = self.repo.obtener_reserva(id_reserva.strip())

        if reserva is None:
            return False, "Error: No se encontró ninguna reserva con ese ID."

        # Comprobamos si el socio llegó dentro del plazo
        if not reserva.puede_recogerse():
            # Si expiró en este preciso momento, lo gestionamos aquí mismo
            if reserva.ha_expirado():
                self._expirar_reserva(reserva)
                return False, "Error: El plazo de recogida ha expirado. El material ya está libre."
            return False, "Error: La reserva no está activa."

        usuario = reserva.usuario
        material = reserva.material

        # Marcamos la reserva como completada y pasamos el material a PRESTADO
        reserva.marcar_recogida()
        material.recoger()    # recoger() cambia de PENDIENTE_RECOGIDA a PRESTADO

        # El cupo ya estaba contabilizado al crear la reserva, así que no lo tocamos

        # Generamos el ID del préstamo definitivo
        while True:
            nuevo_id_prestamo = f"P-{uuid.uuid4().hex[:8].upper()}"
            if self.repo.obtener_prestamo(nuevo_id_prestamo) is None:
                break

        nuevo_prestamo = Prestamo(
            id_prestamo=nuevo_id_prestamo,
            usuario=usuario,
            material=material,
            dias_prestamo=dias_prestamo
        )

        self.repo.guardar_reserva(reserva)
        self.repo.guardar_material(material)
        self.repo.guardar_prestamo(nuevo_prestamo)

        return True, f"¡Éxito! Préstamo '{nuevo_id_prestamo}' creado al recoger la reserva '{id_reserva}'."

    def liberar_reservas_expiradas(self) -> List[str]:
        """
        Revisa todas las reservas activas y libera las que han superado su plazo de recogida.
        Se llama automáticamente al iniciar el controlador.
        Devuelve la lista de IDs de reservas que se han expirado en esta pasada.
        """
        reservas_activas = self.repo.obtener_reservas_activas()
        expiradas = []

        for reserva in reservas_activas:
            if reserva.ha_expirado():
                self._expirar_reserva(reserva)
                expiradas.append(reserva.id_reserva)

        return expiradas

    def _expirar_reserva(self, reserva: Reserva):
        """
        Método interno que ejecuta la liberación de una reserva expirada.
        Restaura el material a DISPONIBLE y devuelve el cupo al socio sin sancionarlo.
        No se llama directamente desde la interfaz; úsarlo desde el controlador.
        """
        usuario = reserva.usuario
        material = reserva.material

        reserva.expirar()
        material.devolver()    # devolver() en MaterialFisico lo pone de vuelta a DISPONIBLE

        if isinstance(usuario, Socio):
            usuario.reducir_prestamos()    # Devolvemos el cupo sin penalizar

        self.repo.guardar_reserva(reserva)
        self.repo.guardar_material(material)
        self.repo.guardar_usuario(usuario)