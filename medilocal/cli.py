"""Terminal fallback using the same Store and validation as the desktop UI."""
import sqlite3

from .i18n import tr
from .store import DataError
from .validation import ValidationError


def run(store, language="es"):
    def t(key, **kw):
        return tr(key, language, **kw)

    def confirm(message):
        print(message)
        return input(t("terminal_confirm")).strip() == t("yes")

    def choose(rows):
        for row in rows:
            print(f'{row["id"]}. {row["nombre"]} ({t(row["tipo"])})')
        value = int(input(t("id")))
        row = next((row for row in rows if row["id"] == value), None)
        if row is None:
            raise DataError("not_found")
        return row

    def profile_form(row=None):
        row = row or {}
        name = input(t("nombre") + ": ")
        print(f'1. {t("Persona")}  2. {t("Mascota")}')
        choice = input(t("choice"))
        if choice not in ("1", "2"):
            raise DataError("invalid_choice")
        store.save_profile(name, ("Persona", "Mascota")[int(choice)-1], row.get("id"))

    def product_form(profile_id, row=None):
        row = row or {}
        if row.get("hora_original") is not None and row:
            print(t("legacy_warning", hour=row["hora_original"]))
        print(f'1. {t("Medicamento")}  2. {t("Suplemento")}')
        choice = input(t("choice"))
        if choice not in ("1", "2"):
            raise DataError("invalid_choice")
        name = input(t("nombre") + ": ")
        amount = input(t("cantidad") + ": ")
        hours = input(t("horarios") + ": ")
        notes = input(t("notas") + ": ")
        store.save_product(profile_id, ("Medicamento", "Suplemento")[int(choice)-1], name, amount, hours, notes, row.get("id"))

    def products(profile):
        while True:
            print(profile["nombre"])
            print(t("terminal_products"))
            option = input(t("choice"))
            if option == "0":
                return
            rows = store.products(profile["id"])
            if option == "1":
                for row in rows:
                    hours = ", ".join(row["horarios"]) if row["hora_original"] is None else t("legacy_warning", hour=row["hora_original"])
                    print(f'{row["id"]}. {row["nombre"]} ({t(row["tipo"])}) | {row["cantidad"]} | {hours}\n{row["notas"]}')
                if not rows:
                    print(t("empty"))
            elif option == "2":
                product_form(profile["id"])
            elif option == "3":
                row = choose(rows)
                print(row["nombre"], row["cantidad"], row["horarios"], row["notas"])
                product_form(profile["id"], row)
            elif option == "4":
                row = choose(rows)
                if confirm(t("confirm_product", name=row["nombre"])):
                    store.delete_product(profile["id"], row["id"])
            else:
                print(t("invalid_choice"))

    print("MediLocal")
    print(t("footer"))
    while True:
        try:
            print(t("terminal_menu"))
            option = input(t("choice"))
            if option == "0":
                return
            if option == "1":
                for row in store.profiles():
                    print(f'{row["id"]}. {row["nombre"]} ({t(row["tipo"])})')
            elif option == "2":
                profile_form()
            elif option == "3":
                products(choose(store.profiles()))
            elif option == "4":
                row = choose(store.profiles())
                print(row["nombre"], t(row["tipo"]))
                profile_form(row)
            elif option == "5":
                row = choose(store.profiles())
                if confirm(t("confirm_profile", name=row["nombre"], count=len(store.products(row["id"])))):
                    store.delete_profile(row["id"])
            elif option == "6":
                print(t("backup_info"))
                print(t("data_location", path=store.path.parent))
                print(t("terminal_backups"))
                op = input(t("choice"))
                if op == "0":
                    continue
                if op not in ("1", "2", "3"):
                    print(t("invalid_choice"))
                    continue
                path = input(t("path"))
                if not path:
                    continue
                if op == "1":
                    from pathlib import Path
                    if Path(path).exists() and not confirm(t("export") + " — " + path):
                        continue
                    store.backup(path)
                    print(t("export_done", path=path))
                elif op == "2" and confirm(t("restore_confirm")):
                    print(t("restore_done", path=store.restore(path)))
                elif op == "3" and confirm(t("import_confirm")):
                    print(t("import_done", count=store.import_legacy(path)))
            else:
                print(t("invalid_choice"))
        except ValidationError as error:
            print(t(error.field) + ": " + t(error.key))
        except DataError as error:
            print(t(str(error)))
        except (sqlite3.Error, OSError):
            print(t("storage_error"))
        except ValueError:
            print(t("invalid_choice"))
        except (EOFError, KeyboardInterrupt):
            return
