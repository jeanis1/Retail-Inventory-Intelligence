"""mock.shop inventory checks.

The Storefront GraphQL API lists products and variants; Playwright then
behaves like a shopper on the demo storefront: adds 1 to the cart, raises
the cart line to 999, and reads the quantity the store corrects it to.
"""

import json
import urllib.request
from pathlib import Path
from urllib.parse import urlencode

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

WORKFLOW_PATH = Path("workflows") / "mock.shop.json"
INPUT_PATH = Path("input") / "mock.shop.csv"

PRODUCTS_PAGE_QUERY = """
query ($first: Int!, $after: String) {
  products(first: $first, after: $after) {
    pageInfo { hasNextPage endCursor }
    nodes { handle }
  }
}
"""

PRODUCT_QUERY = """
query ($handle: String!) {
  product(handle: $handle) {
    title
    productType
    variants(first: 100) {
      nodes { id title sku availableForSale selectedOptions { name value } }
    }
  }
}
"""


def load_workflow():
    with WORKFLOW_PATH.open(encoding="utf-8") as file:
        return json.load(file)


# STOREFRONT API: PRODUCT AND VARIANT LISTING

def graphql(api_url, query, variables=None):
    request = urllib.request.Request(
        api_url,
        data=json.dumps({"query": query, "variables": variables or {}}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        body = json.load(response)

    if body.get("errors"):
        raise RuntimeError(body["errors"][0].get("message", body["errors"]))
    return body["data"]


def iter_product_handles(workflow):
    """Yield every product handle, following the API's cursor pagination."""
    cursor = None
    while True:
        page = graphql(
            workflow["api_url"],
            PRODUCTS_PAGE_QUERY,
            {"first": workflow["page_size"], "after": cursor},
        )["products"]

        for node in page["nodes"]:
            yield node["handle"]

        if not page["pageInfo"]["hasNextPage"]:
            return
        cursor = page["pageInfo"]["endCursor"]


# BROWSER: SHOPPER-STYLE CART CHECK

def variant_page_url(workflow, handle, variant):
    """The storefront selects a variant from URL params, e.g. ?Size=Medium&Color=Ocean."""
    params = {
        option["name"]: option["value"]
        for option in variant["selectedOptions"]
        if option["value"] != "Default Title"
    }
    query = f"?{urlencode(params)}" if params else ""
    return f"{workflow['store_url']}/products/{handle}{query}"


def decline_cookie_banner(page):
    decline = page.get_by_test_id("consent-banner").get_by_role("button", name="Decline")
    if decline.count() and decline.is_visible():
        decline.click()


HYDRATED_JS = """() => {
    const button = document.querySelector('[data-testid=add-to-cart]');
    return !!button && Object.keys(button).some(k => k.startsWith('__reactProps'));
}"""

LINE_QUANTITY_SELECTOR = "[data-testid=cart-drawer] [data-testid=cart-line] input[name=quantity]"


def browser_cart_quantity(page, workflow, url, variant_id):
    """Reveal a variant's stock through the cart.

    Starts from an empty cart (the cart lives in the "cart" cookie), adds 1
    from the product page, sets the cart line to probe_quantity, clicks the
    cart window, and returns the quantity the store sets the line to.
    Returns 0 if Add to cart is disabled.
    """
    probe = str(workflow["probe_quantity"])

    page.context.clear_cookies(name="cart")
    page.goto(url, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_function(HYDRATED_JS, timeout=15000)  # buttons work only after hydration
    decline_cookie_banner(page)

    form = page.locator("form[action='/api/cart']").first
    selected_id = form.locator("input[name='merchandiseId']").input_value()
    if selected_id != variant_id:
        raise ValueError(f"Page selected {selected_id}, expected {variant_id}")

    add_to_cart = page.get_by_test_id("add-to-cart")
    if add_to_cart.is_disabled():
        return 0

    add_to_cart.click()  # product page quantity is 1 by default

    line_quantity = page.locator(LINE_QUANTITY_SELECTOR).first
    line_quantity.wait_for(timeout=10000)
    line_quantity.fill(probe)

    with page.expect_response(
        lambda r: r.url.endswith("/api/cart") and r.request.method == "POST",
        timeout=10000,
    ):
        page.locator("#cart-drawer-title").click()  # click the cart window to submit

    # Give the drawer a moment to re-render the corrected quantity. If the
    # store accepted the full probe, the value legitimately stays the same.
    try:
        page.wait_for_function(
            "([selector, probe]) => document.querySelector(selector)?.value !== probe",
            arg=[LINE_QUANTITY_SELECTOR, probe],
            timeout=3000,
        )
    except PlaywrightTimeoutError:
        pass

    return int(line_quantity.input_value())


# RESULTS

def row(handle, product_url="", name="", product_type="", variant="",
        variant_id="", sku="", quantity="", status="unknown", details=""):
    return {
        "handle": handle,
        "product_url": product_url,
        "product_name": name,
        "product_type": product_type,
        "variant": variant,
        "variant_id": variant_id,
        "sku": sku,
        "quantity": quantity,
        "status": status,
        "details": details,
    }


def variant_stock(page, workflow, url, variant):
    """Return (quantity, status, details) for one variant."""
    if variant.get("availableForSale") is False:
        return 0, "out_of_stock", "availableForSale=false"

    probe = workflow["probe_quantity"]
    quantity = browser_cart_quantity(page, workflow, url, variant["id"])

    if quantity == 0:
        return 0, "out_of_stock", "Add to cart disabled"
    if quantity >= probe:
        return quantity, "at_least_probe", f"Cart kept all {probe}; stock may be higher"
    return quantity, "in_stock", f"Cart reduced {probe} to {quantity}"


def check_product(page, workflow, handle):
    product = graphql(workflow["api_url"], PRODUCT_QUERY, {"handle": handle})["product"]

    if not product:
        return [row(handle, status="error", details="Product not found")]

    results = []
    for variant in product["variants"]["nodes"]:
        url = variant_page_url(workflow, handle, variant)
        result = row(
            handle,
            product_url=url,
            name=product.get("title") or "",
            product_type=product.get("productType") or "",
            variant=variant.get("title") or "Default",
            variant_id=variant.get("id") or "",
            sku=variant.get("sku") or "",
        )
        try:
            quantity, status, details = variant_stock(page, workflow, url, variant)
            result.update(quantity=quantity, status=status, details=details)
        except Exception as exc:
            result.update(status="error", details=f"{type(exc).__name__}: {str(exc)[:400]}")
        results.append(result)

    return results
