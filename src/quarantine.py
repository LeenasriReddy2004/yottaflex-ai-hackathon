
import json
import sqlite3
import uuid
import pandas as pd

from datetime import datetime, timezone
from pathlib import Path


def save_rejects(
    rejected_df,
    config,
    run_id=None,
    metadata=None
):
    """
    Persist rejected records for investigation.

    Each rejected record retains its dataset,
    source file, source row and rejection reason.
    """

    if rejected_df.empty:
        return {
            "dataset": config["dataset"]["name"],
            "rejected_count": 0
        }

    metadata = metadata or {}

    dataset_name = config["dataset"]["name"]

    database_path = Path(config["target"]["database"])

    if not database_path.is_absolute():
        database_path = Path.cwd() / database_path

    database_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    run_id = run_id or str(uuid.uuid4())

    rejected_at = datetime.now(
        timezone.utc
    ).isoformat()

    source_file = metadata.get(
        "source_file", "unknown"
    )

    records = []

    for index, row in rejected_df.iterrows():

        record = row.to_dict()

        record_source = record.pop(
            "source_file", source_file
        )

        if pd.isna(record_source):
            record_source = source_file

        source_row = record.pop("source_row", None)

        if source_row is None or pd.isna(source_row):
            source_row = index + 2

        reject_reason = record.pop(
            "reject_reason", "UNKNOWN"
        )

        if pd.isna(reject_reason):
            reject_reason = "UNKNOWN"

        records.append((
            run_id,
            dataset_name,
            str(record_source),
            int(source_row),
            str(reject_reason),
            json.dumps(record, default=str),
            rejected_at
        ))


      

    create_sql = """
        CREATE TABLE IF NOT EXISTS quarantine_records (
            quarantine_id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL,
            dataset_name TEXT NOT NULL,
            source_file TEXT NOT NULL,
            source_row INTEGER,
            reject_reason TEXT NOT NULL,
            record_json TEXT NOT NULL,
            rejected_at TEXT NOT NULL
        )
    """

    insert_sql = """
        INSERT INTO quarantine_records (
            run_id,
            dataset_name,
            source_file,
            source_row,
            reject_reason,
            record_json,
            rejected_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """

    with sqlite3.connect(database_path) as connection:

        connection.execute(create_sql)

        connection.executemany(
            insert_sql,
            records
        )

    return {
        "dataset": dataset_name,
        "run_id": run_id,
        "rejected_count": len(records),
        "quarantine_table": "quarantine_records"
    }
