"""
database.py

Capa de acceso a datos (Data Access Object).
Se encarga exclusivamente de traducir los objetos del dominio (models.py) 
a tablas relacionales en SQLite, y de reconstruirlos de vuelta.
"""

import sqlite3
import os
from datetime import datetime

# Importamos usando la ruta absoluta desde la raíz del proyecto
from biblioteca.models import (
    EstadoMaterial, EstadoPrestamo, EstadoReserva, TipoDispositivo, RolEmpleado,
    Material, Libro, Revista, Dispositivo, JuegoDeMesa, RecursoDigital,
    Usuario, Socio, Empleado, Prestamo, Reserva
)


class BibliotecaRepository:
    """
    Gestor principal de la base de datos SQLite.
    Abre la conexión, crea las tablas si no existen y maneja las operaciones CRUD
    (Create, Read, Update, Delete) de los objetos del sistema.
    """
    
    def __init__(self, ruta_db: str = "biblioteca.db"):
        """
        Si recibe una ruta relativa, la convierte en absoluta basándose 
        en la ubicación de este archivo.
        """
        if not os.path.isabs(ruta_db):
            # 1. Obtenemos la carpeta donde está db.py (ej: .../biblioteca_POO/biblioteca/)
            carpeta_actual = os.path.dirname(os.path.abspath(__file__))
            
            # 2. Subimos un nivel para llegar a la raíz (ej: .../biblioteca_POO/)
            raiz_proyecto = os.path.dirname(carpeta_actual)
            
            # 3. Construimos la ruta final uniendo la raíz con lo que pida el usuario
            self.ruta_db = os.path.join(raiz_proyecto, ruta_db)
        else:
            self.ruta_db = ruta_db
        self.crear_tablas()

    def _conectar(self) -> sqlite3.Connection:
        """Crea y devuelve una conexión segura a la base de datos."""
        return sqlite3.connect(self.ruta_db)

    def crear_tablas(self):
        """
        Ejecuta el DDL (Data Definition Language) para asegurar que 
        las tablas existen antes de empezar a trabajar.
        """
        conexion = self._conectar()
        cursor = conexion.cursor()
        
        # TABLA USUARIOS (Almacena Socios y Empleados juntos)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id_usuario TEXT PRIMARY KEY,
                nombre TEXT NOT NULL,
                apellidos TEXT NOT NULL,
                email TEXT NOT NULL,
                tipo_usuario TEXT NOT NULL,
                
                -- Atributos exclusivos de Socio
                sancionado INTEGER DEFAULT 0,
                prestamos_activos INTEGER DEFAULT 0,
                max_prestamos INTEGER,
                max_especial INTEGER DEFAULT 0,
                
                -- Atributos exclusivos de Empleado
                rol TEXT
            )
        ''')
        
        # TABLA MATERIALES (Actualizada para soportar Revistas)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS materiales (
                codigo_id TEXT PRIMARY KEY,
                titulo TEXT NOT NULL,
                estado TEXT NOT NULL,
                tipo_material TEXT NOT NULL,
                ubicacion TEXT,
                
                -- Atributos de Libro
                autor TEXT,
                paginas INTEGER,
                isbn TEXT,
                
                -- Atributos de Dispositivo
                tipo_dispositivo TEXT,
                fabricante TEXT,
                so TEXT,
                numero_serie TEXT,
                
                -- Atributos de JuegoDeMesa y Revista
                editorial TEXT,
                min_jugadores INTEGER,
                max_jugadores INTEGER,
                
                -- Atributos exclusivos de Revista
                numero_edicion INTEGER,
                issn TEXT,
                
                -- Atributos de RecursoDigital
                url TEXT,
                licencias_totales INTEGER,
                licencias_disponibles INTEGER
            )
        ''')
        
        # TABLA PRÉSTAMOS (Tabla transaccional con Claves Foráneas)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prestamos (
                id_prestamo TEXT PRIMARY KEY,
                id_usuario TEXT NOT NULL,
                codigo_material TEXT NOT NULL,
                fecha_prestamo TEXT NOT NULL,
                fecha_devolucion_prevista TEXT NOT NULL,
                fecha_devolucion_real TEXT,
                estado TEXT NOT NULL,
                
                FOREIGN KEY (id_usuario) REFERENCES usuarios (id_usuario),
                FOREIGN KEY (codigo_material) REFERENCES materiales (codigo_id)
            )
        ''')

        # TABLA RESERVAS (Registro de apartados pendientes de recogida)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reservas (
                id_reserva TEXT PRIMARY KEY,
                id_usuario TEXT NOT NULL,
                codigo_material TEXT NOT NULL,
                fecha_reserva TEXT NOT NULL,
                fecha_limite_recogida TEXT NOT NULL,
                estado TEXT NOT NULL,

                FOREIGN KEY (id_usuario) REFERENCES usuarios (id_usuario),
                FOREIGN KEY (codigo_material) REFERENCES materiales (codigo_id)
            )
        ''')
        
        conexion.commit()
        conexion.close()

    # ==========================================
    # GUARDADO DE OBJETOS (De Python a SQLite)
    # ==========================================

    def guardar_usuario(self, usuario: Usuario):
        """Traduce un objeto Usuario (Socio o Empleado) y lo inserta/actualiza en SQLite."""
        conexion = self._conectar()
        cursor = conexion.cursor()
        
        consulta = '''
            REPLACE INTO usuarios (
                id_usuario, nombre, apellidos, email, tipo_usuario, 
                sancionado, prestamos_activos, max_prestamos, max_especial, rol
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        
        if isinstance(usuario, Socio):
            valores = (
                usuario.id_usuario, 
                usuario.nombre, 
                usuario.apellidos, 
                usuario.email, 
                "Socio",
                int(usuario.sancionado),
                usuario.prestamos_activos,
                usuario.max_prestamos,
                int(usuario.max_especial),
                None
            )
        elif isinstance(usuario, Empleado):
            valores = (
                usuario.id_usuario, 
                usuario.nombre, 
                usuario.apellidos, 
                usuario.email, 
                "Empleado",
                0, 0, None, 0,
                usuario.rol.value
            )
        else:
            raise ValueError("Tipo de usuario desconocido.")
            
        cursor.execute(consulta, valores)
        conexion.commit()
        conexion.close()

    def guardar_material(self, material: Material):
        """Traduce cualquier tipo de Material a SQL usando diccionarios nombrados."""
        conexion = self._conectar()
        cursor = conexion.cursor()
        
        # 1. En lugar de usar '?', usamos ':nombre_columna' para trabajar con diccionarios y evitar errores
        consulta = '''
            REPLACE INTO materiales (
                codigo_id, titulo, estado, tipo_material, ubicacion,
                autor, paginas, isbn, tipo_dispositivo, fabricante, so, numero_serie,
                editorial, min_jugadores, max_jugadores, numero_edicion, issn,
                url, licencias_totales, licencias_disponibles
            ) VALUES (
                :codigo_id, :titulo, :estado, :tipo_material, :ubicacion,
                :autor, :paginas, :isbn, :tipo_dispositivo, :fabricante, :so, :numero_serie,
                :editorial, :min_jugadores, :max_jugadores, :numero_edicion, :issn,
                :url, :licencias_totales, :licencias_disponibles
            )
        '''
        
        # 2. Creamos el diccionario con todas las columnas a None por defecto
        # (Así nos evitamos escribir los 17 Nones a mano y es súper legible)
        columnas_bd = [
            "codigo_id", "titulo", "estado", "tipo_material", "ubicacion",
            "autor", "paginas", "isbn", "tipo_dispositivo", "fabricante", "so", "numero_serie",
            "editorial", "min_jugadores", "max_jugadores", "numero_edicion", "issn",
            "url", "licencias_totales", "licencias_disponibles"
        ]
        valores = {columna: None for columna in columnas_bd}
        
        # 3. Asignamos los atributos comunes (los que todos los materiales tienen)
        valores["codigo_id"] = material.codigo_id
        valores["titulo"] = material.titulo
        valores["estado"] = material.estado.value
        
        # TRUCO: Si el material es físico, todos tienen 'ubicacion'
        if hasattr(material, "ubicacion"):
            valores["ubicacion"] = material.ubicacion

        # 4. Asignamos por NOMBRE (¡Adiós a los números!)
        if isinstance(material, Libro):
            valores["tipo_material"] = "Libro"
            valores["autor"] = material.autor
            valores["paginas"] = material.paginas
            valores["isbn"] = material.isbn
            
        elif isinstance(material, Revista):
            valores["tipo_material"] = "Revista"
            valores["editorial"] = material.editorial
            valores["numero_edicion"] = material.numero_edicion
            valores["issn"] = material.issn
            
        elif isinstance(material, Dispositivo):
            valores["tipo_material"] = "Dispositivo"
            valores["tipo_dispositivo"] = material.tipo_dispositivo.value
            valores["fabricante"] = material.fabricante
            valores["so"] = material.so
            valores["numero_serie"] = material.numero_serie
            
        elif isinstance(material, JuegoDeMesa):
            valores["tipo_material"] = "JuegoDeMesa"
            valores["editorial"] = material.editorial
            valores["min_jugadores"] = material.min_jugadores
            valores["max_jugadores"] = material.max_jugadores
            
        elif isinstance(material, RecursoDigital):
            valores["tipo_material"] = "RecursoDigital"
            valores["url"] = material.url
            valores["licencias_totales"] = material.licencias_totales
            valores["licencias_disponibles"] = material.licencias_disponibles
            
        else:
            raise ValueError("Clase de material no soportada.")
            
        # 5. Le pasamos el diccionario directamente a SQLite
        cursor.execute(consulta, valores)
        conexion.commit()
        conexion.close()

    def guardar_prestamo(self, prestamo: Prestamo):
        """Guarda un registro de préstamo. Mantiene el formato ISO para las fechas."""
        conexion = self._conectar()
        cursor = conexion.cursor()
        
        fecha_real = None
        
        if prestamo.fecha_devolucion_real is not None:
            fecha_real = prestamo.fecha_devolucion_real.isoformat()
            
        consulta = '''
            REPLACE INTO prestamos (
                id_prestamo, id_usuario, codigo_material, fecha_prestamo, 
                fecha_devolucion_prevista, fecha_devolucion_real, estado
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        '''
        
        valores = (
            prestamo.id_prestamo,
            prestamo.usuario.id_usuario,
            prestamo.material.codigo_id,
            prestamo.fecha_prestamo.isoformat(),
            prestamo.fecha_devolucion_prevista.isoformat(),
            fecha_real,
            prestamo.estado.value
        )
        
        cursor.execute(consulta, valores)
        conexion.commit()
        conexion.close()

    # ==========================================
    # RECUPERACIÓN DE OBJETOS (De SQLite a Python)
    # ==========================================

    def obtener_usuario(self, id_usuario: str) -> Usuario:
        """Busca un usuario en la BD y reconstruye la instancia de Socio o Empleado."""
        conexion = self._conectar()
        cursor = conexion.cursor()
        
        cursor.execute("SELECT * FROM usuarios WHERE id_usuario = ?", (id_usuario,))
        fila = cursor.fetchone()
        conexion.close()
        
        if fila is None:
            return None
            
        (
            db_id, db_nom, db_ape, db_email, db_tipo, 
            db_sancionado, db_activos, db_max_prest, db_especial, db_rol
        ) = fila
        
        if db_tipo == "Socio":
            return Socio(
                id_usuario=db_id,
                nombre=db_nom,
                apellidos=db_ape,
                email=db_email,
                sancionado=bool(db_sancionado),
                prestamos_activos=db_activos,
                max_prestamos=db_max_prest if db_max_prest is not None else 3,
                max_especial=bool(db_especial)
            )
            
        elif db_tipo == "Empleado":
            return Empleado(
                id_usuario=db_id,
                nombre=db_nom,
                apellidos=db_ape,
                email=db_email,
                rol=RolEmpleado(db_rol)
            )
            
        return None

    def obtener_material(self, codigo_id: str) -> Material:
        """Reconstruye el objeto Material exacto basándose en la columna 'tipo_material'."""
        conexion = self._conectar()
        cursor = conexion.cursor()
        
        cursor.execute("SELECT * FROM materiales WHERE codigo_id = ?", (codigo_id,))
        fila = cursor.fetchone()
        conexion.close()
        
        if fila is None:
            return None
            
        # Desempaquetamos siguiendo el orden exacto de columnas del CREATE TABLE
        (
            db_id, db_titulo, db_estado, db_tipo, db_ub, 
            db_autor, db_pag, db_isbn, 
            db_tipo_disp, db_fab, db_so, db_num_serie, 
            db_edit, db_min_jug, db_max_jug, 
            db_num_edicion, db_issn,
            db_url, db_lic_totales, db_lic_disp
        ) = fila
        
        estado_enum = EstadoMaterial(db_estado)
        
        if db_tipo == "Libro":
            return Libro(
                codigo_id=db_id,
                titulo=db_titulo,
                autor=db_autor,
                paginas=db_pag,
                isbn=db_isbn,
                ubicacion=db_ub,
                estado=estado_enum
            )
            
        elif db_tipo == "Revista":
            return Revista(
                codigo_id=db_id,
                titulo=db_titulo,
                editorial=db_edit,
                numero_edicion=db_num_edicion,
                issn=db_issn,
                ubicacion=db_ub,
                estado=estado_enum
            )
            
        elif db_tipo == "Dispositivo":
            return Dispositivo(
                codigo_id=db_id,
                titulo=db_titulo,
                tipo_dispositivo=TipoDispositivo(db_tipo_disp),
                fabricante=db_fab,
                so=db_so,
                numero_serie=db_num_serie,
                ubicacion=db_ub,
                estado=estado_enum
            )
            
        elif db_tipo == "JuegoDeMesa":
            return JuegoDeMesa(
                codigo_id=db_id,
                titulo=db_titulo,
                editorial=db_edit,
                min_jugadores=db_min_jug,
                max_jugadores=db_max_jug,
                ubicacion=db_ub,
                estado=estado_enum
            )
            
        elif db_tipo == "RecursoDigital":
            # Reconstruimos el digital pasando las licencias disponibles al constructor,
            # que las acepta directamente como parámetro para no violar el encapsulamiento
            recurso = RecursoDigital(
                codigo_id=db_id,
                titulo=db_titulo,
                url=db_url,
                licencias_totales=db_lic_totales,
                licencias_disponibles=db_lic_disp,
                estado=estado_enum
            )
            return recurso
            
        return None

    def obtener_prestamo(self, id_prestamo: str) -> Prestamo:
        """
        Reconstruye un Préstamo entero, buscando de paso los objetos del Usuario 
        y el Material implicados mediante sus Claves Foráneas.
        """
        conexion = self._conectar()
        cursor = conexion.cursor()
        
        cursor.execute("SELECT * FROM prestamos WHERE id_prestamo = ?", (id_prestamo,))
        fila = cursor.fetchone()
        conexion.close()
        
        if fila is None:
            return None
            
        (
            db_id, db_id_usuario, db_id_material, 
            db_fecha_prest, db_fecha_prev, db_fecha_real, db_estado
        ) = fila
        
        usuario_obj = self.obtener_usuario(db_id_usuario)
        material_obj = self.obtener_material(db_id_material)
        
        if not usuario_obj or not material_obj:
            raise ValueError("Inconsistencia en BBDD: El usuario o material no existe.")
            
        prestamo = Prestamo(
            id_prestamo=db_id,
            usuario=usuario_obj,
            material=material_obj,
            dias_prestamo=1,
            fecha_prestamo=datetime.fromisoformat(db_fecha_prest)  # Restauramos la fecha original
        )
        
        # Sobreescribimos la fecha de devolución prevista con la que tenía en BD
        # (puede diferir si el préstamo fue extendido en alguna renovación)
        prestamo._fecha_devolucion_prevista = datetime.fromisoformat(db_fecha_prev)
        
        if db_fecha_real is not None:
            prestamo._fecha_devolucion_real = datetime.fromisoformat(db_fecha_real)
        else:
            prestamo._fecha_devolucion_real = None
            
        prestamo._estado = EstadoPrestamo(db_estado)
        
        return prestamo
    

    # ==========================================
    # RESERVAS (Guardado y Recuperación)
    # ==========================================

    def guardar_reserva(self, reserva: Reserva):
        """Inserta o actualiza una reserva en la tabla correspondiente."""
        conexion = self._conectar()
        cursor = conexion.cursor()

        consulta = '''
            REPLACE INTO reservas (
                id_reserva, id_usuario, codigo_material,
                fecha_reserva, fecha_limite_recogida, estado
            ) VALUES (?, ?, ?, ?, ?, ?)
        '''

        valores = (
            reserva.id_reserva,
            reserva.usuario.id_usuario,
            reserva.material.codigo_id,
            reserva.fecha_reserva.isoformat(),
            reserva.fecha_limite_recogida.isoformat(),
            reserva.estado.value
        )

        cursor.execute(consulta, valores)
        conexion.commit()
        conexion.close()

    def obtener_reserva(self, id_reserva: str) -> Reserva:
        """
        Reconstruye una Reserva desde la BD, incluyendo sus objetos de Usuario y Material.
        Devuelve None si no existe el registro.
        """
        conexion = self._conectar()
        cursor = conexion.cursor()

        cursor.execute("SELECT * FROM reservas WHERE id_reserva = ?", (id_reserva,))
        fila = cursor.fetchone()
        conexion.close()

        if fila is None:
            return None

        (
            db_id, db_id_usuario, db_id_material,
            db_fecha_reserva, db_fecha_limite, db_estado
        ) = fila

        usuario_obj = self.obtener_usuario(db_id_usuario)
        material_obj = self.obtener_material(db_id_material)

        if not usuario_obj or not material_obj:
            raise ValueError("Inconsistencia en BBDD: El usuario o material de la reserva no existe.")

        reserva = Reserva(
            id_reserva=db_id,
            usuario=usuario_obj,
            material=material_obj,
            fecha_reserva=datetime.fromisoformat(db_fecha_reserva)
        )

        # Restauramos la fecha límite tal como estaba guardada (no la recalculamos)
        reserva._fecha_limite_recogida = datetime.fromisoformat(db_fecha_limite)
        reserva._estado = EstadoReserva(db_estado)

        return reserva

    def obtener_reservas_activas(self) -> list:
        """
        Devuelve todas las reservas que todavía están en estado ACTIVA.
        El controlador las usará al arrancar para liberar las que hayan expirado.
        """
        conexion = self._conectar()
        cursor = conexion.cursor()

        cursor.execute(
            "SELECT id_reserva FROM reservas WHERE estado = ?",
            (EstadoReserva.ACTIVA.value,)
        )
        filas = cursor.fetchall()
        conexion.close()

        # Reconstruimos cada reserva completa usando obtener_reserva
        return [self.obtener_reserva(fila[0]) for fila in filas]
