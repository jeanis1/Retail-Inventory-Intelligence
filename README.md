# Retail Inventory Intelligence | B2C CPG Competitive Analytics

Unlocking one of the most important sources of competitive intelligence: Exact retail inventory quantities at the individual SKU and product-variant level.

In competitive CPG markets, exact SKU-level retail inventory visibility represents a holy grail of commercial intelligence—revealing not just product availability, but precise stock quantities across variants, retailers, and markets.
Unlike conventional digital shelf monitoring focused on availability, pricing, and assortment, this system retrieves exact SKU/variant inventory counts where accessible, establishing a granular foundation for competitive intelligence, demand sensing, and supply chain analysis.

Through historical inventory tracking and downstream analytics, these insights can be applied to eight critical commercial intelligence dimensions:

* **Exact Inventory Quantities:** Identify stockouts, overstock, inventory imbalances, and potential supply constraints.
* **Sell-Through Velocity:** Estimate product-level sales momentum using inventory changes and replenishment patterns.
* **Competitor Inventory:** Benchmark competitors' stock positions, product performance signals, and market vulnerabilities.
* **SKU-Level Trends:** Identify emerging winners, declining products, and variant-level demand patterns.
* **Retailer Comparisons:** Evaluate distribution effectiveness and inventory performance across retailers, channels, and markets.
* **Promotion Effectiveness:** Assess potential relationships between pricing, marketing activities, and inventory movement.
* **Inventory Forecasting:** Anticipate potential replenishment requirements, stockout risks, and changes in demand.
* **Strategic Value:** Translate granular market intelligence into competitive positioning, distribution optimization, marketing allocation, and commercial decision-making.

## Strategic Business Applications

* **Competitive Intelligence & Market Positioning:** Benchmark competitor inventory depth, SKU assortment, and channel presence to identify market gaps, competitive vulnerabilities, and opportunities to capture market share.
* **Demand Sensing & Market Dynamics:** Analyze historical SKU-level inventory deltas (Δ), potential sell-through velocity, and replenishment patterns to generate directional demand signals and identify emerging market trends.
* **Supply Chain & Distribution Intelligence:** Detect inventory imbalances, recurring stockouts, and potential supply constraints to support more responsive replenishment, inventory allocation, and distribution strategies.
* **Marketing & Revenue Optimization:** Inform promotional timing, inventory-aware marketing investment, and merchandising decisions based on competitive stock positions and emerging commercial opportunities.
* **Strategic Agility & Competitive Advantage:** Translate granular market observations into actionable intelligence that supports faster competitive responses, more informed capital allocation, and proactive market positioning.

## Technical Implementation & Data Pipeline

Developed with Python and Playwright, the system automates product discovery, SKU/variant identification, and inventory verification, demonstrated on Shopify's mock.shop demo storefront.

### Current capabilities

* Automated discovery of products and SKU variants via the mock.shop Storefront API.
* Browser-based inventory verification workflow for the mock.shop demo storefront.
* Retrieval of exact SKU/variant inventory quantities where supported.
* Structured CSV exports of current observed inventory data.

### Downstream analytical capabilities

The system currently produces inventory snapshots rather than performing native forecasting or market analysis. CSV datasets must be exported into third-party analytical tools or data platforms for historical comparison, inventory delta calculations, trend analysis, and forecasting.

**Data pipeline:**

```
Retail Websites → Product & Variant Discovery → Exact SKU-Level Inventory Verification → CSV Export → External Historical Delta Analysis → Competitive & Strategic Intelligence
```

> **Analytical limitation:** Inventory changes are directional signals, not direct measurements of consumer purchases. Replenishment, transfers, adjustments, and differences between retailer-reported inventory and physically available stock must be considered when interpreting market trends. Sell-through, promotional effectiveness, and forecasts require additional data and analytical validation.

---

## mock.shop inventory checker

Checks per-variant inventory for every product on [mock.shop](https://mock.shop).
The auth-free Storefront GraphQL API (`https://mock.shop/api`) lists products and variants;
Playwright then acts like a shopper on the demo storefront
(`https://demostore.hydrogen.mock.shop`). Checkout is never touched.

### Install

```bash
pip install -r requirements.txt
playwright install chromium
```

### Run

```bash
python3 discover.py   # 1. write every product handle to input/mock.shop.csv
python3 main.py       # 2. check each variant, write inventory_results.csv
                      #    add --headed to watch the browser
```

Settings live in `workflows/mock.shop.json` (`api_url`, `store_url`, `page_size`, `probe_quantity`).

#### Step 1: discovery (`discover.py`)

Pages through `products(first, after)` with the API's cursor until `hasNextPage` is false,
and writes the handles to `input/mock.shop.csv`.

#### Step 2: inventory check (`main.py`)

For each handle it reads the variants from the API, then for each variant:

1. `availableForSale = false` → `out_of_stock` (no browser needed).
2. Otherwise, with an empty cart (the `cart` cookie is cleared before each variant): open
   `/products/<handle>?Size=…&Color=…`, decline the cookie banner, confirm the page selected
   the right variant, and click **Add to cart** (quantity 1). When the cart opens, set the
   line's quantity to 999 and click the cart window. The store corrects the line to the
   true available quantity, which is written to the results file.

One browser session is reused for the whole run (scripts stay cached) and images are
turned off, since the check never needs them.

Output: `inventory_results.csv` with handle, product URL, name, type, variant, variant ID,
SKU, quantity, status, details, and `update_time` (US format `MM/DD/YYYY hh:mm:ss AM/PM`).

### Status meanings

- `in_stock`: the store reduced 999 to the true quantity (the `quantity` column).
- `at_least_probe`: the store kept all 999; real stock may be higher.
- `out_of_stock`: not available for sale, or Add to cart is disabled.
- `error`: request failed, product not found, or a page element wasn't found.

mock.shop carts are mocked, so cart numbers reflect mock behaviour, not real stock.

---

## Technical Demonstration & Legal Disclaimer

This project is developed exclusively for educational, research, and portfolio demonstration purposes.

The application is restricted to Shopify's mock.shop development environment, using fictional retail data to demonstrate automated inventory verification techniques without interacting with real retailer inventory systems.

The author does not endorse, encourage, or authorize unauthorized execution against live third-party retail websites, circumvention of access controls, violation of Terms of Service, or interference with retailer infrastructure.

Any adaptation, testing, or deployment involving real third-party retailers requires appropriate authorization and compliance with applicable laws, contractual obligations, and website policies.

This project is a technical proof of concept, not an authorization or recommendation for unauthorized data collection.
