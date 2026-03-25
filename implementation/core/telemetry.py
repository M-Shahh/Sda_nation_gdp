"""
core/telemetry.py -- Pipeline Telemetry (Observer Pattern Subject)
===================================================================
PipelineTelemetry acts as the SUBJECT in the Observer pattern.

It independently monitors all three queue sizes and notifies any
subscribed OBSERVERS (e.g., the Dashboard) when levels change.

This avoids DIP violations — the Core never imports the Dashboard.
The Dashboard subscribes to telemetry and updates itself.

Observer Pattern roles:
  Subject  → PipelineTelemetry   (this file)
  Observer → RealtimeDashboard   (plugins/outputs.py)
  Contract → TelemetryObserver   (core/contracts.py)
"""

from multiprocessing import Queue
from typing import List


class PipelineTelemetry:
    """
    Subject — holds references to all three queues and a list of observers.

    The main orchestrator (main.py) creates this object, passes it the
    queue references, and passes it to the Dashboard for subscription.
    The Dashboard never touches the queues directly.
    """

    def __init__(self,
                 raw_queue: Queue,
                 intermediate_queue: Queue,
                 processed_queue: Queue,
                 max_size: int):
        """
        Parameters:
            raw_queue:          Input → Core workers queue.
            intermediate_queue: Core workers → Aggregator queue.
            processed_queue:    Aggregator → Dashboard queue.
            max_size:           Maximum capacity of each queue.
        """
        self._raw_queue          = raw_queue
        self._intermediate_queue = intermediate_queue
        self._processed_queue    = processed_queue
        self._max_size           = max_size
        self._observers: List    = []

        # Running counters (updated each poll)
        self.total_received  = 0
        self.total_verified  = 0
        self.total_dropped   = 0

    def subscribe(self, observer) -> None:
        """Register an observer to receive telemetry updates."""
        self._observers.append(observer)

    def unsubscribe(self, observer) -> None:
        """Remove a previously subscribed observer."""
        self._observers = [o for o in self._observers if o is not observer]

    def poll_and_notify(self) -> None:
        """
        Poll all queue sizes and notify all subscribed observers.
        Called periodically by the dashboard's animation loop.
        """
        telemetry_data = {
            'raw_queue_size':          self._safe_qsize(self._raw_queue),
            'intermediate_queue_size': self._safe_qsize(self._intermediate_queue),
            'processed_queue_size':    self._safe_qsize(self._processed_queue),
            'max_size':                self._max_size,
            'total_received':          self.total_received,
            'total_verified':          self.total_verified,
            'total_dropped':           self.total_dropped,
        }

        # Notify all observers
        for observer in self._observers:
            observer.on_telemetry_update(telemetry_data)

    def _safe_qsize(self, queue: Queue) -> int:
        """
        Safely get queue size — qsize() may raise on some platforms.
        Returns 0 if unavailable.
        """
        try:
            return queue.qsize()
        except (NotImplementedError, OSError):
            return 0
