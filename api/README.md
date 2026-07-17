# API structure

The Flask application is organized by shared infrastructure and tool ownership:

```text
api/
  index.py                 Vercel's stable Python entrypoint
  app.py                   Flask app factory and blueprint registration
  account/
    routes.py              Shared account HTTP routes and request checks
    service.py             Shared account deletion operation
  core/
    auth.py               Firebase ID-token middleware
    config.py             Environment-backed configuration
    cors.py               Shared CORS response handling
    firebase.py           Firebase Admin/Firestore initialization
    firestore.py          Shared Firestore batch helpers
  tools/
    bite_trail/
      routes.py           BiteTrail HTTP routes and request checks
      service.py          BiteTrail Firestore operations
```

Future tools should add a sibling package under `api/tools/`, for example:

```text
api/tools/chess/routes.py
api/tools/chess/service.py
```

Register that tool's Blueprint in `api/app.py`. Keep Firebase setup, token verification, CORS, and generic Firestore helpers in `api/core/`; keep tool-specific validation and data operations in the corresponding tool package.

`api/index.py` remains the Vercel entrypoint and exports the Flask `app` object.

Protected public routes include:

- `GET /v1/bite-trail/places` for authorised live places and visits.
- `POST` and `DELETE /v1/bite-trail/friends/{friendUid}` for reciprocal relationships.
- `DELETE /v1/bite-trail/visits/{placeId}/{visitId}` for an owned visit.
- `POST /v1/account/profile` for display-name propagation.
- `DELETE /v1/bite-trail/data` and `DELETE /v1/account` for data and account deletion.
