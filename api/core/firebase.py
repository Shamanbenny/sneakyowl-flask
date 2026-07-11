import json
import os

import firebase_admin
from firebase_admin import credentials, firestore


def get_firestore_client():
    if not firebase_admin._apps:
        raw_credentials = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON")
        project_id = os.environ.get("FIREBASE_PROJECT_ID")
        if not raw_credentials or not project_id:
            raise RuntimeError("Firebase Admin is not configured.")
        certificate = credentials.Certificate(json.loads(raw_credentials))
        firebase_admin.initialize_app(certificate, {"projectId": project_id})
    return firestore.client()
