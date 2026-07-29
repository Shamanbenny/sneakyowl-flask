from flask import Blueprint, current_app, g, jsonify, request

from api.account.service import delete_account
from api.tools.bite_trail.service import update_display_name
from api.core.auth import require_firebase_user
from api.core.validation import display_name, email_confirmation, json_object

account_api = Blueprint("account_api", __name__)


@account_api.route("/v1/account", methods=["DELETE", "OPTIONS"])
@require_firebase_user
def delete_account_route():
    try:
        payload = json_object(request.get_json(silent=True))
        if set(payload) != {"email"}:
            raise ValueError("Only the email confirmation may be sent.")
        email = email_confirmation(payload["email"])
    except ValueError as error:
        return jsonify({"error": str(error)}), 400

    authenticated_email = g.firebase_user.get("email")
    if (
        not isinstance(authenticated_email, str)
        or email != authenticated_email.strip().casefold()
    ):
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
    try:
        payload = json_object(request.get_json(silent=True))
        if set(payload) != {"displayName"}:
            raise ValueError("Only displayName may be sent.")
        updated_display_name = display_name(payload["displayName"])
    except ValueError as error:
        return jsonify({"error": str(error)}), 400

    try:
        update_display_name(g.firebase_user["uid"], updated_display_name)
    except Exception:
        current_app.logger.exception(
            "Display-name update failed for Firebase UID %s", g.firebase_user["uid"]
        )
        return jsonify({"error": "Profile update failed on the server."}), 500

    return "", 204
