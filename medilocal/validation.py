"""Shared validation for desktop and terminal; no dosage interpretation."""
import re


class ValidationError(ValueError):
    def __init__(self, field, key):
        self.field, self.key = field, key
        super().__init__(key)


def text(value, field, limit, required=True):
    if not isinstance(value, str):
        raise ValidationError(field, "invalid_text")
    value = value.strip()
    if required and not value:
        raise ValidationError(field, "required")
    if len(value) > limit:
        raise ValidationError(field, "too_long")
    if "\x00" in value:
        raise ValidationError(field, "invalid_text")
    return value


def valid_time(value):
    return isinstance(value, str) and re.fullmatch(r"(?:[01][0-9]|2[0-3]):[0-5][0-9]", value) is not None


def times(value):
    entries = value.split(",") if isinstance(value, str) else value
    if not isinstance(entries, (list, tuple)) or not entries:
        raise ValidationError("horarios", "invalid_times")
    cleaned = []
    for entry in entries:
        if not isinstance(entry, str) or not valid_time(entry.strip()):
            raise ValidationError("horarios", "invalid_times")
        cleaned.append(entry.strip())
    if len(cleaned) > 24:
        raise ValidationError("horarios", "too_many_times")
    return sorted(set(cleaned))


def profile_values(name, kind):
    name = text(name, "nombre", 100)
    if kind not in ("Persona", "Mascota"):
        raise ValidationError("tipo", "invalid_choice")
    return name, kind


def product_values(kind, name, amount, schedule, notes):
    if kind not in ("Medicamento", "Suplemento"):
        raise ValidationError("tipo", "invalid_choice")
    return (kind, text(name, "nombre", 200), text(amount, "cantidad", 300),
            times(schedule), text(notes, "notas", 4000, False))
