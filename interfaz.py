# interfaz.py
# Funciones para la terminal: mostrar mensajes y tablas con colores (colorama)
# y pedir datos al usuario validándolos. Este módulo NO toca la base de datos.

import math

from colorama import Fore, Style, init

# autoreset=True vuelve al color normal después de cada print,
# así no hace falta escribir Style.RESET_ALL al final de cada mensaje.
init(autoreset=True)

# Colores usados en todo el programa, definidos una sola vez para mantener
# un estilo uniforme (si se quiere cambiar un color, se cambia solo acá).
COLOR_TITULO = Fore.CYAN + Style.BRIGHT
COLOR_OPCION = Fore.YELLOW + Style.BRIGHT
COLOR_EXITO = Fore.GREEN
COLOR_ERROR = Fore.RED
COLOR_AVISO = Fore.YELLOW

# Valor máximo aceptado para cantidades, IDs y precios. Evita números gigantes
# que SQLite no puede guardar (sus enteros son de 64 bits).
VALOR_MAXIMO = 999_999_999

# Columnas de la tabla de productos: (clave del diccionario, título, ancho máximo)
COLUMNAS_TABLA = [
    ("id", "ID", 6),
    ("nombre", "Nombre", 32),
    ("descripcion", "Descripción", 30),
    ("cantidad", "Cantidad", 10),
    ("precio", "Precio", 16),
    ("categoria", "Categoría", 16),
]

# Columnas de la tabla del resumen por categoría (opción "Resumen del inventario")
COLUMNAS_RESUMEN = [
    ("categoria", "Categoría", 20),
    ("productos", "Productos", 10),
    ("unidades", "Unidades", 10),
    ("valor", "Valor del stock", 18),
]

# Columnas numéricas: se alinean a la derecha, como en una planilla
COLUMNAS_NUMERICAS = ("id", "cantidad", "precio", "productos", "unidades", "valor")

# Columnas que son montos de dinero: se muestran con formato de precio
COLUMNAS_DINERO = ("precio", "valor")


# ----------------------------------------------------------------------------
# MENSAJES
# ----------------------------------------------------------------------------

def mostrar_titulo(texto):
    """Muestra un título destacado, por ejemplo: ===== REGISTRAR PRODUCTO ====="""
    print()
    print(COLOR_TITULO + f"{'=' * 12} {texto} {'=' * 12}")


def mostrar_exito(mensaje):
    print(COLOR_EXITO + "[OK] " + mensaje)


def mostrar_error(mensaje):
    print(COLOR_ERROR + "[ERROR] " + mensaje)


def mostrar_aviso(mensaje):
    print(COLOR_AVISO + "[!] " + mensaje)


def mostrar_opciones(opciones):
    """Muestra una lista de opciones, cada una es una tupla (número, texto)."""
    # Desempaquetamos cada tupla en dos variables dentro del for
    for numero, texto in opciones:
        print(f"  {COLOR_OPCION}{numero}.{Style.RESET_ALL} {texto}")


def mostrar_menu():
    """Muestra el menú principal con todas las opciones del programa."""
    mostrar_titulo("GESTIÓN DE INVENTARIO")
    mostrar_opciones([
        ("1", "Registrar producto"),
        ("2", "Ver todos los productos"),
        ("3", "Actualizar producto (por ID)"),
        ("4", "Eliminar producto (por ID)"),
        ("5", "Buscar productos (por ID, nombre o categoría)"),
        ("6", "Reporte de bajo stock"),
        ("7", "Entrada / salida de stock"),
        ("8", "Resumen del inventario"),
        ("9", "Exportar a CSV (Excel)"),
        ("0", "Salir"),
    ])


def pausar():
    """Espera un Enter, para que el usuario pueda leer el resultado antes del menú."""
    input("\nPresione Enter para volver al menú...")


# ----------------------------------------------------------------------------
# FORMATO DE DATOS
# ----------------------------------------------------------------------------

def formatear_precio(precio):
    """Convierte 1234.5 en '$1.234,50' (formato argentino: punto para miles, coma para decimales)."""
    texto = f"{precio:,.2f}"  # Python lo arma como '1,234.50'
    # Intercambiamos comas y puntos usando un carácter temporal
    texto = texto.replace(",", "X").replace(".", ",").replace("X", ".")
    return "$" + texto


def formatear_valor(clave, valor):
    """Convierte un valor del producto en texto para mostrarlo en pantalla."""
    if valor is None or valor == "":
        return "-"  # campos opcionales vacíos (descripción o categoría)
    if clave in COLUMNAS_DINERO:
        return formatear_precio(valor)
    return str(valor)


def recortar(texto, ancho):
    """Si el texto no entra en el ancho de la columna, lo corta y agrega '...'."""
    if len(texto) <= ancho:
        return texto
    return texto[: ancho - 3] + "..."


def mostrar_tabla(registros, columnas=COLUMNAS_TABLA):
    """Muestra una lista de diccionarios en forma de tabla.
    Por defecto usa las columnas de productos; se le pueden pasar otras (ej: COLUMNAS_RESUMEN)."""
    # 1) Pasamos todos los valores a texto
    filas = []
    for registro in registros:
        fila = []
        for clave, titulo, ancho_maximo in columnas:
            fila.append(formatear_valor(clave, registro[clave]))
        filas.append(fila)

    # 2) Calculamos el ancho de cada columna: el del texto más largo (o el título),
    #    sin pasarse del ancho máximo definido para esa columna
    anchos = []
    for i, (clave, titulo, ancho_maximo) in enumerate(columnas):
        ancho = len(titulo)
        for fila in filas:
            ancho = max(ancho, len(fila[i]))
        anchos.append(min(ancho, ancho_maximo))

    # 3) Imprimimos el encabezado y una línea separadora
    titulos = []
    for i, (clave, titulo, ancho_maximo) in enumerate(columnas):
        titulos.append(titulo.ljust(anchos[i]))
    print()
    print(COLOR_TITULO + " | ".join(titulos))
    print("-+-".join("-" * ancho for ancho in anchos))

    # 4) Imprimimos cada fila
    for fila in filas:
        celdas = []
        for i, (clave, titulo, ancho_maximo) in enumerate(columnas):
            texto = recortar(fila[i], anchos[i])
            # ljust/rjust completan con espacios para que las columnas queden alineadas
            if clave in COLUMNAS_NUMERICAS:
                texto = texto.rjust(anchos[i])
            else:
                texto = texto.ljust(anchos[i])
            # Los productos sin stock se resaltan en rojo
            if clave == "cantidad" and fila[i] == "0":
                texto = COLOR_ERROR + texto + Style.RESET_ALL
            celdas.append(texto)
        print(" | ".join(celdas))


def mostrar_dato(etiqueta, valor, ancho=12):
    """Muestra una línea 'Etiqueta : valor'. ljust(ancho) alinea los ':' de varias líneas."""
    print(f"  {COLOR_OPCION}{etiqueta.ljust(ancho)}:{Style.RESET_ALL} {valor}")


def mostrar_producto(producto):
    """Muestra todos los datos de un solo producto, uno por línea (sin recortar)."""
    print()
    for clave, titulo, ancho_maximo in COLUMNAS_TABLA:
        mostrar_dato(titulo, formatear_valor(clave, producto[clave]))


# ----------------------------------------------------------------------------
# INGRESO DE DATOS CON VALIDACIÓN
# Cada función repite la pregunta hasta que el dato sea válido.
# Con opcional=True (u obligatorio=False) se acepta Enter vacío y se devuelve None:
# se usa al actualizar ("Enter para mantener el valor actual").
# ----------------------------------------------------------------------------

def pedir_texto(mensaje, obligatorio=True):
    """Pide un texto. Si es obligatorio no acepta vacío; si no, devuelve None al dar Enter."""
    while True:
        texto = input(mensaje).strip()  # strip() quita espacios al inicio y al final
        if texto != "":
            return texto
        if not obligatorio:
            return None
        mostrar_error("Este campo no puede quedar vacío.")


def pedir_entero(mensaje, minimo=0, opcional=False):
    """Pide un número entero mayor o igual a 'minimo'."""
    while True:
        texto = input(mensaje).strip()
        if texto == "" and opcional:
            return None
        try:
            numero = int(texto)  # si no es un entero, int() lanza ValueError
        except ValueError:
            mostrar_error("Debe ingresar un número entero (sin letras ni decimales).")
            continue  # vuelve al inicio del while y pregunta de nuevo
        if numero < minimo:
            mostrar_error(f"El número debe ser mayor o igual a {minimo}.")
        elif numero > VALOR_MAXIMO:
            mostrar_error(f"El número no puede ser mayor a {VALOR_MAXIMO}.")
        else:
            return numero


def pedir_precio(mensaje, opcional=False):
    """Pide un precio mayor a 0. Acepta coma o punto como separador decimal."""
    while True:
        texto = input(mensaje).strip().replace(",", ".")  # "1500,50" -> "1500.50"
        if texto == "" and opcional:
            return None
        try:
            precio = float(texto)
        except ValueError:
            mostrar_error("Debe ingresar un número válido (por ejemplo 1500 o 1500,50), sin puntos de miles.")
            continue
        # isfinite descarta valores especiales como "inf" o "nan" que float() acepta
        if not math.isfinite(precio) or precio <= 0:
            mostrar_error("El precio debe ser un número mayor a 0.")
        elif precio > VALOR_MAXIMO:
            mostrar_error(f"El precio no puede ser mayor a {VALOR_MAXIMO}.")
        else:
            return round(precio, 2)  # guardamos como máximo 2 decimales (centavos)


def pedir_confirmacion(mensaje):
    """Hace una pregunta de sí o no. Devuelve True si la respuesta es 's'."""
    while True:
        respuesta = input(f"{mensaje} (s/n): ").strip().lower()
        if respuesta in ("s", "si", "sí"):
            return True
        if respuesta in ("n", "no"):
            return False
        mostrar_error("Responda 's' para sí o 'n' para no.")
