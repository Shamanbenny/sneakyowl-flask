from functools import wraps

from firebase_admin import auth
from flask import g, jsonify, request

from api.core.firebase import get_firestore_client


def require_firebase_user(handler):
    @wraps(handler)
    def wrapped(*args, **kwargs):
        if request.method == "OPTIONS":
            return "", 204

        authorization = request.headers.get("Authorization", "")
        scheme, _, id_token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not id_token:
            return jsonify({"error": "A Firebase ID token is required."}), 401

        try:
            # Initialising Admin here preserves the previous behavior: a missing
            # backend Firebase configuration is reported as an auth failure.
            get_firestore_client()
            g.firebase_user = auth.verify_id_token(id_token)
        except Exception:
            return jsonify({"error": "Your Firebase session could not be verified."}), 401

        return handler(*args, **kwargs)

    return wrapped
