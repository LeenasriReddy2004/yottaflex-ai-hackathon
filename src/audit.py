
import sqlite3
import uuid

from datetime import datetime, timezone
from pathlib import Path


def start_audit(dataset_name, source_file, run_id=None):
    """Create an audit entry when a pipeline starts."""

    run_id = run_id or str(uuid.uuid4())

    start_time = datetime.now(
        timezone.utc
    ).isoformat()

    return {
        "run_id": run_id,
        "dataset_name": dataset_name,
        "source_file": str(source_file),
        "start_time": start_time
    }


def finish_audit(
    audit,
    database_path,
    input_count=0,
    accepted_count=0,
    rejected_count=0,
    target_count=0,
    status="SUCCESS",
    error_message=None
):
    """Save completed pipeline execution metrics."""

    end_time = datetime.now(
        timezone.utc
    ).isoformat()

    database_path = Path(database_path)

    if not database_path.is_absolute():
        database_path = Path.cwd() / database_path

    database_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    create_sql = """
        CREATE TABLE IF NOT EXISTS pipeline_audit (
            run_id TEXT PRIMARY KEY,
            dataset_name TEXT NOT NULL,
            source_file TEXT,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            input_count INTEGER,
            accepted_count INTEGER,
            rejected_count INTEGER,
            target_count INTEGER,
            status TEXT NOT NULL,
            error_message TEXT
        )
    """

    insert_sql = """
        INSERT INTO pipeline_audit (
            run_id,
            dataset_name,
            source_file,
            start_time,
            end_time,
            input_count,
            accepted_count,
            rejected_count,
            target_count,
            status,
            error_message
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    values = (
        audit["run_id"],
        audit["dataset_name"],
        audit["source_file"],
        audit["start_time"],
        end_time,
        input_count,
        accepted_count,
        rejected_count,
        target_count,
        status,
        error_message
    )

    with sqlite3.connect(database_path) as connection:
        connection.execute(create_sql)
        connection.execute(insert_sql, values)

    return {
        "run_id": audit["run_id"],
        "dataset_name": audit["dataset_name"],
        "status": status,
        "input_count": input_count,
        "accepted_count": accepted_count,
        "rejected_count": rejected_count,
        "target_count": target_count,
        "error_message": error_message
    }
