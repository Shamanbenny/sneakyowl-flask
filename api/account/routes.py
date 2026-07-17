from flask import Blueprint, g, jsonify, request

from api.account.service import delete_account
from api.core.auth import require_firebase_user

account_api = Blueprint("account_api", __name__)


@account_api.route("/v1/account", methods=["DELETE", "OPTIONS"])
@require_firebase_user
def delete_account_route():
    payload = request.get_json(silent=True) or {}
    email = payload.get("email")
    if not isinstance(email, str):
        return jsonify({"error": "Your Gmail address is required to delete an account."}), 400

    if email != g.firebase_user.get("email"):
        return jsonify({"error": "The Gmail-address confirmation did not match."}), 400

    delete_account(g.firebase_user["uid"])

    return "", 204
