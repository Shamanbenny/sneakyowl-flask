from flask import Blueprint, g, jsonify

from api.core.auth import require_firebase_user
from api.tools.bite_trail.service import (
    delete_bite_trail_data,
    delete_visit,
    remove_friend,
    revoke_viewer,
)

bite_trail_api = Blueprint("bite_trail_api", __name__)


@bite_trail_api.route(
    "/v1/bite-trail/visits/<owner_uid>/<place_id>/<visit_id>",
    methods=["DELETE", "OPTIONS"],
)
@require_firebase_user
def delete_visit_route(owner_uid: str, place_id: str, visit_id: str):
    if g.firebase_user["uid"] != owner_uid:
        return jsonify({"error": "You can only delete your own visits."}), 403

    delete_visit(owner_uid, place_id, visit_id)
    return "", 204


@bite_trail_api.route(
    "/v1/bite-trail/friends/<friend_uid>",
    methods=["DELETE", "OPTIONS"],
)
@require_firebase_user
def remove_friend_route(friend_uid: str):
    remove_friend(g.firebase_user["uid"], friend_uid)
    return "", 204


@bite_trail_api.route(
    "/v1/bite-trail/viewers/<viewer_uid>/revoke",
    methods=["POST", "OPTIONS"],
)
@require_firebase_user
def revoke_viewer_route(viewer_uid: str):
    revoke_viewer(g.firebase_user["uid"], viewer_uid)
    return "", 204


@bite_trail_api.route("/v1/bite-trail/data", methods=["DELETE", "OPTIONS"])
@require_firebase_user
def delete_bite_trail_data_route():
    delete_bite_trail_data(g.firebase_user["uid"])
    return "", 204
