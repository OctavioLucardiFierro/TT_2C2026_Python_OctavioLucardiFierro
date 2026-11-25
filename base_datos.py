# base_datos.py
# Módulo que se encarga de TODA la comunicación con la base de datos SQLite.
# Acá solo hay funciones que guardan o leen datos: no se imprime nada ni se le
# piden datos al usuario (de eso se encargan interfaz.py y main.py).

import os
import sqlite3

# Ruta al archivo inventario.db, ubicado en la misma carpeta que este archivo.
# __file__ es la ruta de base_datos.py; así la base se crea siempre junto al
# proyecto, sin importar desde qué carpeta se ejecute el programa
# (con "./inventario.db" dependería de dónde esté parada la terminal).
RUTA_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "inventario.db")

# Únicos campos por los que se permite buscar texto. Se usan como "lista blanca"
# para no meter en el SQL un nombre de columna inventado por el usuario.
CAMPOS_BUSCABLES = ("nombre", "categoria")

# Formas de ordenar el listado: clave -> texto que va después de ORDER BY.
# El ORDER BY no admite "?", por eso solo se aceptan las claves de este diccionario.
# COLLATE NOCASE ordena sin distinguir mayúsculas de minúsculas.
ORDENES = {
    "id": "id",
    "nombre": "nombre COLLATE NOCASE",
    "categoria": "categoria COLLATE NOCASE, nombre COLLATE NOCASE",
    "cantidad": "cantidad, nombre COLLATE NOCASE",
    "precio_asc": "precio, nombre COLLATE NOCASE",
    "precio_desc": "precio DESC, nombre COLLATE NOCASE",
}


def conectar():
    """Abre la conexión con inventario.db (si el archivo no existe, SQLite lo crea)."""
    conexion = sqlite3.connect(RUTA_DB)
    # row_factory hace que cada fila se pueda leer por nombre de columna,
    # por ejemplo fila["nombre"], en lugar de por posición (fila[1]).
    conexion.row_factory = sqlite3.Row
    return conexion


def crear_tabla():
    """Crea la tabla 'productos' si todavía no existe."""
    conexion = conectar()
    try:
        cursor = conexion.cursor()
        # IF NOT EXISTS evita un error si la tabla ya fue creada en otra ejecución
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS productos (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre      TEXT    NOT NULL,
                descripcion TEXT,
                cantidad    INTEGER NOT NULL,
                precio      REAL    NOT NULL,
                categoria   TEXT
            )
        """)
        conexion.commit()
    finally:
        # finally se ejecuta siempre, haya error o no: la conexión nunca queda abierta
        conexion.close()


def consultar(sql, parametros=()):
    """Ejecuta una consulta SELECT y devuelve los resultados como lista de diccionarios."""
    conexion = conectar()
    try:
        cursor = conexion.cursor()
        # Los "?" del SQL se reemplazan por los valores de 'parametros'.
        # Nunca armamos el SQL pegando texto del usuario: así evitamos inyección SQL.
        cursor.execute(sql, parametros)
        filas = cursor.fetchall()
        # dict(fila) convierte cada sqlite3.Row en un diccionario común de Python
        return [dict(fila) for fila in filas]
    finally:
        conexion.close()


def ejecutar_cambio(sql, parametros=()):
    """Ejecuta un INSERT, UPDATE o DELETE, guarda los cambios y devuelve el cursor."""
    conexion = conectar()
    try:
        cursor = conexion.cursor()
        cursor.execute(sql, parametros)
        conexion.commit()  # sin commit los cambios no quedan guardados en el archivo
        # Del cursor se pueden leer después:
        #   cursor.lastrowid -> id generado por el último INSERT
        #   cursor.rowcount  -> cantidad de filas modificadas o eliminadas
        return cursor
    finally:
        conexion.close()


def insertar_producto(nombre, descripcion, cantidad, precio, categoria):
    """Registra un producto nuevo y devuelve el id que le asignó la base de datos."""
    cursor = ejecutar_cambio(
        """
        INSERT INTO productos (nombre, descripcion, cantidad, precio, categoria)
        VALUES (?, ?, ?, ?, ?)
        """,
        (nombre, descripcion, cantidad, precio, categoria),
    )
    return cursor.lastrowid


def obtener_productos(orden="id"):
    """Devuelve todos los productos registrados, ordenados según una clave de ORDENES."""
    if orden not in ORDENES:
        raise ValueError(f"No se puede ordenar por '{orden}'")
    return consultar(f"SELECT * FROM productos ORDER BY {ORDENES[orden]}")


def contar_productos():
    """Devuelve cuántos productos hay registrados."""
    # COUNT(*) cuenta las filas; "AS total" le pone nombre a esa columna del resultado
    resultado = consultar("SELECT COUNT(*) AS total FROM productos")
    return resultado[0]["total"]


def buscar_nombre_repetido(nombre, id_excluido=0):
    """Devuelve los productos que ya tienen exactamente ese nombre (sin distinguir
    mayúsculas). Con id_excluido se ignora un producto: se usa al actualizar,
    para que el producto no se detecte como repetido de sí mismo."""
    return consultar(
        "SELECT * FROM productos WHERE nombre = ? COLLATE NOCASE AND id != ?",
        (nombre, id_excluido),
    )


def obtener_producto_por_id(id_producto):
    """Devuelve el producto con ese id (como diccionario) o None si no existe."""
    resultados = consultar("SELECT * FROM productos WHERE id = ?", (id_producto,))
    # Como el id es único, la lista tiene 0 o 1 elementos
    if len(resultados) == 0:
        return None
    return resultados[0]


def buscar_productos(campo, texto):
    """Busca productos cuyo 'campo' (nombre o categoria) contenga el texto indicado."""
    if campo not in CAMPOS_BUSCABLES:
        raise ValueError(f"No se puede buscar por el campo '{campo}'")

    # El nombre de la columna no puede ir con "?", por eso se valida arriba con la
    # lista blanca. LIKE con % antes y después busca el texto en cualquier parte,
    # así "yer" encuentra "Yerba mate" (y no distingue mayúsculas de minúsculas).
    return consultar(
        f"SELECT * FROM productos WHERE {campo} LIKE ? ORDER BY nombre",
        (f"%{texto}%",),
    )


def actualizar_producto(id_producto, nombre, descripcion, cantidad, precio, categoria):
    """Actualiza todos los datos del producto. Devuelve True si existía y se modificó."""
    cursor = ejecutar_cambio(
        """
        UPDATE productos
        SET nombre = ?, descripcion = ?, cantidad = ?, precio = ?, categoria = ?
        WHERE id = ?
        """,
        (nombre, descripcion, cantidad, precio, categoria, id_producto),
    )
    return cursor.rowcount > 0


def eliminar_producto(id_producto):
    """Elimina el producto con ese id. Devuelve True si existía y se eliminó."""
    cursor = ejecutar_cambio("DELETE FROM productos WHERE id = ?", (id_producto,))
    return cursor.rowcount > 0


def modificar_stock(id_producto, diferencia):
    """Suma unidades al stock (diferencia positiva) o las resta (diferencia negativa).
    Devuelve True si se pudo modificar."""
    # La condición "cantidad + ? >= 0" hace que la base rechace una salida mayor
    # al stock disponible: en ese caso no se modifica ninguna fila (rowcount = 0)
    cursor = ejecutar_cambio(
        "UPDATE productos SET cantidad = cantidad + ? WHERE id = ? AND cantidad + ? >= 0",
        (diferencia, id_producto, diferencia),
    )
    return cursor.rowcount > 0


def obtener_stock_bajo(limite):
    """Devuelve los productos con cantidad igual o menor al límite, de menor a mayor stock."""
    return consultar(
        "SELECT * FROM productos WHERE cantidad <= ? ORDER BY cantidad, nombre",
        (limite,),
    )


def obtener_resumen():
    """Devuelve un diccionario con los totales generales del inventario."""
    # SUM suma los valores de una columna (o de una cuenta, como cantidad * precio).
    # COALESCE(x, 0) devuelve 0 cuando SUM da NULL, que pasa si la tabla está vacía.
    resumen = consultar("""
        SELECT COUNT(*)                            AS productos,
               COALESCE(SUM(cantidad), 0)          AS unidades,
               COALESCE(SUM(cantidad * precio), 0) AS valor
        FROM productos
    """)[0]
    sin_stock = consultar("SELECT COUNT(*) AS total FROM productos WHERE cantidad = 0")
    resumen["sin_stock"] = sin_stock[0]["total"]
    return resumen


def obtener_resumen_por_categoria():
    """Devuelve, por cada categoría, cuántos productos y unidades tiene y cuánto vale su stock."""
    # GROUP BY junta en una sola fila todos los productos de la misma categoría,
    # y COUNT / SUM se calculan dentro de cada grupo
    return consultar("""
        SELECT categoria,
               COUNT(*)               AS productos,
               SUM(cantidad)          AS unidades,
               SUM(cantidad * precio) AS valor
        FROM productos
        GROUP BY categoria COLLATE NOCASE
        ORDER BY valor DESC
    """)
