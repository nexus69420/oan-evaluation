from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseDataTransform(ABC):
    """Base contract for row-level data transformation plugins."""

    @abstractmethod
    def transform(self, row_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform one input JSON row into a normalized JSON object.

        Args:
            row_json: Original input row.

        Returns:
            Transformed row JSON.
        """
        raise NotImplementedError
