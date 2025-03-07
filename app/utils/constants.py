"""Constants for query building."""

# Table mappings
TABLE_MAPPINGS = {
    "transactions": "ciqTransaction",
    "companies": "ciqCompany",
    "transactionTypes": "ciqTransactionType",
    "industries": "ciqSimpleIndustry",
    "countries": "ciqCountryGeo",
    "currencies": "ciqCurrency",
    "transactionRelations": "ciqTransactionToCompanyRel",
    "relationTypes": "ciqTransactionToCompRelType",
    "companyRelations": "ciqCompanyRel"
}

# Field mappings for query parameters to database fields
FIELD_MAPPINGS = {
    # Transaction fields
    "type": "tr.transactionIdTypeId",
    "typeName": "tt.transactionIdTypeName",
    "year": "tr.announcedYear",
    "month": "tr.announcedMonth",
    "day": "tr.announcedDay",
    "size": "tr.transactionSize",
    "transactionId": "tr.transactionId",
    "currency": "tr.currencyId",

    # Company fields
    "company": "c.companyName",
    "companyName": "c.companyName",
    "companyId": "c.companyId",
    "target": "targetcompany.companyName",
    "targetId": "targetcompany.companyId",
    "acquirer": "acquirer.companyName",
    "acquirerId": "acquirer.companyId",
    "buyer": "buyer.companyName",
    "buyerId": "buyer.companyId",

    # Industry fields
    "industry": "si.simpleIndustryId",
    "industryDescription": "si.simpleIndustryDescription",

    # Country fields
    "country": "geo.countryId",
    "countryName": "geo.country",

    # Currency fields
    "currencyId": "cur.currencyId",
    "currencyCode": "cur.currencyCode",

    # Relationship fields
    "relationType": "crt.transactionToCompRelTypeId",

    # Aggregate functions
    "count": "COUNT(tr.transactionId)",
    "countDistinct": "COUNT(DISTINCT({}))",
    "sum": "SUM({})",
    "avg": "AVG({})",
    "min": "MIN({})",
    "max": "MAX({})",

    # Window functions
    "sumOver": "SUM({}) OVER (PARTITION BY {})",
    "avgOver": "AVG({}) OVER (PARTITION BY {})",
    "countOver": "COUNT({}) OVER (PARTITION BY {})"
}

# Join paths for tables
JOIN_PATHS = {
    # Basic joins
    "type": {
        "table": "ciqTransactionType",
        "alias": "tt",
        "condition": "tr.transactionIdTypeId = tt.transactionIdTypeId"
    },
    "transaction_type": {
        "table": "ciqTransactionType",
        "alias": "trtype",
        "condition": "tr.transactionIdTypeId = trtype.transactionIdTypeId"
    },
    "company": {
        "table": "ciqCompany",
        "alias": "c",
        "condition": "tr.companyId = c.companyId"
    },
    "company_alt": {
        "table": "ciqCompany",
        "alias": "company",
        "condition": "tr.companyId = company.companyId"
    },
    "company_reverse": {
        "table": "ciqCompany",
        "alias": "c",
        "condition": "c.companyId = tr.companyId"
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
    },

    # Specialized joins for targeting role-based company relationships
    "target_company": {
        "table": "ciqCompany",
        "alias": "targetcompany",
        "condition": "tr.companyId = targetcompany.companyId"
    },
    "target_industry": {
        "table": "ciqSimpleIndustry",
        "alias": "si",
        "condition": "targetcompany.simpleIndustryId = si.simpleIndustryId",
        "requires": ["target_company"]
    },
    "target_country": {
        "table": "ciqCountryGeo",
        "alias": "country",
        "condition": "targetcompany.countryId = country.countryId",
        "requires": ["target_company"]
    },

    # M&A relationship chain
    "transaction_rel": {
        "table": "ciqTransactionToCompanyRel",
        "alias": "cr",
        "condition": "tr.transactionId = cr.transactionId"
    },
    "relation_type": {
        "table": "ciqTransactionToCompRelType",
        "alias": "crt",
        "condition": "cr.transactionToCompRelTypeId = crt.transactionToCompRelTypeId",
        "requires": ["transaction_rel"]
    },
    "company_rel": {
        "table": "ciqCompanyRel",
        "alias": "crel",
        "condition": "cr.companyRelId = crel.companyRelId",
        "requires": ["transaction_rel"]
    },

    # Buyer/Acquirer joins
    "buyer_company": {
        "table": "ciqCompany",
        "alias": "buyer",
        "condition": "crel.companyId = buyer.companyId",
        "requires": ["company_rel"]
    },
    "acquirer_company": {
        "table": "ciqCompany",
        "alias": "acquirer",
        "condition": "crel.companyId = acquirer.companyId",
        "requires": ["company_rel"]
    },
    "buyer_industry": {
        "table": "ciqSimpleIndustry",
        "alias": "buyersi",
        "condition": "buyer.simpleIndustryId = buyersi.simpleIndustryId",
        "requires": ["buyer_company"]
    },
    "buyer_country": {
        "table": "ciqCountryGeo",
        "alias": "buyergeo",
        "condition": "buyer.countryId = buyergeo.countryId",
        "requires": ["buyer_company"]
    }
}

# Supported filter operators
FILTER_OPERATORS = {
    "gte": ">=",
    "lte": "<=",
    "gt": ">",
    "lt": "<",
    "ne": "!=",
    "like": "LIKE",
    "ilike": "ILIKE",
    "null": "IS NULL",
    "notnull": "IS NOT NULL",
    "between": "BETWEEN {} AND {}"
}

# Special SQL functions
SQL_FUNCTIONS = {
    "distinct": "DISTINCT({})",
    "count": "COUNT({})",
    "count_distinct": "COUNT(DISTINCT({}))",
    "sum": "SUM({})",
    "avg": "AVG({})",
    "min": "MIN({})",
    "max": "MAX({})"
}

# Query patterns for recognition
QUERY_PATTERNS = {
    "private_placements": {
        "conditions": {
            "type": "1"
        },
        "recommended_joins": ["type", "company"]
    },
    "buybacks": {
        "conditions": {
            "type": "14"
        },
        "recommended_joins": ["transaction_type", "company_alt"]
    },
    "ma_transactions": {
        "conditions": {
            "type": "2"
        },
        "recommended_joins": ["transaction_type", "target_company", "transaction_rel",
                              "relation_type", "company_rel", "acquirer_company"]
    },
    "industry_country_analysis": {
        "conditions": {
            "industry": "*",
            "country": "*"
        },
        "recommended_joins": ["company", "industry", "country"]
    }
}