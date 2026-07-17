from firebase_admin import auth

from api.core.firestore import delete_in_batches
from api.core.firebase import get_firestore_client
from api.tools.bite_trail.service import delete_bite_trail_data


def delete_account(uid: str) -> None:
    database = get_firestore_client()
    user = database.collection("users").document(uid)
    # This removes each visit before its parent place, all own preferences and
    # relationship documents, and inbound watch-list copies held by other users.
    delete_bite_trail_data(uid)
    delete_in_batches(
        snapshot.reference for snapshot in user.collection("preferences").stream()
    )
    delete_in_batches(
        snapshot.reference
        for snapshot in database.collection("auditEvents").where("actorUid", "==", uid).stream()
    )
    delete_in_batches(
        snapshot.reference
        for snapshot in database.collection("auditEvents").where("targetUid", "==", uid).stream()
    )
    delete_in_batches([user])
    auth.delete_user(uid)
