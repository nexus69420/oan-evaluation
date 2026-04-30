from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Optional


@dataclass
class MetricResult:
    """
    Standard metric output contract.

    Every metric must return this shape.
    """

    metric_name: str
    score: Optional[float]
    reason: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class BaseMetric(ABC):
    """Base contract for metric plugins."""

    metric_name: str = "base_metric"

    @abstractmethod
    async def evaluate(
        self,
        *,
        row_json: Dict[str, Any],
        transformed_json: Dict[str, Any],
        variables: Dict[str, Any],
        config: Dict[str, Any],
    ) -> MetricResult:
        raise NotImplementedError
