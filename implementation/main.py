"""
main.py -- The Orchestrator (Bootstrap Layer)
=============================================
Wires all Phase 3 components together and starts the pipeline.

Dependency Injection order:
  1. Load config.json
  2. Create three bounded multiprocessing Queues
  3. Create PipelineTelemetry (Subject) with queue references
  4. Create RealtimeDashboard (Observer) — subscribes to telemetry
  5. Start CSVProducer process  (Input)
  6. Start N CoreWorker processes (Scatter)
  7. Start Aggregator process  (Gather)
  8. Run Dashboard in main process (matplotlib needs main thread)

Process layout:
  Process 1        : CSVProducer   → raw_queue
  Process 2..N+1   : CoreWorker    → intermediate_queue  (N parallel)
  Process N+2      : Aggregator    → processed_queue
  Main Process     : Dashboard     ← processed_queue + telemetry
"""

import json
import os
import sys
import multiprocessing

# Core components
from core.engine   import core_worker_process, aggregator_process
from core.telemetry import PipelineTelemetry

# Plugins
from plugins.inputs  import CSVProducer
from plugins.outputs import RealtimeDashboard


def load_config(path: str) -> dict:
    """Load and validate config.json."""
    if not os.path.exists(path):
        print(f"ERROR: config.json not found at: {path}")
        sys.exit(1)

    with open(path, 'r') as f:
        config = json.load(f)

    required = ['dataset_path', 'pipeline_dynamics', 'schema_mapping',
                'processing', 'visualizations']
    for key in required:
        if key not in config:
            print(f"ERROR: Missing required config key: '{key}'")
            sys.exit(1)

    return config


def bootstrap():
    """
    Main wiring function — creates processes and starts the pipeline.
    """
    # ── Step 1: Load configuration ────────────────────────────────────
    base_dir    = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(base_dir, 'config.json')
    config      = load_config(config_path)

    # Resolve dataset path relative to project root
    config['dataset_path'] = os.path.join(
        base_dir, config['dataset_path']
    )

    dynamics     = config['pipeline_dynamics']
    max_size     = dynamics['stream_queue_max_size']
    n_workers    = dynamics['core_parallelism']
    secret_key   = config['processing']['stateless_tasks']['secret_key']
    iterations   = config['processing']['stateless_tasks']['iterations']
    window_size  = config['processing']['stateful_tasks']['running_average_window_size']

    # ── Step 2: Create three bounded queues ───────────────────────────
    raw_queue          = multiprocessing.Queue(maxsize=max_size)
    intermediate_queue = multiprocessing.Queue(maxsize=max_size)
    processed_queue    = multiprocessing.Queue(maxsize=max_size)

    print(f"[Main] Pipeline starting — {n_workers} core workers, queue size {max_size}")

    # ── Step 3: Create PipelineTelemetry (Subject) ────────────────────
    telemetry = PipelineTelemetry(
        raw_queue, intermediate_queue, processed_queue, max_size
    )

    # ── Step 4: Create Dashboard (Observer) — subscribe to telemetry ──
    dashboard = RealtimeDashboard(config)
    telemetry.subscribe(dashboard)

    # ── Step 5: Start Input Producer process ──────────────────────────
    producer = CSVProducer(config)
    input_process = multiprocessing.Process(
        target=producer.run,
        args=(raw_queue,),
        name='CSVProducer',
        daemon=True
    )

    # ── Step 6: Start N Core Worker processes (Scatter) ───────────────
    worker_processes = [
        multiprocessing.Process(
            target=core_worker_process,
            args=(raw_queue, intermediate_queue, secret_key, iterations, i),
            name=f'CoreWorker-{i}',
            daemon=True
        )
        for i in range(n_workers)
    ]

    # ── Step 7: Start Aggregator process (Gather) ─────────────────────
    agg_process = multiprocessing.Process(
        target=aggregator_process,
        args=(intermediate_queue, processed_queue, window_size, n_workers),
        name='Aggregator',
        daemon=True
    )

    # ── Start all background processes ────────────────────────────────
    input_process.start()
    print(f"[Main] CSVProducer started (PID {input_process.pid})")

    for wp in worker_processes:
        wp.start()
    print(f"[Main] {n_workers} CoreWorker processes started")

    agg_process.start()
    print(f"[Main] Aggregator started (PID {agg_process.pid})")

    # ── Step 8: Run dashboard in main process ─────────────────────────
    # matplotlib must run in the main thread
    print("[Main] Dashboard starting...")
    dashboard.run(processed_queue, telemetry)

    # ── Cleanup after dashboard window is closed ──────────────────────
    print("[Main] Dashboard closed. Terminating workers...")
    input_process.terminate()
    for wp in worker_processes:
        wp.terminate()
    agg_process.terminate()
    print("[Main] Pipeline shut down.")


if __name__ == '__main__':
    # Required on Windows for multiprocessing
    multiprocessing.freeze_support()
    bootstrap()
