# datos_ejemplo.py
# Productos de prueba (temática videojuegos y mangas) que el programa ofrece
# cargar cuando el inventario está vacío, para poder probar todas las opciones
# sin tener que registrar los productos a mano.

# Algunos tienen poco o nada de stock a propósito, para probar el reporte de bajo stock.

PRODUCTOS_EJEMPLO = [
    # Mangas
    ("Tokyo Ghoul - Tomo 1", "Manga de Sui Ishida, primer tomo", 12, 13500, "Manga"),
    ("Tokyo Ghoul - Tomo 2", "Manga de Sui Ishida, segundo tomo", 8, 13500, "Manga"),
    ("Tokyo Ghoul - Tomo 3", "Manga de Sui Ishida, tercer tomo", 3, 13500, "Manga"),
    ("Tokyo Ghoul:re - Tomo 1", "Secuela de Tokyo Ghoul, primer tomo", 0, 14500, "Manga"),
    ("Tokyo Ghoul - Box completo", "Colección completa de los 14 tomos", 2, 175000, "Manga"),
    ("Fumando atrás del Super - Tomo 1", "Primer tomo de la serie", 15, 11000, "Manga"),
    ("Fumando atrás del Super - Tomo 2", "Segundo tomo de la serie", 6, 11000, "Manga"),
    ("Fumando atrás del Super - Tomo 3", None, 1, 11500, "Manga"),  # sin descripción
    # Videojuegos
    ("Tokyo Ghoul:re Call to Exist", "Juego de acción para PS4", 4, 45000, "Videojuegos"),
    ("Elden Ring", "Juego de rol y acción para PS5", 7, 85000, "Videojuegos"),
    ("Hollow Knight: Silksong", "Metroidvania para Nintendo Switch", 0, 42000, "Videojuegos"),
    ("Zelda: Tears of the Kingdom", "Aventura para Nintendo Switch", 5, 95000, "Videojuegos"),
    # Consolas, accesorios y coleccionables
    ("Nintendo Switch OLED", "Consola con pantalla OLED de 7 pulgadas", 2, 650000, "Consolas"),
    ("Joystick DualSense", "Control inalámbrico para PS5", 9, 120000, "Accesorios"),
    ("Figura Ken Kaneki", "Figura de colección de Tokyo Ghoul, 18 cm", 3, 48000, "Coleccionables"),
]
