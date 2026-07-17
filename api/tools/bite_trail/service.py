from firebase_admin import firestore

from api.core.firebase import get_firestore_client
from api.core.firestore import delete_in_batches


def delete_visit(owner_uid: str, place_id: str, visit_id: str) -> None:
    database = get_firestore_client()
    place = (
        database.collection("users")
        .document(owner_uid)
        .collection("places")
        .document(place_id)
    )
    visit = place.collection("visits").document(visit_id)
    transaction = database.transaction()

    @firestore.transactional
    def delete_visit_transaction(transaction):
        visit_snapshot = visit.get(transaction=transaction)
        if not visit_snapshot.exists:
            return

        remaining = list(transaction.get(place.collection("visits").limit(2)))
        transaction.delete(visit)
        if len(remaining) <= 1:
            transaction.delete(place)
        transaction.set(database.collection("auditEvents").document(), {
            "actorUid": owner_uid,
            "action": "visit_deleted",
            "placeId": place_id,
            "visitId": visit_id,
            "createdAt": firestore.SERVER_TIMESTAMP,
        })

    delete_visit_transaction(transaction)


def remove_friend(actor_uid: str, friend_uid: str) -> None:
    database = get_firestore_client()
    batch = database.batch()
    batch.delete(
        database.collection("users")
        .document(actor_uid)
        .collection("following")
        .document(friend_uid)
    )
    batch.delete(
        database.collection("users")
        .document(friend_uid)
        .collection("following")
        .document(actor_uid)
    )
    batch.set(database.collection("auditEvents").document(), {
        "actorUid": actor_uid,
        "action": "friend_removed",
        "targetUid": friend_uid,
        "createdAt": firestore.SERVER_TIMESTAMP,
    })
    batch.commit()


def revoke_viewer(owner_uid: str, viewer_uid: str) -> None:
    database = get_firestore_client()
    batch = database.batch()
    batch.delete(
        database.collection("users")
        .document(viewer_uid)
        .collection("following")
        .document(owner_uid)
    )
    batch.set(
        database.collection("users")
        .document(owner_uid)
        .collection("blockedViewers")
        .document(viewer_uid),
        {"createdAt": firestore.SERVER_TIMESTAMP},
    )
    batch.commit()


def delete_bite_trail_data(uid: str) -> None:
    database = get_firestore_client()
    user = database.collection("users").document(uid)

    place_references = []
    for place in user.collection("places").stream():
        delete_in_batches(
            visit.reference for visit in place.reference.collection("visits").stream()
        )
        place_references.append(place.reference)
    delete_in_batches(place_references)
    following_snapshots = list(user.collection("following").stream())
    delete_in_batches(snapshot.reference for snapshot in following_snapshots)
    delete_in_batches(
        snapshot.reference for snapshot in user.collection("blockedViewers").stream()
    )
    # Keep the shared SneakyOwl profile document. Only BiteTrail-owned data is removed.
    delete_in_batches([user.collection("preferences").document("bite-trail")])

    # Following relationships are written bidirectionally. Delete each
    # reciprocal document directly so account deletion does not depend on a
    # collection-group index for `following.ownerUid`.
    delete_in_batches(
        database.collection("users")
        .document(snapshot.id)
        .collection("following")
        .document(uid)
        for snapshot in following_snapshots
    )

    # Also clean up legacy one-sided relationships. These can remain under
    # another user's following subcollection when the deleted account has no
    # reciprocal document of its own.
    other_user_following = []
    for other_user in database.collection("users").stream():
        if other_user.id == uid:
            continue

        following_reference = other_user.reference.collection("following").document(uid)
        if following_reference.get().exists:
            other_user_following.append(following_reference)

    delete_in_batches(other_user_following)
