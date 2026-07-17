from flask import Blueprint, current_app, g, jsonify, request

from api.account.service import delete_account
from api.tools.bite_trail.service import update_display_name
from api.core.auth import require_firebase_user

account_api = Blueprint("account_api", __name__)


@account_api.route("/v1/account", methods=["DELETE", "OPTIONS"])
@require_firebase_user
def delete_account_route():
    payload = request.get_json(silent=True) or {}
    email = payload.get("email")
    if not isinstance(email, str):
        return jsonify({"error": "Your Gmail address is required to delete an account."}), 400

    authenticated_email = g.firebase_user.get("email")
    if not isinstance(authenticated_email, str) or email.strip().lower() != authenticated_email.lower():
        return jsonify({"error": "The Gmail-address confirmation did not match."}), 400

    try:
        delete_account(g.firebase_user["uid"])
    except Exception:
        current_app.logger.exception(
            "Account deletion failed for Firebase UID %s", g.firebase_user["uid"]
        )
        return jsonify({"error": "Account deletion failed on the server."}), 500

    return "", 204


@account_api.route("/v1/account/profile", methods=["POST", "OPTIONS"])
@require_firebase_user
def update_account_profile_route():
    payload = request.get_json(silent=True) or {}
    display_name = payload.get("displayName")
    if not isinstance(display_name, str) or not display_name.strip():
        return jsonify({"error": "Display name cannot be empty."}), 400

    try:
        update_display_name(g.firebase_user["uid"], display_name.strip())
    except Exception:
        current_app.logger.exception(
            "Display-name update failed for Firebase UID %s", g.firebase_user["uid"]
        )
        return jsonify({"error": "Profile update failed on the server."}), 500

    return "", 204
