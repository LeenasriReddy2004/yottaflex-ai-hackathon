
import yaml
from pathlib import Path


SUPPORTED_FORMATS = {"csv", "json"}
SUPPORTED_LOAD_MODES = {"append", "replace", "upsert"}
SUPPORTED_TYPES = {"integer", "float", "string", "datetime"}

REQUIRED_SECTIONS = {
    "dataset",
    "source",
    "schema",
    "keys",
    "target",
    "load",
    "validation"
}


def load_config(config_path):
    """Read and validate a YAML pipeline configuration."""

    path = Path(config_path)

    if not path.is_file():
        raise FileNotFoundError(
            f"Configuration file not found: {path}"
        )

    with path.open("r", encoding="utf-8-sig") as file:
        config = yaml.safe_load(file)

    if not isinstance(config, dict):
        raise ValueError("Configuration must be a YAML mapping")

    missing = REQUIRED_SECTIONS - set(config.keys())

    if missing:
        raise ValueError(
            f"Missing configuration sections: {sorted(missing)}"
        )

    if not config["dataset"].get("name"):
        raise ValueError("Dataset name is required")

    source = config["source"]

    if source.get("format") not in SUPPORTED_FORMATS:
        raise ValueError("Unsupported source format")

    if not source.get("path"):
        raise ValueError("Source path is required")

    schema = config["schema"].get("columns")

    if not isinstance(schema, dict) or not schema:
        raise ValueError("Schema columns must be defined")

    for column, definition in schema.items():
        if not isinstance(definition, dict):
            raise ValueError(f"Invalid definition for {column}")

        if definition.get("type") not in SUPPORTED_TYPES:
            raise ValueError(
                f"Unsupported type for column: {column}"
            )

        if not isinstance(definition.get("nullable"), bool):
            raise ValueError(
                f"Nullable must be true or false: {column}"
            )

    primary_keys = config["keys"].get("primary_key")

    if not isinstance(primary_keys, list) or not primary_keys:
        raise ValueError("At least one primary key is required")

    for key in primary_keys:
        if key not in schema:
            raise ValueError(
                f"Primary key missing from schema: {key}"
            )

        if schema[key]["nullable"]:
            raise ValueError(
                f"Primary key cannot be nullable: {key}"
            )

    foreign_keys = config["keys"].get("foreign_keys", [])

    if not isinstance(foreign_keys, list):
        raise ValueError("Foreign keys must be a list")

    for foreign_key in foreign_keys:
        if not isinstance(foreign_key, dict):
            raise ValueError("Invalid foreign key definition")

        column = foreign_key.get("column")
        reference = foreign_key.get("references", {})

        if column not in schema:
            raise ValueError(
                f"Foreign key column missing from schema: {column}"
            )

        if not reference.get("dataset") or not reference.get("column"):
            raise ValueError("Foreign key reference is incomplete")

    target = config["target"]

    if not target.get("database") or not target.get("table"):
        raise ValueError("Target database and table are required")

    load_mode = config["load"].get("mode")

    if load_mode not in SUPPORTED_LOAD_MODES:
        raise ValueError(f"Unsupported load mode: {load_mode}")

    duplicate_policy = config["load"].get("duplicate_policy")

    if duplicate_policy not in {"reject", "first", "last"}:
        raise ValueError("Unsupported duplicate policy")

    return config
