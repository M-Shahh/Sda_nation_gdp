"""
core/telemetry.py -- Pipeline Telemetry (Observer Pattern Subject)
===================================================================
PipelineTelemetry is the SUBJECT in the Observer pattern.

It monitors all three queue sizes and notifies subscribed
OBSERVERS (e.g. Dashboard) when levels change.

Observer Pattern roles:
  Subject  -> PipelineTelemetry   (this file)
  Observer -> RealtimeDashboard   (plugins/outputs.py)
  Contract -> TelemetryObserver   (core/contracts.py)

TODO: Implement all methods below.
"""

from multiprocessing import Queue
from typing import List


class PipelineTelemetry:
    """
    Subject — holds queue references and a list of observers.
    Main.py creates this, passes queue references, and passes it
    to the Dashboard for subscription.
    """

    def __init__(self,
                 raw_queue: Queue,
                 intermediate_queue: Queue,
                 processed_queue: Queue,
                 max_size: int):
        """
        TODO: Store queue references, max_size, and initialise
        empty observers list and counters.
        """
        pass

    def subscribe(self, observer) -> None:
        """
        Register an observer to receive telemetry updates.
        TODO: Implement.
        """
        pass

    def unsubscribe(self, observer) -> None:
        """
        Remove a previously subscribed observer.
        TODO: Implement.
        """
        pass

    def poll_and_notify(self) -> None:
        """
        Poll all queue sizes and notify all subscribed observers.
        Called periodically by the dashboard's animation loop.
        TODO: Implement.
        """
        pass

    def _safe_qsize(self, queue: Queue) -> int:
        """
        Safely get queue size — qsize() may raise on some platforms.
        Returns 0 if unavailable.
        TODO: Implement.
        """
        pass
