from __future__ import annotations

import re
from dataclasses import dataclass


SELECT_RE = re.compile(r"\bSELECT\b", re.IGNORECASE)
JOIN_RE = re.compile(r"\bJOIN\b", re.IGNORECASE)
WHERE_RE = re.compile(r"\bWHERE\b", re.IGNORECASE)


@dataclass
class QueryFeatures:
    sql_select_tokens: int
    sql_join_tokens: int
    sql_where_tokens: int
    scan_type_index: int
    estimated_rows: float
    historical_drift: float

    def as_vector(self) -> list[float]:
        return [
            float(self.sql_select_tokens),
            float(self.sql_join_tokens),
            float(self.sql_where_tokens),
            float(self.scan_type_index),
            float(self.estimated_rows),
            float(self.historical_drift),
        ]


def parse_sql_token_features(sql: str) -> tuple[int, int, int]:
    return (
        len(SELECT_RE.findall(sql)),
        len(JOIN_RE.findall(sql)),
        len(WHERE_RE.findall(sql)),
    )


def scan_type_to_int(scan_type: str) -> int:
    scan = scan_type.lower().strip()
    if scan == "index":
        return 1
    return 0
