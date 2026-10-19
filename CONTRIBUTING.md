# Contribuir / Contributing

MediLocal es una aplicación local de Python 3.12+ y SQLite. No necesita servicios
externos ni dependencias pip para ejecutarse desde el código fuente; sí requiere
Tkinter/Tk para las ventanas.

1. Creá una rama y usá datos ficticios en una carpeta temporal.
2. Conservá la separación entre interfaz (`medilocal/gui.py`), validación y persistencia.
3. Toda etiqueta nueva debe tener español e inglés en `medilocal/i18n.py`.
4. Probá temas claro y oscuro y tamaños de texto ampliados.
5. Ejecutá `python3 -m unittest discover -v`. Para ventanas, con pantalla disponible:
   `MEDILOCAL_GUI_TESTS=1 python3 -m unittest tests.test_gui -v`.
6. Abrí una pull request describiendo comportamiento, pruebas y limitaciones.

No subas bases de datos, copias, capturas con información personal ni credenciales.
No agregues cálculo de dosis, recomendaciones, red, telemetría o sincronización
como parte de una corrección de interfaz. Esas funciones requieren discutir otro alcance.

Para generar paquetes: `python3 -m pip install -r requirements-build.txt` en un
entorno de construcción separado y luego
`python3 -m PyInstaller --noconfirm --clean --onedir --windowed --name MediLocal app.py`.
La construcción debe realizarse en cada sistema destino; el flujo de GitHub Actions
lo hace en Linux y Windows y prueba cada ejecutable con `--smoke-test`.

## English

Use fictitious data, include Spanish and English UI strings, keep the application
offline, and test both themes and enlarged text. Run the unit and optional native
GUI tests above. Do not commit personal databases or screenshots. Pull requests
should explain behavior, evidence and untested platforms. Build separately on
each target OS; do not claim manual accessibility coverage from automated checks.
