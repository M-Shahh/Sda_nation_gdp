"""
plugins/inputs.py -- Input Source (The Producer)
=================================================
Single Responsibility: Read a CSV file row by row, map column names
to internal generic names using the schema from config.json, cast
to the correct types, and push packets into the raw_queue.

Completely domain-agnostic — it never knows what the data means.
It only knows the schema mapping from config.json.

The input_delay_seconds controls the speed of ingestion.
If the Core workers are slow, raw_queue fills up (backpressure).
"""

import csv
import os
import time
from multiprocessing import Queue
from typing import List


# Type casting map — converts string values to Python primitives
TYPE_CASTERS = {
    'string':  str,
    'integer': int,
    'float':   float,
}


def _apply_schema(row: dict, schema_columns: list) -> dict:
    """
    Pure function — maps raw CSV column names to internal generic names
    and casts values to the correct types.

    Parameters:
        row (dict):            Raw CSV row with original column names.
        schema_columns (list): Schema mapping from config.json.

    Returns:
        dict: Packet with internal_mapping keys and correctly typed values.
    """
    packet = {}
    for col in schema_columns:
        source   = col['source_name']
        internal = col['internal_mapping']
        dtype    = col['data_type']
        caster   = TYPE_CASTERS.get(dtype, str)

        raw_val = row.get(source, '')
        try:
            packet[internal] = caster(raw_val.strip())
        except (ValueError, TypeError):
            packet[internal] = None   # invalid value — engine will handle

    return packet


class CSVProducer:
    """
    Reads a CSV file and pushes generic data packets into raw_queue.

    Runs as a separate process started by main.py.
    Schema mapping is driven entirely by config.json.
    """

    def __init__(self, config: dict):
        self.dataset_path   = config['dataset_path']
        self.schema_columns = config['schema_mapping']['columns']
        self.delay          = config['pipeline_dynamics']['input_delay_seconds']
        self.num_workers    = config['pipeline_dynamics']['core_parallelism']

    def run(self, raw_queue: Queue) -> None:
        """
        Main loop — reads each CSV row, maps it, and puts it in raw_queue.
        Sends one sentinel (None) per core worker at the end.

        Parameters:
            raw_queue (Queue): Bounded queue shared with Core workers.
        """
        if not os.path.exists(self.dataset_path):
            print(f"[Input] ERROR: File not found: {self.dataset_path}")
            # Still send sentinels so workers don't block forever
            for _ in range(self.num_workers):
                raw_queue.put(None)
            return

        with open(self.dataset_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Map column names and cast types (pure function)
                packet = _apply_schema(row, self.schema_columns)

                # Skip rows with any None value after casting
                if any(v is None for v in packet.values()):
                    continue

                # put() blocks automatically when queue is full — natural backpressure
                raw_queue.put(packet)
                time.sleep(self.delay)

        # Send one sentinel per worker to signal end of data
        for _ in range(self.num_workers):
            raw_queue.put(None)

        print("[Input] All rows sent. Sentinels dispatched.")
