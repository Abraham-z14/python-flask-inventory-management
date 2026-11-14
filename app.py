from flask import Flask, jsonify, request

from external_api import (
    OpenFoodFactsError,
    get_product_by_barcode,
    search_product_by_name,
)

app = Flask(__name__)


# In-memory inventory used as our temporary database.
inventory = [
    {
        "id": 1,
        "name": "Rice",
        "quantity": 10,
        "price": 4.99,
        "barcode": "100000000001",
    },
    {
        "id": 2,
        "name": "Chicken",
        "quantity": 6,
        "price": 8.99,
        "barcode": "100000000002",
    },
]


def find_inventory_item(item_id):
    """Return an inventory item by ID, or None if it does not exist."""
    for item in inventory:
        if item["id"] == item_id:
            return item

    return None


def validate_item_data(data, partial=False):
    """
    Validate inventory data.

    partial=False is used for POST, where required fields must exist.
    partial=True is used for PATCH, where only supplied fields are checked.
    """
    if not isinstance(data, dict):
        return "Request body must contain valid JSON."

    required_fields = ["name", "quantity", "price"]

    if not partial:
        for field in required_fields:
            if field not in data:
                return f"{field} is required."

    if "name" in data:
        if not isinstance(data["name"], str) or not data["name"].strip():
            return "name must be a non-empty string."

    if "quantity" in data:
        if (
            not isinstance(data["quantity"], int)
            or isinstance(data["quantity"], bool)
            or data["quantity"] < 0
        ):
            return "quantity must be a non-negative integer."

    if "price" in data:
        if (
            not isinstance(data["price"], (int, float))
            or isinstance(data["price"], bool)
            or data["price"] < 0
        ):
            return "price must be a non-negative number."

    if "barcode" in data:
        if data["barcode"] is not None and not isinstance(
            data["barcode"],
            str,
        ):
            return "barcode must be a string."

    return None


@app.route("/", methods=["GET"])
def home():
    """Return a welcome message."""
    return jsonify(
        {
            "message": "Welcome to the Inventory Management API"
        }
    ), 200


@app.route("/inventory", methods=["GET"])
def get_inventory():
    """Return every inventory item."""
    return jsonify(inventory), 200


@app.route("/inventory/<int:item_id>", methods=["GET"])
def get_inventory_item(item_id):
    """Return one inventory item by ID."""
    item = find_inventory_item(item_id)

    if item is None:
        return jsonify(
            {
                "error": "Inventory item not found"
            }
        ), 404

    return jsonify(item), 200


@app.route("/inventory", methods=["POST"])
def create_inventory_item():
    """Create a new inventory item."""
    data = request.get_json(silent=True)

    error = validate_item_data(data)

    if error:
        return jsonify(
            {
                "error": error
            }
        ), 400

    next_id = max(
        (item["id"] for item in inventory),
        default=0,
    ) + 1

    new_item = {
        "id": next_id,
        "name": data["name"].strip(),
        "quantity": data["quantity"],
        "price": float(data["price"]),
        "barcode": data.get("barcode"),
    }

    inventory.append(new_item)

    return jsonify(new_item), 201


@app.route("/inventory/<int:item_id>", methods=["PATCH"])
def update_inventory_item(item_id):
    """Update selected fields on an existing inventory item."""
    item = find_inventory_item(item_id)

    if item is None:
        return jsonify(
            {
                "error": "Inventory item not found"
            }
        ), 404

    data = request.get_json(silent=True)

    if not isinstance(data, dict) or not data:
        return jsonify(
            {
                "error": "Request body must contain fields to update."
            }
        ), 400

    error = validate_item_data(
        data,
        partial=True,
    )

    if error:
        return jsonify(
            {
                "error": error
            }
        ), 400

    allowed_fields = {
        "name",
        "quantity",
        "price",
        "barcode",
    }

    for key, value in data.items():
        if key not in allowed_fields:
            continue

        if key == "name":
            value = value.strip()

        if key == "price":
            value = float(value)

        item[key] = value

    return jsonify(item), 200


@app.route("/inventory/<int:item_id>", methods=["DELETE"])
def delete_inventory_item(item_id):
    """Delete an inventory item."""
    item = find_inventory_item(item_id)

    if item is None:
        return jsonify(
            {
                "error": "Inventory item not found"
            }
        ), 404

    inventory.remove(item)

    return "", 204


@app.route("/external/barcode/<barcode>", methods=["GET"])
def lookup_external_product_by_barcode(barcode):
    """Look up a product in Open Food Facts by barcode."""
    try:
        product = get_product_by_barcode(barcode)

    except OpenFoodFactsError as error:
        return jsonify(
            {
                "error": str(error)
            }
        ), 502

    if product is None:
        return jsonify(
            {
                "error": "Product not found"
            }
        ), 404

    return jsonify(product), 200


@app.route("/external/search", methods=["GET"])
def lookup_external_product_by_name():
    """Look up a product in Open Food Facts by product name."""
    name = request.args.get(
        "name",
        "",
    ).strip()

    if not name:
        return jsonify(
            {
                "error": "Product name is required"
            }
        ), 400

    try:
        product = search_product_by_name(name)

    except OpenFoodFactsError as error:
        return jsonify(
            {
                "error": str(error)
            }
        ), 502

    if product is None:
        return jsonify(
            {
                "error": "Product not found"
            }
        ), 404

    return jsonify(product), 200


@app.errorhandler(404)
def route_not_found(error):
    """Return JSON instead of Flask's default HTML 404 page."""
    return jsonify(
        {
            "error": "Resource not found"
        }
    ), 404


if __name__ == "__main__":
    app.run(debug=True)