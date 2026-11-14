from app import inventory, find_inventory_item
from external_api import (
    OpenFoodFactsError,
    get_product_by_barcode,
    search_product_by_name,
)


def next_inventory_id():
    """Return the next available inventory ID."""
    return max(
        (item["id"] for item in inventory),
        default=0,
    ) + 1


def display_inventory():
    """Print all inventory items."""
    if not inventory:
        print("Inventory is empty.")
        return

    print("\nCurrent Inventory")
    print("-----------------")

    for item in inventory:
        print(
            f"ID: {item['id']} | "
            f"Name: {item['name']} | "
            f"Quantity: {item['quantity']} | "
            f"Price: ${item['price']:.2f} | "
            f"Barcode: {item.get('barcode') or 'N/A'}"
        )


def add_item_command():
    """Prompt the user to create an inventory item."""
    name = input("Product name: ").strip()

    if not name:
        print("Product name is required.")
        return

    try:
        quantity = int(input("Quantity: "))
        price = float(input("Price: "))
    except ValueError:
        print("Quantity must be an integer and price must be a number.")
        return

    if quantity < 0 or price < 0:
        print("Quantity and price cannot be negative.")
        return

    barcode = input("Barcode (optional): ").strip() or None

    item = {
        "id": next_inventory_id(),
        "name": name,
        "quantity": quantity,
        "price": price,
        "barcode": barcode,
    }

    inventory.append(item)

    print(f"Added {name} to inventory.")


def update_item_command():
    """Prompt the user to update an existing inventory item."""
    try:
        item_id = int(input("Inventory ID to update: "))
    except ValueError:
        print("Inventory ID must be an integer.")
        return

    item = find_inventory_item(item_id)

    if item is None:
        print("Inventory item not found.")
        return

    name = input(
        f"Name [{item['name']}]: "
    ).strip()

    quantity_text = input(
        f"Quantity [{item['quantity']}]: "
    ).strip()

    price_text = input(
        f"Price [{item['price']}]: "
    ).strip()

    barcode_text = input(
        f"Barcode [{item.get('barcode') or 'N/A'}]: "
    ).strip()

    if name:
        item["name"] = name

    if quantity_text:
        try:
            quantity = int(quantity_text)
        except ValueError:
            print("Quantity must be an integer.")
            return

        if quantity < 0:
            print("Quantity cannot be negative.")
            return

        item["quantity"] = quantity

    if price_text:
        try:
            price = float(price_text)
        except ValueError:
            print("Price must be a number.")
            return

        if price < 0:
            print("Price cannot be negative.")
            return

        item["price"] = price

    if barcode_text:
        item["barcode"] = barcode_text

    print(f"Updated inventory item {item_id}.")


def delete_item_command():
    """Prompt the user to delete an inventory item."""
    try:
        item_id = int(input("Inventory ID to delete: "))
    except ValueError:
        print("Inventory ID must be an integer.")
        return

    item = find_inventory_item(item_id)

    if item is None:
        print("Inventory item not found.")
        return

    inventory.remove(item)

    print(f"Deleted {item['name']} from inventory.")


def display_external_product(product):
    """Print normalized Open Food Facts product information."""
    print("\nProduct Found")
    print("-------------")
    print(f"Name: {product['name']}")
    print(f"Barcode: {product.get('barcode') or 'N/A'}")
    print(f"Brand: {product.get('brand') or 'N/A'}")
    print(f"Category: {product.get('category') or 'N/A'}")
    print(f"Source: {product.get('source') or 'Open Food Facts'}")


def add_external_product_to_inventory(product):
    """
    Ask for local inventory information and add an external product.

    Product identity comes from Open Food Facts, while quantity and
    price are entered locally because they are inventory-specific.
    """
    try:
        quantity = int(input("Quantity to add: "))
        price = float(input("Local price: "))
    except ValueError:
        print("Quantity must be an integer and price must be a number.")
        return False

    if quantity < 0 or price < 0:
        print("Quantity and price cannot be negative.")
        return False

    item = {
        "id": next_inventory_id(),
        "name": product["name"],
        "quantity": quantity,
        "price": price,
        "barcode": product.get("barcode"),
        "brand": product.get("brand", ""),
        "category": product.get("category", ""),
        "source": product.get(
            "source",
            "Open Food Facts",
        ),
    }

    inventory.append(item)

    print(
        f"Added {product['name']} to inventory "
        "using Open Food Facts data."
    )

    return True


def barcode_lookup_command():
    """Look up an external product by barcode."""
    barcode = input("Barcode to search: ").strip()

    if not barcode:
        print("Barcode is required.")
        return

    try:
        product = get_product_by_barcode(barcode)
    except (OpenFoodFactsError, ValueError) as error:
        print(f"Lookup failed: {error}")
        return

    if product is None:
        print("Product not found.")
        return

    display_external_product(product)

    add_choice = input(
        "Add this product to inventory? (y/n): "
    ).strip().lower()

    if add_choice == "y":
        add_external_product_to_inventory(product)


def name_lookup_command():
    """Look up an external product by product name."""
    name = input("Product name to search: ").strip()

    if not name:
        print("Product name is required.")
        return

    try:
        product = search_product_by_name(name)
    except (OpenFoodFactsError, ValueError) as error:
        print(f"Lookup failed: {error}")
        return

    if product is None:
        print("Product not found.")
        return

    display_external_product(product)

    add_choice = input(
        "Add this product to inventory? (y/n): "
    ).strip().lower()

    if add_choice == "y":
        add_external_product_to_inventory(product)


def print_menu():
    """Display the available CLI commands."""
    print(
        """
Inventory Management CLI
------------------------
1. View inventory
2. Add inventory item
3. Update inventory item
4. Delete inventory item
5. Look up Open Food Facts product by barcode
6. Search Open Food Facts product by name
7. Exit
"""
    )


def main():
    """Run the interactive inventory management CLI."""
    while True:
        print_menu()

        choice = input("Choose an option: ").strip()

        if choice == "1":
            display_inventory()

        elif choice == "2":
            add_item_command()

        elif choice == "3":
            update_item_command()

        elif choice == "4":
            delete_item_command()

        elif choice == "5":
            barcode_lookup_command()

        elif choice == "6":
            name_lookup_command()

        elif choice == "7":
            print("Goodbye.")
            break

        else:
            print("Invalid option. Please choose 1 through 7.")


if __name__ == "__main__":
    main()