from collections.abc import Iterable

from api.core.firebase import get_firestore_client


def delete_in_batches(references: Iterable) -> None:
    database = get_firestore_client()
    batch = database.batch()
    count = 0

    for reference in references:
        batch.delete(reference)
        count += 1
        if count == 450:
            batch.commit()
            batch = database.batch()
            count = 0

    if count:
        batch.commit()
