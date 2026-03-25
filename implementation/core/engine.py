"""
core/engine.py -- The Functional Core
======================================
Contains ALL business logic for Phase 3. Completely domain-agnostic —
it operates on generic 'metric_value', 'time_period' etc., never on
'GDP' or 'Sensor_Alpha' directly.

Two patterns implemented here:

1. SCATTER-GATHER (Stateless Parallelism):
   - CoreWorker processes run in parallel (scatter).
   - Each independently verifies the cryptographic signature.
   - Verified packets are pushed to the intermediate queue (gather point).

2. FUNCTIONAL CORE, IMPERATIVE SHELL (Stateful Aggregation):
   - Pure function: sliding_window_average(window) — no side effects.
   - Imperative Shell: Aggregator class holds the mutable deque (state)
     and calls the pure function to compute the average.

The engine never imports plugins or knows about CSV files / dashboards.
"""

import hashlib
import time
from collections import deque
from multiprocessing import Queue


# ──────────────────────────────────────────────────────────────
#  FUNCTIONAL CORE — Pure, Stateless Functions
#  These functions have NO side effects. Same input → same output.
# ──────────────────────────────────────────────────────────────

def verify_signature(packet: dict, secret_key: str, iterations: int) -> bool:
    """
    Pure function — verifies a packet's cryptographic signature.

    Uses PBKDF2-HMAC-SHA256:
      password = secret_key
      salt     = raw metric_value rounded to 2 decimal places

    Returns True if the packet is authentic, False if tampered.
    """
    # Format value to 2 decimal places — matches how signature was generated
    raw_value_str = f"{packet['metric_value']:.2f}"

    computed_hash = hashlib.pbkdf2_hmac(
        hash_name  = 'sha256',
        password   = secret_key.encode('utf-8'),
        salt       = raw_value_str.encode('utf-8'),
        iterations = iterations
    ).hex()

    return computed_hash == packet['security_hash']


def sliding_window_average(window: list) -> float:
    """
    Pure function — computes the average of a sliding window of values.

    Parameters:
        window (list): A list of recent metric_value floats.

    Returns:
        float: The mean of all values in the window.
    """
    return sum(window) / len(window) if window else 0.0


# ──────────────────────────────────────────────────────────────
#  SCATTER — CoreWorker (Stateless, runs N copies in parallel)
# ──────────────────────────────────────────────────────────────

def core_worker_process(raw_queue: Queue,
                        intermediate_queue: Queue,
                        secret_key: str,
                        iterations: int,
                        worker_id: int):
    """
    Runs as a separate process (one of N parallel workers).

    Pulls packets from raw_queue, verifies the signature (CPU-heavy),
    and pushes verified packets to intermediate_queue.
    Drops any packet whose signature does not match.

    Uses a sentinel value (None) to know when input is exhausted.
    """
    while True:
        packet = raw_queue.get()        # blocks until a packet is available

        # Sentinel — signals this worker to stop
        if packet is None:
            # Pass the sentinel along so Aggregator knows one worker finished
            intermediate_queue.put(None)
            break

        # --- FUNCTIONAL CORE called here ---
        is_authentic = verify_signature(packet, secret_key, iterations)

        if is_authentic:
            packet['verified'] = True
            intermediate_queue.put(packet)
        # Silently drop unverified packets


# ──────────────────────────────────────────────────────────────
#  GATHER — Aggregator (Stateful, single process)
#  IMPERATIVE SHELL wrapping the FUNCTIONAL CORE
# ──────────────────────────────────────────────────────────────

def aggregator_process(intermediate_queue: Queue,
                       processed_queue: Queue,
                       window_size: int,
                       num_workers: int):
    """
    Runs as a single process — the Gather point.

    IMPERATIVE SHELL: maintains the mutable sliding window (deque).
    FUNCTIONAL CORE:  calls sliding_window_average() to compute the mean.

    Pulls verified packets from intermediate_queue, computes a running
    average, and pushes enriched packets to processed_queue.

    Waits for all N worker sentinels before stopping.
    """
    # Imperative Shell owns the mutable state
    window = deque(maxlen=window_size)
    sentinels_received = 0

    while True:
        packet = intermediate_queue.get()

        # Count sentinels — one per core worker
        if packet is None:
            sentinels_received += 1
            if sentinels_received >= num_workers:
                # All workers done — signal dashboard to stop
                processed_queue.put(None)
                break
            continue  # wait for remaining workers

        # Update the sliding window (Imperative Shell — mutable state)
        window.append(packet['metric_value'])

        # --- FUNCTIONAL CORE called here ---
        avg = sliding_window_average(list(window))

        # Enrich packet with computed result
        packet['computed_metric'] = round(avg, 4)
        processed_queue.put(packet)
