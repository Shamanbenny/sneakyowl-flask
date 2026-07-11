from flask import Flask, request

from api.core.config import allowed_origins


def configure_cors(application: Flask) -> None:
    @application.after_request
    def add_cors_headers(response):
        origin = request.headers.get("Origin")
        if origin and origin in allowed_origins():
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Vary"] = "Origin"
            response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type, Idempotency-Key"
            response.headers["Access-Control-Allow-Methods"] = "DELETE, POST, OPTIONS"
        return response
