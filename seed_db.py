"""Generate ~50 mock subcontractor profiles with a realistic spread of
document expiration dates covering all three status buckets.

Standalone and reproducible: fixed random seed, safe to rerun (drops and
recreates tables each time).
"""

import random
from datetime import date, timedelta

from db import get_connection, init_schema

SEED = 42

TRADES = [
    "Electrical", "Plumbing", "MEP", "Concrete", "Steel", "Drywall",
    "Roofing", "Excavation", "Glazing", "Painting", "HVAC", "Masonry",
    "Landscaping", "Demolition", "Fire Protection",
]

FIRST_WORDS = [
    "Summit", "Ironclad", "Bluestone", "Cascade", "Vanguard", "Redwood",
    "Granite", "Horizon", "Pinnacle", "Coastal", "Atlas", "Keystone",
    "Meridian", "Tri-State", "Northgate", "Union", "Apex", "Sterling",
    "Bedrock", "Harborview",
]

COMPANY_TYPES = ["Contracting", "Services", "Group", "Builders", "Solutions", "Co."]

SCOPE_TEMPLATES = {
    "Electrical": "Interior wiring, panel installation, and lighting",
    "Plumbing": "Water supply, drainage, and fixture installation",
    "MEP": "Mechanical, electrical, and plumbing coordination",
    "Concrete": "Foundation pours and structural concrete work",
    "Steel": "Structural steel erection and welding",
    "Drywall": "Framing, drywall hanging, and finishing",
    "Roofing": "Roof deck installation and waterproofing",
    "Excavation": "Site grading and excavation",
    "Glazing": "Window and curtain wall installation",
    "Painting": "Interior and exterior painting",
    "HVAC": "Ductwork and climate control system installation",
    "Masonry": "Brick and block wall construction",
    "Landscaping": "Site grading, planting, and hardscape",
    "Demolition": "Selective demolition and debris removal",
    "Fire Protection": "Sprinkler system installation and inspection",
}


def make_name(rng: random.Random, used: set) -> str:
    while True:
        name = f"{rng.choice(FIRST_WORDS)} {rng.choice(COMPANY_TYPES)}"
        if name not in used:
            used.add(name)
            return name


def make_pm_email(name: str) -> str:
    slug = name.lower().replace(" ", "").replace(".", "").replace("-", "")
    return f"pm@{slug}.example.com"


def pick_expiration(rng: random.Random, today: date) -> date:
    """Pick an expiration date, weighted so the overall seed set has a
    visible mix of green, yellow, and red across all subcontractors."""
    bucket = rng.choices(["green", "yellow", "red"], weights=[60, 20, 20])[0]
    if bucket == "green":
        return today + timedelta(days=rng.randint(16, 400))
    if bucket == "yellow":
        return today + timedelta(days=rng.randint(1, 15))
    return today - timedelta(days=rng.randint(0, 120))


def seed(num_subcontractors: int = 50, today: date | None = None) -> None:
    today = today or date.today()
    rng = random.Random(SEED)
    used_names: set = set()

    conn = get_connection()
    conn.executescript("DROP TABLE IF EXISTS documents; DROP TABLE IF EXISTS subcontractors;")
    init_schema(conn)

    for _ in range(num_subcontractors):
        trade = rng.choice(TRADES)
        name = make_name(rng, used_names)
        scope = SCOPE_TEMPLATES[trade]
        pm_email = make_pm_email(name)

        cur = conn.execute(
            "INSERT INTO subcontractors (name, trade, scope_of_work, pm_email) VALUES (?, ?, ?, ?)",
            (name, trade, scope, pm_email),
        )
        sub_id = cur.lastrowid

        doc_types = ["General Liability Insurance", "Workers' Compensation"]
        if rng.random() < 0.6:
            doc_types.append("Safety Certification")

        for doc_type in doc_types:
            expiration = pick_expiration(rng, today)
            conn.execute(
                "INSERT INTO documents (subcontractor_id, doc_type, expiration_date) VALUES (?, ?, ?)",
                (sub_id, doc_type, expiration.isoformat()),
            )

    conn.commit()
    conn.close()


if __name__ == "__main__":
    seed()
    print("Seed complete: 50 subcontractors with documents inserted into compliance.db")
