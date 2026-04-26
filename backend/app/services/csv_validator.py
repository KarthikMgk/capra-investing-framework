import io
from dataclasses import dataclass, field

import pandas as pd

SCREENER_REQUIRED_COLUMNS = [
    "Symbol",
    "Name",
    "PE",
    "PB",
    "EPS",
    "ROE",
    "Debt_to_Equity",
    "Revenue_Growth",
    "Promoter_Holding",
]

RBI_REQUIRED_COLUMNS = [
    "Date",
    "Repo_Rate",
    "Credit_Growth",
    "Liquidity_Indicator",
]


@dataclass
class ValidationResult:
    is_valid: bool
    missing_columns: list[str] = field(default_factory=list)
    found_columns: list[str] = field(default_factory=list)


def _validate(file_bytes: bytes, required: list[str]) -> ValidationResult:
    if not file_bytes:
        return ValidationResult(is_valid=False, missing_columns=required, found_columns=[])
    try:
        df = pd.read_csv(io.BytesIO(file_bytes))
    except Exception:
        return ValidationResult(is_valid=False, missing_columns=required, found_columns=[])

    found = [c.strip() for c in df.columns]
    missing = [col for col in required if col not in found]
    return ValidationResult(is_valid=len(missing) == 0, missing_columns=missing, found_columns=found)


def validate_screener(file_bytes: bytes) -> ValidationResult:
    return _validate(file_bytes, SCREENER_REQUIRED_COLUMNS)


def validate_rbi(file_bytes: bytes) -> ValidationResult:
    return _validate(file_bytes, RBI_REQUIRED_COLUMNS)
