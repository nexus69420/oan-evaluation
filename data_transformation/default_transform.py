from __future__ import annotations

from typing import Any, Dict

from .base import BaseDataTransform


class DefaultDataTransform(BaseDataTransform):
    """
    Default no-op transform that preserves current row shape.

    Teams can create custom classes in this folder and wire them in config.
    """

    def transform(self, row_json: Dict[str, Any]) -> Dict[str, Any]:
        return dict(row_json)
