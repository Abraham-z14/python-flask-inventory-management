from unittest.mock import Mock, patch

import pytest
import requests

from external_api import (
    OpenFoodFactsError,
    get_product_by_barcode,
    search_product_by_name,
)


@patch("external_api.requests.get")
def test_get_product_by_barcode_returns_normalized_product(mock_get):
    mock_response = Mock()

    mock_response.json.return_value = {
        "status": 1,
        "code": "3017624010701",
        "product": {
            "product_name": "Nutella",
            "brands": "Ferrero",
            "categories": "Spreads, Hazelnut spreads",
        },
    }

    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    product = get_product_by_barcode("3017624010701")

    assert product == {
        "name": "Nutella",
        "barcode": "3017624010701",
        "brand": "Ferrero",
        "category": "Spreads, Hazelnut spreads",
        "source": "Open Food Facts",
    }

    mock_get.assert_called_once()


@patch("external_api.requests.get")
def test_get_product_by_barcode_returns_none_when_not_found(mock_get):
    mock_response = Mock()

    mock_response.json.return_value = {
        "status": 0,
        "code": "9999999999999",
        "product": {},
    }

    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    product = get_product_by_barcode("9999999999999")

    assert product is None


def test_get_product_by_barcode_rejects_blank_barcode():
    with pytest.raises(ValueError):
        get_product_by_barcode("   ")


@patch("external_api.requests.get")
def test_get_product_by_barcode_handles_request_failure(mock_get):
    mock_get.side_effect = requests.exceptions.ConnectionError(
        "network unavailable"
    )

    with pytest.raises(OpenFoodFactsError):
        get_product_by_barcode("3017624010701")


@patch("external_api.requests.get")
def test_search_product_by_name_returns_first_product(mock_get):
    mock_response = Mock()

    mock_response.json.return_value = {
        "products": [
            {
                "code": "3017624010701",
                "product_name": "Nutella",
                "brands": "Ferrero",
                "categories": "Spreads",
            }
        ]
    }

    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    product = search_product_by_name("Nutella")

    assert product == {
        "name": "Nutella",
        "barcode": "3017624010701",
        "brand": "Ferrero",
        "category": "Spreads",
        "source": "Open Food Facts",
    }


@patch("external_api.requests.get")
def test_search_product_by_name_returns_none_when_no_results(mock_get):
    mock_response = Mock()

    mock_response.json.return_value = {
        "products": []
    }

    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    assert search_product_by_name("Definitely Not Real Food") is None


def test_search_product_by_name_rejects_blank_name():
    with pytest.raises(ValueError):
        search_product_by_name("")