from flask.views import MethodView
from flask_smorest import Blueprint, abort
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from custom_decorators import jwt_required_with_doc
from db import db
from models import StoreModel
from schemas import StoreSchema

blp = Blueprint("stores", __name__, description="Operations on Stores")


@blp.route("/store/<int:store_id>")
class Store(MethodView):
    @blp.response(200, StoreSchema)
    def get(self, store_id):
        """Gets store by store ID

        Returns store based on Store ID.
        """
        store = StoreModel.query.get_or_404(store_id)
        return store

    @jwt_required_with_doc(fresh=True)
    def delete(self, store_id):
        """Deletes Store by Store ID

        Deletes store based on Store ID
        """
        store = StoreModel.query.get_or_404(store_id)
        db.session.delete(store)
        db.session.commit()
        return {"message": "Store Deleted"}


@blp.route("/store")
class StoreList(MethodView):
    @blp.response(200, StoreSchema(many=True))
    def get(self):
        """Gets all Stores

        Returns all Stores
        """
        return StoreModel.query.all()

    @jwt_required_with_doc()
    @blp.arguments(StoreSchema)
    @blp.response(201, StoreSchema)
    def post(self, store_data):
        """Creates a new Store

        Creates a new Store with the specified Name.
        """
        store = StoreModel(**store_data)
        try:
            db.session.add(store)
            db.session.commit()
        except IntegrityError:
            abort(400, "Store with this name already exists.")
        except SQLAlchemyError:
            abort(500, "An Error occurred while creating the store.")
        return store
