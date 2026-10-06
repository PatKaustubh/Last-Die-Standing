from __future__ import annotations

from .decision_intelligence import analyze_decision_question, infer_focus_area


DEFAULT_SUGGESTIONS = [
    "Where should we improve bus routes first?",
    "Which areas need flood preparedness this week?",
    "Where is healthcare access weakest?",
    "Train the forecast model",
]


def respond_to_assistant(message: str) -> dict[str, object]:
    cleaned = message.strip()
    normalized = cleaned.lower()
    if not cleaned:
        return _response(
            "Ask me about mobility, healthcare, safety, utilities, environment, or service gaps.",
            DEFAULT_SUGGESTIONS,
        )

    if normalized in {"hi", "hello", "hey", "help", "start"}:
        return _response(
            (
                "Hi. I can help analyze community data, explain the dashboard, "
                "surface priority areas, or suggest next actions."
            ),
            DEFAULT_SUGGESTIONS,
        )

    if any(term in normalized for term in ("train", "model", "forecast model")):
        return _response(
            (
                "Use the Train button to run the civic risk forecast trainer. "
                "It will return backend, error metrics, feature importance, and "
                "predicted risk bands for each neighborhood."
            ),
            [
                "Train the model",
                "What features influence risk most?",
                "Which area is forecasted highest risk?",
            ],
        )

    focus = infer_focus_area(cleaned)
    analysis = analyze_decision_question(cleaned, focus_area=focus)
    top = analysis["recommended_focus"]
    evidence = analysis["evidence"][0]
    drivers = ", ".join(str(driver) for driver in evidence["top_drivers"][:2])
    reply = (
        f"{top} is the leading result for this question. "
        f"The current score is {evidence['risk_score']} with drivers: {drivers}. "
        f"Recommended next step: {analysis['recommendations'][0]['title']}."
    )
    return _response(
        reply,
        [
            f"What should we do first in {top}?",
            "Show me the evidence",
            "Compare this with another area",
            "Train the forecast model",
        ],
        analysis=analysis,
    )


def _response(
    reply: str,
    suggestions: list[str],
    analysis: dict[str, object] | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "reply": reply,
        "suggestions": suggestions,
    }
    if analysis is not None:
        payload["analysis"] = analysis
    return payload
