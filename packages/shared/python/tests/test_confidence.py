"""Tests for confidence scoring and routing logic."""

from unittest.mock import patch
import os

import pytest

from order_shared.utils.confidence import compute_weighted_confidence, route_by_confidence


class TestComputeWeightedConfidence:
    """Test weighted confidence computation."""

    def test_all_perfect_scores(self) -> None:
        scores = {"customer_name": 100.0, "pickup_date": 100.0, "commodity": 100.0}
        result = compute_weighted_confidence(scores, ["customer_name", "pickup_date", "commodity"])
        assert result == 100.0

    def test_mixed_scores(self) -> None:
        scores = {"customer_name": 90.0, "pickup_date": 80.0, "commodity": 70.0}
        result = compute_weighted_confidence(scores, ["customer_name", "pickup_date", "commodity"])
        assert result == 80.0

    def test_missing_field_scores_count_as_zero(self) -> None:
        scores = {"customer_name": 100.0}
        result = compute_weighted_confidence(scores, ["customer_name", "pickup_date"])
        # customer_name=100, pickup_date=0 (not in scores) -> avg = 50
        assert result == 50.0

    def test_empty_mandatory_fields(self) -> None:
        scores = {"customer_name": 95.0}
        result = compute_weighted_confidence(scores, [])
        assert result == 0.0

    def test_custom_weights(self) -> None:
        scores = {"customer_name": 100.0, "commodity": 50.0}
        weights = {"customer_name": 2.0, "commodity": 1.0}
        result = compute_weighted_confidence(
            scores, ["customer_name", "commodity"], weights=weights
        )
        # (100*2 + 50*1) / (2+1) = 250/3 = 83.33
        assert abs(result - 83.33) < 0.01


class TestRouteByConfidence:
    """Test confidence-based routing decisions."""

    @patch.dict(os.environ, {
        "THRESHOLD_AUTO_PROCESS": "95",
        "THRESHOLD_HUMAN_REVIEW": "80",
        "THRESHOLD_AUTO_COMMUNICATION": "70",
    })
    def test_auto_process_high_confidence(self) -> None:
        route = route_by_confidence(97.5, has_missing_mandatory=False)
        assert route.target_queue == "auto-process"

    @patch.dict(os.environ, {
        "THRESHOLD_AUTO_PROCESS": "95",
        "THRESHOLD_HUMAN_REVIEW": "80",
        "THRESHOLD_AUTO_COMMUNICATION": "70",
    })
    def test_hitl_medium_confidence(self) -> None:
        route = route_by_confidence(85.0, has_missing_mandatory=False)
        assert route.target_queue == "hitl"
        assert route.hitl_queue_type == "confidence_review"

    @patch.dict(os.environ, {
        "THRESHOLD_AUTO_PROCESS": "95",
        "THRESHOLD_HUMAN_REVIEW": "80",
        "THRESHOLD_AUTO_COMMUNICATION": "70",
    })
    def test_exception_low_confidence(self) -> None:
        route = route_by_confidence(60.0, has_missing_mandatory=False)
        assert route.target_queue == "exception"

    @patch.dict(os.environ, {
        "THRESHOLD_AUTO_PROCESS": "95",
        "THRESHOLD_HUMAN_REVIEW": "80",
        "THRESHOLD_AUTO_COMMUNICATION": "70",
    })
    def test_communication_missing_fields_above_threshold(self) -> None:
        route = route_by_confidence(85.0, has_missing_mandatory=True)
        assert route.target_queue == "communication"

    @patch.dict(os.environ, {
        "THRESHOLD_AUTO_PROCESS": "95",
        "THRESHOLD_HUMAN_REVIEW": "80",
        "THRESHOLD_AUTO_COMMUNICATION": "70",
    })
    def test_hitl_missing_fields_below_comm_threshold(self) -> None:
        route = route_by_confidence(55.0, has_missing_mandatory=True)
        assert route.target_queue == "hitl"
        assert route.hitl_queue_type == "validation_failure"

    @patch.dict(os.environ, {
        "THRESHOLD_AUTO_PROCESS": "95",
        "THRESHOLD_HUMAN_REVIEW": "80",
        "THRESHOLD_AUTO_COMMUNICATION": "70",
    })
    def test_hazmat_always_hitl(self) -> None:
        route = route_by_confidence(99.0, has_missing_mandatory=False, is_hazmat=True)
        assert route.target_queue == "hitl"
        assert route.hitl_queue_type == "validation_failure"

    @patch.dict(os.environ, {
        "THRESHOLD_AUTO_PROCESS": "95",
        "THRESHOLD_HUMAN_REVIEW": "80",
        "THRESHOLD_AUTO_COMMUNICATION": "70",
    })
    def test_duplicate_always_hitl(self) -> None:
        route = route_by_confidence(97.0, has_missing_mandatory=False, is_duplicate=True)
        assert route.target_queue == "hitl"
        assert route.hitl_queue_type == "duplicate_review"

    @patch.dict(os.environ, {
        "THRESHOLD_AUTO_PROCESS": "95",
        "THRESHOLD_HUMAN_REVIEW": "80",
        "THRESHOLD_AUTO_COMMUNICATION": "70",
    })
    def test_customer_always_hitl(self) -> None:
        route = route_by_confidence(98.0, has_missing_mandatory=False, customer_always_hitl=True)
        assert route.target_queue == "hitl"
        assert route.hitl_queue_type == "confidence_review"

    @patch.dict(os.environ, {
        "THRESHOLD_AUTO_PROCESS": "95",
        "THRESHOLD_HUMAN_REVIEW": "80",
        "THRESHOLD_AUTO_COMMUNICATION": "70",
    })
    def test_boundary_exactly_at_auto_process(self) -> None:
        route = route_by_confidence(95.0, has_missing_mandatory=False)
        assert route.target_queue == "auto-process"

    @patch.dict(os.environ, {
        "THRESHOLD_AUTO_PROCESS": "95",
        "THRESHOLD_HUMAN_REVIEW": "80",
        "THRESHOLD_AUTO_COMMUNICATION": "70",
    })
    def test_boundary_just_below_auto_process(self) -> None:
        route = route_by_confidence(94.9, has_missing_mandatory=False)
        assert route.target_queue == "hitl"
        assert route.hitl_queue_type == "confidence_review"
