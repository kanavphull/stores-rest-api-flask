from flask.views import MethodView
from flask_smorest import Blueprint, abort
from sqlalchemy.exc import SQLAlchemyError

from custom_decorators import jwt_required_with_doc
from db import db
from models import ItemModel
from schemas import ItemSchema, ItemUpdateSchema

blp = Blueprint("items", __name__, description="Operations on Items")


@blp.route("/item/<int:item_id>")
class Item(MethodView):
    @blp.response(200, ItemSchema)
    def get(self, item_id):
        """Finds Item by ID

        Returns Item Based on ID.
        """
        item = ItemModel.query.get_or_404(item_id)
        return item

    @jwt_required_with_doc()
    @blp.arguments(
        ItemUpdateSchema, example={"name": "Updated Item Name", "price": 14.69}
    )
    @blp.response(200, ItemSchema)
    def put(self, item_data, item_id):
        """Updates the name and price of a specific Item

        Updates the name and price of an item with a particular item ID. <br>
        Store ID associated with an Item cannot be changed. <br>
        If no item with that ID exists, it creates a new item with that ID, but for that,
        associated store ID also needs to passed in request.
        """
        item = ItemModel.query.get(item_id)
        if item:
            item.price = item_data["price"]
            item.name = item_data["name"]
        else:
            item = ItemModel(id=item_id, **item_data)

        db.session.add(item)
        db.session.commit()

        return item

    @jwt_required_with_doc(fresh=True)
    def delete(self, item_id):
        """Deletes Item by ID

        Deletes items based on item IDs
        """
        item = ItemModel.query.get(item_id)
        db.session.delete(item)
        db.session.commit()
        return {"message": "Item Deleted"}


@blp.route("/item")
class ItemList(MethodView):
    @blp.response(200, ItemSchema(many=True))
    def get(self):
        """Gets all Items

        Returns all Items present in Database.
        """
        return ItemModel.query.all()

    @jwt_required_with_doc()
    @blp.arguments(ItemSchema)
    @blp.response(201, ItemSchema)
    def post(self, item_data):
        """Creates a new Item

        Creates a new Item with a name, price and ID of associated Store.
        """
        item = ItemModel(**item_data)

        try:
            db.session.add(item)
            db.session.commit()
        except SQLAlchemyError:
            abort(500, "An Error occurred while inserting the item.")

        return item, 201
