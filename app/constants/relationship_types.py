"""Constants for relationship types from ciqTransactionToCompRelType.csv."""
# Relationship type ID to name mapping
RELATIONSHIP_TYPES = {
    1: "Acquirer",
    2: "Target",
    3: "Seller",
    4: "Investor",
    5: "Advisor"
    # ... any additional types from your CSV
}

# Relationship type name to ID mapping
RELATIONSHIP_TYPES_BY_NAME = {v: k for k, v in RELATIONSHIP_TYPES.items()}

# Relationship types that require company joins
COMPANY_RELATIONSHIP_TYPES = [1, 2, 3, 4]  # All except possibly Advisor

# Common relationship combinations
RELATIONSHIP_COMBINATIONS = {
    "acquisition": [1, 2],  # Acquirer + Target
    "investment": [4],      # Investor only
    "divestiture": [2, 3]   # Target + Seller
}

# Join paths based on the database schema
RELATIONSHIP_JOIN_PATHS = {
    "transaction_company_rel": {
        "table": "ciqTransactionToCompanyRel",
        "alias": "tcr",
        "condition": "tr.transactionId = tcr.transactionId"
    },
    "comp_rel_type": {
        "table": "ciqTransactionToCompRelType",
        "alias": "crt",
        "condition": "tcr.transactionToCompRelTypeId = crt.transactionToCompRelTypeId",
        "requires": ["transaction_company_rel"]
    },
    "related_company": {
        "table": "ciqCompany",
        "alias": "rc",
        "condition": "tcr.companyRelId = rc.companyId",
        "requires": ["transaction_company_rel"]
    }
}

# Fields available in the relationship tables
RELATIONSHIP_FIELDS = {
    "relationship_type": "crt.transactionToCompRelTypeId",
    "relationship_name": "crt.transactionToCompanyRelType",
    "lead_investor": "tcr.leadInvestorFlag",
    "individual_equity": "tcr.individualEquity",
    "current_investment": "tcr.currentInvestment",
    "percent_acquired": "tcr.percentAcquired",
    "company_rel_id": "tcr.companyRelId"
}

# Join requirements for each relationship type
JOIN_REQUIREMENTS = {
    1: ["transaction_company_rel", "comp_rel_type"],  # Acquirer
    2: ["transaction_company_rel", "comp_rel_type"],  # Target
    3: ["transaction_company_rel", "comp_rel_type"],  # Seller
    4: ["transaction_company_rel", "comp_rel_type"],  # Investor
    5: ["transaction_to_advisor", "advisor_type"]     # Advisor
}

# Flag values
FLAG_VALUES = {
    "lead_investor": {
        0: "Not Lead Investor",
        1: "Lead Investor"
    },
    "individual_equity": {
        0: "Not Individual Equity",
        1: "Individual Equity"
    }
}