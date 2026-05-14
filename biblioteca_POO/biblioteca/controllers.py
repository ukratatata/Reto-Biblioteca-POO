"""
controllers.py

Capa de Control (Controlador) según el patrón MVC.
Actúa como intermediario entre la Interfaz Gráfica (Tkinter) y la Base de Datos.
Aplica las reglas de negocio asegurando que todo se actualice de forma coherente.
"""

import uuid
import threading
from typing import Callable, List, Optional, Tuple

from biblioteca.models import (
    Usuario, Material, Prestamo, Reserva, Socio, Empleado, MaterialFisico,
    RolEmpleado, EstadoMaterial, ConfiguracionBiblioteca
)
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

        # reprogramamos para la siguiente vuelta
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

        return self.repo.obtener_usuario(id_usuario.strip().upper())

    def buscar_material(self, codigo_material: str) -> Material:
        """
        Busca un material en el catálogo por su código único.
        Devuelve el objeto Material o None si no existe.
        """
        if not codigo_material:
            return None

        return self.repo.obtener_material(codigo_material.strip().upper())

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
        usuario = self.buscar_usuario(id_usuario)
        material = self.buscar_material(codigo_material)

        if usuario is None:
            return False, "Error: El usuario indicado no existe en el sistema."

        if material is None:
            return False, "Error: El material indicado no existe en el catálogo."

        # Solo los Socios tienen la restricción de cupos y sanciones
        if isinstance(usuario, Socio):
            if not usuario.puede_prestar:
                return False, "Error: El usuario ha superado su límite de préstamos o está sancionado."

        if not material.puede_prestarse():
            return False, f"Error: El material '{material.titulo}' no está disponible para préstamo."

        material.prestar()

        if isinstance(usuario, Socio):
            usuario.incrementar_prestamos()

        # Generamos un ID corto y seguro mediante un bucle que crea codigos de baja probabilidad 
        while True: # de repeticion y ademas lo contraresta con la base de datos
            nuevo_id_prestamo = f"P-{uuid.uuid4().hex[:8].upper()}"
            if self.repo.obtener_prestamo(nuevo_id_prestamo) is None:
                break

        nuevo_prestamo = Prestamo(
            id_prestamo=nuevo_id_prestamo,
            usuario=usuario,
            material=material,
            dias_prestamo=dias_prestamo
        )

        self.repo.guardar_material(material)
        self.repo.guardar_usuario(usuario)
        self.repo.guardar_prestamo(nuevo_prestamo)

        return True, f"¡Éxito! Préstamo '{nuevo_id_prestamo}' registrado correctamente."

    def procesar_devolucion(self, id_prestamo: str) -> Tuple[bool, str]:
        """
        Registra el retorno de un material al catálogo, cierra el préstamo
        y libera el cupo del usuario, aplicando sanciones si corresponde.
        """
        if not id_prestamo:
            return False, "Error: Debe proporcionar un ID de préstamo válido."

        prestamo = self.repo.obtener_prestamo(id_prestamo.strip().upper())

        if prestamo is None:
            return False, "Error: No se ha encontrado el registro del préstamo."

        if not prestamo.puede_finalizarse():
            return False, "Aviso: Este préstamo ya consta como devuelto en el sistema."

        usuario = prestamo.usuario
        material = prestamo.material

        prestamo.finalizar_prestamo()
        material.devolver()

        if isinstance(usuario, Socio):
            usuario.reducir_prestamos()

        self.repo.guardar_prestamo(prestamo)
        self.repo.guardar_material(material)
        self.repo.guardar_usuario(usuario)

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
        """
        usuario = self.buscar_usuario(id_usuario)
        material = self.buscar_material(codigo_material)

        if usuario is None:
            return False, "Error: El usuario indicado no existe en el sistema."

        if material is None:
            return False, "Error: El material indicado no existe en el catálogo."

        if not isinstance(material, MaterialFisico):
            return False, "Error: Las reservas solo aplican a materiales físicos."

        if not isinstance(usuario, Socio):
            return False, "Error: Solo los socios pueden realizar reservas."

        if not usuario.puede_prestar:
            return False, "Error: El socio tiene el cupo lleno o está sancionado."

        if not material.puede_reservarse():
            return False, f"Error: '{material.titulo}' no está disponible para reservar."

        material.reservar_recogida()
        usuario.incrementar_prestamos()

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

        horas = ConfiguracionBiblioteca.HORAS_LIMITE_RECOGIDA
        return True, f"¡Éxito! Reserva '{nuevo_id_reserva}' creada. El socio tiene {horas}h para recoger."

    def procesar_recogida(
        self,
        id_reserva: str,
        dias_prestamo: int = None
    ) -> Tuple[bool, str]:
        """
        Formaliza la llegada del socio al mostrador para recoger su material apartado.
        Cierra la reserva y genera el Préstamo definitivo con su fecha de devolución.
        """
        if not id_reserva:
            return False, "Error: Debe proporcionar un ID de reserva válido."

        reserva = self.repo.obtener_reserva(id_reserva.strip().upper())

        if reserva is None:
            return False, "Error: No se encontró ninguna reserva con ese ID."

        if not reserva.puede_recogerse():
            if reserva.ha_expirado():
                self._expirar_reserva(reserva)
                return False, "Error: El plazo de recogida ha expirado. El material ya está libre."
            return False, "Error: La reserva no está activa."

        usuario = reserva.usuario
        material = reserva.material

        reserva.marcar_recogida()
        material.recoger()

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
        """
        usuario = reserva.usuario
        material = reserva.material

        reserva.expirar()
        material.devolver()

        if isinstance(usuario, Socio):
            usuario.reducir_prestamos()

        self.repo.guardar_reserva(reserva)
        self.repo.guardar_material(material)
        self.repo.guardar_usuario(usuario)

    # ==========================================
    # 4. LOGIN Y AUTENTICACIÓN
    # ==========================================

    def login_por_email(
        self,
        email: str,
        password: str
    ) -> Tuple[bool, str, Optional[Usuario]]:
        """
        Intenta autenticar a un usuario por email y contraseña.

        Retorna:
            - (True, "Bienvenido...", objeto_usuario) si las credenciales son correctas.
            - (False, "Mensaje de error", None) si el email no existe o la clave es errónea.
        """
        if not email or not password:
            return False, "Error: Introduce email y contraseña.", None

        usuario = self.repo.obtener_usuario_por_email(email)

        if usuario is None:
            return False, "Error: No existe ninguna cuenta con ese email.", None

        if not usuario.verificar_password(password):
            return False, "Error: Contraseña incorrecta.", None

        return True, f"Bienvenido, {usuario.nombre}.", usuario

    # ==========================================
    # 5. GESTIÓN DE USUARIOS
    # ==========================================

    def crear_socio(
        self,
        nombre: str,
        apellidos: str,
        email: str,
        password: str
    ) -> Tuple[bool, str]:
        """
        Registra un nuevo socio en el sistema con su contraseña inicial.
        El ID se genera automáticamente con el formato US-XXXX.
        """
        if self.repo.obtener_usuario_por_email(email):
            return False, f"Error: El email '{email}' ya está registrado."

        id_usuario = self.repo.siguiente_id_socio()

        nuevo_socio = Socio(
            id_usuario=id_usuario,
            nombre=nombre,
            apellidos=apellidos,
            email=email
        )
        nuevo_socio.establecer_password(password)

        self.repo.guardar_usuario(nuevo_socio)
        return True, f"Socio creado correctamente con ID '{id_usuario}'."

    def crear_empleado(
        self,
        nombre: str,
        apellidos: str,
        email: str,
        password: str,
        rol: RolEmpleado = RolEmpleado.AUXILIAR
    ) -> Tuple[bool, str]:
        """
        Registra un nuevo empleado con ID automático formato UE-XXXX.
        Solo debe llamarse desde el panel de administrador.
        """
        if self.repo.obtener_usuario_por_email(email):
            return False, f"Error: El email '{email}' ya está registrado."

        id_usuario = self.repo.siguiente_id_empleado()

        nuevo_empleado = Empleado(
            id_usuario=id_usuario,
            nombre=nombre,
            apellidos=apellidos,
            email=email,
            rol=rol
        )
        nuevo_empleado.establecer_password(password)

        self.repo.guardar_usuario(nuevo_empleado)
        return True, f"Empleado creado correctamente con ID '{id_usuario}' ({rol.value})."

    def siguiente_id_socio(self) -> str:
        """Devuelve el siguiente ID libre para un socio, para mostrarlo en el formulario."""
        return self.repo.siguiente_id_socio()

    def siguiente_id_empleado(self) -> str:
        """Devuelve el siguiente ID libre para un empleado, para mostrarlo en el formulario."""
        return self.repo.siguiente_id_empleado()

    def modificar_socio(
        self,
        id_usuario: str,
        nombre: str,
        apellidos: str,
        email: str
    ) -> Tuple[bool, str]:
        """Actualiza los datos básicos de un socio existente."""
        usuario = self.buscar_usuario(id_usuario)
        if usuario is None or not isinstance(usuario, Socio):
            return False, "Error: Socio no encontrado."

        existente = self.repo.obtener_usuario_por_email(email)
        if existente and existente.id_usuario != id_usuario:
            return False, f"Error: El email '{email}' ya está registrado en otra cuenta."

        usuario.nombre    = nombre
        usuario.apellidos = apellidos
        usuario.email     = email
        self.repo.guardar_usuario(usuario)
        return True, f"Socio '{id_usuario}' actualizado correctamente."

    def eliminar_socio(self, id_usuario: str) -> Tuple[bool, str]:
        """
        Elimina un socio del sistema de forma permanente.
        Rechaza la operación si el socio tiene préstamos activos.
        """
        usuario = self.buscar_usuario(id_usuario)
        if usuario is None or not isinstance(usuario, Socio):
            return False, "Error: Socio no encontrado."

        if usuario.prestamos_activos > 0:
            return False, "Error: El socio tiene préstamos activos. Devuélvalos antes de eliminar la cuenta."

        self.repo.eliminar_usuario(id_usuario)
        return True, f"Socio '{id_usuario}' eliminado correctamente."

    def modificar_empleado(
        self,
        id_objetivo: str,
        nombre: str,
        apellidos: str,
        email: str,
        rol: RolEmpleado
    ) -> Tuple[bool, str]:
        """
        Actualiza los datos de un empleado existente.
        Solo accesible para administradores; no requiere contraseña actual.
        Comprueba que el nuevo email no esté ya en uso por otra cuenta.
        """
        usuario = self.buscar_usuario(id_objetivo)
        if usuario is None or not isinstance(usuario, Empleado):
            return False, "Error: Empleado no encontrado."

        existente = self.repo.obtener_usuario_por_email(email)
        if existente and existente.id_usuario != id_objetivo:
            return False, f"Error: El email '{email}' ya está registrado en otra cuenta."

        usuario.nombre    = nombre
        usuario.apellidos = apellidos
        usuario.email     = email
        usuario.rol       = rol
        self.repo.guardar_usuario(usuario)
        return True, f"Empleado '{id_objetivo}' actualizado correctamente."

    def resetear_password_admin(
        self,
        id_objetivo: str,
        nueva_password: str
    ) -> Tuple[bool, str]:
        """
        Permite a un administrador resetear la contraseña de cualquier usuario
        sin necesitar conocer la contraseña actual.
        La verificación de que quien llama es admin se hace en la UI.
        """
        usuario = self.buscar_usuario(id_objetivo)
        if usuario is None:
            return False, "Error: El usuario no existe."

        if len(nueva_password) < 6:
            return False, "Error: La contraseña debe tener al menos 6 caracteres."

        usuario.establecer_password(nueva_password)
        self.repo.guardar_usuario(usuario)
        return True, f"Contraseña de '{id_objetivo}' actualizada correctamente."

    def cambiar_rol_empleado(
        self,
        id_usuario: str,
        nuevo_rol: RolEmpleado
    ) -> Tuple[bool, str]:
        """Cambia el rol de un empleado. Solo accesible para administradores."""
        usuario = self.buscar_usuario(id_usuario)

        if usuario is None:
            return False, "Error: El usuario no existe."

        if not isinstance(usuario, Empleado):
            return False, "Error: Solo se puede cambiar el rol de un empleado."

        usuario.rol = nuevo_rol
        self.repo.guardar_usuario(usuario)
        return True, f"Rol de '{id_usuario}' actualizado a {nuevo_rol.value}."

    def cambiar_sancion_socio(self, id_usuario: str) -> Tuple[bool, str]:
        """Alterna la sanción de un socio. Accesible para bibliotecario y superior."""
        usuario = self.buscar_usuario(id_usuario)

        if usuario is None:
            return False, "Error: El usuario no existe."

        if not isinstance(usuario, Socio):
            return False, "Error: Solo se puede sancionar a un socio."

        usuario.cambiar_sancionar()
        accion = "sancionado" if usuario.sancionado else "indultado"
        self.repo.guardar_usuario(usuario)
        return True, f"Socio '{id_usuario}' {accion} correctamente."

    def cambiar_email_usuario(
        self,
        id_usuario: str,
        nuevo_email: str
    ) -> Tuple[bool, str]:
        """
        Permite a cualquier usuario cambiar su propio email desde la UI.
        Comprueba que el nuevo email no esté ya en uso por otra cuenta.
        """
        usuario = self.buscar_usuario(id_usuario)

        if usuario is None:
            return False, "Error: El usuario no existe."

        existente = self.repo.obtener_usuario_por_email(nuevo_email)
        if existente and existente.id_usuario != id_usuario:
            return False, "Error: Ese email ya está registrado en otra cuenta."

        usuario.email = nuevo_email
        self.repo.guardar_usuario(usuario)
        return True, "Email actualizado correctamente."

    def cambiar_password_usuario(
        self,
        id_usuario: str,
        password_actual: str,
        nueva_password: str
    ) -> Tuple[bool, str]:
        """
        Cambia la contraseña de un usuario verificando primero la actual.
        Así no se puede cambiar la clave de otra persona aunque tengas su ID.
        """
        usuario = self.buscar_usuario(id_usuario)

        if usuario is None:
            return False, "Error: El usuario no existe."

        if not usuario.verificar_password(password_actual):
            return False, "Error: La contraseña actual es incorrecta."

        usuario.establecer_password(nueva_password)
        self.repo.guardar_usuario(usuario)
        return True, "Contraseña actualizada correctamente."

    # ==========================================
    # 6. GESTIÓN DE MATERIALES
    # ==========================================

    def siguiente_id_material(self, tipo_material: str) -> str:
        """
        Devuelve el siguiente ID libre para el tipo de material indicado.
        tipo_material: 'Libro' | 'Revista' | 'Dispositivo' | 'JuegoDeMesa' | 'RecursoDigital'
        """
        mapa = {
            "Libro":          self.repo.siguiente_id_libro,
            "Revista":        self.repo.siguiente_id_revista,
            "Dispositivo":    self.repo.siguiente_id_dispositivo,
            "JuegoDeMesa":    self.repo.siguiente_id_juego,
            "RecursoDigital": self.repo.siguiente_id_digital,
        }
        generador = mapa.get(tipo_material)
        if not generador:
            raise ValueError(f"Tipo de material desconocido: {tipo_material}")
        return generador()

    def buscar_materiales(
        self,
        titulo: str = None,
        tipo_material: str = None,
        autor: str = None,
        editorial: str = None,
        isbn: str = None,
        issn: str = None,
        fabricante: str = None,
        ubicacion: str = None,
        estado: str = None,
        solo_disponibles: bool = False
    ) -> List[Material]:
        """
        Búsqueda avanzada de materiales con filtros combinables.
        Cualquier combinación de parámetros es válida; si no se pasa ninguno
        devuelve el catálogo completo.
        """
        return self.repo.buscar_materiales(
            titulo=titulo,
            tipo_material=tipo_material,
            autor=autor,
            editorial=editorial,
            isbn=isbn,
            issn=issn,
            fabricante=fabricante,
            ubicacion=ubicacion,
            estado=estado,
            solo_disponibles=solo_disponibles
        )

    def crear_material(self, material: Material) -> Tuple[bool, str]:
        """
        Añade un nuevo material al catálogo.
        Comprueba que el código no esté ya en uso.
        """
        if self.repo.obtener_material(material.codigo_id):
            return False, f"Error: El código '{material.codigo_id}' ya existe en el catálogo."

        self.repo.guardar_material(material)
        return True, f"Material '{material.codigo_id}' añadido correctamente."

    def modificar_material(self, material: Material) -> Tuple[bool, str]:
        """
        Guarda los cambios realizados sobre un material existente.
        La UI se encarga de construir el objeto modificado antes de llamar a esto.
        """
        if not self.repo.obtener_material(material.codigo_id):
            return False, f"Error: El material '{material.codigo_id}' no existe en el catálogo."

        self.repo.guardar_material(material)
        return True, f"Material '{material.codigo_id}' actualizado correctamente."

    def eliminar_material(self, codigo_id: str) -> Tuple[bool, str]:
        """
        Elimina un material del catálogo de forma permanente.
        Rechaza la operación si el material está en circulación.
        """
        material = self.repo.obtener_material(codigo_id)

        if material is None:
            return False, "Error: El material no existe en el catálogo."

        if material.estado in (EstadoMaterial.PRESTADO, EstadoMaterial.PENDIENTE_RECOGIDA):
            return False, "Error: No se puede eliminar un material que está en circulación."

        self.repo.eliminar_material(codigo_id)
        return True, f"Material '{codigo_id}' eliminado del catálogo."

    # ==========================================
    # 7. LISTADOS PARA LA INTERFAZ
    # ==========================================

    def obtener_todos_los_usuarios(self) -> List[Usuario]:
        """Devuelve el listado completo de usuarios para el panel de administración."""
        return self.repo.obtener_todos_los_usuarios()

    def obtener_prestamos_de_usuario(self, id_usuario: str) -> List:
        """Devuelve el historial de préstamos de un socio para la vista 'Mis préstamos'."""
        return self.repo.obtener_prestamos_de_usuario(id_usuario)

    def obtener_prestamos_activos(self) -> List:
        """Devuelve todos los préstamos pendientes de devolución para el panel del auxiliar."""
        return self.repo.obtener_prestamos_activos()

    def obtener_todos_los_prestamos(self) -> List:
        """
        Devuelve el historial completo de préstamos, incluidos los ya devueltos.
        El auxiliar lo usa cuando activa la vista de historial en la pestaña de préstamos.
        """
        return self.repo.obtener_todos_los_prestamos()

    def obtener_reservas_de_usuario(self, id_usuario: str) -> List:
        """Devuelve el historial de reservas de un socio para la vista 'Mis reservas'."""
        return self.repo.obtener_reservas_de_usuario(id_usuario)

    def obtener_reservas_activas(self) -> List:
        """Devuelve todas las reservas pendientes de recogida para el panel del auxiliar."""
        return self.repo.obtener_reservas_activas()
