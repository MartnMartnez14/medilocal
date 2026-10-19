# Seguridad / Security

Esta versión preliminar guarda todos los perfiles en una base SQLite local.
No está cifrada. Los perfiles no tienen contraseñas ni permisos independientes.
La aplicación no usa la red ni envía datos de salud. Las copias también contienen
información sensible sin cifrar. Protegé tu cuenta del sistema y tus respaldos.

No adjuntes tu base ni datos reales a un issue público. Para una vulnerabilidad,
usá **Security → Advisories → Report a vulnerability** en GitHub si la opción está
habilitada. Si no está disponible, abrí un issue solicitando un canal privado,
sin publicar detalles de explotación ni datos personales.

Solo se acepta una instancia por carpeta de datos. No abras la base con otras
aplicaciones mientras MediLocal está en uso. No se admite almacenar la base activa
en carpetas compartidas o sincronizadas ni utilizarla por red.

Los archivos importados se abren en modo de lectura, se comprueban y se copian
como datos a un esquema conocido: no se ejecutan disparadores ni vistas importadas.
Una restauración valida primero la copia, crea un respaldo del estado actual y
reemplaza el archivo completo. No sustituye una política de copias externas.

## English

The database and backups are **not encrypted**. All profiles are accessible to
anyone using the same OS account. No health information is sent over the network.
Keep backups private. Never attach real databases or personal screenshots to
public issues. Use GitHub private vulnerability reporting when available; otherwise
request a private channel without disclosing vulnerability details publicly.

Only one instance per data directory is supported. Network/shared/synchronized
active databases and external writers are not supported. Invalid backup files are
rejected without replacing the active data. An automatic safety copy is created
before every restore.
