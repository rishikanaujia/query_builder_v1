"""Constants for industries from ciqSimpleIndustry.csv."""
# Industry ID to name mapping
INDUSTRIES = {
    1: "Aerospace & Defense",
    2: "Automobiles & Components",
    3: "Banks",
    4: "Capital Goods",
    5: "Chemicals",
    6: "Commercial Services & Supplies",
    7: "Construction & Engineering",
    8: "Consumer Durables & Apparel",
    9: "Consumer Services",
    10: "Diversified Financials",
    11: "Education Services",
    12: "Energy Equipment & Services",
    13: "Food & Staples Retailing",
    14: "Food, Beverage & Tobacco",
    15: "Healthcare Equipment & Services",
    16: "Hotels, Restaurants & Leisure",
    17: "Household & Personal Products",
    18: "Independent Power Producers",
    19: "Insurance",
    20: "Internet & Catalog Retail",
    # ... continue with all 74 industries
    32: "Pharmaceuticals & Biotechnology",
    34: "Real Estate",
    60: "Software & Services",
    63: "Technology Hardware & Equipment",
    69: "Telecommunications Services",
    70: "Transportation",
    # ... remainder of industries
}

# Industry name to ID mapping
INDUSTRIES_BY_NAME = {v: k for k, v in INDUSTRIES.items()}

# Industry groupings
INDUSTRY_SECTORS = {
    "Technology": [60, 63],  # Software & Services, Technology Hardware
    "Healthcare": [15, 32],  # Healthcare Equipment, Pharmaceuticals
    "Financial": [3, 10, 19],  # Banks, Diversified Financials, Insurance
    "Real Estate": [34],
    "Consumer": [8, 9, 14, 16, 17, 20],  # Consumer products & services
    # ... other sector groupings
}

# Reverse mapping for lookup by industry ID
INDUSTRY_TO_SECTOR = {}
for sector, ids in INDUSTRY_SECTORS.items():
    for id in ids:
        INDUSTRY_TO_SECTOR[id] = sector