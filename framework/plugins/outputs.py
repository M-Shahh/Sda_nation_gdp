"""
plugins/outputs.py -- Real-Time Dashboard (Observer) Skeleton
==============================================================
Single Responsibility: Subscribe to PipelineTelemetry and render
a live matplotlib dashboard showing pipeline health and data charts.

Observer Pattern role:
  - Implements TelemetryObserver protocol (core/contracts.py).
  - Subscribes to PipelineTelemetry (the Subject).
  - on_telemetry_update() is called every animation tick.

Dashboard layout:
  Row 1: Three colour-coded queue health bars (telemetry)
  Row 2: Two real-time line charts (Live Values + Running Average)

Colour coding:
  Green  (0-49%)  -> Flowing smoothly
  Yellow (50-79%) -> Queue filling
  Red    (80%+)   -> Heavy backpressure

TODO: Implement all methods below.
"""

from collections import deque
from multiprocessing import Queue
from typing import List

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.animation as animation

try:
    matplotlib.use("TkAgg")
except Exception:
    matplotlib.use("Agg")


def _queue_colour(fill_ratio: float) -> str:
    """
    Return a colour based on how full a queue is.
    Green < 0.50, Yellow 0.50-0.79, Red >= 0.80
    TODO: Implement.
    """
    pass


def _queue_label(fill_ratio: float) -> str:
    """
    Return a status label based on fill ratio.
    TODO: Implement.
    """
    pass


class RealtimeDashboard:
    """
    Real-time dashboard — satisfies TelemetryObserver protocol.
    Subscribes to PipelineTelemetry and updates colour-coded
    queue bars and two live line charts.
    """

    MAX_DISPLAY_POINTS = 60

    def __init__(self, config: dict):
        """
        TODO: Store config, initialise rolling data buffers (deque),
        telemetry snapshot dict, and counters.
        """
        pass

    def on_telemetry_update(self, telemetry_data: dict) -> None:
        """
        Observer contract method — called by PipelineTelemetry
        every animation frame. Store the latest telemetry snapshot.
        TODO: Implement.
        """
        pass

    def run(self, processed_queue: Queue, telemetry) -> None:
        """
        Start the dashboard. Blocks until window is closed.
        Builds layout, starts FuncAnimation, calls plt.show().
        TODO: Implement.
        """
        pass

    def _build_layout(self) -> None:
        """
        Create the figure with telemetry bars on top row
        and two line charts on bottom row.
        TODO: Implement.
        """
        pass

    def _animate(self, frame: int) -> None:
        """
        Called every 100ms by FuncAnimation.
        1. Poll telemetry subject.
        2. Drain packets from processed_queue.
        3. Redraw telemetry bars and line charts.
        TODO: Implement.
        """
        pass

    def _draw_telemetry_bars(self) -> None:
        """
        Redraw all three queue health bars with colour-coded fill.
        TODO: Implement.
        """
        pass

    def _draw_line_charts(self) -> None:
        """
        Update both line charts with latest data buffers.
        TODO: Implement.
        """
        pass

    def _style_dark(self, ax) -> None:
        """
        Apply dark theme to an axes object.
        TODO: Implement.
        """
        pass
