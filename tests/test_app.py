from unittest.mock import patch

import pytest

from app import app, inventory


@pytest.fixture(autouse=True)
def reset_inventory():
    """Restore the inventory before each test."""
    inventory.clear()

    inventory.extend(
        [
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
    )


@pytest.fixture
def client():
    return app.test_client()


def test_homepage_returns_welcome_message(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "welcome" in response.get_json()["message"].lower()


def test_get_inventory_returns_all_items(client):
    response = client.get("/inventory")
    data = response.get_json()

    assert response.status_code == 200
    assert isinstance(data, list)
    assert len(data) == 2


def test_get_inventory_item_by_id(client):
    response = client.get("/inventory/1")
    data = response.get_json()

    assert response.status_code == 200
    assert data["id"] == 1
    assert data["name"] == "Rice"


def test_get_missing_inventory_item_returns_404(client):
    response = client.get("/inventory/999")

    assert response.status_code == 404
    assert "error" in response.get_json()


def test_create_inventory_item(client):
    response = client.post(
        "/inventory",
        json={
            "name": "Milk",
            "quantity": 4,
            "price": 3.49,
            "barcode": "100000000003",
        },
    )

    data = response.get_json()

    assert response.status_code == 201
    assert data["id"] == 3
    assert data["name"] == "Milk"
    assert data["quantity"] == 4
    assert data["price"] == 3.49
    assert len(inventory) == 3


def test_create_inventory_item_rejects_missing_data(client):
    response = client.post(
        "/inventory",
        json={
            "name": "Milk",
        },
    )

    assert response.status_code == 400
    assert "error" in response.get_json()


def test_patch_inventory_item(client):
    response = client.patch(
        "/inventory/1",
        json={
            "quantity": 20,
            "price": 5.49,
        },
    )

    data = response.get_json()

    assert response.status_code == 200
    assert data["id"] == 1
    assert data["name"] == "Rice"
    assert data["quantity"] == 20
    assert data["price"] == 5.49


def test_patch_missing_inventory_item_returns_404(client):
    response = client.patch(
        "/inventory/999",
        json={
            "quantity": 20,
        },
    )

    assert response.status_code == 404


def test_delete_inventory_item(client):
    response = client.delete("/inventory/2")

    assert response.status_code == 204
    assert len(inventory) == 1
    assert inventory[0]["id"] == 1


def test_delete_missing_inventory_item_returns_404(client):
    response = client.delete("/inventory/999")

    assert response.status_code == 404


@patch("app.get_product_by_barcode")
def test_external_barcode_route_returns_product(
    mock_lookup,
    client,
):
    mock_lookup.return_value = {
        "name": "Nutella",
        "barcode": "3017624010701",
        "brand": "Ferrero",
        "category": "Spreads",
        "source": "Open Food Facts",
    }

    response = client.get(
        "/external/barcode/3017624010701"
    )

    data = response.get_json()

    assert response.status_code == 200
    assert data["name"] == "Nutella"
    assert data["barcode"] == "3017624010701"


@patch("app.get_product_by_barcode")
def test_external_barcode_route_returns_404_when_missing(
    mock_lookup,
    client,
):
    mock_lookup.return_value = None

    response = client.get(
        "/external/barcode/9999999999999"
    )

    assert response.status_code == 404


@patch("app.search_product_by_name")
def test_external_search_route_returns_product(
    mock_search,
    client,
):
    mock_search.return_value = {
        "name": "Nutella",
        "barcode": "3017624010701",
        "brand": "Ferrero",
        "category": "Spreads",
        "source": "Open Food Facts",
    }

    response = client.get(
        "/external/search?name=Nutella"
    )

    data = response.get_json()

    assert response.status_code == 200
    assert data["name"] == "Nutella"


def test_external_search_route_requires_name(client):
    response = client.get("/external/search")

    assert response.status_code == 400