"""
Site catalogue for the Nomadic Engine configurator.

Each site has:
  name         — display name
  region       — continent/region grouping
  location     — city/country label
  temperature  — hot | warm | temperate | cool | cold
  precipitation— wet | rainy | moderate | dry | snowy
  cost         — low | medium | high
  connectivity — slow | medium | fast
  safety       — low | medium | high
  climate_zone — tropical | dry_arid | temperate | continental | polar | mountain_alpine

TODO: populate all 42 sites (6 per region × 7 regions).
      Currently contains 2 example sites per region as placeholders.
"""

SITES: list[dict] = [

    # ── South America ─────────────────────────────────────────────────────────
    {
        "name": "Atacama Plateau", "region": "South America", "location": "Antofagasta, CL",
        "temperature": "cool", "precipitation": "dry",
        "cost": "low", "connectivity": "medium", "safety": "medium",
        "climate_zone": "dry_arid",
    },
    {
        "name": "Patagonia Fjord", "region": "South America", "location": "Aysén, CL",
        "temperature": "cold", "precipitation": "rainy",
        "cost": "medium", "connectivity": "medium", "safety": "high",
        "climate_zone": "temperate",
    },

    # ── Antarctica ────────────────────────────────────────────────────────────
    {
        "name": "Ross Shelf", "region": "Antarctica", "location": "Ross Sea, AQ",
        "temperature": "cold", "precipitation": "snowy",
        "cost": "high", "connectivity": "slow", "safety": "medium",
        "climate_zone": "polar",
    },
    {
        "name": "Dry Valley", "region": "Antarctica", "location": "McMurdo, AQ",
        "temperature": "cold", "precipitation": "dry",
        "cost": "high", "connectivity": "slow", "safety": "medium",
        "climate_zone": "polar",
    },

    # ── Oceania ───────────────────────────────────────────────────────────────
    {
        "name": "Red Centre", "region": "Oceania", "location": "Northern Territory, AU",
        "temperature": "hot", "precipitation": "dry",
        "cost": "medium", "connectivity": "medium", "safety": "high",
        "climate_zone": "dry_arid",
    },
    {
        "name": "Fiordland Edge", "region": "Oceania", "location": "South Island, NZ",
        "temperature": "cool", "precipitation": "rainy",
        "cost": "high", "connectivity": "fast", "safety": "high",
        "climate_zone": "temperate",
    },

    # ── North America ─────────────────────────────────────────────────────────
    {
        "name": "Red Mesa", "region": "North America", "location": "Utah, US",
        "temperature": "hot", "precipitation": "dry",
        "cost": "medium", "connectivity": "fast", "safety": "medium",
        "climate_zone": "dry_arid",
    },
    {
        "name": "Yukon Bend", "region": "North America", "location": "Yukon, CA",
        "temperature": "cold", "precipitation": "snowy",
        "cost": "medium", "connectivity": "medium", "safety": "high",
        "climate_zone": "continental",
    },

    # ── Europe ────────────────────────────────────────────────────────────────
    {
        "name": "Skye Moor", "region": "Europe", "location": "Highlands, UK",
        "temperature": "temperate", "precipitation": "rainy",
        "cost": "medium", "connectivity": "medium", "safety": "high",
        "climate_zone": "temperate",
    },
    {
        "name": "Pine Hollow", "region": "Europe", "location": "Lapland, SE",
        "temperature": "cold", "precipitation": "snowy",
        "cost": "medium", "connectivity": "fast", "safety": "high",
        "climate_zone": "continental",
    },

    # ── Asia ──────────────────────────────────────────────────────────────────
    {
        "name": "Gobi Edge", "region": "Asia", "location": "Ömnögovi, MN",
        "temperature": "hot", "precipitation": "dry",
        "cost": "low", "connectivity": "medium", "safety": "medium",
        "climate_zone": "dry_arid",
    },
    {
        "name": "Hokkaido Forest", "region": "Asia", "location": "Hokkaido, JP",
        "temperature": "cold", "precipitation": "snowy",
        "cost": "high", "connectivity": "fast", "safety": "high",
        "climate_zone": "continental",
    },

    # ── Africa ────────────────────────────────────────────────────────────────
    {
        "name": "Rift Highlands", "region": "Africa", "location": "Rift Valley, KE",
        "temperature": "temperate", "precipitation": "moderate",
        "cost": "low", "connectivity": "medium", "safety": "medium",
        "climate_zone": "temperate",
    },
    {
        "name": "Namib Dune", "region": "Africa", "location": "Erongo, NA",
        "temperature": "hot", "precipitation": "dry",
        "cost": "medium", "connectivity": "medium", "safety": "high",
        "climate_zone": "dry_arid",
    },
]

REGIONS: list[str] = sorted({s["region"] for s in SITES})

def get_site(name: str) -> dict | None:
    return next((s for s in SITES if s["name"] == name), None)

def sites_by_region(region: str) -> list[dict]:
    return [s for s in SITES if s["region"] == region]


def site_to_roof_style(site: dict) -> str:
    """Return the suggested roof_style for a site based on its climate."""
    zone  = site.get("climate_zone", "")
    precip = site.get("precipitation", "")

    if zone in ("polar", "mountain_alpine"):
        return "pitched"
    if zone == "dry_arid":
        return "plain"
    if zone == "tropical":
        return "slanted"
    if zone == "continental":
        return "pitched" if precip == "snowy" else "slanted"
    if zone == "temperate":
        return "slanted" if precip in ("rainy", "wet") else "divided"
    return "any"
