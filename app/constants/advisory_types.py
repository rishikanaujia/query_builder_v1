"""Constants for advisory types from ciqAdvisorType.csv."""
# Advisory type ID to name mapping
ADVISORY_TYPES = {
    1: "Financial Advisor",
    2: "Legal Advisor",
    3: "Lead Manager",
    4: "Co-Manager",
    5: "Accounting Advisor",
    6: "Fairness Opinion Provider",
    7: "Technical Advisor",
    8: "Strategic Advisor"
    # ... all types from your CSV
}

# Advisory type name to ID mapping
ADVISORY_TYPES_BY_NAME = {v: k for k, v in ADVISORY_TYPES.items()}

# Advisory type categories
ADVISORY_CATEGORIES = {
    "financial": [1, 3, 4, 6],  # Financial-related advisors
    "legal": [2],               # Legal advisors
    "technical": [5, 7],        # Technical advisors
    "strategic": [8]            # Strategic advisors
}

# Join paths based on database schema
ADVISORY_JOIN_PATHS = {
    "transaction_to_advisor": {
        "table": "ciqTransactionToAdvisor",
        "alias": "tadv",
        "condition": "tr.transactionId = tadv.transactionId"
    },
    "advisor_type": {
        "table": "ciqAdvisorType",
        "alias": "advtype",
        "condition": "tadv.advisorTypeId = advtype.advisorTypeId",
        "requires": ["transaction_to_advisor"]
    },
    "advisor_company": {
        "table": "ciqCompany",
        "alias": "advisor",
        "condition": "tadv.companyId = advisor.companyId",
        "requires": ["transaction_to_advisor"]
    }
}

# Fields available in the advisor tables
ADVISORY_FIELDS = {
    "advisor_type_id": "advtype.advisorTypeId",
    "advisor_type_name": "advtype.advisorTypeName",
    "advisor_company_id": "tadv.companyId",
    "advisor_company_name": "advisor.companyName"
}

# Common advisory combinations for different transaction types
TYPICAL_ADVISORIES = {
    1: [1, 2],         # Private Placement: Financial, Legal
    2: [1, 2, 6, 8],   # M&A: Financial, Legal, Fairness, Strategic
    3: [1, 2, 3, 4],   # IPO: Financial, Legal, Lead Manager, Co-Manager
    4: [1, 2, 3, 4]    # Secondary Offering: Financial, Legal, Lead Manager, Co-Manager
}