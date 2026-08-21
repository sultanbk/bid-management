"""
Synthetic data generator for the Sysco Intelligent Supplier Collaboration Portal.

Generates:
  - products.csv     (~600 catalog SKUs across 6 categories)
  - suppliers.csv     (~24 suppliers, ~4 per category)
  - bid_a.json         (cold bid — customer #1)
  - bid_b.json         (warm bid — customer #2, ~65% item overlap with Bid A)

No external dependencies (no Faker) so this runs anywhere with plain Python 3.
Re-run anytime to regenerate — it's deterministic (fixed random seed) unless
you change SEED below.

Usage:
    python3 generate_synthetic_data.py
Output lands in the same folder as this script.
"""

import csv
import json
import random
import os

SEED = 42
random.seed(SEED)

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# 1. CATEGORY DEFINITIONS
# Each category: (name, [(item_base_name, [spec_variants])])
# ---------------------------------------------------------------------------

CATEGORIES = {
    "Disposables & Paper Goods": [
        ("Tissue Paper, 2-ply", ["case of 24", "case of 36", "case of 48"]),
        ("Napkins, White", ["pack of 500", "pack of 1000", "case of 6000"]),
        ("Disposable Cups, 12oz", ["sleeve of 50", "case of 1000"]),
        ("Foil Wrap, Heavy Duty", ["18in x 500ft roll", "12in x 1000ft roll"]),
        ("Plastic Cutlery Set", ["case of 1000", "case of 500"]),
        ("Food Storage Containers", ["32oz, case of 150", "16oz, case of 250"]),
        ("Trash Liners, Heavy Duty", ["55gal, case of 100", "33gal, case of 150"]),
        ("Paper Towel Rolls", ["case of 30", "case of 12"]),
    ],
    "Proteins": [
        ("Chicken Breast, Boneless", ["40lb case, fresh", "40lb case, frozen"]),
        ("Ground Beef, 80/20", ["10lb tube", "40lb case"]),
        ("Pork Loin, Boneless", ["30lb case"]),
        ("Salmon Fillet, Atlantic", ["10lb case, fresh", "20lb case, frozen"]),
        ("Shrimp, 21/25 count", ["5lb bag frozen", "20lb case frozen"]),
        ("Turkey Breast, Sliced", ["10lb case"]),
        ("Bacon, Sliced", ["15lb case"]),
        ("Deli Ham, Sliced", ["10lb case"]),
    ],
    "Produce": [
        ("Romaine Lettuce", ["case of 24 heads"]),
        ("Roma Tomatoes", ["25lb case"]),
        ("Yellow Onions", ["50lb bag"]),
        ("Russet Potatoes", ["50lb bag"]),
        ("Bell Peppers, Mixed", ["11lb case"]),
        ("Bananas", ["40lb case"]),
        ("Carrots, Whole", ["25lb bag"]),
        ("Avocados", ["case of 48"]),
    ],
    "Dry Goods & Pantry": [
        ("Long Grain Rice", ["50lb bag"]),
        ("All-Purpose Flour", ["50lb bag"]),
        ("Pasta, Penne", ["20lb case"]),
        ("Dried Black Beans", ["25lb bag"]),
        ("Vegetable Oil", ["35lb jug", "6x1gal case"]),
        ("Granulated Sugar", ["50lb bag"]),
        ("Coffee, Ground Regular", ["case of 42, 2.5oz"]),
        ("Ketchup Packets", ["case of 1000"]),
    ],
    "Dairy & Refrigerated": [
        ("Shredded Mozzarella", ["6x5lb case"]),
        ("Whole Milk", ["6x1gal case"]),
        ("Butter, Unsalted", ["36x1lb case"]),
        ("Eggs, Large Grade A", ["15dz case"]),
        ("Cream Cheese", ["24x3lb case"]),
        ("Sour Cream", ["4x5lb case"]),
    ],
    "Kitchen Equipment & Smallwares": [
        ("Sheet Pans, Aluminum", ["18x26in, pack of 12"]),
        ("Mixing Bowls, Stainless", ["set of 8"]),
        ("Cutting Boards, HDPE", ["18x24in, pack of 6"]),
        ("Chef Knife Set", ["set of 5"]),
        ("Food Storage Racks", ["6-shelf, wire"]),
        ("Insulated Food Carriers", ["full pan size"]),
    ],
}

SPEC_UNITS_NOTE = {
    "Disposables & Paper Goods": "case/pack based",
    "Proteins": "weight based, fresh/frozen",
    "Produce": "weight or count based",
    "Dry Goods & Pantry": "weight based",
    "Dairy & Refrigerated": "case/weight based, refrigerated",
    "Kitchen Equipment & Smallwares": "unit/set based, non-perishable",
}

# ---------------------------------------------------------------------------
# 2. GENERATE PRODUCT CATALOG (~600 SKUs)
# ---------------------------------------------------------------------------

def generate_products(target_count=600):
    products = []
    sku_counter = 10000
    items_pool = []
    for category, items in CATEGORIES.items():
        for base_name, specs in items:
            for spec in specs:
                items_pool.append((category, base_name, spec))

    # Cycle through the pool, adding slight brand/grade variants to reach target_count
    brand_tags = ["Value Select", "Chef's Reserve", "Sysco Classic", "Sysco Imperial",
                  "Sysco Reliance", "House Brand", "Premium Choice", "Standard Grade"]

    i = 0
    while len(products) < target_count:
        category, base_name, spec = items_pool[i % len(items_pool)]
        brand = brand_tags[(i // len(items_pool)) % len(brand_tags)]
        name = f"{brand} {base_name}"
        sku = f"SYS-{sku_counter}"
        sku_counter += 1
        products.append({
            "sku": sku,
            "name": name,
            "category": category,
            "spec": spec,
        })
        i += 1

    return products[:target_count]


PRODUCTS = generate_products(600)

with open(os.path.join(OUT_DIR, "products.csv"), "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["sku", "name", "category", "spec"])
    writer.writeheader()
    writer.writerows(PRODUCTS)

print(f"Generated {len(PRODUCTS)} products -> products.csv")

# ---------------------------------------------------------------------------
# 3. GENERATE SUPPLIERS (~4 per category, ~24 total)
# ---------------------------------------------------------------------------

SUPPLIER_NAME_PARTS = [
    "Meridian", "Crestline", "Harborview", "Northgate", "Bluepoint", "Summit",
    "Fairfield", "Ridgeway", "Coastal", "Prairie", "Ironwood", "Silverline",
    "Golden State", "Riverbend", "Cedar Grove", "Union", "Continental", "Anchor",
    "Vantage", "Cornerstone", "Redwood", "Highline", "Sterling", "Pacific Crest",
]
SUPPLIER_SUFFIX = ["Foods", "Distributors", "Supply Co.", "Wholesale", "Provisions", "Trading Co."]

def generate_suppliers():
    suppliers = []
    idx = 0
    for category in CATEGORIES:
        for _ in range(4):
            name_part = SUPPLIER_NAME_PARTS[idx % len(SUPPLIER_NAME_PARTS)]
            suffix = SUPPLIER_SUFFIX[idx % len(SUPPLIER_SUFFIX)]
            name = f"{name_part} {suffix}"
            reliability = round(random.uniform(0.55, 0.98), 2)
            email_domain = name.lower().replace(" ", "").replace(".", "").replace(",", "")
            suppliers.append({
                "name": name,
                "category": category,
                "reliability_score": reliability,
                "contact_email": f"sales@{email_domain}.com",
            })
            idx += 1
    return suppliers


SUPPLIERS = generate_suppliers()

with open(os.path.join(OUT_DIR, "suppliers.csv"), "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["name", "category", "reliability_score", "contact_email"])
    writer.writeheader()
    writer.writerows(SUPPLIERS)

print(f"Generated {len(SUPPLIERS)} suppliers -> suppliers.csv")

# ---------------------------------------------------------------------------
# 4. GENERATE BID A and BID B (messy, realistic customer requests)
# Bid B overlaps ~65% with Bid A, plus a few new items, to power the
# "institutional memory" demo moment.
# ---------------------------------------------------------------------------

# Pull a working list of "messy" phrasings (deliberately NOT identical to
# catalog names) so the matching agent has real work to do.
MESSY_PHRASINGS = [
    ("2-ply tissue paper, bulk case", "Disposables & Paper Goods", 40),
    ("white napkins, 1000ct", "Disposables & Paper Goods", 20),
    ("12oz disposable cups", "Disposables & Paper Goods", 15),
    ("heavy duty foil roll", "Disposables & Paper Goods", 10),
    ("plastic forks/spoons/knives combo", "Disposables & Paper Goods", 30),
    ("trash bags, 55 gallon", "Disposables & Paper Goods", 25),
    ("boneless skinless chicken breast, fresh", "Proteins", 60),
    ("80/20 ground beef", "Proteins", 45),
    ("sliced bacon, food service", "Proteins", 20),
    ("atlantic salmon fillets", "Proteins", 15),
    ("romaine lettuce heads", "Produce", 30),
    ("roma tomatoes, case", "Produce", 25),
    ("yellow onions, 50lb", "Produce", 20),
    ("russet potatoes bulk", "Produce", 35),
    ("long grain white rice, 50lb", "Dry Goods & Pantry", 20),
    ("all purpose flour", "Dry Goods & Pantry", 15),
    ("penne pasta, dry", "Dry Goods & Pantry", 18),
    ("vegetable cooking oil, jug", "Dry Goods & Pantry", 12),
    ("shredded mozzarella cheese", "Dairy & Refrigerated", 25),
    ("large grade A eggs", "Dairy & Refrigerated", 30),
    ("unsalted butter", "Dairy & Refrigerated", 18),
    ("whole milk, gallon", "Dairy & Refrigerated", 22),
    ("aluminum sheet pans", "Kitchen Equipment & Smallwares", 10),
    ("stainless mixing bowl set", "Kitchen Equipment & Smallwares", 4),
    ("HDPE cutting boards", "Kitchen Equipment & Smallwares", 6),
]

def build_bid(customer_name, segment, item_indices, bid_id):
    items = []
    for i in item_indices:
        desc, category, qty = MESSY_PHRASINGS[i]
        items.append({"raw_description": desc, "quantity": qty, "category_hint": category})
    return {
        "bid_id": bid_id,
        "customer_name": customer_name,
        "customer_segment": segment,
        "raw_document_note": "Simulated extraction from a messy customer PDF/Excel submission.",
        "items": items,
    }

random.seed(SEED)  # reset for reproducibility of bid selection
all_indices = list(range(len(MESSY_PHRASINGS)))
random.shuffle(all_indices)

bid_a_indices = sorted(all_indices[:18])
overlap_count = round(len(bid_a_indices) * 0.65)
bid_b_overlap = random.sample(bid_a_indices, overlap_count)
remaining = [i for i in all_indices if i not in bid_a_indices]
bid_b_new = remaining[:len(bid_a_indices) - overlap_count]
bid_b_indices = sorted(bid_b_overlap + bid_b_new)

BID_A = build_bid("Riverside Regional Hospital", "hospital", bid_a_indices, "BID-A-001")
BID_B = build_bid("Lakeside Medical Center", "hospital", bid_b_indices, "BID-B-002")

with open(os.path.join(OUT_DIR, "bid_a.json"), "w") as f:
    json.dump(BID_A, f, indent=2)

with open(os.path.join(OUT_DIR, "bid_b.json"), "w") as f:
    json.dump(BID_B, f, indent=2)

overlap_pct = len(set(bid_a_indices) & set(bid_b_indices)) / len(bid_a_indices) * 100

print(f"Bid A: {len(bid_a_indices)} items -> bid_a.json")
print(f"Bid B: {len(bid_b_indices)} items -> bid_b.json")
print(f"Actual overlap between Bid A and Bid B: {overlap_pct:.0f}%")
