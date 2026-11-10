import sqlite3
import pandas as pd

from src.performance import benchmark_pipeline


DB_PATH = "output/warehouse.db"


def load_customer_reference():
    connection = sqlite3.connect(DB_PATH)

    try:
        return pd.read_sql_query(
            "SELECT * FROM customers",
            connection
        )
    finally:
        connection.close()


def main():
    print("=" * 60)
    print("YOTTAFLEX AI - PERFORMANCE REPORT")
    print("=" * 60)

    print("\nCUSTOMERS PERFORMANCE")

    customer_result = benchmark_pipeline(
        "config/customers.yaml"
    )

    for key, value in customer_result.items():
        print(f"{key}: {value}")

    customers = load_customer_reference()

    print("\nCustomer reference records:", len(customers))

    print("\nORDERS PERFORMANCE")

    order_result = benchmark_pipeline(
        "config/orders.yaml",
        reference_data={"customers": customers}
    )

    for key, value in order_result.items():
        print(f"{key}: {value}")

    print("\n" + "=" * 60)
    print("PERFORMANCE REPORT COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    main()