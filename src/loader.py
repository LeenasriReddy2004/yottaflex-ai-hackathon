
import sqlite3
from pathlib import Path
import pandas as pd

SQL_TYPES = {
    "integer": "INTEGER",
    "float": "REAL",
    "string": "TEXT",
    "datetime": "TEXT"
}


def quote_identifier(name):
    return '"' + str(name).replace('"', '""') + '"'


def load_data(dataframe, config):
    target = config["target"]
    database_path = Path(target["database"])

    if not database_path.is_absolute():
        database_path = Path.cwd() / database_path

    database_path.parent.mkdir(parents=True, exist_ok=True)

    table_name = target["table"]
    table = quote_identifier(table_name)

    schema = config["schema"]["columns"]
    primary_keys = config["keys"]["primary_key"]
    mode = config["load"]["mode"]

    if mode not in {"append", "replace", "upsert"}:
        raise ValueError(f"Unsupported load mode: {mode}")

    if not set(dataframe.columns).issubset(schema):
        raise ValueError("Unexpected columns in DataFrame")

    if not set(primary_keys).issubset(dataframe.columns):
        raise ValueError("Primary key missing from DataFrame")

    if dataframe.duplicated(subset=primary_keys).any():
        raise ValueError("Duplicate primary keys in input")

    definitions = []

    for column in dataframe.columns:
        data_type = schema[column]["type"]

        if data_type not in SQL_TYPES:
            raise ValueError(f"Unsupported data type: {data_type}")

        definition = f"{quote_identifier(column)} {SQL_TYPES[data_type]}"

        if column in primary_keys:
            definition += " NOT NULL"

        definitions.append(definition)

    pk_sql = ", ".join(quote_identifier(key) for key in primary_keys)

    create_sql = (
        f"CREATE TABLE IF NOT EXISTS {table} ("
        + ", ".join(definitions)
        + f", PRIMARY KEY ({pk_sql}))"
    )

    columns = list(dataframe.columns)
    column_sql = ", ".join(quote_identifier(c) for c in columns)
    placeholders = ", ".join(["?"] * len(columns))

    insert_sql = (
        f"INSERT INTO {table} ({column_sql}) VALUES ({placeholders})"
    )

    if mode == "upsert":
        updates = [
            c for c in columns if c not in primary_keys
        ]

        if updates:
            assignments = ", ".join(
                f"{quote_identifier(c)} = excluded.{quote_identifier(c)}"
                for c in updates
            )
            insert_sql += (
                f" ON CONFLICT ({pk_sql}) DO UPDATE SET {assignments}"
            )
        else:
            insert_sql += f" ON CONFLICT ({pk_sql}) DO NOTHING"

    records = []

    for row in dataframe.itertuples(index=False, name=None):
        converted = []

        for value in row:
            if pd.isna(value):
                converted.append(None)
            elif hasattr(value, "isoformat"):
                converted.append(value.isoformat())
            else:
                converted.append(value)

        records.append(tuple(converted))

    inserted_count = 0
    updated_count = 0
    deleted_count = 0

    with sqlite3.connect(database_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute(create_sql)

        existing_columns = {
            row[1]
            for row in connection.execute(
                f"PRAGMA table_info({table})"
            ).fetchall()
        }

        if existing_columns != set(columns):
            raise ValueError("Target schema does not match input schema")

        if mode == "replace":
            connection.execute(f"DELETE FROM {table}")
            inserted_count = len(records)

        elif mode == "append":
            inserted_count = len(records)

        elif mode == "upsert":
            key_select = ", ".join(
                quote_identifier(key) for key in primary_keys
            )

            existing_keys = set(
                connection.execute(
                    f"SELECT {key_select} FROM {table}"
                ).fetchall()
            )

            for record in records:
                key = tuple(
                    record[columns.index(column)]
                    for column in primary_keys
                )

                if key in existing_keys:
                    updated_count += 1
                else:
                    inserted_count += 1

        connection.executemany(insert_sql, records)

        delete_column = "operation"

        if delete_column in dataframe.columns:
            delete_records = dataframe[
                dataframe[delete_column].astype(str).str.lower() == "delete"
            ]

            for _, record in delete_records.iterrows():
                conditions = " AND ".join(
                    f"{quote_identifier(key)} = ?"
                    for key in primary_keys
                )

                values = tuple(record[key] for key in primary_keys)

                cursor = connection.execute(
                    f"DELETE FROM {table} WHERE {conditions}",
                    values
                )

                deleted_count += cursor.rowcount

        target_count = connection.execute(
            f"SELECT COUNT(*) FROM {table}"
        ).fetchone()[0]

    return {
        "table": table_name,
        "load_mode": mode,
        "processed_count": len(records),
        "inserted_count": inserted_count,
        "updated_count": updated_count,
        "deleted_count": deleted_count,
        "target_count": target_count,
        "database": str(database_path)
    }
