from unittest.mock import patch

import pytest

from app import inventory
from cli import (
    add_item_command,
    barcode_lookup_command,
    delete_item_command,
    display_inventory,
    main,
    name_lookup_command,
    update_item_command,
)


@pytest.fixture(autouse=True)
def reset_inventory():
    """Restore inventory before every CLI test."""
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


def test_display_inventory_prints_items(capsys):
    display_inventory()

    output = capsys.readouterr().out

    assert "Rice" in output
    assert "Chicken" in output


def test_add_item_command(monkeypatch, capsys):
    answers = iter(
        [
            "Milk",
            "4",
            "3.49",
            "123456789",
        ]
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda prompt="": next(answers),
    )

    add_item_command()

    assert len(inventory) == 3
    assert inventory[-1]["name"] == "Milk"
    assert inventory[-1]["quantity"] == 4
    assert inventory[-1]["price"] == 3.49

    output = capsys.readouterr().out
    assert "Added Milk" in output


def test_update_item_command(monkeypatch):
    answers = iter(
        [
            "1",
            "Brown Rice",
            "20",
            "5.99",
            "",
        ]
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda prompt="": next(answers),
    )

    update_item_command()

    assert inventory[0]["name"] == "Brown Rice"
    assert inventory[0]["quantity"] == 20
    assert inventory[0]["price"] == 5.99


def test_delete_item_command(monkeypatch):
    monkeypatch.setattr(
        "builtins.input",
        lambda prompt="": "2",
    )

    delete_item_command()

    assert len(inventory) == 1
    assert inventory[0]["id"] == 1


@patch("cli.get_product_by_barcode")
def test_barcode_lookup_can_add_external_product(
    mock_lookup,
    monkeypatch,
):
    mock_lookup.return_value = {
        "name": "Nutella",
        "barcode": "3017624010701",
        "brand": "Ferrero",
        "category": "Spreads",
        "source": "Open Food Facts",
    }

    answers = iter(
        [
            "3017624010701",
            "y",
            "3",
            "6.99",
        ]
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda prompt="": next(answers),
    )

    barcode_lookup_command()

    added_item = inventory[-1]

    assert added_item["name"] == "Nutella"
    assert added_item["barcode"] == "3017624010701"
    assert added_item["quantity"] == 3
    assert added_item["price"] == 6.99
    assert added_item["source"] == "Open Food Facts"


@patch("cli.search_product_by_name")
def test_name_lookup_can_add_external_product(
    mock_search,
    monkeypatch,
):
    mock_search.return_value = {
        "name": "Peanut Butter",
        "barcode": "55555",
        "brand": "Example Brand",
        "category": "Spreads",
        "source": "Open Food Facts",
    }

    answers = iter(
        [
            "Peanut Butter",
            "y",
            "2",
            "4.50",
        ]
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda prompt="": next(answers),
    )

    name_lookup_command()

    added_item = inventory[-1]

    assert added_item["name"] == "Peanut Butter"
    assert added_item["quantity"] == 2
    assert added_item["source"] == "Open Food Facts"


@patch("cli.get_product_by_barcode")
def test_barcode_lookup_handles_missing_product(
    mock_lookup,
    monkeypatch,
    capsys,
):
    mock_lookup.return_value = None

    monkeypatch.setattr(
        "builtins.input",
        lambda prompt="": "9999999999999",
    )

    barcode_lookup_command()

    output = capsys.readouterr().out

    assert "Product not found" in output
    assert len(inventory) == 2


def test_main_can_exit(monkeypatch, capsys):
    monkeypatch.setattr(
        "builtins.input",
        lambda prompt="": "7",
    )

    main()

    output = capsys.readouterr().out

    assert "Goodbye" in output