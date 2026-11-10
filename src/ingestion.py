
import json
from pathlib import Path

import pandas as pd


def ingest_data(config):
    """
    Read source data using the supplied YAML configuration.

    Returns:
        dataframe: Loaded source records.
        metadata: Source file information.
    """

    source = config["source"]

    source_path = Path(source["path"])

    if not source_path.is_absolute():
        source_path = Path.cwd() / source_path

    source_format = source["format"].lower()

    metadata = {
        "source_file": str(source_path),
        "source_format": source_format
    }

    if not source_path.is_file():
        raise FileNotFoundError(
            f"Source file not found: {source_path}"
        )

    try:
        if source_format == "csv":
            try:
                dataframe = pd.read_csv(
                    source_path,
                    encoding=source.get("encoding", "utf-8"),
                    sep=source.get("delimiter", ",")
                )

            except pd.errors.EmptyDataError:
                expected_columns = list(
                    config.get("schema", {}).get("columns", {}).keys()
                )

                dataframe = pd.DataFrame(
                    columns=expected_columns
                )

        elif source_format == "json":
            with source_path.open(
                "r",
                encoding=source.get("encoding", "utf-8")
            ) as file:
                records = json.load(file)

            if isinstance(records, dict):
                records = [records]

            if not isinstance(records, list):
                raise ValueError(
                    "JSON input must contain an object or list of objects"
                )

            if any(not isinstance(row, dict) for row in records):
                raise ValueError(
                    "Every JSON record must be an object"
                )

            dataframe = pd.DataFrame(records)

        else:
            raise ValueError(
                f"Unsupported source format: {source_format}"
            )

    except (
        pd.errors.ParserError,
        json.JSONDecodeError,
        UnicodeDecodeError
    ) as error:
        raise ValueError(
            f"Failed to read source file: {error}"
        ) from error

    metadata["input_count"] = len(dataframe)
    metadata["columns"] = list(dataframe.columns)

    return dataframe, metadata
