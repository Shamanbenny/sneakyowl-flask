from firebase_admin import auth

from api.core.firestore import delete_in_batches
from api.core.firebase import get_firestore_client
from api.tools.bite_trail.service import delete_bite_trail_data


def delete_account(uid: str) -> None:
    database = get_firestore_client()
    user = database.collection("users").document(uid)
    # This removes all BiteTrail visits, relationships, and configuration while
    # retaining shared-account cleanup below.
    delete_bite_trail_data(uid)
    delete_in_batches([user])
    try:
        auth.delete_user(uid)
    except auth.UserNotFoundError:
        # A retry after a partially completed deletion is safe and idempotent.
        pass
