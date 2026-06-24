"""Order Intelligence Platform — Shared models, adapters, and utilities."""

__version__ = "0.1.0"

from order_shared.models import (
    OrderSchema,
    Address,
    TimeWindow,
    EmailRecord,
    AgentMessage,
    ExtractionResult,
    ValidationResultModel,
)
from order_shared.adapters import create_adapters, get_adapters
from order_shared.utils import (
    normalize_date,
    normalize_weight,
    normalize_phone,
    expand_address_abbreviations,
    compute_weighted_confidence,
    route_by_confidence,
    mask_pii,
    get_logger,
)

__all__ = [
    "OrderSchema",
    "Address",
    "TimeWindow",
    "EmailRecord",
    "AgentMessage",
    "ExtractionResult",
    "ValidationResultModel",
    "create_adapters",
    "get_adapters",
    "normalize_date",
    "normalize_weight",
    "normalize_phone",
    "expand_address_abbreviations",
    "compute_weighted_confidence",
    "route_by_confidence",
    "mask_pii",
    "get_logger",
]
