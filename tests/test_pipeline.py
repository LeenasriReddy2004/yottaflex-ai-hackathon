
import sqlite3
import pandas as pd
import pytest

from src.ingestion import ingest_data
from src.validation import validate_data, validate_foreign_keys
from src.loader import load_data


def customer_config(file_path):
    return {
        "source": {
            "path": str(file_path),
            "format": "csv",
            "encoding": "utf-8",
            "delimiter": ","
        },
        "schema": {
            "columns": {
                "customer_id": {"type": "integer", "nullable": False},
                "customer_name": {"type": "string", "nullable": False},
                "email": {"type": "string", "nullable": False}
            }
        },
        "keys": {"primary_key": ["customer_id"]},
        "load": {"duplicate_policy": "reject"},
        "validation": {
            "trim_strings": True,
            "allow_extra_columns": False
        }
    }


def loader_config(database_path, include_operation=False):
    columns = {
        "customer_id": {"type": "integer", "nullable": False},
        "customer_name": {"type": "string", "nullable": False},
        "email": {"type": "string", "nullable": False}
    }

    if include_operation:
        columns["operation"] = {
            "type": "string",
            "nullable": False
        }

    return {
        "target": {
            "database": str(database_path),
            "table": "customers"
        },
        "schema": {"columns": columns},
        "keys": {"primary_key": ["customer_id"]},
        "load": {"mode": "upsert"}
    }


def test_empty_csv(tmp_path):
    file_path = tmp_path / "empty.csv"
    file_path.write_text("", encoding="utf-8")

    dataframe, metadata = ingest_data(customer_config(file_path))

    assert len(dataframe) == 0
    assert "customer_id" in dataframe.columns
    assert metadata["input_count"] == 0


def test_malformed_csv(tmp_path):
    file_path = tmp_path / "malformed.csv"

    file_path.write_text(
        "customer_id,customer_name,email\n"
        "1,John,john@example.com\n"
        "2,David,david@example.com,EXTRA\n",
        encoding="utf-8"
    )

    with pytest.raises(ValueError, match="Failed to read source file"):
        ingest_data(customer_config(file_path))


def test_duplicate_primary_key():
    dataframe = pd.DataFrame({
        "customer_id": [1, 1, 2],
        "customer_name": ["John", "David", "Sam"],
        "email": [
            "john@example.com",
            "david@example.com",
            "sam@example.com"
        ]
    })

    accepted, rejected = validate_data(
        dataframe, customer_config("dummy.csv")
    )

    assert len(rejected) == 2
    assert "DUPLICATE_PRIMARY_KEY" in rejected["reject_reason"].values


def test_null_required_values():
    dataframe = pd.DataFrame({
        "customer_id": [1, 2],
        "customer_name": ["John", None],
        "email": ["john@example.com", "david@example.com"]
    })

    accepted, rejected = validate_data(
        dataframe, customer_config("dummy.csv")
    )

    assert len(rejected) == 1
    assert len(accepted) == 1


def test_invalid_foreign_key():
    orders = pd.DataFrame({
        "order_id": [101, 102],
        "customer_id": [1, 999]
    })

    config = {
        "keys": {
            "foreign_keys": [{
                "column": "customer_id",
                "references": {
                    "dataset": "customers",
                    "column": "customer_id"
                }
            }]
        }
    }

    customers = pd.DataFrame({"customer_id": [1, 2, 3]})

    accepted, rejected = validate_foreign_keys(
        orders, config, {"customers": customers}
    )

    assert len(accepted) == 1
    assert len(rejected) == 1
    assert "INVALID_FOREIGN_KEY" in rejected["reject_reason"].iloc[0]


def test_backfill_upsert_no_duplicate_records(tmp_path):
    database = tmp_path / "warehouse.db"
    config = loader_config(database)

    dataframe = pd.DataFrame({
        "customer_id": [1, 2],
        "customer_name": ["John", "David"],
        "email": ["john@example.com", "david@example.com"]
    })

    load_data(dataframe, config)
    result = load_data(dataframe, config)

    with sqlite3.connect(database) as connection:
        count = connection.execute(
            "SELECT COUNT(*) FROM customers"
        ).fetchone()[0]

    assert count == 2
    assert result["target_count"] == 2
    assert result["updated_count"] == 2


def test_delete_event(tmp_path):
    database = tmp_path / "warehouse.db"
    config = loader_config(database, include_operation=True)

    initial_data = pd.DataFrame({
        "customer_id": [1],
        "customer_name": ["John"],
        "email": ["john@example.com"],
        "operation": ["insert"]
    })

    load_data(initial_data, config)

    delete_data = pd.DataFrame({
        "customer_id": [1],
        "customer_name": ["John"],
        "email": ["john@example.com"],
        "operation": ["delete"]
    })

    result = load_data(delete_data, config)

    with sqlite3.connect(database) as connection:
        count = connection.execute(
            "SELECT COUNT(*) FROM customers"
        ).fetchone()[0]

    assert count == 0
    assert result["deleted_count"] == 1
