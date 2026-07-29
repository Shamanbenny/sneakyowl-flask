from flask import Blueprint, g, jsonify

from api.core.auth import require_firebase_user
from api.core.validation import document_id, firebase_uid
from api.tools.bite_trail.service import (
    create_friend,
    delete_bite_trail_data,
    delete_visit,
    get_visible_places,
    remove_friend,
    revoke_viewer,
)

bite_trail_api = Blueprint("bite_trail_api", __name__)


@bite_trail_api.route(
    "/v1/bite-trail/visits/<place_id>/<visit_id>",
    methods=["DELETE", "OPTIONS"],
)
@require_firebase_user
def delete_visit_route(place_id: str, visit_id: str):
    try:
        place_id = document_id(place_id, "place ID")
        visit_id = document_id(visit_id, "visit ID")
        delete_visit(g.firebase_user["uid"], place_id, visit_id)
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    except PermissionError as error:
        return jsonify({"error": str(error)}), 403
    return "", 204


@bite_trail_api.route("/v1/bite-trail/places", methods=["GET", "OPTIONS"])
@require_firebase_user
def visible_places_route():
    return jsonify(get_visible_places(g.firebase_user["uid"]))


@bite_trail_api.route(
    "/v1/bite-trail/friends/<friend_uid>",
    methods=["POST", "OPTIONS"],
)
@require_firebase_user
def create_friend_route(friend_uid: str):
    try:
        friend_uid = firebase_uid(friend_uid, "friend UID")
        create_friend(g.firebase_user["uid"], friend_uid)
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    return "", 204


@bite_trail_api.route(
    "/v1/bite-trail/friends/<friend_uid>",
    methods=["DELETE", "OPTIONS"],
)
@require_firebase_user
def remove_friend_route(friend_uid: str):
    try:
        friend_uid = firebase_uid(friend_uid, "friend UID")
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    remove_friend(g.firebase_user["uid"], friend_uid)
    return "", 204


@bite_trail_api.route(
    "/v1/bite-trail/viewers/<viewer_uid>/revoke",
    methods=["POST", "OPTIONS"],
)
@require_firebase_user
def revoke_viewer_route(viewer_uid: str):
    try:
        viewer_uid = firebase_uid(viewer_uid, "viewer UID")
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    revoke_viewer(g.firebase_user["uid"], viewer_uid)
    return "", 204


@bite_trail_api.route("/v1/bite-trail/data", methods=["DELETE", "OPTIONS"])
@require_firebase_user
def delete_bite_trail_data_route():
    delete_bite_trail_data(g.firebase_user["uid"])
    return "", 204
