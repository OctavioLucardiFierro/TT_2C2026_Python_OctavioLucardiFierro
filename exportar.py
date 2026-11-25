# exportar.py
# Guarda listados de productos en archivos CSV, que se pueden abrir con Excel
# o Google Sheets. Usa el manejo de archivos visto en clase: with open(...).

import csv
import os
from datetime import datetime

# Carpeta donde se guardan los archivos, junto a los .py del proyecto
CARPETA_EXPORTACIONES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "exportaciones")

ENCABEZADOS = ["ID", "Nombre", "Descripción", "Cantidad", "Precio", "Categoría"]


def exportar_csv(productos, nombre_archivo):
    """Guarda los productos en exportaciones/<nombre_archivo>_<fecha y hora>.csv
    y devuelve la ruta del archivo creado."""
    # exist_ok=True: si la carpeta ya existe no da error
    os.makedirs(CARPETA_EXPORTACIONES, exist_ok=True)

    # La fecha y hora en el nombre evita pisar exportaciones anteriores
    fecha_hora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    ruta = os.path.join(CARPETA_EXPORTACIONES, f"{nombre_archivo}_{fecha_hora}.csv")

    # newline="" lo pide el módulo csv para que no queden líneas en blanco de más en Windows.
    # "utf-8-sig" agrega una marca al inicio del archivo para que Excel muestre bien tildes y eñes.
    with open(ruta, "w", newline="", encoding="utf-8-sig") as archivo:
        # Excel en español usa ";" para separar columnas, porque la "," es el separador decimal
        escritor = csv.writer(archivo, delimiter=";")
        escritor.writerow(ENCABEZADOS)
        for producto in productos:
            escritor.writerow([
                producto["id"],
                producto["nombre"],
                producto["descripcion"] or "",  # "or" reemplaza None (campo vacío) por ""
                producto["cantidad"],
                f"{producto['precio']:.2f}".replace(".", ","),  # 2500.5 -> "2500,50"
                producto["categoria"] or "",
            ])
    return ruta
