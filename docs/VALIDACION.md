# Validación — MediLocal 2.0.0b1

Fecha de referencia: 19 de octubre de 2026. Todas las pruebas y capturas usan
perfiles y productos ficticios. La base antigua del equipo no fue importada ni
modificada para desarrollar o verificar esta versión.

## Evidencia local

- Python 3.12.3, Tk 8.6.14 y SQLite del sistema en Linux.
- 28 pruebas automatizadas de datos, migración, copias, preferencias, bloqueo y CLI.
- 5 pruebas adicionales de ventanas nativas, habilitadas con `MEDILOCAL_GUI_TESTS=1`.
- Idiomas español/inglés y temas claro/oscuro recorridos en las pantallas de perfiles,
  productos y copias. Verificación de persistencia de idioma, tema y texto a 20 puntos.
- Formularios reales: entrada inválida no guarda; corrección y guardado crea un
  registro con múltiples horarios. Apertura de formularios y detalles, cancelación
  de selectores de archivos y eliminación cancelada.
- Capturas reales del área cliente de MediLocal en las cuatro combinaciones de
  idioma/tema, revisadas visualmente. No son imágenes generadas de una aplicación futura.
- Fallos simulados de escritura: conservan el destino anterior o la base activa,
  según corresponda; la restauración no continúa si falla el respaldo previo.
- Copias corruptas, versiones incompatibles, disparadores y relaciones huérfanas
  rechazados. Importación antigua conserva IDs y horarios inválidos, incluso vacíos.
- El historial local versionado contiene los archivos fuente originales, README y
  `.gitignore`; no contiene bases SQLite. La publicación se hace con una lista explícita
  de fuentes, documentación, pruebas y capturas ficticias.

## Construcción y publicación

El flujo `desktop.yml` ejecuta pruebas, construye una carpeta autónoma con
PyInstaller en Ubuntu 22.04 x64 y Windows Server 2022 x64, y ejecuta el binario
resultante con `--smoke-test`. Esa opción usa una carpeta temporal y verifica
datos, respaldo/restauración y ventanas en los dos idiomas y temas.

Los ZIP incluyen ejecutable, `_internal`, README y avisos de licencias. Se genera
un SHA-256 para cada ZIP. Las versiones etiquetadas `v2.*` se publican como
**preliminares**, nunca como una versión estable por este flujo.

El estado real y los registros de cada construcción están en
[GitHub Actions](https://github.com/MartnMartnez14/medilocal/actions). La existencia
de este archivo de flujo no demuestra por sí sola una ejecución exitosa.

## Límites y verificaciones pendientes

- Sin validación manual en un equipo Windows de usuario final. El runner de CI
  no representa todas las versiones y configuraciones de Windows.
- Sin prueba en una máquina limpia sin Python instalado: el empaquetado incluye
  el intérprete, pero la prueba de CI se realiza en un entorno de construcción.
- Sin pruebas con Orca, NVDA, JAWS u otros lectores de pantalla. Usar controles
  ttk estándar no basta para afirmar compatibilidad con ellos.
- La prueba automatizada de apertura no demuestra un recorrido manual completo
  con teclado, foco, escala del sistema ni distintas resoluciones.
- Se conservan los diálogos nativos del sistema (archivos y confirmaciones): su
  apariencia y parte de sus botones dependen del idioma y tema del sistema operativo.
- Sin certificación WCAG ni auditoría independiente de seguridad o validación clínica.
- Sin macOS, ARM, sistemas de 32 bits, red multiusuario ni bases activas sincronizadas.
- Los paquetes no están firmados digitalmente y pueden generar advertencias del sistema.

## Criterio de aceptación manual antes de una versión estable

En Linux y Windows, con carpetas de prueba:

1. Extraer el ZIP en un equipo sin Python y abrir sin terminal ni permisos elevados.
2. Crear y editar perfiles de persona y mascota; agregar, editar y borrar productos.
3. Recorrer todo con Tab/Shift+Tab, Enter, Espacio y Escape, verificando el foco.
4. Cambiar ambos temas e idiomas, aumentar texto, reducir ventana y comprobar que
   controles, errores, notas y confirmaciones sigan siendo legibles y alcanzables.
5. Probar un lector de pantalla por sistema y registrar controles que no anuncie.
6. Cerrar/reabrir, actualizar la carpeta del programa y comprobar datos y preferencias.
7. Exportar, modificar datos y restaurar; revisar el respaldo previo y cancelar otra
   restauración. Importar una base antigua ficticia con horario válido e inválido.

## English

Local automated checks cover persistence, validation, migration, backups and CLI,
plus opt-in native GUI tests. Four language/theme screenshots were visually
reviewed on Linux. CI builds and smoke-tests each platform separately. Neither
CI nor standard ttk widgets establish manual Windows, clean-machine, keyboard or
screen-reader compatibility. Those checks remain required before a stable release.
