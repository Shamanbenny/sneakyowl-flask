import unicodedata


def _contains_control_character(value: str) -> bool:
    return any(unicodedata.category(character) == "Cc" for character in value)


def json_object(payload) -> dict:
    if not isinstance(payload, dict):
        raise ValueError("The request body must be a JSON object.")
    return payload


def document_id(value, field_name: str, maximum_length: int = 1500) -> str:
    if (
        not isinstance(value, str)
        or not value
        or len(value.encode("utf-8")) > maximum_length
        or "/" in value
        or _contains_control_character(value)
    ):
        raise ValueError(f"Invalid {field_name}.")
    return value


def firebase_uid(value, field_name: str) -> str:
    return document_id(value, field_name, maximum_length=128)


def display_name(value) -> str:
    if not isinstance(value, str):
        raise ValueError("Display name cannot be empty.")

    normalized = unicodedata.normalize("NFKC", value).strip()
    if (
        not normalized
        or len(normalized) > 80
        or _contains_control_character(normalized)
    ):
        raise ValueError("Display name must be 1 to 80 characters without control characters.")
    return normalized


def email_confirmation(value) -> str:
    if not isinstance(value, str):
        raise ValueError("Your Gmail address is required to delete an account.")

    normalized = value.strip().casefold()
    if not normalized or _contains_control_character(normalized):
        raise ValueError("Your Gmail address is required to delete an account.")
    return normalized
