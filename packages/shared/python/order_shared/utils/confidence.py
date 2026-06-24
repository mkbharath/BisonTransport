"""Confidence scoring and routing logic."""

import os
from dataclasses import dataclass


@dataclass
class ConfidenceRoute:
    """Result of confidence-based routing decision."""

    target_queue: str
    hitl_queue_type: str | None = None
    reason: str = ""


def get_threshold(name: str, default: int) -> float:
    """Get a threshold value from environment or return default."""
    return float(os.environ.get(f"THRESHOLD_{name}", str(default)))


def compute_weighted_confidence(
    field_scores: dict[str, float],
    mandatory_fields: list[str],
    weights: dict[str, float] | None = None,
) -> float:
    """Compute overall confidence as weighted average of mandatory field scores.

    Args:
        field_scores: {field_name: confidence_0_to_100}
        mandatory_fields: list of field names that are mandatory
        weights: optional {field_name: weight}; defaults to equal weights

    Returns:
        Overall confidence score 0-100.
    """
    if not mandatory_fields:
        return 0.0

    relevant_scores: list[tuple[float, float]] = []
    for field in mandatory_fields:
        score = field_scores.get(field, 0.0)
        weight = weights.get(field, 1.0) if weights else 1.0
        relevant_scores.append((score, weight))

    if not relevant_scores:
        return 0.0

    total_weighted = sum(score * weight for score, weight in relevant_scores)
    total_weight = sum(weight for _, weight in relevant_scores)

    if total_weight == 0:
        return 0.0

    return total_weighted / total_weight


def route_by_confidence(
    overall_confidence: float,
    has_missing_mandatory: bool,
    is_duplicate: bool = False,
    is_hazmat: bool = False,
    customer_always_hitl: bool = False,
) -> ConfidenceRoute:
    """Determine routing based on confidence score and validation results.

    Routing logic:
    - Hazmat always → HITL (validation_failure queue)
    - Customer with always_hitl flag → HITL (confidence_review queue)
    - Duplicate detected → HITL (duplicate_review queue)
    - >= auto_process threshold + no missing fields → auto-process queue
    - >= human_review threshold → HITL (confidence_review queue)
    - Missing mandatory + auto-comm threshold met → communication queue
    - < human_review threshold → exception queue
    """
    auto_process = get_threshold("AUTO_PROCESS", 95)
    human_review = get_threshold("HUMAN_REVIEW", 80)
    auto_comm = get_threshold("AUTO_COMMUNICATION", 70)

    # Priority overrides
    if is_hazmat:
        return ConfidenceRoute(
            target_queue="hitl",
            hitl_queue_type="validation_failure",
            reason="Hazmat orders always require human review",
        )

    if customer_always_hitl:
        return ConfidenceRoute(
            target_queue="hitl",
            hitl_queue_type="confidence_review",
            reason="Customer profile configured for mandatory HITL review",
        )

    if is_duplicate:
        return ConfidenceRoute(
            target_queue="hitl",
            hitl_queue_type="duplicate_review",
            reason="Potential duplicate order detected",
        )

    # Confidence-based routing
    if overall_confidence >= auto_process and not has_missing_mandatory:
        return ConfidenceRoute(
            target_queue="auto-process",
            reason=f"Confidence {overall_confidence:.1f}% >= {auto_process}% threshold; all mandatory fields present",
        )

    if has_missing_mandatory:
        if overall_confidence >= auto_comm:
            return ConfidenceRoute(
                target_queue="communication",
                reason=f"Missing mandatory fields; confidence {overall_confidence:.1f}% >= auto-comm threshold {auto_comm}%",
            )
        else:
            return ConfidenceRoute(
                target_queue="hitl",
                hitl_queue_type="validation_failure",
                reason=f"Missing mandatory fields; confidence {overall_confidence:.1f}% below auto-comm threshold",
            )

    if overall_confidence >= human_review:
        return ConfidenceRoute(
            target_queue="hitl",
            hitl_queue_type="confidence_review",
            reason=f"Confidence {overall_confidence:.1f}% in review range ({human_review}%-{auto_process}%)",
        )

    return ConfidenceRoute(
        target_queue="exception",
        hitl_queue_type="exception",
        reason=f"Confidence {overall_confidence:.1f}% below {human_review}% threshold",
    )
