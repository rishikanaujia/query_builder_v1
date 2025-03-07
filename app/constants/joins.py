"""Consolidated join paths for query building."""
from app.constants.transaction_types import TRANSACTION_TYPE_JOIN_PATHS
from app.constants.relationship_types import RELATIONSHIP_JOIN_PATHS
from app.constants.advisory_types import ADVISORY_JOIN_PATHS
from app.constants.transaction_statuses import STATUS_JOIN_PATHS
from app.constants.company_relationships import COMPANY_REL_JOIN_PATHS, ROLE_SPECIFIC_JOINS

# Base transaction table joins
BASE_JOINS = {
    "company": {
        "table": "ciqCompany",
        "alias": "c",
        "condition": "tr.companyId = c.companyId"
    },
    "industry": {
        "table": "ciqSimpleIndustry",
        "alias": "si",
        "condition": "c.simpleIndustryId = si.simpleIndustryId",
        "requires": ["company"]
    },
    "country": {
        "table": "ciqCountryGeo",
        "alias": "geo",
        "condition": "c.countryId = geo.countryId",
        "requires": ["company"]
    },
    "currency": {
        "table": "ciqCurrency",
        "alias": "cur",
        "condition": "tr.currencyId = cur.currencyId"
    }
}

# Combine all join paths into a single dictionary
ALL_JOIN_PATHS = {
    **BASE_JOINS,
    **TRANSACTION_TYPE_JOIN_PATHS,
    **RELATIONSHIP_JOIN_PATHS,
    **ADVISORY_JOIN_PATHS,
    **STATUS_JOIN_PATHS,
    **COMPANY_REL_JOIN_PATHS,
    **ROLE_SPECIFIC_JOINS
}