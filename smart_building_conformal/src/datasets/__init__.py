"""Dataset adapter registry.

Every adapter lowers one source into the common representation defined in
:mod:`src.datasets.base`, so the study runner selects an adapter by id and never
branches on the dataset again.
"""

from __future__ import annotations

from .base import (
    ChronologicalPartitioner,
    DatasetAdapter,
    GroupPartitioner,
    PARTITIONS,
    Partitioner,
    PreparedDataset,
    PreparedSeries,
    Provenance,
    config_hash,
    file_checksum,
)

_REGISTRY: dict[str, type[DatasetAdapter]] = {}


def register(adapter_cls: type[DatasetAdapter]) -> type[DatasetAdapter]:
    _REGISTRY[adapter_cls.dataset_id] = adapter_cls
    return adapter_cls


def get_adapter(dataset_id: str) -> DatasetAdapter:
    """Instantiate the adapter registered under ``dataset_id``."""
    # Imported lazily so that a missing optional dependency in one adapter does
    # not prevent the others from being used.
    from . import bdg2, pleia, rico  # noqa: F401

    key = dataset_id.lower()
    if key not in _REGISTRY:
        raise KeyError(
            f"unknown dataset {dataset_id!r}; registered: {sorted(_REGISTRY)}"
        )
    return _REGISTRY[key]()


def available() -> list[str]:
    from . import bdg2, pleia, rico  # noqa: F401

    return sorted(_REGISTRY)


__all__ = [
    "ChronologicalPartitioner", "DatasetAdapter", "GroupPartitioner",
    "PARTITIONS", "Partitioner", "PreparedDataset", "PreparedSeries",
    "Provenance", "available", "config_hash", "file_checksum", "get_adapter",
    "register",
]
