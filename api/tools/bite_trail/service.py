from collections import defaultdict

from firebase_admin import auth, firestore

from api.core.firebase import get_firestore_client
from api.core.firestore import delete_in_batches
from api.core.validation import display_name as normalize_display_name

SNEAKY_OWL_UID = "AXOel5MZ8Yelb5a1bHgFcieT80y2"


def bite_trail_root(database):
    return database.collection("tools").document("bite-trail")


def following_reference(database, uid: str, friend_uid: str):
    return (
        bite_trail_root(database)
        .collection("followings")
        .document(uid)
        .collection("relationships")
        .document(friend_uid)
    )


def place_reference(database, place_id: str):
    return bite_trail_root(database).collection("places").document(place_id)


def is_bite_trail_visit(visit_reference) -> bool:
    place = visit_reference.parent.parent
    return (
        place is not None
        and place.parent.id == "places"
        and place.parent.parent.id == "bite-trail"
        and place.parent.parent.parent.id == "tools"
    )


def bite_trail_visits_for_owner(uid: str, operator: str):
    database = get_firestore_client()
    return [
        snapshot
        for snapshot in database.collection_group("visits").where(
            filter=firestore.FieldFilter("ownerUid", operator, uid)
        ).stream()
        if is_bite_trail_visit(snapshot.reference)
    ]


def chunked(items, size=30):
    for index in range(0, len(items), size):
        yield items[index : index + size]


def display_name_for(uid: str) -> str | None:
    snapshot = get_firestore_client().collection("users").document(uid).get()
    if not snapshot.exists:
        return None
    display_name = snapshot.to_dict().get("displayName")
    return display_name if isinstance(display_name, str) and display_name else None


def following_snapshots(uid: str):
    database = get_firestore_client()
    return list(
        bite_trail_root(database)
        .collection("followings")
        .document(uid)
        .collection("relationships")
        .stream()
    )


def create_friend(actor_uid: str, friend_uid: str) -> None:
    if not friend_uid or friend_uid == actor_uid:
        raise ValueError("You cannot add your own BiteTrail list.")

    database = get_firestore_client()
    actor_name = display_name_for(actor_uid)
    friend_name = display_name_for(friend_uid)
    if not friend_name:
        raise ValueError("This BiteTrail profile does not exist.")
    if not actor_name:
        raise ValueError("Your BiteTrail profile does not exist.")

    actor_reference = following_reference(database, actor_uid, friend_uid)
    if actor_reference.get().exists:
        raise ValueError("This friend is already on your watch list.")

    batch = database.batch()
    batch.set(actor_reference, {
        "friendUid": friend_uid,
        "friendDisplayName": friend_name,
        "createdAt": firestore.SERVER_TIMESTAMP,
    })
    batch.set(following_reference(database, friend_uid, actor_uid), {
        "friendUid": actor_uid,
        "friendDisplayName": actor_name,
        "createdAt": firestore.SERVER_TIMESTAMP,
    })
    batch.set(database.collection("auditEvents").document(), {
        "actorUid": actor_uid,
        "action": "friend_added",
        "targetUid": friend_uid,
        "createdAt": firestore.SERVER_TIMESTAMP,
    })
    batch.commit()


def remove_friend(actor_uid: str, friend_uid: str) -> None:
    database = get_firestore_client()
    batch = database.batch()
    batch.delete(following_reference(database, actor_uid, friend_uid))
    batch.delete(following_reference(database, friend_uid, actor_uid))
    batch.set(database.collection("auditEvents").document(), {
        "actorUid": actor_uid,
        "action": "friend_removed",
        "targetUid": friend_uid,
        "createdAt": firestore.SERVER_TIMESTAMP,
    })
    batch.commit()


def revoke_viewer(owner_uid: str, viewer_uid: str) -> None:
    # Revocation is temporary: it only removes the reciprocal relationship.
    # The viewer can accept a future friend link again.
    remove_friend(owner_uid, viewer_uid)


def get_visible_places(viewer_uid: str) -> list[dict]:
    database = get_firestore_client()
    friend_uids = [
        snapshot.to_dict().get("friendUid")
        for snapshot in following_snapshots(viewer_uid)
        if isinstance(snapshot.to_dict().get("friendUid"), str)
    ]
    # SneakyOwl is deliberately fetched live only through this relationship
    # list. If it is absent, the frontend uses the static snapshot instead.
    owner_uids = list(dict.fromkeys([viewer_uid, *friend_uids]))
    visits_by_place = defaultdict(list)

    for owner_chunk in chunked(owner_uids):
        for visit in database.collection_group("visits").where(
            filter=firestore.FieldFilter("ownerUid", "in", owner_chunk)
        ).stream():
            if not is_bite_trail_visit(visit.reference):
                continue
            visit_data = visit.to_dict()
            parent_place = visit.reference.parent.parent
            visits_by_place[parent_place.path].append((parent_place, visit.id, visit_data))

    places = []
    for entries in visits_by_place.values():
        parent_place, _, _ = entries[0]
        place_snapshot = parent_place.get()
        if not place_snapshot.exists:
            continue
        place_data = place_snapshot.to_dict()
        visits = [
            {
                "id": visit_id,
                "ownerUid": visit_data["ownerUid"],
                "ownerDisplayName": visit_data["ownerDisplayName"],
                "ratingOutOf10": visit_data["ratingOutOf10"],
                "costPerPerson": visit_data["costPerPerson"],
                "currency": visit_data["currency"],
                "itemsBought": visit_data["itemsBought"],
                "comments": visit_data["comments"],
                "visitedAt": visit_data["visitedAt"],
            }
            for _, visit_id, visit_data in entries
        ]
        places.append({
            "id": parent_place.id,
            "name": place_data["name"],
            "locationLabel": place_data["locationLabel"],
            "latitude": place_data["latitude"],
            "longitude": place_data["longitude"],
            "cuisineGenre": place_data["cuisineGenre"],
            "visits": visits,
        })
    return places


def delete_visit(actor_uid: str, place_id: str, visit_id: str) -> None:
    database = get_firestore_client()
    place = place_reference(database, place_id)
    visit = place.collection("visits").document(visit_id)
    transaction = database.transaction()

    @firestore.transactional
    def delete_visit_transaction(transaction):
        visit_snapshot = visit.get(transaction=transaction)
        if not visit_snapshot.exists:
            return
        if visit_snapshot.to_dict().get("ownerUid") != actor_uid:
            raise PermissionError("You can only delete your own visits.")

        remaining = [
            snapshot
            for snapshot in place.collection("visits").stream(transaction=transaction)
            if snapshot.id != visit_id
        ]
        transaction.delete(visit)
        if not remaining:
            transaction.delete(place)
        transaction.set(database.collection("auditEvents").document(), {
            "actorUid": actor_uid,
            "action": "visit_deleted",
            "placeId": place_id,
            "visitId": visit_id,
            "createdAt": firestore.SERVER_TIMESTAMP,
        })

    delete_visit_transaction(transaction)


def delete_visits_for_owner(uid: str) -> None:
    database = get_firestore_client()
    visits = bite_trail_visits_for_owner(uid, "==")
    places = {
        snapshot.reference.parent.parent.path: snapshot.reference.parent.parent
        for snapshot in visits
    }
    delete_in_batches(snapshot.reference for snapshot in visits)

    for place in places.values():
        transaction = database.transaction()

        @firestore.transactional
        def delete_orphaned_place(transaction):
            snapshots = list(place.collection("visits").stream(transaction=transaction))
            if not snapshots:
                transaction.delete(place)

        delete_orphaned_place(transaction)


def update_display_name(uid: str, display_name: str) -> None:
    display_name = normalize_display_name(display_name)
    if display_name == "SneakyOwl" and uid != SNEAKY_OWL_UID:
        display_name = "NotSneakyOwl"

    database = get_firestore_client()
    references = [database.collection("users").document(uid)]
    references.extend(
        visit.reference
        for visit in bite_trail_visits_for_owner(uid, "==")
    )
    references.extend(
        following_reference(database, snapshot.id, uid)
        for snapshot in following_snapshots(uid)
    )

    for reference_chunk in chunked(references, size=450):
        batch = database.batch()
        for reference in reference_chunk:
            fields = (
                {"displayName": display_name, "updatedAt": firestore.SERVER_TIMESTAMP}
                if reference.path == database.collection("users").document(uid).path
                else {"ownerDisplayName": display_name}
                if "/visits/" in reference.path
                else {"friendDisplayName": display_name}
            )
            batch.update(reference, fields)
        batch.commit()

    auth.update_user(uid, display_name=display_name)


def delete_bite_trail_data(uid: str) -> None:
    database = get_firestore_client()
    delete_visits_for_owner(uid)

    relationships = following_snapshots(uid)
    delete_in_batches(snapshot.reference for snapshot in relationships)
    delete_in_batches(
        following_reference(database, snapshot.id, uid) for snapshot in relationships
    )
    delete_in_batches([bite_trail_root(database).collection("users").document(uid)])
