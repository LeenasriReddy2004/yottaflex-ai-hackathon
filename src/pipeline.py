
import time
import uuid
import pandas as pd

from src.config_loader import load_config
from src.ingestion import ingest_data
from src.validation import validate_data, validate_foreign_keys
from src.transformation import transform_data
from src.loader import load_data
from src.quarantine import save_rejects
from src.audit import start_audit, finish_audit


def run_pipeline(config_path, reference_data=None, max_retries=2):
    start_clock = time.perf_counter()
    last_error = None

    for attempt in range(max_retries + 1):
        run_id = str(uuid.uuid4())
        config = load_config(config_path)

        dataset_name = config["dataset"]["name"]
        source_file = config["source"]["path"]
        database_path = config["target"]["database"]

        audit = start_audit(dataset_name, source_file, run_id)

        input_count = 0
        accepted_count = 0
        rejected_count = 0
        target_count = 0

        try:
            dataframe, metadata = ingest_data(config)
            input_count = len(dataframe)

            valid_df, rejected_df = validate_data(
                dataframe, config, metadata
            )

            if config["keys"].get("foreign_keys"):
                if reference_data is None:
                    raise ValueError(
                        "Reference data is required for foreign key validation"
                    )

                valid_df, fk_rejected = validate_foreign_keys(
                    valid_df, config, reference_data
                )

                rejected_df = pd.concat(
                    [rejected_df, fk_rejected],
                    ignore_index=True
                )

            quarantine_result = save_rejects(
                rejected_df, config, run_id, metadata
            )

            transformed_df = transform_data(valid_df, config)
            accepted_count = len(transformed_df)
            rejected_count = len(rejected_df)

            load_result = load_data(transformed_df, config)
            target_count = load_result["target_count"]

            audit_result = finish_audit(
                audit,
                database_path,
                input_count=input_count,
                accepted_count=accepted_count,
                rejected_count=rejected_count,
                target_count=target_count,
                status="SUCCESS"
            )

            return {
                "run_id": run_id,
                "dataset": dataset_name,
                "status": "SUCCESS",
                "attempt": attempt + 1,
                "input_count": input_count,
                "accepted_count": accepted_count,
                "rejected_count": rejected_count,
                "target_count": target_count,
                "load_result": load_result,
                "quarantine_result": quarantine_result,
                "audit_result": audit_result,
                "duration_seconds": round(
                    time.perf_counter() - start_clock, 4
                )
            }

        except Exception as error:
            last_error = error

            try:
                finish_audit(
                    audit,
                    database_path,
                    input_count=input_count,
                    accepted_count=accepted_count,
                    rejected_count=rejected_count,
                    target_count=target_count,
                    status="FAILED",
                    error_message=str(error)
                )
            except Exception as audit_error:
                print("Audit recording failed:", audit_error)

            if attempt == max_retries:
                raise

            time.sleep(1)

    raise last_error
