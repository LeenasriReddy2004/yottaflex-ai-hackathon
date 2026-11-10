
import random
from pathlib import Path

import pandas as pd


def generate_synthetic_data(
    output_dir="data/generated",
    record_count=100000,
    seed=42
):
    """Generate reproducible synthetic customer and order data."""

    random.seed(seed)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    cities = [
        "Hyderabad",
        "Bangalore",
        "Chennai",
        "Pune",
        "Mumbai"
    ]

    statuses = [
        "completed",
        "pending",
        "cancelled"
    ]

    customers = []

    for i in range(record_count):

        customers.append({
            "customer_id": i + 1001,
            "customer_name": f"Customer_{i + 1}",
            "email": f"customer{i + 1}@example.com",
            "city": random.choice(cities),
            "created_at": "2026-01-01T10:00:00"
        })

    customers_df = pd.DataFrame(customers)

    orders = []

    for i in range(record_count):

        customer_id = random.randint(
            1001,
            record_count + 1000
        )

        orders.append({
            "order_id": i + 5001,
            "customer_id": customer_id,
            "order_date": "2026-02-01T10:00:00",
            "amount": round(random.uniform(10, 10000), 2),
            "status": random.choice(statuses)
        })

    orders_df = pd.DataFrame(orders)

    # Deliberately introduce data-quality issues.
    if record_count >= 10:

        # Duplicate customer key
        customers_df.loc[
            1, "customer_id"
        ] = customers_df.loc[0, "customer_id"]

        # Missing customer email
        customers_df.loc[2, "email"] = None

        # Invalid order foreign key
        orders_df.loc[
            3, "customer_id"
        ] = record_count + 999999

        # Duplicate order key
        orders_df.loc[
            5, "order_id"
        ] = orders_df.loc[4, "order_id"]

        # Missing order amount
        orders_df.loc[6, "amount"] = None

        # Boundary amount
        orders_df.loc[7, "amount"] = 0.00

    customers_path = output_dir / "customers_100k.csv"
    orders_path = output_dir / "orders_100k.csv"

    customers_df.to_csv(
        customers_path,
        index=False
    )

    orders_df.to_csv(
        orders_path,
        index=False
    )

    return {
        "customers_generated": len(customers_df),
        "orders_generated": len(orders_df),
        "seed": seed,
        "customers_file": str(customers_path),
        "orders_file": str(orders_path)
    }
