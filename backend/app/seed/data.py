"""Static seed data: 15 products + 8 knowledge entries.

Edits here are picked up by re-running `python -m app.seed.seed`. The seed
script upserts on `sku` (products) / `title` (knowledge entries), so renaming
those keys creates new rows rather than mutating existing ones.
"""
from decimal import Decimal
from typing import TypedDict


class ProductSeed(TypedDict):
    sku: str
    name: str
    description: str
    category: str
    price: Decimal
    stock: int


class KnowledgeSeed(TypedDict):
    title: str
    content: str
    category: str


PRODUCTS: list[ProductSeed] = [
    # --- Laptops ---
    {
        "sku": "LAP-001",
        "name": "Lenovo ThinkBook 14 G6",
        "description": (
            "14-inch business laptop with AMD Ryzen 7 7730U, 16GB DDR4 RAM, 512GB NVMe SSD, "
            "and a 1080p anti-glare display. Engineered for daily use by developers and "
            "analysts, with a MIL-STD-810H tested aluminum chassis. Ships with Windows 11 "
            "Pro and a 1-year on-site warranty (extendable to 3 years)."
        ),
        "category": "laptop",
        "price": Decimal("999.00"),
        "stock": 24,
    },
    {
        "sku": "LAP-002",
        "name": "Apple MacBook Air 13\" M3",
        "description": (
            "13.6-inch MacBook Air with Apple M3 chip (8-core CPU, 10-core GPU), 16GB unified "
            "memory, 512GB SSD. Liquid Retina display, 18-hour battery life, MagSafe charging. "
            "Includes AppleCare+ Business eligibility and 14-day return window."
        ),
        "category": "laptop",
        "price": Decimal("1499.00"),
        "stock": 12,
    },
    {
        "sku": "LAP-003",
        "name": "Dell Latitude 5550",
        "description": (
            "15.6-inch enterprise notebook with Intel Core Ultra 7 165U vPro, 16GB DDR5, "
            "512GB SSD, and TPM 2.0. ProSupport Plus options available. Designed for fleet "
            "deployment with serial number reporting and BIOS management hooks."
        ),
        "category": "laptop",
        "price": Decimal("1399.00"),
        "stock": 8,
    },
    {
        "sku": "LAP-004",
        "name": "HP EliteBook 840 G11",
        "description": (
            "14-inch ultraportable for hybrid work, Intel Core Ultra 5 135U, 16GB LPDDR5x, "
            "512GB NVMe. HP Wolf Security pre-loaded, 5MP IR camera with privacy shutter, "
            "and Wi-Fi 6E. 3-year HP Active Care warranty included."
        ),
        "category": "laptop",
        "price": Decimal("1599.00"),
        "stock": 0,  # Intentionally out of stock to validate Phase 3 filtering.
    },
    # --- Monitors ---
    {
        "sku": "MON-001",
        "name": "Dell UltraSharp U2723QE 27\" 4K",
        "description": (
            "27-inch 4K USB-C hub monitor, 3840x2160 IPS Black panel with 2000:1 contrast, "
            "90W USB-C power delivery, RJ-45 Ethernet, and KVM switch. ComfortView Plus low "
            "blue light. 3-year Premium Panel Exchange warranty."
        ),
        "category": "monitor",
        "price": Decimal("629.00"),
        "stock": 35,
    },
    {
        "sku": "MON-002",
        "name": "LG 27UP850N-W 27\" 4K UHD",
        "description": (
            "27-inch 4K IPS monitor with 96W USB-C charging, DisplayHDR 400, and ergonomic "
            "tilt/height/pivot stand. AMD FreeSync support and built-in stereo speakers. "
            "Ideal for content review and design teams."
        ),
        "category": "monitor",
        "price": Decimal("449.00"),
        "stock": 22,
    },
    {
        "sku": "MON-003",
        "name": "Samsung ViewFinity S6 32\" QHD",
        "description": (
            "32-inch QHD (2560x1440) monitor with 99% sRGB and HDR10 support. USB-C 65W "
            "power delivery and integrated KVM. Three-sided borderless design for clean "
            "multi-monitor stacking."
        ),
        "category": "monitor",
        "price": Decimal("389.00"),
        "stock": 18,
    },
    # --- Keyboards ---
    {
        "sku": "KB-001",
        "name": "Logitech MX Keys S",
        "description": (
            "Wireless low-profile keyboard with smart backlighting, multi-device pairing for "
            "up to 3 hosts, and Logi Bolt receiver. USB-C rechargeable. Compatible with "
            "Windows, macOS, Linux, iOS, Android, and ChromeOS."
        ),
        "category": "keyboard",
        "price": Decimal("119.00"),
        "stock": 60,
    },
    {
        "sku": "KB-002",
        "name": "Keychron K2 V2 Wireless Mechanical",
        "description": (
            "75% layout wireless mechanical keyboard with hot-swappable Gateron Brown "
            "switches, RGB backlight, and Bluetooth 5.1 (3 devices). Aluminum frame. "
            "Compatible with Mac and Windows layouts via toggle."
        ),
        "category": "keyboard",
        "price": Decimal("99.00"),
        "stock": 40,
    },
    {
        "sku": "KB-003",
        "name": "Cherry KC 200 MX",
        "description": (
            "Full-size wired keyboard with German-engineered Cherry MX2A Silent Red switches, "
            "USB-C cable, and dedicated multimedia keys. Built for 100M keystrokes per key. "
            "TAA-compliant for government procurement."
        ),
        "category": "keyboard",
        "price": Decimal("89.00"),
        "stock": 25,
    },
    # --- Mice ---
    {
        "sku": "MS-001",
        "name": "Logitech MX Master 3S",
        "description": (
            "Advanced wireless mouse with 8000 DPI optical sensor, MagSpeed scroll wheel, "
            "and quiet clicks (90% sound reduction). USB-C fast charging — 1 minute charge "
            "for 3 hours of use. Pairs with up to 3 devices via Bluetooth or Logi Bolt."
        ),
        "category": "mouse",
        "price": Decimal("99.00"),
        "stock": 80,
    },
    {
        "sku": "MS-002",
        "name": "Microsoft Bluetooth Ergonomic Mouse",
        "description": (
            "Sculpted ergonomic mouse with thumb scoop, four-way scrolling, and Bluetooth 5.0 "
            "Low Energy. Up to 15 months of battery life on two AA cells. Available in matte "
            "black and arctic white. Right-handed only."
        ),
        "category": "mouse",
        "price": Decimal("49.00"),
        "stock": 55,
    },
    # --- Accessories ---
    {
        "sku": "DOC-001",
        "name": "CalDigit TS4 Thunderbolt 4 Dock",
        "description": (
            "18-port Thunderbolt 4 dock with 98W host charging, dual 6K or single 8K display "
            "output, 2.5GbE, UHS-II SD card reader, and digital optical audio. Aluminum "
            "chassis, 230W power supply included. Mac and Windows compatible."
        ),
        "category": "accessory",
        "price": Decimal("399.00"),
        "stock": 14,
    },
    {
        "sku": "WC-001",
        "name": "Logitech Brio 500 1080p Webcam",
        "description": (
            "1080p/30fps webcam with auto light correction, RightSight 2 framing, and "
            "integrated privacy shutter. USB-C connection. Certified for Microsoft Teams, "
            "Zoom, and Google Meet. Includes detachable monitor mount."
        ),
        "category": "accessory",
        "price": Decimal("129.00"),
        "stock": 30,
    },
    {
        "sku": "HS-001",
        "name": "Jabra Evolve2 65 UC Stereo",
        "description": (
            "On-ear wireless headset with 3-mic noise-cancelling system, up to 37 hours of "
            "talk time, and a busy light visible from 360 degrees. USB-A Bluetooth dongle "
            "included. Certified for Microsoft Teams and Zoom UC. Foldable design."
        ),
        "category": "accessory",
        "price": Decimal("279.00"),
        "stock": 20,
    },
]


KNOWLEDGE_ENTRIES: list[KnowledgeSeed] = [
    {
        "title": "Return Policy",
        "category": "returns",
        "content": (
            "All hardware purchases qualify for a 30-day return window starting from the "
            "delivery date. Items must be returned in their original packaging, including all "
            "cables, manuals, and accessories. Opened software, custom-configured laptops, "
            "and clearance items are final sale and not eligible for return. A 15% restocking "
            "fee applies to opened items in resaleable condition; sealed returns are refunded "
            "in full to the original payment method within 5 business days of receipt at our "
            "warehouse. Customers cover return shipping unless the return is the result of a "
            "shipping error or a defective product, in which case a prepaid label will be "
            "issued."
        ),
    },
    {
        "title": "Shipping & Delivery",
        "category": "shipping",
        "content": (
            "Standard ground shipping is free on orders over $250 within the contiguous US "
            "and typically arrives in 3-5 business days. Expedited 2-day air is available for "
            "a flat $25 fee per shipment, and overnight delivery is available for $60. Orders "
            "placed before 2:00 PM Eastern on a business day ship the same day; orders placed "
            "after that cutoff or on weekends ship the next business day. We do not currently "
            "ship to PO boxes or APO/FPO addresses. Tracking numbers are emailed automatically "
            "once the carrier picks up the package."
        ),
    },
    {
        "title": "Warranty Coverage",
        "category": "warranty",
        "content": (
            "All new products carry the manufacturer's standard warranty, which ranges from 1 "
            "to 3 years depending on the brand and SKU. Extended warranties (up to 5 years "
            "total) and on-site service plans are available at the time of checkout for most "
            "laptops, monitors, and docking stations. Warranty claims for accidental damage, "
            "spills, or unauthorized modifications are not covered under the standard plan; "
            "the Accidental Damage Protection rider is required and must be purchased within "
            "30 days of delivery. Open a warranty case through your account portal or by "
            "emailing support@example.com with your order number and a description of the "
            "issue."
        ),
    },
    {
        "title": "Payment Terms (Net 30)",
        "category": "payment",
        "content": (
            "Verified business accounts may apply for Net 30 invoicing on orders of $1,000 or "
            "more. Approval requires a completed credit application, two trade references, "
            "and a most-recent 12-month tax return or audited financial statement. Once "
            "approved, your account is assigned a credit limit between $5,000 and $250,000 "
            "based on the application. Invoices are issued at shipment and are due 30 days "
            "from the invoice date. Late payments accrue 1.5% interest per month. We also "
            "accept ACH, wire transfer, and major credit cards (Visa, MasterCard, American "
            "Express) on every order regardless of credit terms."
        ),
    },
    {
        "title": "Bulk Discount Tiers",
        "category": "general",
        "content": (
            "Volume pricing is available on hardware orders that meet category thresholds. "
            "Orders of 10-24 identical units receive a 5% discount; 25-49 units, 8%; 50-99 "
            "units, 12%; and 100+ units, 15%. Discounts are calculated per SKU and per "
            "purchase order — they cannot be aggregated across multiple POs. Mixed orders "
            "qualify for the discount tier of the largest single-SKU line. Combined hardware-"
            "and-services bundles over $5,000 qualify for an additional negotiated discount; "
            "contact your account manager to scope the deal before placing the order."
        ),
    },
    {
        "title": "International Shipping",
        "category": "shipping",
        "content": (
            "We ship to Canada, Mexico, the UK, the EU, Australia, Japan, and Singapore. "
            "International orders are processed via DHL Express or FedEx International "
            "Priority and typically arrive in 4-8 business days depending on customs "
            "clearance. The customer is the importer of record and is responsible for any "
            "duties, taxes, and brokerage fees assessed by the destination country. We "
            "include a commercial invoice with every shipment. Lithium-ion batteries (laptops "
            "and accessories with built-in cells) ship in compliance with IATA Section II "
            "regulations and may not be combined with hazmat-restricted goods."
        ),
    },
    {
        "title": "Damaged Goods Procedure",
        "category": "returns",
        "content": (
            "If a shipment arrives with visible carrier damage, refuse delivery and contact "
            "support within 24 hours so we can file a claim with the carrier. If the damage "
            "is concealed and only discovered after opening, photograph the box, packaging, "
            "and product before contacting support; we need these images to complete the "
            "claim. Replacement units are shipped via overnight delivery at no charge once "
            "the damage report is approved (typically within one business day). Do not "
            "discard the original packaging until the replacement has been delivered and "
            "inspected."
        ),
    },
    {
        "title": "RMA Process",
        "category": "warranty",
        "content": (
            "To return a defective product under warranty, request an RMA number through your "
            "account portal or by emailing support@example.com. RMA numbers are valid for 14 "
            "days from issue and must be visible on the outside of the return shipment. "
            "Include all original accessories — missing items will be deducted from the "
            "credit. Repaired or replacement units are typically shipped within 5 business "
            "days of receipt at our depot. If the depot determines the unit is not defective, "
            "we will return the unit to you and may charge a $75 inspection fee."
        ),
    },
]
