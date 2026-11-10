import sqlite3
import pandas as pd

from src.performance import benchmark_pipeline

db_path = "output/warehouse.db"

# Read customer reference data
conn = sqlite3.connect(db_path)

customers = pd.read_sql_query(
    "SELECT customer_id FROM customers",
    conn
)

# Count orders before rerun
before = conn.execute(
    "SELECT COUNT(*) FROM orders"
).fetchone()[0]

conn.close()

print("Orders before rerun:", before)

# Run the same 100K orders pipeline again
result = benchmark_pipeline(
    "config/orders.yaml",
    {"customers": customers}
)

print("Pipeline result:", result)

# Count orders after rerun
conn = sqlite3.connect(db_path)

after = conn.execute(
    "SELECT COUNT(*) FROM orders"
).fetchone()[0]

conn.close()

print("Orders after rerun:", after)

print("IDEMPOTENCY:", "PASSED" if before == after else "FAILED")