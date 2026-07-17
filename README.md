# SneakyOwl Flask API

This Vercel-hosted Flask service handles BiteTrail operations that require Firebase Admin privileges:

- Return the signed-in user's and reciprocal friends' live visits, grouped by global place.
- Add, remove, or temporarily revoke both sides of a friend relationship.
- Update a display name across Firebase Auth, the shared profile, visits, and relationship caches.
- Delete a visit and remove its parent place when it becomes empty.
- Delete all BiteTrail data for the signed-in user using the indexed visit owner UID.
- Permanently delete the signed-in user's Firebase Authentication account and
  Firestore account data after server-side Gmail-address confirmation.

Account deletion is exposed at `DELETE /v1/account`. The request body must
contain the signed-in Gmail address as `{ "email": "<gmail-address>" }`; the
server compares it case-insensitively with the verified Firebase token email.
The operation removes the user's global visits, BiteTrail configuration, and
reciprocal relationship documents before deleting the shared profile and Auth
account.

The Flask code is organized by tool. See [api/README.md](./api/README.md) for the package layout and guidance for adding future tools.

All protected endpoints expect a Firebase ID token from the SneakyOwl frontend:

```http
Authorization: Bearer <firebase-id-token>
```

The server verifies this token with Firebase Admin and derives the acting UID from it. Never trust a UID submitted by the browser.

## Configuration

Copy `.env.example` for local development. In Vercel, configure the same values as encrypted environment variables:

```text
FIREBASE_PROJECT_ID
FIREBASE_SERVICE_ACCOUNT_JSON
ALLOWED_ORIGINS
```

`FIREBASE_SERVICE_ACCOUNT_JSON` is a one-line service-account JSON value. It must never be added to the frontend repository or exposed through a `NEXT_PUBLIC_` variable.

`ALLOWED_ORIGINS` is comma-separated; include the exact local origin (for
example, `http://localhost:3000`), `https://sneakyowl.net`, and any preview
domain that should call this API.

After deployment, set `NEXT_PUBLIC_SNEAKYOWL_API_BASE_URL` in the SneakyOwl frontend to the deployed Flask URL.

## Local development

```bash
pip install -r requirements.txt
vercel dev
```

The Flask app is served through Vercel's Python runtime configuration in `vercel.json`.
