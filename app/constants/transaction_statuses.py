"""Constants for transaction statuses from ciqTransactionStatus.csv."""
# Status ID to name mapping
TRANSACTION_STATUSES = {
    1: "Announced",
    2: "Completed",
    3: "Pending",
    4: "Terminated",
    5: "Withdrawn",
    6: "Rumored",
    7: "Expired",
    8: "Pending Regulatory Approval",
    9: "Pending Shareholder Approval",
    10: "In Progress"
    # ... all statuses from your CSV
}

# Status name to ID mapping
TRANSACTION_STATUSES_BY_NAME = {v: k for k, v in TRANSACTION_STATUSES.items()}

# Status groupings
STATUS_GROUPS = {
    "active": [1, 2, 3, 8, 9, 10],  # All active statuses
    "completed": [2],               # Successfully completed
    "terminated": [4, 5, 7],        # No longer proceeding
    "in_progress": [1, 3, 8, 9, 10] # Still moving forward
}

# Join paths based on database schema
STATUS_JOIN_PATHS = {
    "transaction_status": {
        "table": "ciqTransactionStatus",
        "alias": "ts",
        "condition": "tr.statusId = ts.statusId"
    }
}

# Fields available in the status table
STATUS_FIELDS = {
    "status_id": "tr.statusId",
    "status_name": "ts.statusName"
}

# Default statuses to include in queries
DEFAULT_INCLUDED_STATUSES = [1, 2, 3, 8, 9, 10]  # Active statuses

# Statuses that should be excluded by default
DEFAULT_EXCLUDED_STATUSES = [4, 5, 7]  # Terminated statuses