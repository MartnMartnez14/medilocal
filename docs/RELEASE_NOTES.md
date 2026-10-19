# MediLocal 2.0.0 beta 2 — diagnóstico / diagnostic build

Esta beta investiga un error persistente de «Ver detalles» reportado en Linux.
**La causa aún no está confirmada; esta publicación no anuncia el fallo como resuelto.**

- El mensaje de error permite **Copiar diagnóstico**: versión, tipo de excepción,
  funciones y líneas de módulos conocidos, entorno técnico y preferencias visuales.
- No incluye nombres, productos, dosis, notas, rutas personales, mensajes completos
  de excepción ni variables locales. No se guarda en un archivo ni se envía por red.
- Si falla la construcción de una ventana, se cierra la ventana incompleta y se
  libera el control. Las ventanas se muestran después de construir su contenido.
- Se amplía la prueba de cada ejecutable: crear un suplemento desde el formulario,
  abrir detalles por botón, Enter y doble clic, y abrir edición en ambos idiomas/temas.

## Cómo probar sin perder tus datos

1. Cerrá MediLocal. Si querés, exportá antes una copia con la beta anterior.
2. Descargá el ZIP de tu sistema y extraé **la carpeta completa en una carpeta nueva**.
3. Abrí el ejecutable nuevo, conservando `_internal` a su lado. No borres ni
   reemplaces la carpeta de datos del usuario: los perfiles y preferencias se reutilizan.
4. Abrí el mismo registro con **Ver detalles**. Si falla, pulsá **Copiar diagnóstico**
   y pegá el texto en el chat o reporte. No adjuntes tu base ni capturas con datos reales.
5. Si abre bien, indicá que el registro ahora se muestra; eso todavía requiere
   verificar el caso antes de dar el fallo por cerrado.

No cambia el esquema de la base ni interpreta tratamientos. Los paquetes siguen
siendo preliminares y sin firma digital. Windows se comprueba automáticamente;
la validación manual y los lectores de pantalla siguen pendientes.

## English

This is a **diagnostic beta**, not a confirmed fix for the Linux details-dialog issue.
Errors offer **Copy diagnostic**, containing allowlisted technical metadata and
function/line references only. No personal entries, paths, full exception messages,
source lines or local variables are included. No diagnostic files or network
transmissions are created. Copying happens only when explicitly requested.

Close MediLocal, extract the whole ZIP into a **new folder**, and open the new
executable with `_internal` alongside it. Existing profiles and preferences remain
in the OS user's data directory; do not delete or replace that directory. Open the
same entry, copy the diagnostic if it fails, and report the result without attaching
personal databases. The schema is unchanged. Automated packaging checks now cover
actual details actions and editing in both languages and themes.
