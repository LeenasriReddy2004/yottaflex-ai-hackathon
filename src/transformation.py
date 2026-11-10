
def transform_data(dataframe, config):
    """
    Apply deterministic transformations declared in YAML.
    """

    df = dataframe.copy()

    transformations = config.get("transformations", {})

    for column, operation in transformations.items():

        if column not in df.columns:
            raise ValueError(
                f"Transformation column not found: {column}"
            )

        if operation == "lowercase":
            df[column] = df[column].map(
                lambda value: value.lower()
                if isinstance(value, str) else value
            )

        elif operation == "uppercase":
            df[column] = df[column].map(
                lambda value: value.upper()
                if isinstance(value, str) else value
            )

        elif operation == "title":
            df[column] = df[column].map(
                lambda value: value.title()
                if isinstance(value, str) else value
            )

        elif operation == "round_2":
            df[column] = df[column].round(2)

        else:
            raise ValueError(
                f"Unsupported transformation: {operation}"
            )

    return df
