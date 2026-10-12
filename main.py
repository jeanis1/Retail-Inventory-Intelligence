"""Step 2: check inventory for every handle in input/mock.shop.csv."""

import argparse
import csv
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright

from engine import INPUT_PATH, check_product, load_workflow, row

OUTPUT_PATH = Path("inventory_results.csv")

COLUMNS = [
    "handle", "product_url", "product_name", "product_type", "variant",
    "variant_id", "sku", "quantity", "status", "details", "update_time",
]


def load_handles():
    with INPUT_PATH.open(newline="", encoding="utf-8") as file:
        return [r["handle"].strip() for r in csv.DictReader(file) if r.get("handle", "").strip()]


def main(headed=False):
    workflow = load_workflow()
    handles = load_handles()
    print(f"{INPUT_PATH}: {len(handles)} products")

    with sync_playwright() as playwright:
        # Images are never needed for the check; skipping them speeds up every page.
        browser = playwright.chromium.launch(
            headless=not headed,
            args=["--blink-settings=imagesEnabled=false"],
        )
        # One context for the whole run keeps scripts cached between pages;
        # each check empties the cart itself.
        page = browser.new_context().new_page()

        try:
            with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=COLUMNS)
                writer.writeheader()

                for handle in handles:
                    try:
                        results = check_product(page, workflow, handle)
                    except Exception as exc:
                        results = [row(handle, status="error", details=f"{type(exc).__name__}: {exc}")]

                    for result in results:
                        # US format, e.g. 10/11/2026 05:32:10 PM
                        result["update_time"] = datetime.now().strftime("%m/%d/%Y %I:%M:%S %p")
                        writer.writerow(result)
                        print(handle, result["variant"], result["quantity"], result["status"])

                    file.flush()
        finally:
            browser.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--headed", action="store_true", help="show the browser window")
    main(parser.parse_args().headed)
