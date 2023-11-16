from flask.views import MethodView
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt,
    get_jwt_identity,
)
from flask_smorest import Blueprint, abort
from passlib.hash import pbkdf2_sha256
from sqlalchemy import or_

from blocklist import BLOCKLIST
from custom_decorators import jwt_required_with_doc
from db import db
from models import UserModel
from schemas import UserRegisterSchema, UserSchema
from tasks import send_user_registration_email

blp = Blueprint("User", "users", description="Operations on Users")


@blp.route("/register")
class UserRegister(MethodView):
    @blp.arguments(UserRegisterSchema)
    def post(self, user_data):
        """Registers a New User

        Registers a New User with a Username, Password and Email.
        """
        if UserModel.query.filter(
            or_(
                UserModel.username == user_data["username"],
                UserModel.email == user_data["email"],
            )
        ).first():
            abort(409, message="A User with that username or email already exists")

        user = UserModel(
            username=user_data["username"],
            email=user_data["email"],
            password=pbkdf2_sha256.hash(user_data["password"]),
        )
        db.session.add(user)
        db.session.commit()

        send_user_registration_email(email=user.email, username=user.username)

        # Uncomment this code to use background worker
        # current_app.queue.enqueue(
        #     send_user_registration_email, user.email, user.username
        # )

        return {"message": "User Created Successfully"}, 201


@blp.route("/login")
class UserLogin(MethodView):
    @blp.arguments(UserSchema)
    def post(self, user_data):
        """Logs in User and Generates Access Tokens

        Takes Username and Password and logs in a particular User. <br>
        Returns an Access Token and a Refresh Token which can be used to
        generate another non-fresh access token.
        """
        user = UserModel.query.filter(
            UserModel.username == user_data["username"]
        ).first()

        if user and pbkdf2_sha256.verify(user_data["password"], user.password):
            access_token = create_access_token(identity=user.id, fresh=True)
            refresh_token = create_refresh_token(identity=user.id)
            return {"access_token": access_token, "refresh_token": refresh_token}, 200

        abort(401, message="Invalid Credentials")


@blp.route("/refresh")
class TokenRefresh(MethodView):
    @jwt_required_with_doc(refresh=True)
    def post(self):
        """Generates a non-Fresh Access Token using Refresh Token.

        Generates a non-Fresh Access Token using a Refresh Token. <br>
        This can be done only once. <br>
        NON-Fresh Token cannot be used to Delete anything in the Database.
        """
        current_user = get_jwt_identity()
        new_token = create_access_token(identity=current_user, fresh=False)

        # Adding refresh token to blocklist after refreshing token once
        jti = get_jwt()["jti"]
        BLOCKLIST.add(jti)

        return {"access_token": new_token}, 200


@blp.route("/logout")
class UserLogout(MethodView):
    @jwt_required_with_doc()
    def post(self):
        """Logs Out the User

        Logs out the User rendering the Access Token invalid.
        """
        jti = get_jwt()["jti"]
        BLOCKLIST.add(jti)
        return {"message": "Successfully logged out"}, 200


@blp.route("/user/<int:user_id>")
class User(MethodView):
    @blp.response(200, UserSchema)
    def get(self, user_id):
        """Gets User by ID

        Returns User Based on ID
        """
        user = UserModel.query.get_or_404(user_id)
        return user

    @jwt_required_with_doc(fresh=True)
    def delete(self, user_id):
        """Deletes a User

        Deletes the Registration of a Particular User by ID.
        """
        user = UserModel.query.get_or_404(user_id)

        db.session.delete(user)
        db.session.commit()

        return {"message": "User Deleted"}, 200
