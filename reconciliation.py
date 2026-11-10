import sqlite3
import yaml


DB_PATH = "output/warehouse.db"


def get_config(path):
    with open(path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def reconcile_dataset(config_path):
    config = get_config(config_path)

    dataset_name = config["dataset"]["name"]
    table_name = config["target"]["table"]

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute(f'SELECT COUNT(*) FROM "{table_name}"')
    warehouse_count = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT accepted_count, target_count, status
        FROM pipeline_audit
        WHERE dataset_name = ?
        ORDER BY start_time DESC
        LIMIT 1
        """,
        (dataset_name,)
    )

    audit = cursor.fetchone()
    connection.close()

    if audit is None:
        print(f"{dataset_name}: No audit record found")
        return

    accepted_count, target_count, status = audit

    print(f"\nDataset: {dataset_name}")
    print(f"Latest pipeline status: {status}")
    print(f"Latest accepted records: {accepted_count}")
    print(f"Audit target count: {target_count}")
    print(f"Current warehouse count: {warehouse_count}")

    if target_count == warehouse_count:
        print("RECONCILIATION: PASSED")
    else:
        print("RECONCILIATION: COUNT MISMATCH")


if __name__ == "__main__":
    reconcile_dataset("config/customers.yaml")
    reconcile_dataset("config/orders.yaml")