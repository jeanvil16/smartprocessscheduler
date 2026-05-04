from __future__ import annotations

import hashlib
from dataclasses import dataclass
import numpy as np
from sklearn.ensemble import RandomForestRegressor

from .feature_extractor import QueryFeatures


def make_fingerprint(sql: str) -> str:
    normalized = " ".join(sql.lower().split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]


@dataclass
class RuntimePrediction:
    runtime_ms: float


class RuntimePredictor:
    def __init__(self) -> None:
        # Bootstrap model with synthetic but plausible samples.
        self.model = RandomForestRegressor(n_estimators=64, random_state=7)
        self.x_train = np.array(
            [
                [1, 0, 1, 1, 1200, 30],
                [1, 2, 1, 0, 45000, 180],
                [1, 4, 2, 0, 280000, 500],
                [1, 1, 0, 1, 3500, 45],
                [2, 3, 3, 0, 900000, 700],
                [1, 0, 0, 1, 500, 25],
            ],
            dtype=float,
        )
        self.y_train = np.array([42, 290, 680, 95, 1200, 20], dtype=float)
        self.model.fit(self.x_train, self.y_train)

    def predict(self, features: QueryFeatures) -> RuntimePrediction:
        y = self.model.predict(np.array([features.as_vector()], dtype=float))[0]
        return RuntimePrediction(runtime_ms=max(1.0, float(y)))

    def partial_refit(self, features: QueryFeatures, observed_runtime_ms: float) -> None:
        x_new = np.array([features.as_vector()], dtype=float)
        y_new = np.array([observed_runtime_ms], dtype=float)
        self.x_train = np.vstack([self.x_train, x_new])
        self.y_train = np.concatenate([self.y_train, y_new])
        self.model.fit(self.x_train, self.y_train)
