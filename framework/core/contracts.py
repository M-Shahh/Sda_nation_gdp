"""
core/contracts.py -- The Contracts (Owned by the Core)
=======================================================
Defines all structural interfaces (Protocols) for Phase 3.

Three protocols:
  - DataSink:          Output modules must implement write().
  - PipelineService:   Input modules call execute() to send data in.
  - TelemetryObserver: Dashboard subscribes to telemetry updates.

The Core owns ALL contracts. Nothing outside Core defines these rules.
"""

from typing import Protocol, List, Any, runtime_checkable


@runtime_checkable
class DataSink(Protocol):
    """
    Outbound abstraction — Core calls this to deliver results.
    Any output module must implement write().
    """
    def write(self, records: List[dict]) -> None:
        ...


@runtime_checkable
class PipelineService(Protocol):
    """
    Inbound abstraction — Input modules call execute() to send raw data.
    """
    def execute(self, raw_data: List[Any]) -> None:
        ...


@runtime_checkable
class TelemetryObserver(Protocol):
    """
    Observer contract — Dashboard subscribes to PipelineTelemetry.
    on_telemetry_update() is called whenever queue levels are polled.
    """
    def on_telemetry_update(self, telemetry_data: dict) -> None:
        ...
