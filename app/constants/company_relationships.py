"""Constants for company relationships in transactions."""
# Lead investor flag values
LEAD_INVESTOR_FLAGS = {
    0: "Not Lead Investor",
    1: "Lead Investor"
}

# Individual equity flag values
INDIVIDUAL_EQUITY_FLAGS = {
    0: "Not Individual Equity",
    1: "Individual Equity"
}

# Company relationship fields from schema
COMPANY_REL_FIELDS = {
    "transaction_id": "tcr.transactionId",
    "company_rel_id": "tcr.companyRelId",
    "relationship_type_id": "tcr.transactionToCompRelTypeId",
    "lead_investor_flag": "tcr.leadInvestorFlag",
    "individual_equity": "tcr.individualEquity",
    "current_investment": "tcr.currentInvestment",
    "percent_acquired": "tcr.percentAcquired"
}

# Join paths based on database schema
COMPANY_REL_JOIN_PATHS = {
    "transaction_company_rel": {
        "table": "ciqTransactionToCompanyRel",
        "alias": "tcr",
        "condition": "tr.transactionId = tcr.transactionId"
    },
    "company_rel": {
        "table": "ciqCompany",
        "alias": "rc",  # related company
        "condition": "tcr.companyRelId = rc.companyId",
        "requires": ["transaction_company_rel"]
    },
    "comp_rel_type": {
        "table": "ciqTransactionToCompRelType",
        "alias": "crt",
        "condition": "tcr.transactionToCompRelTypeId = crt.transactionToCompRelTypeId",
        "requires": ["transaction_company_rel"]
    }
}

# Role-specific company joins
ROLE_SPECIFIC_JOINS = {
    "acquirer": {
        "table": "ciqCompany",
        "alias": "acquirer",
        "condition": "tcr.companyRelId = acquirer.companyId AND tcr.transactionToCompRelTypeId = 1",
        "requires": ["transaction_company_rel"]
    },
    "target": {
        "table": "ciqCompany",
        "alias": "target",
        "condition": "tr.companyId = target.companyId",  # Target is usually the main company
    },
    "seller": {
        "table": "ciqCompany",
        "alias": "seller",
        "condition": "tcr.companyRelId = seller.companyId AND tcr.transactionToCompRelTypeId = 3",
        "requires": ["transaction_company_rel"]
    },
    "investor": {
        "table": "ciqCompany",
        "alias": "investor",
        "condition": "tcr.companyRelId = investor.companyId AND tcr.transactionToCompRelTypeId = 4",
        "requires": ["transaction_company_rel"]
    }
}

# Common relationship query patterns
RELATIONSHIP_PATTERNS = {
    "acquisition": {
        "joins": ["transaction_company_rel", "comp_rel_type", "acquirer"],
        "where": "crt.transactionToCompRelTypeId = 1"
    },
    "investment": {
        "joins": ["transaction_company_rel", "comp_rel_type", "investor"],
        "where": "crt.transactionToCompRelTypeId = 4"
    },
    "divestiture": {
        "joins": ["transaction_company_rel", "comp_rel_type", "seller"],
        "where": "crt.transactionToCompRelTypeId = 3"
    }
}