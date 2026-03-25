"""
plugins/inputs.py -- Input Source (The Producer) Skeleton
==========================================================
Single Responsibility: Read a CSV file row by row, map column names
to internal generic names using the schema from config.json, cast
to correct types, and push packets into the raw_queue.

Completely domain-agnostic — operates only on schema mappings.

TODO: Implement all functions and methods below.
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
    and casts values to the correct types based on schema_columns.

    Parameters:
        row (dict):            Raw CSV row with original column names.
        schema_columns (list): Schema mapping list from config.json.

    Returns:
        dict: Packet with internal_mapping keys and correctly typed values.

    TODO: Implement schema mapping and type casting.
    """
    pass


class CSVProducer:
    """
    Reads a CSV file and pushes generic data packets into raw_queue.
    Runs as a separate process started by main.py.
    Schema mapping is driven entirely by config.json.
    """

    def __init__(self, config: dict):
        """
        TODO: Extract dataset_path, schema_columns, delay,
        and num_workers from config.
        """
        pass

    def run(self, raw_queue: Queue) -> None:
        """
        Main loop — reads each CSV row, applies schema mapping,
        and puts packets into raw_queue.
        Sends one sentinel (None) per core worker at the end.

        TODO: Implement CSV reading and queue production.
        """
        pass
