from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from statistics import mean


@dataclass(frozen=True)
class CivicSignal:
    neighborhood: str
    district: str
    latitude: float
    longitude: float
    mobility_delay_min: float
    bus_crowding_percent: int
    incident_reports: int
    emergency_response_min: float
    air_quality_index: int
    flood_risk: float
    clinic_wait_days: float
    service_requests: int
    waste_overflow_reports: int
    energy_peak_percent: int
    sentiment_score: float
    weekly_change_percent: float

    @property
    def sentiment_gap(self) -> float:
        return _bound((0.65 - self.sentiment_score) / 0.75, 0, 1)


@dataclass(frozen=True)
class Recommendation:
    title: str
    action: str
    impact: str
    effort: str
    owners: tuple[str, ...]
    eta_days: int


@dataclass(frozen=True)
class QuestionContext:
    intent: str
    sort_direction: str
    matched_metrics: tuple[str, ...]
    mentioned_neighborhoods: tuple[str, ...]
    modifiers: tuple[str, ...]
    explanation: tuple[str, ...]


FOCUS_KEYWORDS: dict[str, tuple[str, ...]] = {
    "mobility": (
        "traffic",
        "transit",
        "bus",
        "route",
        "commute",
        "congestion",
        "mobility",
        "transport",
    ),
    "public_safety": (
        "safety",
        "incident",
        "emergency",
        "crime",
        "response",
        "preparedness",
    ),
    "health": (
        "health",
        "clinic",
        "hospital",
        "wellness",
        "care",
        "medical",
    ),
    "environment": (
        "air",
        "pollution",
        "climate",
        "flood",
        "rain",
        "heat",
        "environment",
        "waste",
    ),
    "utilities": (
        "energy",
        "power",
        "utility",
        "utilities",
        "water",
        "grid",
        "leak",
    ),
    "citizen_services": (
        "citizen",
        "complaint",
        "feedback",
        "service",
        "requests",
        "engagement",
    ),
}


METRIC_KEYWORDS: dict[str, tuple[str, ...]] = {
    "mobility_delay_min": (
        "delay",
        "traffic",
        "congestion",
        "commute",
        "road",
        "travel",
    ),
    "bus_crowding_percent": (
        "bus",
        "crowding",
        "crowded",
        "transit",
        "route",
        "routes",
    ),
    "incident_reports": (
        "incident",
        "incidents",
        "safety",
        "crime",
        "accident",
        "accidents",
    ),
    "emergency_response_min": (
        "emergency",
        "response",
        "ambulance",
        "fire",
        "dispatch",
    ),
    "air_quality_index": (
        "air",
        "aqi",
        "pollution",
        "smog",
        "emissions",
    ),
    "flood_risk": (
        "flood",
        "flooding",
        "rain",
        "rainfall",
        "storm",
        "waterlogging",
        "disaster",
    ),
    "clinic_wait_days": (
        "clinic",
        "hospital",
        "health",
        "care",
        "medical",
        "wait",
        "wellness",
    ),
    "service_requests": (
        "complaint",
        "complaints",
        "request",
        "requests",
        "311",
        "service",
        "citizen",
    ),
    "waste_overflow_reports": (
        "waste",
        "garbage",
        "trash",
        "overflow",
        "sanitation",
    ),
    "energy_peak_percent": (
        "energy",
        "power",
        "electric",
        "utility",
        "utilities",
        "grid",
    ),
    "sentiment_gap": (
        "trust",
        "sentiment",
        "satisfaction",
        "frustration",
        "equity",
        "inclusive",
        "accessibility",
    ),
    "weekly_change_percent": (
        "trend",
        "forecast",
        "predict",
        "prediction",
        "rising",
        "increasing",
        "growth",
        "next",
        "week",
        "month",
    ),
}


URGENCY_KEYWORDS = {
    "urgent",
    "fastest",
    "immediate",
    "today",
    "tonight",
    "this week",
    "emergency",
    "critical",
}

LOW_RISK_KEYWORDS = {
    "least",
    "lowest",
    "safest",
    "stable",
    "best performing",
    "low risk",
    "healthy",
}

EQUITY_KEYWORDS = {
    "equity",
    "inclusive",
    "accessibility",
    "vulnerable",
    "elderly",
    "disabled",
    "low income",
}

BUDGET_KEYWORDS = {
    "budget",
    "low cost",
    "cheap",
    "quick win",
    "minimal",
}


SAMPLE_SIGNALS: tuple[CivicSignal, ...] = (
    CivicSignal(
        neighborhood="Central Square",
        district="Core",
        latitude=12.9716,
        longitude=77.5946,
        mobility_delay_min=34.0,
        bus_crowding_percent=91,
        incident_reports=38,
        emergency_response_min=8.8,
        air_quality_index=118,
        flood_risk=0.42,
        clinic_wait_days=5.5,
        service_requests=144,
        waste_overflow_reports=18,
        energy_peak_percent=84,
        sentiment_score=0.18,
        weekly_change_percent=12.0,
    ),
    CivicSignal(
        neighborhood="East Junction",
        district="Industrial",
        latitude=12.9851,
        longitude=77.6408,
        mobility_delay_min=41.0,
        bus_crowding_percent=88,
        incident_reports=31,
        emergency_response_min=9.6,
        air_quality_index=151,
        flood_risk=0.64,
        clinic_wait_days=6.1,
        service_requests=117,
        waste_overflow_reports=23,
        energy_peak_percent=92,
        sentiment_score=0.09,
        weekly_change_percent=16.0,
    ),
    CivicSignal(
        neighborhood="River Ward",
        district="Lowland",
        latitude=12.9542,
        longitude=77.5788,
        mobility_delay_min=24.0,
        bus_crowding_percent=67,
        incident_reports=19,
        emergency_response_min=7.1,
        air_quality_index=103,
        flood_risk=0.86,
        clinic_wait_days=4.7,
        service_requests=132,
        waste_overflow_reports=11,
        energy_peak_percent=73,
        sentiment_score=0.24,
        weekly_change_percent=21.0,
    ),
    CivicSignal(
        neighborhood="North Hills",
        district="Residential",
        latitude=13.0148,
        longitude=77.5762,
        mobility_delay_min=18.0,
        bus_crowding_percent=54,
        incident_reports=12,
        emergency_response_min=6.2,
        air_quality_index=84,
        flood_risk=0.24,
        clinic_wait_days=3.2,
        service_requests=63,
        waste_overflow_reports=4,
        energy_peak_percent=66,
        sentiment_score=0.52,
        weekly_change_percent=4.0,
    ),
    CivicSignal(
        neighborhood="Old Market",
        district="Historic",
        latitude=12.9634,
        longitude=77.6125,
        mobility_delay_min=29.0,
        bus_crowding_percent=79,
        incident_reports=27,
        emergency_response_min=8.1,
        air_quality_index=132,
        flood_risk=0.58,
        clinic_wait_days=7.8,
        service_requests=155,
        waste_overflow_reports=26,
        energy_peak_percent=78,
        sentiment_score=0.12,
        weekly_change_percent=14.0,
    ),
    CivicSignal(
        neighborhood="Lakeside",
        district="Mixed Use",
        latitude=12.9479,
        longitude=77.6271,
        mobility_delay_min=16.0,
        bus_crowding_percent=48,
        incident_reports=10,
        emergency_response_min=5.4,
        air_quality_index=71,
        flood_risk=0.35,
        clinic_wait_days=2.8,
        service_requests=52,
        waste_overflow_reports=5,
        energy_peak_percent=58,
        sentiment_score=0.61,
        weekly_change_percent=3.0,
    ),
)


def build_platform_snapshot() -> dict[str, object]:
    scored = [_signal_summary(signal, "overall") for signal in SAMPLE_SIGNALS]
    priority = sorted(scored, key=lambda item: item["risk_score"], reverse=True)

    return {
        "name": "CivicLens AI",
        "mode": "demo",
        "overview": _overview_for("overall", priority),
        "neighborhoods": priority,
        "alerts": _detect_alerts("overall", priority),
        "recommended_focus": priority[0]["neighborhood"],
        "data_sources": [
            "Transit operations",
            "311 service requests",
            "Air quality sensors",
            "Emergency dispatch",
            "Clinic access reports",
            "Utility load monitors",
        ],
    }


def analyze_decision_question(
    question: str, focus_area: str | None = None
) -> dict[str, object]:
    focus = _normalize_focus(focus_area) or infer_focus_area(question)
    context = _question_context(question)
    scored = sorted(
        (_signal_summary(signal, focus, context) for signal in SAMPLE_SIGNALS),
        key=lambda item: item["risk_score"],
        reverse=context.sort_direction == "desc",
    )
    top = scored[0]
    runner_up = scored[1]
    recommendations = _recommendations_for(focus, top["neighborhood"], context)
    confidence = _confidence_for(question, focus)

    return {
        "question": question,
        "focus_area": focus,
        "answer": _answer_for(question, focus, top, runner_up, context),
        "confidence": confidence,
        "overview": _overview_for(focus, scored, context),
        "neighborhoods": scored,
        "alerts": _detect_alerts(focus, scored),
        "recommended_focus": top["neighborhood"],
        "question_context": asdict(context),
        "priority_neighborhoods": scored[:3],
        "insights": _insights_for(focus, top, runner_up, context),
        "recommendations": [asdict(item) for item in recommendations],
        "decision_options": _decision_options_for(focus, top["neighborhood"], context),
        "evidence": _evidence_for(focus, scored[:3]),
        "automation": {
            "suggested_workflow": "Create cross-department action brief",
            "next_trigger": "Notify owners when any priority score rises above 75",
            "owner_queue": [owner for item in recommendations for owner in item.owners][:4],
        },
    }


def infer_focus_area(question: str) -> str:
    normalized = question.lower()
    matches: dict[str, int] = {}
    for focus, keywords in FOCUS_KEYWORDS.items():
        matches[focus] = sum(1 for keyword in keywords if keyword in normalized)

    best_focus, best_count = max(matches.items(), key=lambda item: item[1])
    return best_focus if best_count else "overall"


def _question_context(question: str) -> QuestionContext:
    normalized = question.lower()
    terms = set(re.findall(r"[a-z0-9]+", normalized))

    matched_metrics = tuple(
        metric
        for metric, keywords in METRIC_KEYWORDS.items()
        if any(_contains_phrase(normalized, terms, keyword) for keyword in keywords)
    )
    mentioned_neighborhoods = tuple(
        signal.neighborhood
        for signal in SAMPLE_SIGNALS
        if signal.neighborhood.lower() in normalized
        or signal.district.lower() in normalized
    )

    modifiers: list[str] = []
    if any(keyword in normalized for keyword in URGENCY_KEYWORDS):
        modifiers.append("urgency")
    if any(keyword in normalized for keyword in EQUITY_KEYWORDS):
        modifiers.append("equity")
    if any(keyword in normalized for keyword in BUDGET_KEYWORDS):
        modifiers.append("budget")
    if any(keyword in normalized for keyword in ("forecast", "predict", "next", "trend")):
        modifiers.append("forecast")

    low_risk = any(keyword in normalized for keyword in LOW_RISK_KEYWORDS)
    intent = "least_risk" if low_risk else "priority"
    sort_direction = "asc" if low_risk else "desc"

    explanation: list[str] = []
    if matched_metrics:
        explanation.append(
            "Matched data signals: "
            + ", ".join(_metric_label(metric) for metric in matched_metrics[:4])
        )
    if mentioned_neighborhoods:
        explanation.append(
            "Neighborhood mentioned: " + ", ".join(mentioned_neighborhoods)
        )
    if modifiers:
        explanation.append("Question modifiers: " + ", ".join(modifiers))
    if low_risk:
        explanation.append("Ranked from lowest risk to highest risk")
    if not explanation:
        explanation.append("Using overall civic pressure because no specific signal matched")

    return QuestionContext(
        intent=intent,
        sort_direction=sort_direction,
        matched_metrics=matched_metrics,
        mentioned_neighborhoods=mentioned_neighborhoods,
        modifiers=tuple(modifiers),
        explanation=tuple(explanation),
    )


def _contains_phrase(normalized: str, terms: set[str], phrase: str) -> bool:
    return phrase in normalized if " " in phrase else phrase in terms


def _normalize_focus(focus_area: str | None) -> str | None:
    if not focus_area:
        return None
    normalized = focus_area.strip().lower().replace("-", "_").replace(" ", "_")
    if normalized in FOCUS_KEYWORDS or normalized == "overall":
        return normalized
    return None


def _signal_summary(
    signal: CivicSignal, focus: str, context: QuestionContext | None = None
) -> dict[str, object]:
    base_score = _risk_score(signal, focus)
    adjustment = _question_adjustment(signal, context)
    score = round(_bound(base_score + adjustment, 0, 100))
    return {
        "neighborhood": signal.neighborhood,
        "district": signal.district,
        "latitude": signal.latitude,
        "longitude": signal.longitude,
        "risk_score": score,
        "base_score": base_score,
        "question_adjustment": round(adjustment),
        "severity": _severity(score),
        "drivers": _drivers_for(signal, focus, context),
        "metrics": {
            "mobility_delay_min": signal.mobility_delay_min,
            "bus_crowding_percent": signal.bus_crowding_percent,
            "incident_reports": signal.incident_reports,
            "emergency_response_min": signal.emergency_response_min,
            "air_quality_index": signal.air_quality_index,
            "flood_risk": signal.flood_risk,
            "clinic_wait_days": signal.clinic_wait_days,
            "service_requests": signal.service_requests,
            "waste_overflow_reports": signal.waste_overflow_reports,
            "energy_peak_percent": signal.energy_peak_percent,
            "sentiment_score": signal.sentiment_score,
            "weekly_change_percent": signal.weekly_change_percent,
        },
    }


def _risk_score(signal: CivicSignal, focus: str) -> int:
    profiles = {
        "mobility": (
            (signal.mobility_delay_min / 45, 42),
            (signal.bus_crowding_percent / 100, 34),
            (signal.incident_reports / 45, 14),
            (signal.sentiment_gap, 10),
        ),
        "public_safety": (
            (signal.incident_reports / 45, 42),
            (signal.emergency_response_min / 12, 32),
            (signal.service_requests / 170, 14),
            (signal.sentiment_gap, 12),
        ),
        "health": (
            (signal.clinic_wait_days / 9, 46),
            (signal.air_quality_index / 170, 20),
            (signal.service_requests / 170, 18),
            (signal.sentiment_gap, 16),
        ),
        "environment": (
            (signal.air_quality_index / 170, 32),
            (signal.flood_risk, 30),
            (signal.waste_overflow_reports / 30, 24),
            (signal.weekly_change_percent / 25, 14),
        ),
        "utilities": (
            (signal.energy_peak_percent / 100, 38),
            (signal.waste_overflow_reports / 30, 24),
            (signal.service_requests / 170, 22),
            (signal.weekly_change_percent / 25, 16),
        ),
        "citizen_services": (
            (signal.service_requests / 170, 38),
            (signal.sentiment_gap, 30),
            (signal.waste_overflow_reports / 30, 18),
            (signal.weekly_change_percent / 25, 14),
        ),
        "overall": (
            (signal.mobility_delay_min / 45, 18),
            (signal.incident_reports / 45, 14),
            (signal.air_quality_index / 170, 14),
            (signal.flood_risk, 14),
            (signal.clinic_wait_days / 9, 14),
            (signal.service_requests / 170, 12),
            (signal.energy_peak_percent / 100, 8),
            (signal.sentiment_gap, 6),
        ),
    }
    weighted = profiles.get(focus, profiles["overall"])
    return round(
        _bound(sum(min(value, 1.0) * weight for value, weight in weighted), 0, 100)
    )


def _question_adjustment(
    signal: CivicSignal, context: QuestionContext | None
) -> float:
    if context is None:
        return 0

    adjustment = 0.0
    if context.matched_metrics:
        metric_pressure = mean(
            _metric_pressure(signal, metric) for metric in context.matched_metrics
        )
        adjustment += metric_pressure * 22

    if signal.neighborhood in context.mentioned_neighborhoods:
        adjustment += 24

    if "urgency" in context.modifiers:
        adjustment += min(signal.weekly_change_percent / 25, 1) * 8
        adjustment += min(signal.emergency_response_min / 12, 1) * 4

    if "equity" in context.modifiers:
        adjustment += signal.sentiment_gap * 8
        adjustment += min(signal.clinic_wait_days / 9, 1) * 5
        adjustment += min(signal.service_requests / 170, 1) * 4

    if "forecast" in context.modifiers:
        adjustment += min(signal.weekly_change_percent / 25, 1) * 10

    if "budget" in context.modifiers:
        adjustment += _low_effort_pressure(signal) * 6

    if context.intent == "least_risk":
        adjustment = 0

    return adjustment


def _metric_pressure(signal: CivicSignal, metric: str) -> float:
    values = {
        "mobility_delay_min": signal.mobility_delay_min / 45,
        "bus_crowding_percent": signal.bus_crowding_percent / 100,
        "incident_reports": signal.incident_reports / 45,
        "emergency_response_min": signal.emergency_response_min / 12,
        "air_quality_index": signal.air_quality_index / 170,
        "flood_risk": signal.flood_risk,
        "clinic_wait_days": signal.clinic_wait_days / 9,
        "service_requests": signal.service_requests / 170,
        "waste_overflow_reports": signal.waste_overflow_reports / 30,
        "energy_peak_percent": signal.energy_peak_percent / 100,
        "sentiment_gap": signal.sentiment_gap,
        "weekly_change_percent": signal.weekly_change_percent / 25,
    }
    return _bound(values.get(metric, 0), 0, 1)


def _low_effort_pressure(signal: CivicSignal) -> float:
    return mean(
        (
            min(signal.service_requests / 170, 1),
            min(signal.mobility_delay_min / 45, 1),
            signal.sentiment_gap,
        )
    )


def _drivers_for(
    signal: CivicSignal, focus: str, context: QuestionContext | None = None
) -> list[str]:
    driver_map = {
        "mobility": [
            f"{signal.mobility_delay_min:.0f} minute average delay",
            f"{signal.bus_crowding_percent}% bus crowding",
            f"{signal.incident_reports} reported incidents",
        ],
        "public_safety": [
            f"{signal.incident_reports} safety incidents",
            f"{signal.emergency_response_min:.1f} minute response time",
            f"{signal.service_requests} service requests",
        ],
        "health": [
            f"{signal.clinic_wait_days:.1f} day clinic wait",
            f"AQI {signal.air_quality_index}",
            f"{signal.service_requests} resident requests",
        ],
        "environment": [
            f"AQI {signal.air_quality_index}",
            f"{signal.flood_risk:.0%} flood risk",
            f"{signal.waste_overflow_reports} waste overflow reports",
        ],
        "utilities": [
            f"{signal.energy_peak_percent}% peak load",
            f"{signal.waste_overflow_reports} waste overflow reports",
            f"{signal.weekly_change_percent:.0f}% weekly pressure increase",
        ],
        "citizen_services": [
            f"{signal.service_requests} open requests",
            f"{signal.sentiment_score:.2f} sentiment score",
            f"{signal.weekly_change_percent:.0f}% weekly change",
        ],
    }
    drivers = driver_map.get(
        focus,
        [
            f"{signal.mobility_delay_min:.0f} minute mobility delay",
            f"AQI {signal.air_quality_index}",
            f"{signal.service_requests} service requests",
        ],
    )

    question_drivers = [
        _metric_driver(signal, metric)
        for metric in (context.matched_metrics if context else ())
    ]
    merged: list[str] = []
    for driver in question_drivers + drivers:
        if driver and driver not in merged:
            merged.append(driver)
    return merged[:4]


def _metric_driver(signal: CivicSignal, metric: str) -> str:
    labels = {
        "mobility_delay_min": f"{signal.mobility_delay_min:.0f} minute mobility delay",
        "bus_crowding_percent": f"{signal.bus_crowding_percent}% bus crowding",
        "incident_reports": f"{signal.incident_reports} reported incidents",
        "emergency_response_min": f"{signal.emergency_response_min:.1f} minute emergency response",
        "air_quality_index": f"AQI {signal.air_quality_index}",
        "flood_risk": f"{signal.flood_risk:.0%} flood risk",
        "clinic_wait_days": f"{signal.clinic_wait_days:.1f} day clinic wait",
        "service_requests": f"{signal.service_requests} open service requests",
        "waste_overflow_reports": f"{signal.waste_overflow_reports} waste overflow reports",
        "energy_peak_percent": f"{signal.energy_peak_percent}% peak utility load",
        "sentiment_gap": f"{signal.sentiment_score:.2f} resident sentiment",
        "weekly_change_percent": f"{signal.weekly_change_percent:.0f}% weekly change",
    }
    return labels.get(metric, "")


def _metric_label(metric: str) -> str:
    labels = {
        "mobility_delay_min": "mobility delay",
        "bus_crowding_percent": "bus crowding",
        "incident_reports": "incident reports",
        "emergency_response_min": "emergency response",
        "air_quality_index": "air quality",
        "flood_risk": "flood risk",
        "clinic_wait_days": "clinic wait",
        "service_requests": "service requests",
        "waste_overflow_reports": "waste overflow",
        "energy_peak_percent": "energy peak load",
        "sentiment_gap": "resident sentiment",
        "weekly_change_percent": "weekly trend",
    }
    return labels.get(metric, metric.replace("_", " "))


def _overview_for(
    focus: str,
    scored: list[dict[str, object]],
    context: QuestionContext | None = None,
) -> list[dict[str, object]]:
    top = scored[0]
    avg_risk = mean(float(item["risk_score"]) for item in scored)
    priority_count = len([item for item in scored if item["risk_score"] >= 60])

    if context is not None:
        matched_count = len(context.matched_metrics) + len(context.mentioned_neighborhoods)
        top_adjustment = max(int(item.get("question_adjustment", 0)) for item in scored)
        signal_detail = (
            ", ".join(_metric_label(metric) for metric in context.matched_metrics[:2])
            if context.matched_metrics
            else "overall civic pressure"
        )
        top_label = "Lowest Risk" if context.intent == "least_risk" else "Top Area"
        return [
            _metric(
                "Query Match",
                str(matched_count or 1),
                "question signals used by the model",
            ),
            _metric(
                top_label,
                str(top["neighborhood"]),
                f"score {top['risk_score']} after query weighting",
            ),
            _metric(
                "Question Boost",
                f"+{top_adjustment}",
                signal_detail,
            ),
            _metric(
                "Action Areas",
                str(priority_count),
                "scores above 60 after this question",
            ),
        ]

    overview_by_focus = {
        "mobility": [
            _metric("Priority Areas", str(priority_count), "mobility scores above 60"),
            _metric("Top Corridor", str(top["neighborhood"]), f"risk score {top['risk_score']}"),
            _metric(
                "Avg Delay",
                f"{mean(signal.mobility_delay_min for signal in SAMPLE_SIGNALS):.0f} min",
                "weighted across active corridors",
            ),
            _metric(
                "Peak Crowding",
                f"{max(signal.bus_crowding_percent for signal in SAMPLE_SIGNALS)}%",
                "highest observed bus load",
            ),
        ],
        "public_safety": [
            _metric("Priority Areas", str(priority_count), "safety scores above 60"),
            _metric("Top Area", str(top["neighborhood"]), f"risk score {top['risk_score']}"),
            _metric(
                "Incidents",
                str(sum(signal.incident_reports for signal in SAMPLE_SIGNALS)),
                "reported in the active window",
            ),
            _metric(
                "Slowest Response",
                f"{max(signal.emergency_response_min for signal in SAMPLE_SIGNALS):.1f} min",
                "highest neighborhood response time",
            ),
        ],
        "health": [
            _metric("Priority Areas", str(priority_count), "health access scores above 60"),
            _metric("Top Area", str(top["neighborhood"]), f"risk score {top['risk_score']}"),
            _metric(
                "Avg Clinic Wait",
                f"{mean(signal.clinic_wait_days for signal in SAMPLE_SIGNALS):.1f} days",
                "across community access points",
            ),
            _metric(
                "Longest Wait",
                f"{max(signal.clinic_wait_days for signal in SAMPLE_SIGNALS):.1f} days",
                "highest local backlog",
            ),
        ],
        "environment": [
            _metric("Priority Areas", str(priority_count), "environment scores above 60"),
            _metric("Top Area", str(top["neighborhood"]), f"risk score {top['risk_score']}"),
            _metric(
                "Avg AQI",
                f"{mean(signal.air_quality_index for signal in SAMPLE_SIGNALS):.0f}",
                "across active sensors",
            ),
            _metric(
                "Flood Watch",
                str(len([signal for signal in SAMPLE_SIGNALS if signal.flood_risk >= 0.55])),
                "areas above the flood watch level",
            ),
        ],
        "utilities": [
            _metric("Priority Areas", str(priority_count), "utility scores above 60"),
            _metric("Top Area", str(top["neighborhood"]), f"risk score {top['risk_score']}"),
            _metric(
                "Peak Load",
                f"{max(signal.energy_peak_percent for signal in SAMPLE_SIGNALS)}%",
                "highest utility pressure",
            ),
            _metric(
                "Overflow Reports",
                str(sum(signal.waste_overflow_reports for signal in SAMPLE_SIGNALS)),
                "waste and field service pressure",
            ),
        ],
        "citizen_services": [
            _metric("Priority Areas", str(priority_count), "service scores above 60"),
            _metric("Top Area", str(top["neighborhood"]), f"risk score {top['risk_score']}"),
            _metric(
                "Open Requests",
                str(sum(signal.service_requests for signal in SAMPLE_SIGNALS)),
                "citizen and service desk signals",
            ),
            _metric(
                "Lowest Sentiment",
                f"{min(signal.sentiment_score for signal in SAMPLE_SIGNALS):.2f}",
                "lowest neighborhood trust signal",
            ),
        ],
    }

    return overview_by_focus.get(
        focus,
        [
            _metric(
                "Priority Areas",
                str(priority_count),
                "neighborhoods above the action threshold",
            ),
            _metric(
                "Avg Mobility Delay",
                f"{mean(signal.mobility_delay_min for signal in SAMPLE_SIGNALS):.0f} min",
                "weighted across active corridors",
            ),
            _metric(
                "Open Requests",
                str(sum(signal.service_requests for signal in SAMPLE_SIGNALS)),
                "citizen and service desk signals",
            ),
            _metric(
                "Resilience Score",
                f"{100 - avg_risk:.0f}",
                "higher means lower combined risk",
            ),
        ],
    )


def _metric(label: str, value: str, detail: str) -> dict[str, str]:
    return {"label": label, "value": value, "detail": detail}


def _detect_alerts(
    focus: str = "overall", scored: list[dict[str, object]] | None = None
) -> list[dict[str, object]]:
    alerts: list[dict[str, object]] = []
    for signal in SAMPLE_SIGNALS:
        if signal.flood_risk >= 0.8:
            alerts.append(
                _alert(
                    "environment",
                    "High flood exposure",
                    signal.neighborhood,
                    "critical",
                    f"{signal.flood_risk:.0%} modeled flood risk",
                )
            )
        if signal.air_quality_index >= 145:
            alerts.append(
                _alert(
                    "environment",
                    "Air quality spike",
                    signal.neighborhood,
                    "high",
                    f"AQI {signal.air_quality_index} exceeds healthy operating range",
                )
            )
        if signal.mobility_delay_min >= 38:
            alerts.append(
                _alert(
                    "mobility",
                    "Transit corridor delay",
                    signal.neighborhood,
                    "high",
                    f"{signal.mobility_delay_min:.0f} minute average delay",
                )
            )
        if signal.clinic_wait_days >= 7:
            alerts.append(
                _alert(
                    "health",
                    "Care access backlog",
                    signal.neighborhood,
                    "medium",
                    f"{signal.clinic_wait_days:.1f} day clinic wait",
                )
            )

    if focus != "overall":
        alerts = [alert for alert in alerts if alert["area"] == focus]
        for item in (scored or [])[:3]:
            score = int(item["risk_score"])
            if score < 60:
                continue
            alerts.append(
                _alert(
                    focus,
                    f"{focus.replace('_', ' ').title()} priority score",
                    str(item["neighborhood"]),
                    _severity(score),
                    f"Priority model score {score} driven by {item['drivers'][0]}",
                )
            )

    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    return sorted(alerts, key=lambda item: severity_order[str(item["severity"])])[:6]


def _alert(
    area: str, title: str, neighborhood: str, severity: str, rationale: str
) -> dict[str, object]:
    return {
        "area": area,
        "title": title,
        "neighborhood": neighborhood,
        "severity": severity,
        "rationale": rationale,
    }


def _answer_for(
    question: str,
    focus: str,
    top: dict[str, object],
    runner_up: dict[str, object],
    context: QuestionContext,
) -> str:
    focus_label = focus.replace("_", " ")
    drivers = ", ".join(str(driver) for driver in top["drivers"][:2])
    explanation = " ".join(context.explanation[:2])
    if context.intent == "least_risk":
        return (
            f"For {focus_label}, {top['neighborhood']} is the lowest-risk option "
            f"with a score of {top['risk_score']}. The strongest stability signals are "
            f"{drivers}. {runner_up['neighborhood']} is the next-best low-risk area. "
            f"{explanation}"
        )

    adjustment = int(top.get("question_adjustment", 0))
    adjustment_text = (
        f" The question added {adjustment} relevance points for this area."
        if adjustment > 0
        else ""
    )
    return (
        f"For {focus_label}, {top['neighborhood']} is the strongest priority "
        f"with a score of {top['risk_score']}. The main drivers are {drivers}. "
        f"{runner_up['neighborhood']} is the next area to watch, so the first "
        "decision should combine immediate response in the top area with a "
        f"preventive action in the runner-up.{adjustment_text} {explanation}"
    )


def _insights_for(
    focus: str,
    top: dict[str, object],
    runner_up: dict[str, object],
    context: QuestionContext,
) -> list[dict[str, object]]:
    focus_text = focus.replace("_", " ")
    return [
        {
            "title": "Question Match",
            "body": (
                f"The question was interpreted as {context.intent.replace('_', ' ')} "
                f"for {focus_text}; {context.explanation[0]}"
            ),
            "signal": top["severity"],
        },
        {
            "title": "Near-Term Forecast",
            "body": (
                f"{top['neighborhood']} has enough trend pressure that the model "
                "keeps it near the front of the action queue."
            ),
            "signal": "watch",
        },
        {
            "title": "Equity Lens",
            "body": (
                "Low sentiment and high request volume suggest residents are "
                "already feeling the service impact."
            ),
            "signal": "community",
        },
        {
            "title": "Automation Fit",
            "body": (
                "This decision can trigger a shared brief, owner assignment, "
                "and threshold-based follow-up alert."
            ),
            "signal": focus,
        },
    ]


def _recommendations_for(
    focus: str, neighborhood: object, context: QuestionContext | None = None
) -> tuple[Recommendation, ...]:
    area = str(neighborhood)
    if context and context.intent == "least_risk":
        return (
            Recommendation(
                "Use as a resilience benchmark",
                f"Study practices in {area} and compare them with higher-risk areas.",
                "Turns a stable area into a practical learning reference.",
                "Low",
                ("Analytics", "District Office"),
                10,
            ),
            Recommendation(
                "Preserve service quality",
                f"Keep monitoring {area} so low-risk conditions do not degrade.",
                "Protects current performance while resources shift elsewhere.",
                "Low",
                ("Public Services", "Community Partners"),
                14,
            ),
        )

    if context and "budget" in context.modifiers:
        return (
            Recommendation(
                "Run a low-cost action sprint",
                f"Bundle quick fixes and resident updates for {area}.",
                "Improves visible service quality without a large capital project.",
                "Low",
                ("District Office", "Public Services"),
                7,
            ),
            Recommendation(
                "Escalate only the highest-risk tickets",
                f"Use the model score to route the top issues in {area}.",
                "Keeps staff time focused on the most consequential cases.",
                "Low",
                ("Analytics", "Operations"),
                5,
            ),
        )

    recommendations = {
        "mobility": (
            Recommendation(
                "Rebalance peak transit capacity",
                f"Add short-turn buses and adjust signal priority around {area}.",
                "Reduces delay and crowding in the highest-pressure corridor.",
                "Medium",
                ("Transit Operations", "Traffic Engineering"),
                14,
            ),
            Recommendation(
                "Publish adaptive commuter guidance",
                f"Send route alternatives and crowding alerts for {area}.",
                "Improves resident choices while operational fixes roll out.",
                "Low",
                ("Communications", "Transit Operations"),
                5,
            ),
        ),
        "public_safety": (
            Recommendation(
                "Stage response units by predicted demand",
                f"Pre-position emergency coverage near {area} during peak periods.",
                "Cuts response time in the highest-risk window.",
                "Medium",
                ("Emergency Management", "Public Safety"),
                10,
            ),
            Recommendation(
                "Launch incident prevention micro-campaign",
                f"Target outreach and lighting checks in {area}.",
                "Reduces repeat incidents tied to visible local conditions.",
                "Low",
                ("Public Safety", "Community Partners"),
                21,
            ),
        ),
        "health": (
            Recommendation(
                "Open temporary access hours",
                f"Extend clinic and mobile care availability for {area}.",
                "Reduces wait time for residents with limited alternatives.",
                "Medium",
                ("Public Health", "Clinic Network"),
                14,
            ),
            Recommendation(
                "Route wellness outreach by risk cluster",
                f"Prioritize screening and follow-up messages in {area}.",
                "Finds unmet needs before they become urgent visits.",
                "Low",
                ("Public Health", "Community Volunteers"),
                10,
            ),
        ),
        "environment": (
            Recommendation(
                "Activate climate resilience response",
                f"Inspect drainage, waste hotspots, and air quality mitigations in {area}.",
                "Lowers flood, pollution, and sanitation risk together.",
                "Medium",
                ("Environment", "Public Works"),
                12,
            ),
            Recommendation(
                "Issue targeted resident advisories",
                f"Send air and rain preparedness updates for {area}.",
                "Improves community readiness during the next risk window.",
                "Low",
                ("Environment", "Communications"),
                3,
            ),
        ),
        "utilities": (
            Recommendation(
                "Shift peak utility demand",
                f"Run demand response and field inspection workflows in {area}.",
                "Reduces outage risk and pressure on crews.",
                "Medium",
                ("Utilities", "Energy Partners"),
                14,
            ),
            Recommendation(
                "Prioritize repeated service hotspots",
                f"Batch utility and waste tickets for {area}.",
                "Cuts duplicate dispatch and clears visible service issues.",
                "Low",
                ("Utilities", "Public Works"),
                7,
            ),
        ),
        "citizen_services": (
            Recommendation(
                "Create a service recovery sprint",
                f"Bundle repeated 311 requests in {area} into one owner-led sprint.",
                "Improves closure rate and resident trust.",
                "Medium",
                ("Public Services", "District Office"),
                14,
            ),
            Recommendation(
                "Close the loop with residents",
                f"Send status updates for high-volume request categories in {area}.",
                "Reduces repeat contacts and improves transparency.",
                "Low",
                ("Public Services", "Communications"),
                5,
            ),
        ),
    }
    return recommendations.get(
        focus,
        (
            Recommendation(
                "Stand up a cross-functional action brief",
                f"Coordinate mobility, health, safety, and services work in {area}.",
                "Aligns departments around the highest combined civic pressure.",
                "Medium",
                ("Mayor's Office", "Public Services", "Analytics"),
                7,
            ),
            Recommendation(
                "Monitor runner-up risk daily",
                "Track the second-highest area with automated threshold alerts.",
                "Prevents a second hotspot from becoming urgent.",
                "Low",
                ("Analytics", "District Office"),
                3,
            ),
        ),
    )


def _decision_options_for(
    focus: str, neighborhood: object, context: QuestionContext | None = None
) -> list[dict[str, object]]:
    area = str(neighborhood)
    if context and context.intent == "least_risk":
        return [
            {
                "option": "Benchmark and replicate",
                "best_for": f"Learning from {area}",
                "tradeoff": "Does not directly relieve high-risk areas today",
                "readiness_score": 82,
            },
            {
                "option": "Maintain current coverage",
                "best_for": "Preventing service decline",
                "tradeoff": "Keeps a small amount of capacity in a stable area",
                "readiness_score": 76,
            },
            {
                "option": "Shift capacity elsewhere",
                "best_for": "Maximizing urgent relief",
                "tradeoff": f"Could let conditions in {area} worsen later",
                "readiness_score": 70,
            },
        ]

    return [
        {
            "option": "Immediate intervention",
            "best_for": f"Visible relief in {area}",
            "tradeoff": "Uses more staff capacity this week",
            "readiness_score": 86,
        },
        {
            "option": "Preventive monitoring",
            "best_for": "Lower-cost risk control",
            "tradeoff": "Impact is slower and less visible",
            "readiness_score": 72,
        },
        {
            "option": "Community co-response",
            "best_for": "Trust, feedback, and equity concerns",
            "tradeoff": "Needs strong partner coordination",
            "readiness_score": 78 if focus in {"health", "citizen_services"} else 68,
        },
    ]


def _evidence_for(
    focus: str, priority_neighborhoods: list[dict[str, object]]
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for item in priority_neighborhoods:
        metrics = item["metrics"]
        assert isinstance(metrics, dict)
        rows.append(
            {
                "neighborhood": item["neighborhood"],
                "risk_score": item["risk_score"],
                "severity": item["severity"],
                "top_drivers": item["drivers"],
                "trend": f"{metrics['weekly_change_percent']}% weekly change",
            }
        )
    return rows


def _confidence_for(question: str, focus: str) -> float:
    has_focus_match = focus != "overall"
    has_specific_question = len(question.split()) >= 5
    confidence = 0.74
    if has_focus_match:
        confidence += 0.08
    if has_specific_question:
        confidence += 0.06
    return round(min(confidence, 0.92), 2)


def _severity(score: int) -> str:
    if score >= 75:
        return "critical"
    if score >= 60:
        return "high"
    if score >= 45:
        return "medium"
    return "low"


def _bound(value: float, low: float, high: float) -> float:
    return min(max(value, low), high)
