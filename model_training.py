from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from .decision_intelligence import SAMPLE_SIGNALS, CivicSignal


FEATURES = (
    "mobility_delay_min",
    "bus_crowding_percent",
    "incident_reports",
    "emergency_response_min",
    "air_quality_index",
    "flood_risk",
    "clinic_wait_days",
    "service_requests",
    "waste_overflow_reports",
    "energy_peak_percent",
    "sentiment_gap",
    "weekly_change_percent",
)


@dataclass(frozen=True)
class TrainingExample:
    neighborhood: str
    week: int
    features: tuple[float, ...]
    label: float


def train_advanced_civic_model(
    accelerator: str = "auto",
    epochs: int = 120,
    learning_rate: float = 0.08,
) -> dict[str, Any]:
    """Train a small forecast model with an accelerator-aware backend.

    The local MVP trains on deterministic synthetic history generated from the
    sample civic signals. In a cloud build, this function is the seam to move
    into Vertex AI custom training with GPU-backed containers.
    """

    epochs = max(10, min(epochs, 500))
    examples = _build_training_examples()
    backend = _select_backend(accelerator)

    if backend["array_module"] is not None:
        training = _train_vectorized(
            examples,
            backend["array_module"],
            epochs=epochs,
            learning_rate=learning_rate,
        )
    else:
        training = _train_python(
            examples,
            epochs=epochs,
            learning_rate=learning_rate,
        )

    predictions = _forecast_neighborhoods(training["weights"], training["bias"])
    return {
        "model_name": "civic-risk-forecast-v1",
        "training_mode": "accelerated_data_science",
        "backend": backend["name"],
        "accelerator_requested": accelerator,
        "accelerator_active": backend["accelerator_active"],
        "samples": len(examples),
        "features": list(FEATURES),
        "epochs": epochs,
        "metrics": training["metrics"],
        "feature_importance": _feature_importance(training["weights"]),
        "predictions": predictions,
        "model_card": {
            "purpose": "Forecast near-term civic risk by neighborhood.",
            "explainability": "Linear weights expose which civic signals drive predictions.",
            "responsible_ai": [
                "Uses explainable feature importance.",
                "Keeps confidence and evidence visible to decision makers.",
                "Treats model output as decision support, not automatic policy.",
            ],
        },
        "cloud_path": {
            "training": "Vertex AI custom training job with GPU when configured",
            "warehouse": "BigQuery feature table for historical civic data",
            "serving": "Vertex AI Endpoint or Cloud Run inference service",
            "monitoring": "Model drift and fairness checks before automated rollout",
        },
    }


def _select_backend(accelerator: str) -> dict[str, Any]:
    requested = accelerator.lower().strip()
    if requested in {"auto", "gpu", "cuda"}:
        try:
            import cupy  # type: ignore[import-not-found]

            return {
                "name": "cupy-gpu",
                "array_module": cupy,
                "accelerator_active": True,
            }
        except ImportError:
            pass

    if requested in {"auto", "cpu", "vectorized"}:
        try:
            import numpy  # type: ignore[import-not-found]

            return {
                "name": "numpy-vectorized-cpu",
                "array_module": numpy,
                "accelerator_active": requested in {"cpu", "vectorized"},
            }
        except ImportError:
            pass

    return {
        "name": "python-cpu-fallback",
        "array_module": None,
        "accelerator_active": False,
    }


def _build_training_examples() -> list[TrainingExample]:
    examples: list[TrainingExample] = []
    for signal in SAMPLE_SIGNALS:
        for week in range(1, 17):
            drift = 1 + (week - 8) * 0.018
            seasonal_rain = 1 + (0.10 if week in {10, 11, 12, 13} else 0)
            synthetic = _synthetic_signal(signal, drift, seasonal_rain)
            label = _future_risk_label(synthetic, week)
            examples.append(
                TrainingExample(
                    neighborhood=signal.neighborhood,
                    week=week,
                    features=_features_for(synthetic),
                    label=label,
                )
            )
    return examples


def _synthetic_signal(
    signal: CivicSignal, drift: float, seasonal_rain: float
) -> CivicSignal:
    return CivicSignal(
        neighborhood=signal.neighborhood,
        district=signal.district,
        latitude=signal.latitude,
        longitude=signal.longitude,
        mobility_delay_min=signal.mobility_delay_min * drift,
        bus_crowding_percent=round(_bound(signal.bus_crowding_percent * drift, 0, 100)),
        incident_reports=round(signal.incident_reports * drift),
        emergency_response_min=signal.emergency_response_min * drift,
        air_quality_index=round(signal.air_quality_index * drift),
        flood_risk=_bound(signal.flood_risk * seasonal_rain, 0, 1),
        clinic_wait_days=signal.clinic_wait_days * drift,
        service_requests=round(signal.service_requests * drift),
        waste_overflow_reports=round(signal.waste_overflow_reports * seasonal_rain),
        energy_peak_percent=round(_bound(signal.energy_peak_percent * drift, 0, 100)),
        sentiment_score=_bound(signal.sentiment_score - ((drift - 1) * 0.3), 0, 1),
        weekly_change_percent=signal.weekly_change_percent * drift,
    )


def _features_for(signal: CivicSignal) -> tuple[float, ...]:
    return (
        signal.mobility_delay_min / 45,
        signal.bus_crowding_percent / 100,
        signal.incident_reports / 45,
        signal.emergency_response_min / 12,
        signal.air_quality_index / 170,
        signal.flood_risk,
        signal.clinic_wait_days / 9,
        signal.service_requests / 170,
        signal.waste_overflow_reports / 30,
        signal.energy_peak_percent / 100,
        signal.sentiment_gap,
        signal.weekly_change_percent / 25,
    )


def _future_risk_label(signal: CivicSignal, week: int) -> float:
    trend_weight = min(signal.weekly_change_percent / 25, 1) * 0.18
    rain_weight = (0.10 if week in {10, 11, 12, 13} else 0) * signal.flood_risk
    base = (
        signal.mobility_delay_min / 45 * 0.13
        + signal.incident_reports / 45 * 0.10
        + signal.air_quality_index / 170 * 0.12
        + signal.flood_risk * 0.13
        + signal.clinic_wait_days / 9 * 0.12
        + signal.service_requests / 170 * 0.12
        + signal.energy_peak_percent / 100 * 0.08
        + signal.sentiment_gap * 0.10
        + signal.waste_overflow_reports / 30 * 0.10
    )
    return _bound(base + trend_weight + rain_weight, 0, 1)


def _train_vectorized(
    examples: list[TrainingExample],
    xp: Any,
    epochs: int,
    learning_rate: float,
) -> dict[str, Any]:
    x = xp.asarray([example.features for example in examples], dtype=float)
    y = xp.asarray([example.label for example in examples], dtype=float)
    weights = xp.zeros(len(FEATURES), dtype=float)
    bias = 0.0

    for _ in range(epochs):
        predictions = x @ weights + bias
        errors = predictions - y
        weights -= learning_rate * ((x.T @ errors) / len(examples))
        bias -= learning_rate * float(errors.mean())

    predictions = x @ weights + bias
    metrics = _metrics_from_arrays(y, predictions, xp)
    return {
        "weights": _to_list(weights, xp),
        "bias": float(bias),
        "metrics": metrics,
    }


def _train_python(
    examples: list[TrainingExample],
    epochs: int,
    learning_rate: float,
) -> dict[str, Any]:
    weights = [0.0 for _ in FEATURES]
    bias = 0.0

    for _ in range(epochs):
        grad_w = [0.0 for _ in FEATURES]
        grad_b = 0.0
        for example in examples:
            prediction = _dot(weights, example.features) + bias
            error = prediction - example.label
            for index, value in enumerate(example.features):
                grad_w[index] += error * value
            grad_b += error
        count = len(examples)
        weights = [
            weight - learning_rate * (gradient / count)
            for weight, gradient in zip(weights, grad_w)
        ]
        bias -= learning_rate * (grad_b / count)

    labels = [example.label for example in examples]
    predictions = [_dot(weights, example.features) + bias for example in examples]
    return {
        "weights": weights,
        "bias": bias,
        "metrics": _metrics_from_lists(labels, predictions),
    }


def _forecast_neighborhoods(weights: list[float], bias: float) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for signal in SAMPLE_SIGNALS:
        score = round(_bound((_dot(weights, _features_for(signal)) + bias) * 100, 0, 100))
        rows.append(
            {
                "neighborhood": signal.neighborhood,
                "forecast_risk_score": score,
                "risk_band": _risk_band(score),
            }
        )
    return sorted(rows, key=lambda row: row["forecast_risk_score"], reverse=True)


def _feature_importance(weights: list[float]) -> list[dict[str, Any]]:
    total = sum(abs(weight) for weight in weights) or 1
    rows = [
        {
            "feature": feature,
            "importance": round(abs(weight) / total, 3),
            "direction": "raises risk" if weight >= 0 else "lowers risk",
        }
        for feature, weight in zip(FEATURES, weights)
    ]
    return sorted(rows, key=lambda row: row["importance"], reverse=True)


def _metrics_from_arrays(y: Any, predictions: Any, xp: Any) -> dict[str, float]:
    errors = predictions - y
    mse = float((errors * errors).mean())
    mae = float(xp.abs(errors).mean())
    variance = float(((y - y.mean()) * (y - y.mean())).mean()) or 1
    return {
        "mae": round(mae, 4),
        "rmse": round(math.sqrt(mse), 4),
        "r2": round(1 - (mse / variance), 4),
    }


def _metrics_from_lists(labels: list[float], predictions: list[float]) -> dict[str, float]:
    errors = [prediction - label for label, prediction in zip(labels, predictions)]
    mse = sum(error * error for error in errors) / len(errors)
    mae = sum(abs(error) for error in errors) / len(errors)
    mean_label = sum(labels) / len(labels)
    variance = sum((label - mean_label) ** 2 for label in labels) / len(labels) or 1
    return {
        "mae": round(mae, 4),
        "rmse": round(math.sqrt(mse), 4),
        "r2": round(1 - (mse / variance), 4),
    }


def _to_list(values: Any, xp: Any) -> list[float]:
    if xp.__name__ == "cupy":
        values = xp.asnumpy(values)
    return [float(value) for value in values.tolist()]


def _dot(weights: list[float] | tuple[float, ...], values: tuple[float, ...]) -> float:
    return sum(weight * value for weight, value in zip(weights, values))


def _risk_band(score: int) -> str:
    if score >= 75:
        return "critical"
    if score >= 60:
        return "high"
    if score >= 45:
        return "medium"
    return "low"


def _bound(value: float, low: float, high: float) -> float:
    return min(max(value, low), high)
