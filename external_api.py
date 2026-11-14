import requests


BASE_URL = "https://world.openfoodfacts.org"

HEADERS = {
    "User-Agent": (
        "PythonFlaskInventoryManagement/1.0 "
        "(student inventory management project)"
    )
}


class OpenFoodFactsError(Exception):
    """Raised when Open Food Facts cannot be reached successfully."""


def get_product_by_barcode(barcode):
    """
    Retrieve one Open Food Facts product using its barcode.

    Returns a normalized product dictionary when found.
    Returns None when Open Food Facts reports that the product does not exist.
    Raises OpenFoodFactsError for network/service failures.
    """
    barcode = str(barcode).strip()

    if not barcode:
        raise ValueError("Barcode is required.")

    url = f"{BASE_URL}/api/v2/product/{barcode}.json"

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as error:
        raise OpenFoodFactsError(
            "Could not retrieve product data from Open Food Facts."
        ) from error
    except ValueError as error:
        raise OpenFoodFactsError(
            "Open Food Facts returned invalid JSON."
        ) from error

    if data.get("status") != 1:
        return None

    product = data.get("product", {})

    return {
        "name": product.get("product_name") or "Unknown Product",
        "barcode": data.get("code") or barcode,
        "brand": product.get("brands") or "",
        "category": product.get("categories") or "",
        "source": "Open Food Facts",
    }


def search_product_by_name(name):
    """
    Search Open Food Facts by product name.

    Open Food Facts currently uses its legacy search endpoint for
    free-text product-name searching.

    Returns the first normalized product result or None if no result exists.
    """
    name = str(name).strip()

    if not name:
        raise ValueError("Product name is required.")

    url = f"{BASE_URL}/cgi/search.pl"

    params = {
        "search_terms": name,
        "search_simple": 1,
        "action": "process",
        "json": 1,
        "page_size": 1,
        "fields": "code,product_name,brands,categories",
    }

    try:
        response = requests.get(
            url,
            params=params,
            headers=HEADERS,
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as error:
        raise OpenFoodFactsError(
            "Could not search Open Food Facts."
        ) from error
    except ValueError as error:
        raise OpenFoodFactsError(
            "Open Food Facts returned invalid JSON."
        ) from error

    products = data.get("products", [])

    if not products:
        return None

    product = products[0]

    return {
        "name": product.get("product_name") or "Unknown Product",
        "barcode": product.get("code") or "",
        "brand": product.get("brands") or "",
        "category": product.get("categories") or "",
        "source": "Open Food Facts",
    }