"""Constants for transaction types from ciqTransactionType.csv."""
# Transaction type ID to name mapping
TRANSACTION_TYPES = {
    1: "Private Placement",
    2: "M&A Transaction",
    3: "IPO",
    4: "Secondary Offering",
    5: "Buyout",
    6: "Venture Capital/Private Equity",
    7: "Spin-off/Split-off",
    14: "Buyback"
    # Add any additional types from your CSV
}

# Transaction type name to ID mapping
TRANSACTION_TYPES_BY_NAME = {v: k for k, v in TRANSACTION_TYPES.items()}

# Transaction types that require relationship joins
RELATIONSHIP_TRANSACTION_TYPES = [2, 5]  # M&A and Buyouts

# Transaction types that typically involve multiple companies
MULTI_COMPANY_TRANSACTION_TYPES = [2, 5, 7]  # M&A, Buyouts, Spin-offs

# Join paths for transaction types based on database schema
TRANSACTION_TYPE_JOIN_PATHS = {
    "transaction_type": {
        "table": "ciqTransactionType",
        "alias": "tt",
        "condition": "tr.transactionIdTypeId = tt.transactionIdTypeId"
    }
}

# Default fields to select for each transaction type
DEFAULT_FIELDS_BY_TYPE = {
    1: ["tr.transactionId", "c.companyName", "tr.announcedDay", "tr.announcedMonth",
        "tr.announcedYear", "tr.transactionSize", "tr.currencyId"],
    2: ["tr.transactionId", "target.companyName AS Target", "acquirer.companyName AS Acquirer",
        "tr.announcedDay", "tr.announcedMonth", "tr.announcedYear", "tr.transactionSize", "tr.currencyId"],
    # Additional default fields for other types
}

# Common query patterns for each transaction type
COMMON_PATTERNS_BY_TYPE = {
    1: {
        "private_placements_by_company": {
            "description": "Count of private placements by company",
            "select": "c.companyName, COUNT(tr.transactionId) AS privatePlacementCount",
            "group_by": "c.companyName",
            "order_by": "privatePlacementCount DESC"
        }
    },
    2: {
        "acquisitions_by_company": {
            "description": "Acquisitions made by a company",
            "joins": ["tcr", "crt"],
            "where": "crt.transactionToCompRelTypeId = 1"  # Acquirer relationship
        }
    },
    14: {
        "buybacks_by_industry": {
            "description": "Buybacks grouped by industry",
            "select": "si.simpleIndustryDescription, SUM(tr.transactionSize) AS totalBuybackValue",
            "group_by": "si.simpleIndustryDescription",
            "order_by": "totalBuybackValue DESC"
        }
    }
}