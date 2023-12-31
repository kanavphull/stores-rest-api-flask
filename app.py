import os

from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_smorest import Api

from blocklist import BLOCKLIST
from db import db
from resources.item import blp as ItemBlueprint
from resources.store import blp as StoreBlueprint
from resources.tag import blp as TagBlueprint
from resources.user import blp as UserBlueprint


def create_app(db_url=None):
    app = Flask(__name__)
    load_dotenv()

    # Uncomment this code to use background worker
    # connection = redis.from_url(os.getenv("REDIS_URL"))

    # app.queue = Queue("emails", connection=connection)
    app.config["PROPAGATE_EXCEPTIONS"] = True
    app.config["API_TITLE"] = "Stores REST API"
    app.config["API_VERSION"] = "v1"
    app.config["OPENAPI_VERSION"] = "3.0.3"
    app.config["OPENAPI_URL_PREFIX"] = "/"
    app.config["OPENAPI_SWAGGER_UI_PATH"] = "/swagger-ui"
    app.config[
        "OPENAPI_SWAGGER_UI_URL"
    ] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"

    app.config["API_SPEC_OPTIONS"] = {
        "components": {
            "securitySchemes": {
                "Bearer Auth": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "Authorization",
                    "bearerFormat": "JWT",
                    "description": "Enter: **'Bearer &lt;JWT&gt;'**, where JWT is the access token",
                }
            }
        },
        "info": {
            "description": "- The Stores REST API is a comprehensive solution that facilitates the management of stores and their corresponding inventory. This API empowers users to effortlessly create, organize, and oversee various stores, each housing a collection of items available for tracking and management. The API is connected to a `PostgreSQL` Database hosted on `ElephantSQL`.<br><br> \n \
- It allows users to perform **CRUD** (Create, Read, Update, Delete) operations on stores and their respective items. It provides endpoints for managing stores, adding items to stores, and retrieving information about items within those stores. Furthermore, we can use `tags` to group related items in a store. <br><br> \n \
- It also uses Secure Authentication using `JWT`. Newly Registered Users receive a welcome email using `Mailgun`. A `worker node` processes the mailing requests which are stored in a `Redis` Task Queue. Deployments are made on `Render`. For Database Migrations, `flask-migrate` is used which uses `alembic` under the hood to generate migrations.<br><br> \n \
- Tech Stack Used: `Python`, `Flask, Docker`, `Flask-Smorest` and `Flask-SQLAlchemy` <br><br> \n \
- The Documentation of the API can be found below. It is created using `OpenAPI Specification` which is beautifully rendered as a webpage by `Swagger UI`. It can also be used to **test** its functionality. \n \
            "
        },
    }

    app.config["SQLALCHEMY_DATABASE_URI"] = db_url or os.getenv(
        "DATABASE_URL", "sqlite:///data.db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)

    Migrate(app, db)

    api = Api(app)

    # with app.app_context():
    #     db.create_all()

    app.config["JWT_SECRET_KEY"] = "kanav"
    jwt = JWTManager(app)

    @jwt.token_in_blocklist_loader
    def check_if_token_in_blocklist(jwt_header, jwt_payload):
        return jwt_payload["jti"] in BLOCKLIST

    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        return (
            jsonify(
                {"description": "The token has been revoked.", "error": "token_revoked"}
            ),
            401,
        )

    @jwt.needs_fresh_token_loader
    def token_not_fresh_callback(jwt_header, jwt_payload):
        return (
            jsonify(
                {
                    "description": "The token is not fresh.",
                    "error": "fresh_token_required",
                }
            ),
            401,
        )

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return (
            jsonify({"message": "The token has expired.", "error": "token_expired"}),
            401,
        )

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return (
            jsonify(
                {"message": "Signature verification failed.", "error": "invalid_token"}
            ),
            401,
        )

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return (
            jsonify(
                {
                    "description": "Request does not contain an access token.",
                    "error": "authorization_required",
                }
            ),
            401,
        )

    api.register_blueprint(ItemBlueprint)
    api.register_blueprint(StoreBlueprint)
    api.register_blueprint(TagBlueprint)
    api.register_blueprint(UserBlueprint)

    return app
