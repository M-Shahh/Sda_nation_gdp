"""
plugins/outputs.py -- Real-Time Dashboard (Observer)
======================================================
Single Responsibility: Subscribe to PipelineTelemetry and render
a live matplotlib dashboard showing pipeline health and data charts.

Observer Pattern role:
  - Implements TelemetryObserver protocol (core/contracts.py).
  - Subscribes to PipelineTelemetry (the Subject).
  - on_telemetry_update() is called every animation tick.

Dashboard layout (2 rows):
  Row 1: Three telemetry bars (Raw / Intermediate / Processed queues)
  Row 2: Two real-time line charts (Live Values + Running Average)

Colour coding for queue fill level:
  Green  (0–49%)  → Flowing smoothly
  Yellow (50–79%) → Queue filling up
  Red    (80%+)   → Heavy backpressure
"""

from collections import deque
from multiprocessing import Queue
from typing import List

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.patches as mpatches

try:
    matplotlib.use("TkAgg")
except Exception:
    matplotlib.use("Agg")


# ──────────────────────────────────────────────────────────
#  Backpressure colour thresholds
# ──────────────────────────────────────────────────────────

def _queue_colour(fill_ratio: float) -> str:
    """Return a colour based on how full a queue is."""
    if fill_ratio >= 0.80:
        return '#E53E3E'   # Red   — heavy backpressure
    if fill_ratio >= 0.50:
        return '#F6AD55'   # Yellow — queue filling
    return '#48BB78'       # Green  — flowing smoothly


def _queue_label(fill_ratio: float) -> str:
    if fill_ratio >= 0.80:
        return 'BACKPRESSURE'
    if fill_ratio >= 0.50:
        return 'FILLING'
    return 'OK'


# ──────────────────────────────────────────────────────────
#  RealtimeDashboard — The Observer
# ──────────────────────────────────────────────────────────

class RealtimeDashboard:
    """
    Real-time dashboard that satisfies TelemetryObserver protocol.

    Subscribes to PipelineTelemetry and updates:
      - Three colour-coded queue health bars (telemetry row)
      - Live sensor values line chart
      - Running average line chart
    """

    # How many data points to show on the rolling x-axis
    MAX_DISPLAY_POINTS = 60

    def __init__(self, config: dict):
        self.config       = config
        self.viz_config   = config['visualizations']
        self.chart_cfgs   = self.viz_config['data_charts']
        self.tel_config   = self.viz_config['telemetry']

        # Rolling data buffers for the two line charts
        self._x_vals   = deque(maxlen=self.MAX_DISPLAY_POINTS)
        self._y_vals   = deque(maxlen=self.MAX_DISPLAY_POINTS)
        self._y_avg    = deque(maxlen=self.MAX_DISPLAY_POINTS)

        # Latest telemetry snapshot (updated by on_telemetry_update)
        self._telemetry = {
            'raw_queue_size': 0,
            'intermediate_queue_size': 0,
            'processed_queue_size': 0,
            'max_size': 50,
            'total_received': 0,
            'total_verified': 0,
            'total_dropped': 0,
        }

        # Counters
        self._packets_shown = 0
        self._pipeline_done = False

        self._fig  = None
        self._axes = None

    # ── Observer contract ────────────────────────────────────

    def on_telemetry_update(self, telemetry_data: dict) -> None:
        """
        Called by PipelineTelemetry every animation frame.
        Simply stores the latest snapshot — drawing happens in _animate().
        """
        self._telemetry = telemetry_data

    # ── Main run loop ────────────────────────────────────────

    def run(self, processed_queue: Queue, telemetry) -> None:
        """
        Start the dashboard. Blocks until the window is closed.

        Parameters:
            processed_queue: Queue of enriched packets from Aggregator.
            telemetry:       PipelineTelemetry subject to poll each frame.
        """
        self._processed_queue = processed_queue
        self._telemetry_subject = telemetry

        self._build_layout()

        # FuncAnimation drives both data ingestion and chart updates
        self._anim = animation.FuncAnimation(
            self._fig,
            self._animate,
            interval=100,      # update every 100ms
            cache_frame_data=False
        )

        plt.tight_layout(rect=[0, 0, 1, 0.95])
        plt.show()

    # ── Layout builder ───────────────────────────────────────

    def _build_layout(self) -> None:
        """Create the figure with telemetry bars on top, charts below."""
        self._fig = plt.figure(figsize=(16, 9))
        self._fig.patch.set_facecolor('#1A202C')

        self._fig.suptitle(
            'Real-Time Pipeline Dashboard',
            fontsize=14, fontweight='bold', color='white', y=0.98
        )

        # Count how many telemetry bars to show
        tel = self.tel_config
        num_bars = sum([
            tel.get('show_raw_stream', True),
            tel.get('show_intermediate_stream', True),
            tel.get('show_processed_stream', True),
        ])

        # Row 1: telemetry bars side by side
        # Row 2: two data charts side by side
        gs = self._fig.add_gridspec(
            2, max(num_bars, 2),
            left=0.06, right=0.97,
            top=0.92, bottom=0.08,
            hspace=0.50, wspace=0.35
        )

        # Build telemetry bar axes
        self._tel_axes = []
        bar_labels = []
        if tel.get('show_raw_stream', True):
            bar_labels.append(('raw_queue_size', 'Raw Stream\n(Input -> Core)'))
        if tel.get('show_intermediate_stream', True):
            bar_labels.append(('intermediate_queue_size', 'Intermediate Stream\n(Core -> Aggregator)'))
        if tel.get('show_processed_stream', True):
            bar_labels.append(('processed_queue_size', 'Processed Stream\n(Aggregator -> Output)'))

        self._bar_keys = [b[0] for b in bar_labels]
        self._bar_names = [b[1] for b in bar_labels]

        for i in range(len(bar_labels)):
            ax = self._fig.add_subplot(gs[0, i])
            self._tel_axes.append(ax)
            self._style_dark(ax)

        # Build line chart axes (always 2 charts spanning the bottom row)
        num_cols = max(num_bars, 2)
        mid = num_cols // 2
        self._ax_values = self._fig.add_subplot(gs[1, :mid])
        self._ax_avg    = self._fig.add_subplot(gs[1, mid:])

        self._style_dark(self._ax_values)
        self._style_dark(self._ax_avg)

        # Configure line chart labels from config
        chart_map = {c['type']: c for c in self.chart_cfgs}

        cfg_val = chart_map.get('real_time_line_graph_values', {})
        self._ax_values.set_title(
            cfg_val.get('title', 'Live Values'),
            color='white', fontsize=10, fontweight='bold', pad=8)
        self._ax_values.set_xlabel(cfg_val.get('x_axis', 'time'), color='#A0AEC0', fontsize=8)
        self._ax_values.set_ylabel(cfg_val.get('y_axis', 'value'), color='#A0AEC0', fontsize=8)

        cfg_avg = chart_map.get('real_time_line_graph_average', {})
        self._ax_avg.set_title(
            cfg_avg.get('title', 'Running Average'),
            color='white', fontsize=10, fontweight='bold', pad=8)
        self._ax_avg.set_xlabel(cfg_avg.get('x_axis', 'time'), color='#A0AEC0', fontsize=8)
        self._ax_avg.set_ylabel(cfg_avg.get('y_axis', 'avg'), color='#A0AEC0', fontsize=8)

        # Line plot objects (updated each frame)
        self._line_val, = self._ax_values.plot([], [], color='#63B3ED',
                                                linewidth=1.8, marker='o',
                                                markersize=3, label='Verified Value')
        self._line_avg, = self._ax_avg.plot([], [], color='#F6AD55',
                                             linewidth=2.2, label='Running Avg')

        self._ax_values.legend(fontsize=8, facecolor='#2D3748',
                               labelcolor='white', edgecolor='#4A5568')
        self._ax_avg.legend(fontsize=8, facecolor='#2D3748',
                            labelcolor='white', edgecolor='#4A5568')

    # ── Animation frame ──────────────────────────────────────

    def _animate(self, frame: int) -> None:
        """
        Called every 100ms by FuncAnimation.
        1. Poll telemetry subject → updates self._telemetry via observer.
        2. Drain up to 10 packets from processed_queue.
        3. Redraw telemetry bars and line charts.
        """
        # Step 1: Poll telemetry (subject notifies this observer)
        self._telemetry_subject.poll_and_notify()

        # Step 2: Drain packets from processed queue (non-blocking)
        packets_this_frame = 0
        while packets_this_frame < 10:
            try:
                packet = self._processed_queue.get_nowait()
            except Exception:
                break

            if packet is None:
                # Sentinel — pipeline is done
                self._pipeline_done = True
                break

            self._x_vals.append(packet.get('time_period', self._packets_shown))
            self._y_vals.append(packet.get('metric_value', 0))
            self._y_avg.append(packet.get('computed_metric', 0))
            self._packets_shown += 1
            packets_this_frame += 1

        # Step 3: Redraw everything
        self._draw_telemetry_bars()
        self._draw_line_charts()

        if self._pipeline_done and self._packets_shown > 0:
            self._fig.suptitle(
                f'Pipeline Complete — {self._packets_shown} packets processed',
                fontsize=13, fontweight='bold', color='#48BB78', y=0.98
            )

    # ── Telemetry bar drawing ────────────────────────────────

    def _draw_telemetry_bars(self) -> None:
        """Redraw all three queue health bars with colour-coded fill."""
        max_size = max(self._telemetry.get('max_size', 50), 1)

        for i, (key, name) in enumerate(zip(self._bar_keys, self._bar_names)):
            ax = self._tel_axes[i]
            ax.clear()
            self._style_dark(ax)

            current = self._telemetry.get(key, 0)
            ratio   = min(current / max_size, 1.0)
            colour  = _queue_colour(ratio)
            status  = _queue_label(ratio)

            # Background bar (empty part)
            ax.barh(0, max_size, height=0.5, color='#2D3748',
                    edgecolor='#4A5568', linewidth=1)
            # Filled part
            ax.barh(0, current, height=0.5, color=colour,
                    edgecolor='none', alpha=0.9)

            # Labels
            ax.text(max_size / 2, 0, f'{current}/{max_size}',
                    ha='center', va='center', fontsize=10,
                    fontweight='bold', color='white')
            ax.text(max_size / 2, 0.45, f'{status}',
                    ha='center', va='bottom', fontsize=8,
                    color=colour, fontweight='bold')

            ax.set_xlim(0, max_size)
            ax.set_ylim(-0.5, 0.8)
            ax.set_title(name, color='#A0AEC0', fontsize=8,
                         fontweight='bold', pad=6)
            ax.set_yticks([])
            ax.set_xticks([0, max_size // 2, max_size])
            ax.tick_params(colors='#718096', labelsize=7)

    # ── Line chart drawing ───────────────────────────────────

    def _draw_line_charts(self) -> None:
        """Update both line charts with latest data buffers."""
        if not self._x_vals:
            return

        x = list(self._x_vals)
        y = list(self._y_vals)
        a = list(self._y_avg)

        # Live values chart
        self._line_val.set_data(x, y)
        self._ax_values.relim()
        self._ax_values.autoscale_view()
        self._ax_values.tick_params(colors='#A0AEC0', labelsize=7)

        # Running average chart
        self._line_avg.set_data(x, a)
        self._ax_avg.relim()
        self._ax_avg.autoscale_view()
        self._ax_avg.tick_params(colors='#A0AEC0', labelsize=7)

    # ── Style helper ─────────────────────────────────────────

    def _style_dark(self, ax) -> None:
        """Apply dark theme to an axes object."""
        ax.set_facecolor('#2D3748')
        ax.tick_params(colors='#A0AEC0', labelsize=7)
        for spine in ax.spines.values():
            spine.set_edgecolor('#4A5568')
