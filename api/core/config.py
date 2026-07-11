import os


def allowed_origins() -> set[str]:
    configured = os.environ.get("ALLOWED_ORIGINS", "")
    return {origin.strip() for origin in configured.split(",") if origin.strip()}
