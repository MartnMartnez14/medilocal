# MediLocal 2.0.0 beta 1

Primera interfaz de escritorio en Python/Tkinter, con español e inglés, temas
claro y oscuro, tamaño de texto ajustable y preferencias guardadas por equipo.

- Perfiles de personas y mascotas; medicamentos y suplementos con varios horarios.
- Búsqueda, edición, detalles y eliminación con confirmación.
- Datos locales en la carpeta del usuario, fuera del ejecutable.
- Importación voluntaria desde la versión antigua, sin cambiar el original.
- Copias SQLite consistentes y restauración validada con respaldo previo.
- Alternativa de terminal: `python3 app.py --cli`, desde el código fuente.

Descargá el ZIP de tu sistema y extraé la carpeta completa. Windows: abrí
`MediLocal.exe`. Linux: abrí `MediLocal`; si hace falta, permití su ejecución en
las propiedades del archivo. Conservá `_internal` junto al ejecutable.

Es una versión preliminar, sin firma digital. Los paquetes se generan y se someten
a una prueba automatizada por sistema en GitHub Actions. Eso no demuestra pruebas
manuales de Windows, lectores de pantalla o compatibilidad con todas las
distribuciones Linux. Consultá `docs/VALIDACION.md` en el repositorio.

No incluye recomendaciones, cálculo de dosis, avisos, cuentas ni sincronización.
La base y las copias **no están cifradas**. Todos los perfiles de la misma cuenta
del equipo son accesibles desde la aplicación. No compartas tus archivos de datos.

## English

First desktop beta: Spanish/English, dark/light themes, adjustable text and saved
preferences. Includes people/pet profiles, medication/supplement entries, multiple
daily times, search, safe deletion, backups, validated restore and optional import
from the old CLI database. Extract the whole ZIP and launch MediLocal; keep the
`_internal` folder alongside the executable.

No accounts, synchronization, automated reminders or medical recommendations.
Data and backups are **not encrypted**. Packages are unsigned. Automated CI smoke
checks do not establish manual Windows or screen-reader accessibility coverage.
