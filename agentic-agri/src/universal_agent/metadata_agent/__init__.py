"""Metadata agent sub-graph package."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .graph import MetadataAgentGraph


def __getattr__(name: str):
    if name == "MetadataAgentGraph":
        from .graph import MetadataAgentGraph

        return MetadataAgentGraph
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
