# main.py
# Proyecto Final - Talento Tech - Introducción a Python (2C 2026)
# Autor: Octavio Lucardi Fierro
#
# Sistema de gestión de inventario por terminal. Los productos se guardan en
# la base de datos SQLite 'inventario.db' (tabla 'productos').
#
# Organización del proyecto:
#   main.py          -> menú principal y lógica de cada opción (este archivo)
#   base_datos.py    -> funciones que leen y escriben en la base de datos
#   interfaz.py      -> colores, tablas y pedido de datos validados al usuario
#   exportar.py      -> exportación de listados a archivos CSV
#   datos_ejemplo.py -> productos de prueba para cargar si el inventario está vacío
#
# Para ejecutarlo: python main.py

import sqlite3

import base_datos
import datos_ejemplo
import exportar
import interfaz


# ----------------------------------------------------------------------------
# FUNCIONES AUXILIARES
# ----------------------------------------------------------------------------

def elegir_producto():
    """Muestra los productos, pide un ID y devuelve ese producto.
    Si el ID no existe lo vuelve a pedir. Devuelve None si no hay productos o si se cancela."""
    productos = base_datos.obtener_productos()
    if len(productos) == 0:
        interfaz.mostrar_aviso("No hay productos registrados.")
        return None

    # Mostramos la tabla para que el usuario vea qué ID tiene cada producto
    interfaz.mostrar_tabla(productos)
    print()
    while True:
        id_producto = interfaz.pedir_entero("Ingrese el ID del producto (0 para cancelar): ", minimo=0)
        if id_producto == 0:
            interfaz.mostrar_aviso("Operación cancelada.")
            return None

        producto = base_datos.obtener_producto_por_id(id_producto)
        if producto is not None:
            return producto
        # El ID no existe: avisamos y el while vuelve a preguntar
        interfaz.mostrar_error(f"No existe ningún producto con el ID {id_producto}.")


def confirmar_si_nombre_repetido(nombre, id_excluido=0):
    """Avisa si ya existe otro producto con el mismo nombre y pregunta si seguir.
    Devuelve True si se puede continuar (no hay repetidos o el usuario acepta)."""
    repetidos = base_datos.buscar_nombre_repetido(nombre, id_excluido)
    if len(repetidos) == 0:
        return True

    interfaz.mostrar_aviso(f"Ya existe un producto llamado '{nombre}':")
    interfaz.mostrar_tabla(repetidos)
    return interfaz.pedir_confirmacion("\n¿Desea continuar de todas formas?")


def mantener_si_vacio(valor_nuevo, valor_actual):
    """Al actualizar: si el usuario dejó el campo vacío (None), se conserva el valor actual."""
    if valor_nuevo is None:
        return valor_actual
    return valor_nuevo


def pedir_texto_opcional_editado(mensaje, valor_actual):
    """Al actualizar un campo opcional: Enter mantiene el valor y '-' lo deja vacío."""
    texto = interfaz.pedir_texto(mensaje, obligatorio=False)
    if texto == "-":
        return None  # None se guarda como NULL en la base (campo vacío)
    return mantener_si_vacio(texto, valor_actual)


def ofrecer_datos_ejemplo():
    """Si el inventario está vacío, ofrece cargar los productos de prueba de datos_ejemplo.py."""
    if base_datos.contar_productos() > 0:
        return

    cantidad = len(datos_ejemplo.PRODUCTOS_EJEMPLO)
    interfaz.mostrar_aviso("El inventario está vacío.")
    if not interfaz.pedir_confirmacion(
        f"¿Desea cargar {cantidad} productos de ejemplo (videojuegos y mangas) para probar el programa?"
    ):
        return

    # Cada producto de ejemplo es una tupla, que desempaquetamos en 5 variables
    for nombre, descripcion, stock, precio, categoria in datos_ejemplo.PRODUCTOS_EJEMPLO:
        base_datos.insertar_producto(nombre, descripcion, stock, precio, categoria)
    interfaz.mostrar_exito(f"Se cargaron {cantidad} productos de ejemplo.")


# ----------------------------------------------------------------------------
# OPCIONES DEL MENÚ
# ----------------------------------------------------------------------------

def registrar_producto():
    """Opción 1: pide los datos de un producto nuevo y lo guarda."""
    interfaz.mostrar_titulo("REGISTRAR PRODUCTO")
    nombre = interfaz.pedir_texto("Nombre: ")
    # Antes de pedir el resto de los datos, avisamos si el nombre ya existe
    if not confirmar_si_nombre_repetido(nombre):
        interfaz.mostrar_aviso("Registro cancelado. Para sumar unidades a un producto que ya existe use la opción 7.")
        return

    descripcion = interfaz.pedir_texto("Descripción (opcional): ", obligatorio=False)
    cantidad = interfaz.pedir_entero("Cantidad disponible: ", minimo=0)
    precio = interfaz.pedir_precio("Precio: $")
    categoria = interfaz.pedir_texto("Categoría (opcional): ", obligatorio=False)

    nuevo_id = base_datos.insertar_producto(nombre, descripcion, cantidad, precio, categoria)
    interfaz.mostrar_exito(f"Producto '{nombre}' registrado con el ID {nuevo_id}.")


def ver_productos():
    """Opción 2: muestra todos los productos registrados, en el orden que elija el usuario."""
    interfaz.mostrar_titulo("PRODUCTOS REGISTRADOS")
    if base_datos.contar_productos() == 0:
        interfaz.mostrar_aviso("No hay productos registrados.")
        return  # return sin valor: termina la función acá

    print("Ordenar por:")
    opciones = [
        ("1", "ID (orden de carga)"),
        ("2", "Nombre (A-Z)"),
        ("3", "Categoría (A-Z)"),
        ("4", "Cantidad (de menor a mayor)"),
        ("5", "Precio (de menor a mayor)"),
        ("6", "Precio (de mayor a menor)"),
    ]
    interfaz.mostrar_opciones(opciones)
    # Con Enter (sin escribir nada) se ordena por ID
    opcion = interfaz.pedir_opcion(opciones, "Elija una opción (Enter = por ID): ", por_defecto="1")

    # Cada opción del menú corresponde a una clave del diccionario base_datos.ORDENES
    ordenes = {
        "1": "id",
        "2": "nombre",
        "3": "categoria",
        "4": "cantidad",
        "5": "precio_asc",
        "6": "precio_desc",
    }
    productos = base_datos.obtener_productos(ordenes[opcion])
    interfaz.mostrar_tabla(productos)

    # Sumamos las unidades recorriendo la lista
    unidades = 0
    for producto in productos:
        unidades += producto["cantidad"]
    print(f"\nTotal: {len(productos)} producto(s), {unidades} unidad(es) en stock.")


def actualizar_producto():
    """Opción 3: modifica los datos de un producto elegido por su ID."""
    interfaz.mostrar_titulo("ACTUALIZAR PRODUCTO")
    producto = elegir_producto()
    if producto is None:
        return

    interfaz.mostrar_producto(producto)
    print("\nIngrese los nuevos datos. Presione Enter para mantener el valor actual (entre []).")
    print("En descripción y categoría puede escribir '-' para dejar el campo vacío.")

    # En cada campo mostramos el valor actual entre corchetes y, si el usuario
    # da Enter sin escribir nada, lo conservamos
    nombre = mantener_si_vacio(
        interfaz.pedir_texto(f"Nombre [{producto['nombre']}]: ", obligatorio=False),
        producto["nombre"],
    )
    # Si cambió el nombre, avisamos si otro producto ya se llama así
    if not confirmar_si_nombre_repetido(nombre, id_excluido=producto["id"]):
        interfaz.mostrar_aviso("Actualización cancelada.")
        return

    descripcion = pedir_texto_opcional_editado(
        f"Descripción [{interfaz.formatear_valor('descripcion', producto['descripcion'])}]: ",
        producto["descripcion"],
    )
    cantidad = mantener_si_vacio(
        interfaz.pedir_entero(f"Cantidad [{producto['cantidad']}]: ", minimo=0, opcional=True),
        producto["cantidad"],
    )
    precio = mantener_si_vacio(
        interfaz.pedir_precio(f"Precio [{interfaz.formatear_precio(producto['precio'])}]: $", opcional=True),
        producto["precio"],
    )
    categoria = pedir_texto_opcional_editado(
        f"Categoría [{interfaz.formatear_valor('categoria', producto['categoria'])}]: ",
        producto["categoria"],
    )

    # Armamos un diccionario con los datos nuevos para compararlo con el original
    datos_nuevos = {
        "id": producto["id"],
        "nombre": nombre,
        "descripcion": descripcion,
        "cantidad": cantidad,
        "precio": precio,
        "categoria": categoria,
    }
    if datos_nuevos == producto:
        interfaz.mostrar_aviso("No se modificó ningún dato.")
        return

    if base_datos.actualizar_producto(producto["id"], nombre, descripcion, cantidad, precio, categoria):
        interfaz.mostrar_exito(f"Producto con ID {producto['id']} actualizado:")
        interfaz.mostrar_producto(datos_nuevos)
    else:
        interfaz.mostrar_error("No se pudo actualizar: el producto ya no existe.")


def eliminar_producto():
    """Opción 4: elimina un producto elegido por su ID, previa confirmación."""
    interfaz.mostrar_titulo("ELIMINAR PRODUCTO")
    producto = elegir_producto()
    if producto is None:
        return

    interfaz.mostrar_producto(producto)
    # Pedimos confirmación porque la eliminación no se puede deshacer
    if not interfaz.pedir_confirmacion(f"\n¿Seguro que desea eliminar '{producto['nombre']}'?"):
        interfaz.mostrar_aviso("Eliminación cancelada.")
        return

    if base_datos.eliminar_producto(producto["id"]):
        interfaz.mostrar_exito(f"Producto '{producto['nombre']}' eliminado correctamente.")
    else:
        interfaz.mostrar_error("No se pudo eliminar: el producto ya no existe.")


def buscar_productos():
    """Opción 5: submenú para buscar por ID, por nombre o por categoría."""
    interfaz.mostrar_titulo("BUSCAR PRODUCTOS")
    opciones = [
        ("1", "Buscar por ID"),
        ("2", "Buscar por nombre"),
        ("3", "Buscar por categoría"),
        ("0", "Volver al menú principal"),
    ]
    interfaz.mostrar_opciones(opciones)
    # pedir_opcion repregunta hasta que la opción sea válida, así no hace falta un "case _"
    opcion = interfaz.pedir_opcion(opciones)

    match opcion:
        case "1":
            id_producto = interfaz.pedir_entero("ID a buscar: ", minimo=1)
            producto = base_datos.obtener_producto_por_id(id_producto)
            if producto is None:
                interfaz.mostrar_aviso(f"No existe ningún producto con el ID {id_producto}.")
            else:
                interfaz.mostrar_producto(producto)

        # "2" | "3" significa: si la opción es "2" o "3"
        case "2" | "3":
            # campo: nombre de la columna en la base / texto_campo: cómo se lo muestra
            if opcion == "2":
                campo, texto_campo = "nombre", "el nombre"
            else:
                campo, texto_campo = "categoria", "la categoría"

            texto = interfaz.pedir_texto(f"Ingrese {texto_campo} (o una parte) a buscar: ")
            resultados = base_datos.buscar_productos(campo, texto)
            if len(resultados) == 0:
                interfaz.mostrar_aviso(f"No se encontraron productos con '{texto}' en {texto_campo}.")
            else:
                interfaz.mostrar_tabla(resultados)
                print(f"\nResultados: {len(resultados)} producto(s).")

        case "0":
            return


def reporte_stock_bajo():
    """Opción 6: lista los productos con cantidad igual o menor a un límite dado por el usuario."""
    interfaz.mostrar_titulo("REPORTE DE BAJO STOCK")
    limite = interfaz.pedir_entero("Mostrar productos con cantidad igual o menor a: ", minimo=0)

    productos = base_datos.obtener_stock_bajo(limite)
    if len(productos) == 0:
        interfaz.mostrar_exito(f"No hay productos con cantidad igual o menor a {limite}.")
        return

    interfaz.mostrar_aviso(f"{len(productos)} producto(s) con cantidad igual o menor a {limite}:")
    interfaz.mostrar_tabla(productos)


def movimiento_stock():
    """Opción 7: suma (entrada) o resta (salida) unidades al stock de un producto."""
    interfaz.mostrar_titulo("ENTRADA / SALIDA DE STOCK")
    producto = elegir_producto()
    if producto is None:
        return

    stock_actual = producto["cantidad"]
    print(f"\nProducto: {producto['nombre']} | Stock actual: {stock_actual} unidad(es)")

    opciones = [("1", "Entrada (sumar unidades, por ejemplo una compra al proveedor)")]
    # Si no hay stock no se puede registrar una salida, así que esa opción no se ofrece
    if stock_actual > 0:
        opciones.append(("2", "Salida (restar unidades, por ejemplo una venta)"))
    else:
        interfaz.mostrar_aviso("El producto no tiene stock: solo se pueden registrar entradas.")
    opciones.append(("0", "Cancelar"))
    interfaz.mostrar_opciones(opciones)
    opcion = interfaz.pedir_opcion(opciones)

    # diferencia es lo que se suma al stock: positiva en una entrada, negativa en una salida
    match opcion:
        case "1":
            # El máximo evita que el stock total supere el valor máximo permitido
            unidades = interfaz.pedir_entero(
                "Unidades que ingresan: ", minimo=1, maximo=interfaz.VALOR_MAXIMO - stock_actual
            )
            diferencia = unidades
        case "2":
            # No se pueden sacar más unidades de las que hay: si se intenta, se vuelve a preguntar
            unidades = interfaz.pedir_entero(
                f"Unidades que salen (máximo {stock_actual}): ", minimo=1, maximo=stock_actual
            )
            diferencia = -unidades
        case "0":
            interfaz.mostrar_aviso("Operación cancelada.")
            return

    if base_datos.modificar_stock(producto["id"], diferencia):
        stock_nuevo = stock_actual + diferencia
        interfaz.mostrar_exito(
            f"Stock de '{producto['nombre']}' actualizado: {stock_actual} -> {stock_nuevo} unidad(es)."
        )
        if stock_nuevo == 0:
            interfaz.mostrar_aviso("El producto se quedó sin stock.")
    else:
        interfaz.mostrar_error("No se pudo modificar el stock (el producto no existe o no alcanza el stock).")


def resumen_inventario():
    """Opción 8: muestra totales del inventario y un detalle por categoría."""
    interfaz.mostrar_titulo("RESUMEN DEL INVENTARIO")
    resumen = base_datos.obtener_resumen()
    if resumen["productos"] == 0:
        interfaz.mostrar_aviso("No hay productos registrados.")
        return

    print()
    interfaz.mostrar_dato("Productos distintos", resumen["productos"], ancho=24)
    interfaz.mostrar_dato("Unidades en stock", resumen["unidades"], ancho=24)
    interfaz.mostrar_dato("Valor total del stock", interfaz.formatear_precio(resumen["valor"]), ancho=24)
    interfaz.mostrar_dato("Productos sin stock", resumen["sin_stock"], ancho=24)

    por_categoria = base_datos.obtener_resumen_por_categoria()
    # Los productos sin categoría vienen con None: les ponemos un texto más claro
    for fila in por_categoria:
        if fila["categoria"] is None:
            fila["categoria"] = "Sin categoría"

    print("\nDetalle por categoría (de mayor a menor valor):")
    interfaz.mostrar_tabla(por_categoria, interfaz.COLUMNAS_RESUMEN)


def exportar_productos():
    """Opción 9: guarda el inventario completo o el reporte de bajo stock en un archivo CSV."""
    interfaz.mostrar_titulo("EXPORTAR A CSV")
    opciones = [
        ("1", "Inventario completo"),
        ("2", "Reporte de bajo stock"),
        ("0", "Volver al menú principal"),
    ]
    interfaz.mostrar_opciones(opciones)
    opcion = interfaz.pedir_opcion(opciones)

    match opcion:
        case "1":
            productos = base_datos.obtener_productos()
            nombre_archivo = "inventario"
        case "2":
            limite = interfaz.pedir_entero("Exportar productos con cantidad igual o menor a: ", minimo=0)
            productos = base_datos.obtener_stock_bajo(limite)
            nombre_archivo = f"bajo_stock_{limite}"
        case "0":
            return

    if len(productos) == 0:
        interfaz.mostrar_aviso("No hay productos para exportar.")
        return

    try:
        ruta = exportar.exportar_csv(productos, nombre_archivo)
    except OSError as error:
        # Por ejemplo: no hay permiso para escribir en la carpeta
        interfaz.mostrar_error(f"No se pudo guardar el archivo: {error}")
        return

    interfaz.mostrar_exito(f"Se exportaron {len(productos)} producto(s) al archivo:")
    print(f"  {ruta}")


# ----------------------------------------------------------------------------
# PROGRAMA PRINCIPAL
# ----------------------------------------------------------------------------

def main():
    """Prepara la base de datos y muestra el menú hasta que se elija Salir."""
    try:
        base_datos.crear_tabla()
        ofrecer_datos_ejemplo()
    except sqlite3.Error as error:
        interfaz.mostrar_error(f"No se pudo abrir la base de datos: {error}")
        return

    while True:
        interfaz.mostrar_menu()
        opcion = input("\nElija una opción: ").strip()

        # Cualquier error de la base de datos se captura acá, se informa y el
        # programa sigue funcionando en lugar de cerrarse
        try:
            match opcion:
                case "1":
                    registrar_producto()
                case "2":
                    ver_productos()
                case "3":
                    actualizar_producto()
                case "4":
                    eliminar_producto()
                case "5":
                    buscar_productos()
                case "6":
                    reporte_stock_bajo()
                case "7":
                    movimiento_stock()
                case "8":
                    resumen_inventario()
                case "9":
                    exportar_productos()
                case "0":
                    print(interfaz.COLOR_TITULO + "\nSaliendo del sistema... ¡Hasta luego!")
                    break  # rompe el while True y termina el programa
                case _:
                    interfaz.mostrar_error("Opción no válida, elija un número del 0 al 9.")
                    continue  # vuelve a mostrar el menú sin pausar
        except sqlite3.Error as error:
            interfaz.mostrar_error(f"Ocurrió un problema con la base de datos: {error}")

        interfaz.pausar()


# Este bloque solo se ejecuta si se corre "python main.py" directamente,
# no cuando el archivo se importa desde otro módulo
if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        # Ctrl+C (o cerrar la entrada) no muestra un error feo, cierra el programa prolijamente
        print("\n\nPrograma interrumpido. ¡Hasta luego!")
