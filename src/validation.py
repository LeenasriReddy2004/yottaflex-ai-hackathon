
import pandas as pd


def validate_data(dataframe, config, metadata=None):
    """
    Validate source records against YAML schema metadata.

    Returns:
        valid_df: Records that pass validation.
        rejected_df: Invalid records with rejection reasons.
    """

    metadata = metadata or {}
    schema = config["schema"]["columns"]
    source_columns = set(dataframe.columns)
    expected_columns = set(schema.keys())

    missing_columns = expected_columns - source_columns
    extra_columns = source_columns - expected_columns

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {sorted(missing_columns)}"
        )

    if extra_columns and not config["validation"].get(
        "allow_extra_columns", False
    ):
        raise ValueError(
            f"Unexpected columns detected: {sorted(extra_columns)}"
        )

    df = dataframe[list(schema.keys())].copy()
    original_indices = df.index.tolist()

    errors = [[] for _ in range(len(df))]

    # Apply deterministic string trimming.
    if config["validation"].get("trim_strings", True):
        for column, definition in schema.items():
            if definition["type"] == "string":
                df[column] = df[column].map(
                    lambda value: value.strip()
                    if isinstance(value, str) else value
                )

    # Validate and convert data types.
    for column, definition in schema.items():

        expected_type = definition["type"]
        original_values = df[column].copy()

        if expected_type == "integer":
            converted = pd.to_numeric(
                original_values, errors="coerce"
            )

            invalid = (
                original_values.notna()
                & (
                    converted.isna()
                    | (converted % 1 != 0)
                )
            )

            for position in range(len(df)):
                if invalid.iloc[position]:
                    errors[position].append(
                        f"INVALID_INTEGER:{column}"
                    )

            df[column] = converted

        elif expected_type == "float":
            converted = pd.to_numeric(
                original_values, errors="coerce"
            )

            invalid = original_values.notna() & converted.isna()

            for position in range(len(df)):
                if invalid.iloc[position]:
                    errors[position].append(
                        f"INVALID_FLOAT:{column}"
                    )

            df[column] = converted

        elif expected_type == "datetime":
            converted = pd.to_datetime(
                original_values,
                errors="coerce",
                format="mixed"
            )

            invalid = original_values.notna() & converted.isna()

            for position in range(len(df)):
                if invalid.iloc[position]:
                    errors[position].append(
                        f"INVALID_DATETIME:{column}"
                    )

            df[column] = converted

        elif expected_type == "string":
            invalid = original_values.notna() & ~original_values.map(
                lambda value: isinstance(value, str)
            )

            for position in range(len(df)):
                if invalid.iloc[position]:
                    errors[position].append(
                        f"INVALID_STRING:{column}"
                    )

            df[column] = original_values

    # Validate nullability.
    for column, definition in schema.items():
        if not definition["nullable"]:
            null_positions = df[column].isna().tolist()

            for position, is_null in enumerate(null_positions):
                if is_null:
                    errors[position].append(
                        f"NULL_NOT_ALLOWED:{column}"
                    )

    # Validate primary keys.
    primary_keys = config["keys"]["primary_key"]

    duplicate_mask = df.duplicated(
        subset=primary_keys,
        keep=False
    )

    duplicate_policy = config["load"].get(
        "duplicate_policy", "reject"
    )

    if duplicate_policy == "reject":
        for position, is_duplicate in enumerate(
            duplicate_mask.tolist()
        ):
            if is_duplicate:
                errors[position].append("DUPLICATE_PRIMARY_KEY")

    elif duplicate_policy in {"first", "last"}:
        duplicate_mask = df.duplicated(
            subset=primary_keys,
            keep=duplicate_policy
        )

        for position, is_duplicate in enumerate(
            duplicate_mask.tolist()
        ):
            if is_duplicate:
                errors[position].append("DUPLICATE_PRIMARY_KEY")

    # Separate accepted and rejected records.
    rejected_positions = [
        position for position, reasons in enumerate(errors)
        if reasons
    ]

    valid_positions = [
        position for position, reasons in enumerate(errors)
        if not reasons
    ]

    valid_df = df.iloc[valid_positions].copy()

    rejected_df = dataframe.iloc[rejected_positions].copy()

    rejected_df["source_row"] = [
        original_indices[position] + 2
        for position in rejected_positions
    ]

    rejected_df["source_file"] = metadata.get(
        "source_file", "unknown"
    )

    rejected_df["reject_reason"] = [
        ";".join(errors[position])
        for position in rejected_positions
    ]

    return valid_df.reset_index(drop=True), rejected_df.reset_index(
        drop=True
    )

def validate_foreign_keys(dataframe, config, reference_data):
    """
    Validate foreign key references against parent datasets.

    reference_data example:
    {
        "customers": customers_dataframe
    }
    """

    df = dataframe.copy()
    errors = [[] for _ in range(len(df))]

    foreign_keys = config["keys"].get("foreign_keys", [])

    for foreign_key in foreign_keys:

        column = foreign_key["column"]
        reference = foreign_key["references"]

        parent_dataset = reference["dataset"]
        parent_column = reference["column"]

        if parent_dataset not in reference_data:
            raise ValueError(
                f"Reference dataset not supplied: {parent_dataset}"
            )

        parent_df = reference_data[parent_dataset]

        if parent_column not in parent_df.columns:
            raise ValueError(
                f"Reference column missing: {parent_column}"
            )

        valid_values = set(
            parent_df[parent_column].dropna().tolist()
        )

        for position, value in enumerate(df[column].tolist()):

            if pd.isna(value):
                continue

            if value not in valid_values:
                errors[position].append(
                    f"INVALID_FOREIGN_KEY:{column}:{value}"
                )

    rejected_positions = [
        i for i, reasons in enumerate(errors) if reasons
    ]

    valid_positions = [
        i for i, reasons in enumerate(errors) if not reasons
    ]

    valid_df = df.iloc[valid_positions].copy()
    rejected_df = df.iloc[rejected_positions].copy()

    rejected_df["reject_reason"] = [
        ";".join(errors[i]) for i in rejected_positions
    ]

    return (
        valid_df.reset_index(drop=True),
        rejected_df.reset_index(drop=True)
    )
