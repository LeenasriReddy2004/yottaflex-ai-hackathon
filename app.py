
import sqlite3
import time
from pathlib import Path

import pandas as pd
import streamlit as st

from src.pipeline import run_pipeline

st.set_page_config(
    page_title="YottaFlex AI",
    page_icon="⚡",
    layout="wide"
)

DB_PATH = "output/warehouse.db"
CUSTOMERS_CONFIG = "config/customers.yaml"
ORDERS_CONFIG = "config/orders.yaml"


def get_connection():
    return sqlite3.connect(DB_PATH)


def get_table_count(table_name):
    allowed_tables = {
        "customers",
        "orders",
        "pipeline_audit",
        "quarantine_records"
    }

    if table_name not in allowed_tables:
        return 0

    if not Path(DB_PATH).exists():
        return 0

    connection = get_connection()

    try:
        cursor = connection.cursor()
        cursor.execute(f'SELECT COUNT(*) FROM "{table_name}"')
        return cursor.fetchone()[0]
    except sqlite3.Error:
        return 0
    finally:
        connection.close()


def load_customers():
    if get_table_count("customers") == 0:
        return pd.DataFrame()

    connection = get_connection()

    try:
        return pd.read_sql_query(
            "SELECT * FROM customers",
            connection
        )
    finally:
        connection.close()


def get_audit_logs():
    if not Path(DB_PATH).exists():
        return pd.DataFrame()

    connection = get_connection()

    try:
        return pd.read_sql_query(
            """
            SELECT *
            FROM pipeline_audit
            ORDER BY start_time DESC
            LIMIT 50
            """,
            connection
        )
    except sqlite3.Error:
        return pd.DataFrame()
    finally:
        connection.close()


def get_quarantine_records():
    if not Path(DB_PATH).exists():
        return pd.DataFrame()

    connection = get_connection()

    try:
        return pd.read_sql_query(
            """
            SELECT *
            FROM quarantine_records
            ORDER BY rejected_at DESC
            LIMIT 100
            """,
            connection
        )
    except sqlite3.Error:
        return pd.DataFrame()
    finally:
        connection.close()


def execute_pipeline(dataset):
    if dataset == "customers":
        config_path = CUSTOMERS_CONFIG
        reference_data = None
    else:
        config_path = ORDERS_CONFIG
        customers = load_customers()

        if customers.empty:
            raise ValueError(
                "Customers data is required before processing orders."
            )

        reference_data = {"customers": customers}

    start_time = time.perf_counter()

    result = run_pipeline(
        config_path,
        reference_data=reference_data
    )

    duration = time.perf_counter() - start_time

    result["duration_seconds"] = round(duration, 4)
    result["records_per_second"] = round(
        result["input_count"] / duration if duration > 0 else 0,
        2
    )

    return result


st.markdown("""
<style>
.main {
    background-color: #f5f7fb;
}
[data-testid="stMetric"] {
    background: white;
    padding: 18px;
    border-radius: 12px;
    border: 1px solid #e5e7eb;
}
div.stButton > button {
    border-radius: 8px;
    font-weight: 600;
    min-height: 42px;
}
</style>
""", unsafe_allow_html=True)

st.sidebar.title("⚡ YottaFlex AI")
st.sidebar.caption("Configuration-Driven Data Pipeline")

page = st.sidebar.radio(
    "NAVIGATION",
    [
        "Dashboard",
        "Run Pipeline",
        "Data Quality",
        "Performance",
        "Audit Logs",
        "Warehouse"
    ]
)

st.sidebar.divider()

if Path(DB_PATH).exists():
    st.sidebar.success("Database Connected")
else:
    st.sidebar.warning("Database Not Found")


if page == "Dashboard":

    st.title("YottaFlex AI Data Pipeline")
    st.write("Monitor, execute and analyze your data workflows.")

    st.divider()

    customers_count = get_table_count("customers")
    orders_count = get_table_count("orders")
    audit_count = get_table_count("pipeline_audit")
    rejected_count = get_table_count("quarantine_records")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Customers", f"{customers_count:,}")
    col2.metric("Orders", f"{orders_count:,}")
    col3.metric("Pipeline Runs", f"{audit_count:,}")
    col4.metric("Rejected Records", f"{rejected_count:,}")

    st.subheader("Project Overview")

    st.write(
        "A configuration-driven data processing system "
        "that ingests, validates, transforms and loads datasets."
    )

    col1, col2 = st.columns(2)

    with col1:
        st.info(
            "**Customer Pipeline**\n\n"
            "Validates customer records, primary keys "
            "and required fields."
        )

    with col2:
        st.info(
            "**Orders Pipeline**\n\n"
            "Validates orders and customer foreign keys "
            "before warehouse loading."
        )

    st.subheader("Pipeline Architecture")

    st.code(
        "CSV Files → YAML Configuration → Ingestion → "
        "Validation → Transformation → SQLite Warehouse\n"
        "                                      ↓\n"
        "                              Audit & Quarantine"
    )

    if st.button("Refresh Dashboard"):
        st.rerun()


elif page == "Run Pipeline":

    st.title("Run Data Pipeline")

    st.write("Execute customer and orders datasets.")

    st.warning(
        "Run the customer pipeline before the orders pipeline."
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Run Customers Pipeline", use_container_width=True):
            try:
                with st.spinner("Processing customers..."):
                    result = execute_pipeline("customers")

                st.success("Customer pipeline completed!")
                st.json(result)

            except Exception as error:
                st.error(f"Pipeline failed: {error}")

    with col2:
        if st.button("Run Orders Pipeline", use_container_width=True):
            try:
                with st.spinner("Processing orders..."):
                    result = execute_pipeline("orders")

                st.success("Orders pipeline completed!")
                st.json(result)

            except Exception as error:
                st.error(f"Pipeline failed: {error}")

    st.divider()

    if st.button("Run Both Pipelines", use_container_width=True):
        try:
            with st.spinner("Running customer pipeline..."):
                customer_result = execute_pipeline("customers")

            st.success("Customer pipeline completed.")

            with st.spinner("Running orders pipeline..."):
                orders_result = execute_pipeline("orders")

            st.success("Both pipelines completed!")

            st.subheader("Customer Results")
            st.json(customer_result)

            st.subheader("Orders Results")
            st.json(orders_result)

        except Exception as error:
            st.error(f"Pipeline execution failed: {error}")


elif page == "Data Quality":

    st.title("Data Quality")

    col1, col2, col3 = st.columns(3)

    col1.metric("Customer Records", f"{get_table_count('customers'):,}")
    col2.metric("Order Records", f"{get_table_count('orders'):,}")
    col3.metric("Rejected Records", f"{get_table_count('quarantine_records'):,}")

    st.subheader("Quarantined Records")

    quarantine = get_quarantine_records()

    if not quarantine.empty:
        st.dataframe(
            quarantine,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No quarantine records available.")


elif page == "Performance":

    st.title("Pipeline Performance")

    logs = get_audit_logs()

    if not logs.empty:

        latest = logs.iloc[0]

        col1, col2, col3 = st.columns(3)

        col1.metric("Input Records", f"{int(latest['input_count']):,}")
        col2.metric("Accepted Records", f"{int(latest['accepted_count']):,}")
        col3.metric("Rejected Records", f"{int(latest['rejected_count']):,}")

        st.subheader("Recent Pipeline Runs")

        st.dataframe(
            logs,
            use_container_width=True,
            hide_index=True
        )

    else:
        st.info("No performance data available yet.")

    st.caption(
        "For fresh throughput measurements, run performance_report.py."
    )


elif page == "Audit Logs":

    st.title("Pipeline Audit Logs")

    logs = get_audit_logs()

    if not logs.empty:
        st.dataframe(
            logs,
            use_container_width=True,
            hide_index=True
        )

        st.download_button(
            "Download Audit Logs",
            data=logs.to_csv(index=False),
            file_name="pipeline_audit_logs.csv",
            mime="text/csv"
        )
    else:
        st.info("No audit logs found.")


elif page == "Warehouse":

    st.title("Data Warehouse")

    warehouse_data = pd.DataFrame({
        "Dataset": ["Customers", "Orders"],
        "Table": ["customers", "orders"],
        "Total Records": [
            get_table_count("customers"),
            get_table_count("orders")
        ]
    })

    st.dataframe(
        warehouse_data,
        use_container_width=True,
        hide_index=True
    )

    st.subheader("Customer Sample")

    customers = load_customers()

    if not customers.empty:
        st.dataframe(
            customers.head(20),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No customer records available.")

    if st.button("Refresh Warehouse"):
        st.rerun()


st.divider()

st.caption(
    "YottaFlex AI | Python | Pandas | SQLite | Streamlit"
)
