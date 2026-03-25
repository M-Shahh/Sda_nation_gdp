================================================================
  Phase 3: Generic Concurrent Real-Time Pipeline
  README — How to Run
================================================================

MAIN FILE
---------
  python main.py

PROJECT STRUCTURE
-----------------
  phase3_project/
  ├── main.py              <- ENTRY POINT — run this file
  ├── config.json          <- All runtime configuration
  ├── readme.txt           <- This file
  ├── class_diagram.puml   <- PlantUML class diagram source
  ├── sequence_diagram.puml <- PlantUML sequence diagram source
  │
  ├── core/
  │   ├── contracts.py     <- Protocols: DataSink, PipelineService,
  │   │                       TelemetryObserver
  │   ├── engine.py        <- Functional Core: verify_signature(),
  │   │                       sliding_window_average(), CoreWorker,
  │   │                       Aggregator
  │   └── telemetry.py     <- PipelineTelemetry (Observer Subject)
  │
  ├── plugins/
  │   ├── inputs.py        <- CSVProducer (generic schema mapping)
  │   └── outputs.py       <- RealtimeDashboard (Observer)
  │
  └── data/
      └── sample_sensor_data.csv   <- Place your dataset here

ADDING AN UNSEEN DATASET
------------------------
  1. Copy your CSV file into the data/ folder.
  2. Open config.json and update:
       "dataset_path": "data/YOUR_FILE.csv"
  3. Update "schema_mapping" → "columns" to match your column headers.
     Example for a climate dataset:
       { "source_name": "Station_ID",   "internal_mapping": "entity_name",  "data_type": "string"  }
       { "source_name": "Unix_Time",    "internal_mapping": "time_period",  "data_type": "integer" }
       { "source_name": "Temperature",  "internal_mapping": "metric_value", "data_type": "float"   }
       { "source_name": "Hash",         "internal_mapping": "security_hash","data_type": "string"  }
  4. Update "secret_key" in processing.stateless_tasks if needed.
  5. Run: python main.py

NO CODE CHANGES NEEDED — only config.json changes.

INSTALL DEPENDENCIES
--------------------
  pip install matplotlib numpy

CONFIGURATION REFERENCE (config.json)
--------------------------------------
  dataset_path                     : path to CSV file
  pipeline_dynamics.input_delay_seconds  : seconds between each row read
  pipeline_dynamics.core_parallelism     : number of parallel worker processes
  pipeline_dynamics.stream_queue_max_size: max items in each queue (backpressure)
  processing.stateless_tasks.secret_key  : PBKDF2 secret key for verification
  processing.stateless_tasks.iterations  : PBKDF2 iterations (default 100000)
  processing.stateful_tasks.running_average_window_size : sliding window size

WHAT YOU WILL SEE
-----------------
  - Three colour-coded queue health bars (Green/Yellow/Red)
  - Live Sensor Values chart (verified packets only)
  - Running Average chart (sliding window)
  - Pipeline Complete message when all data is processed

================================================================
