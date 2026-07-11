from flask import Flask, jsonify

from api.core.cors import configure_cors
from api.tools.bite_trail.routes import bite_trail_api


def create_app() -> Flask:
    application = Flask(__name__)
    configure_cors(application)
    application.register_blueprint(bite_trail_api)

    @application.route("/", methods=["GET"])
    def home():
        return jsonify({"service": "SneakyOwl BiteTrail API", "status": "ok"})

    return application


app = create_app()
