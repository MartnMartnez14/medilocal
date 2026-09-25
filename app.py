from database import conectar, crear_base_datos


# =========================
# PERFILES
# =========================

def crear_perfil():
    print("\n--- Crear perfil ---")

    nombre = input("Nombre o apodo: ").strip()

    if not nombre:
        print("⚠ El nombre no puede estar vacío.")
        return

    print("\nTipo de perfil:")
    print("1. Persona")
    print("2. Mascota")

    opcion = input("Elegí una opción: ").strip()

    if opcion == "1":
        tipo = "Persona"
    elif opcion == "2":
        tipo = "Mascota"
    else:
        print("⚠ Opción no válida.")
        return

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute(
        "INSERT INTO perfiles (nombre, tipo) VALUES (?, ?)",
        (nombre, tipo)
    )

    conexion.commit()
    conexion.close()

    print(f"\n✓ Perfil '{nombre}' creado correctamente.")


def obtener_perfiles():
    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute(
        "SELECT id, nombre, tipo FROM perfiles ORDER BY nombre"
    )

    perfiles = cursor.fetchall()

    conexion.close()

    return perfiles


def ver_perfiles():
    perfiles = obtener_perfiles()

    print("\n--- Perfiles ---")

    if not perfiles:
        print("Todavía no hay perfiles.")
        return

    for id_perfil, nombre, tipo in perfiles:

        if tipo == "Persona":
            icono = "🧑"
        else:
            icono = "🐾"

        print(f"{id_perfil}. {icono} {nombre} — {tipo}")


# =========================
# MEDICAMENTOS / SUPLEMENTOS
# =========================

def agregar_producto(perfil_id, nombre_perfil):

    print(f"\n--- Agregar a {nombre_perfil} ---")

    print("\n¿Qué querés registrar?")
    print("1. 💊 Medicamento")
    print("2. 🥛 Suplemento")

    opcion = input("\nElegí una opción: ").strip()

    if opcion == "1":
        tipo = "Medicamento"

    elif opcion == "2":
        tipo = "Suplemento"

    else:
        print("⚠ Opción no válida.")
        return

    nombre = input("\nNombre: ").strip()

    if not nombre:
        print("⚠ El nombre no puede estar vacío.")
        return

    cantidad = input("Cantidad / dosis indicada: ").strip()

    if not cantidad:
        print("⚠ La cantidad no puede estar vacía.")
        return

    hora = input("Hora (HH:MM): ").strip()

    if not hora:
        print("⚠ La hora no puede estar vacía.")
        return

    notas = input("Notas (opcional): ").strip()

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        INSERT INTO productos
        (perfil_id, tipo, nombre, cantidad, hora, notas)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        perfil_id,
        tipo,
        nombre,
        cantidad,
        hora,
        notas
    ))

    conexion.commit()
    conexion.close()

    print(
        f"\n✓ {tipo} '{nombre}' agregado "
        f"correctamente a {nombre_perfil}."
    )


def ver_productos(perfil_id):

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT id, tipo, nombre, cantidad, hora, notas
        FROM productos
        WHERE perfil_id = ?
        ORDER BY hora
    """, (perfil_id,))

    productos = cursor.fetchall()

    conexion.close()

    print("\n--- Medicamentos y suplementos ---")

    if not productos:
        print("Todavía no hay registros.")
        return

    for id_producto, tipo, nombre, cantidad, hora, notas in productos:

        if tipo == "Medicamento":
            icono = "💊"
        else:
            icono = "🥛"


        print(f"\n{id_producto}. {icono} {nombre}")
        print(f"   Tipo: {tipo}")
        print(f"   Cantidad: {cantidad}")
        print(f"   Hora: {hora}")

        if notas:
            print(f"   Notas: {notas}")

def eliminar_producto(perfil_id):

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT id, tipo, nombre
        FROM productos
        WHERE perfil_id = ?
        ORDER BY hora
    """, (perfil_id,))

    productos = cursor.fetchall()

    if not productos:
        print("\nTodavía no hay registros para eliminar.")
        conexion.close()
        return

    print("\n--- Eliminar medicamento/suplemento ---")

    for id_producto, tipo, nombre in productos:
        print(f"{id_producto}. {nombre} ({tipo})")

    print("\n0. Volver")

    entrada = input("\nIngresá el ID del registro: ").strip()

    if entrada == "0":
        conexion.close()
        return

    try:
        producto_id = int(entrada)
    except ValueError:
        print("⚠ Tenés que ingresar un número.")
        conexion.close()
        return

    producto_encontrado = None

    for producto in productos:

        if producto[0] == producto_id:
            producto_encontrado = producto
            break

    if producto_encontrado is None:
        print("⚠ Ese ID no existe en este perfil.")
        conexion.close()
        return

    _, tipo, nombre = producto_encontrado

    confirmacion = input(
        f'\n¿Seguro que querés eliminar "{nombre}"? (s/n): '
    ).strip().lower()

    if confirmacion != "s":
        print("Eliminación cancelada.")
        conexion.close()
        return

    cursor.execute(
        "DELETE FROM productos WHERE id = ? AND perfil_id = ?",
        (producto_id, perfil_id)
    )

    conexion.commit()
    conexion.close()

    print(f'\n✓ "{nombre}" eliminado correctamente.')

def editar_producto(perfil_id):

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT id, tipo, nombre, cantidad, hora, notas
        FROM productos
        WHERE perfil_id = ?
        ORDER BY hora
    """, (perfil_id,))

    productos = cursor.fetchall()

    if not productos:
        print("\nTodavía no hay registros para editar.")
        conexion.close()
        return

    print("\n--- Editar medicamento/suplemento ---")

    for id_producto, tipo, nombre, cantidad, hora, notas in productos:

        if tipo == "Medicamento":
            icono = "💊"
        else:
            icono = "🥛"

        print(f"{id_producto}. {icono} {nombre}")

    print("\n0. Volver")

    entrada = input("\nIngresá el ID del registro a editar: ").strip()

    if entrada == "0":
        conexion.close()
        return

    try:
        producto_id = int(entrada)
    except ValueError:
        print("⚠ Tenés que ingresar un número.")
        conexion.close()
        return

    producto_encontrado = None

    for producto in productos:

        if producto[0] == producto_id:
            producto_encontrado = producto
            break

    if producto_encontrado is None:
        print("⚠ Ese ID no existe en este perfil.")
        conexion.close()
        return

    _, tipo, nombre, cantidad, hora, notas = producto_encontrado

    print(f"\nEditando: {nombre}")
    print("Presioná Enter para mantener el valor actual.")

    nuevo_nombre = input(
        f"Nombre [{nombre}]: "
    ).strip()

    nueva_cantidad = input(
        f"Cantidad [{cantidad}]: "
    ).strip()

    nueva_hora = input(
        f"Hora [{hora}]: "
    ).strip()

    nuevas_notas = input(
        f"Notas [{notas or 'sin notas'}]: "
    ).strip()

    if not nuevo_nombre:
        nuevo_nombre = nombre

    if not nueva_cantidad:
        nueva_cantidad = cantidad

    if not nueva_hora:
        nueva_hora = hora

    if not nuevas_notas:
        nuevas_notas = notas

    cursor.execute("""
        UPDATE productos
        SET nombre = ?, cantidad = ?, hora = ?, notas = ?
        WHERE id = ? AND perfil_id = ?
    """, (
        nuevo_nombre,
        nueva_cantidad,
        nueva_hora,
        nuevas_notas,
        producto_id,
        perfil_id
    ))

    conexion.commit()
    conexion.close()

    print(f'\n✓ "{nuevo_nombre}" actualizado correctamente.')

# =========================
# PERFIL
# =========================

def eliminar_producto(perfil_id):

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT id, tipo, nombre
        FROM productos
        WHERE perfil_id = ?
        ORDER BY hora
    """, (perfil_id,))

    productos = cursor.fetchall()

    if not productos:
        print("\nTodavía no hay medicamentos o suplementos para eliminar.")
        conexion.close()
        return

    print("\n--- Eliminar medicamento/suplemento ---")

    for id_producto, tipo, nombre in productos:

        if tipo == "Medicamento":
            icono = "💊"
        else:
            icono = "🥛"

        print(f"{id_producto}. {icono} {nombre}")

    print("\n0. Volver")

    entrada = input("\nIngresá el ID del registro a eliminar: ").strip()

    if entrada == "0":
        conexion.close()
        return

    try:
        producto_id = int(entrada)
    except ValueError:
        print("⚠ Tenés que ingresar un número.")
        conexion.close()
        return

    producto_encontrado = None

    for producto in productos:

        if producto[0] == producto_id:
            producto_encontrado = producto
            break

    if producto_encontrado is None:
        print("⚠ Ese ID no existe.")
        conexion.close()
        return

    _, tipo, nombre = producto_encontrado

    confirmacion = input(
        f'\n¿Seguro que querés eliminar "{nombre}"? (s/n): '
    ).strip().lower()

    if confirmacion != "s":
        print("Eliminación cancelada.")
        conexion.close()
        return

    cursor.execute(
        "DELETE FROM productos WHERE id = ? AND perfil_id = ?",
        (producto_id, perfil_id)
    )

    conexion.commit()
    conexion.close()

    print(f'\n✓ "{nombre}" eliminado correctamente.')

def abrir_perfil():

    perfiles = obtener_perfiles()

    if not perfiles:
        print("\n⚠ Primero tenés que crear un perfil.")
        return

    print("\n--- Seleccionar perfil ---")

    for id_perfil, nombre, tipo in perfiles:

        icono = "🧑" if tipo == "Persona" else "🐾"

        print(f"{id_perfil}. {icono} {nombre}")

    entrada = input(
        "\nIngresá el número del perfil "
        "(o 0 para volver): "
    ).strip()

    if entrada == "0":
        return

    try:
        perfil_id = int(entrada)
    except ValueError:
        print("⚠ Tenés que ingresar un número.")
        return

    perfil_seleccionado = None

    for perfil in perfiles:

        if perfil[0] == perfil_id:
            perfil_seleccionado = perfil
            break

    if perfil_seleccionado is None:
        print("⚠ Ese perfil no existe.")
        return

    _, nombre, tipo = perfil_seleccionado

    menu_perfil(perfil_id, nombre, tipo)


def menu_perfil(perfil_id, nombre, tipo):

    while True:

        icono = "🧑" if tipo == "Persona" else "🐾"

        print("\n========================")
        print(f"   {icono} {nombre}")
        print("========================")

        print("1. Agregar medicamento/suplemento")
        print("2. Ver medicamentos/suplementos")
        print("3. Editar medicamento/suplemento")
        print("4. Eliminar medicamento/suplemento")
        print("5. Volver")

        opcion = input("\nElegí una opción: ").strip()

        if opcion == "1":
            agregar_producto(perfil_id, nombre)

        elif opcion == "2":
            ver_productos(perfil_id)

        elif opcion == "3":
            editar_producto(perfil_id)

        elif opcion == "4":
            eliminar_producto(perfil_id)

        elif opcion == "5":
            break

        else:
            print("⚠ Opción no válida.")

# =========================
# MENÚ PRINCIPAL
# =========================

def menu():

    crear_base_datos()

    while True:

        print("\n========================")
        print("      💊 MediLocal")
        print("========================")

        print("1. Crear perfil")
        print("2. Ver perfiles")
        print("3. Abrir perfil")
        print("4. Salir")

        opcion = input("\nElegí una opción: ").strip()

        if opcion == "1":
            crear_perfil()

        elif opcion == "2":
            ver_perfiles()

        elif opcion == "3":
            abrir_perfil()

        elif opcion == "4":
            print("\nHasta luego 👋")
            break

        else:
            print("\n⚠ Opción no válida.")


if __name__ == "__main__":
    menu()
