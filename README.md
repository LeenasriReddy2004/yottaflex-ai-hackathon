# YottaFlex AI – Configuration-Driven Data Loader

## About the Project

I developed this project as part of the YottaFlex.ai Hackathon.

While working on this project, my goal was to make the data loading process easier, more flexible, and reliable. Instead of writing separate code for every dataset, I wanted to build a system where I could manage different datasets using YAML configuration files.

The pipeline reads the input data, checks it for errors, validates the records, applies the required transformations, and stores the processed data in a SQLite database.

I also included features to handle rejected records and maintain audit logs so that each pipeline run can be monitored and reviewed.

## What Does This Project Do?

Here are the main features I implemented:

- Uses YAML configuration files to define dataset details and validation rules.
- Reads data from CSV files.
- Checks column names, data types, and required values.
- Identifies duplicate records and invalid data.
- Validates foreign key relationships between datasets.
- Applies transformations such as lowercase, title case, and rounding values.
- Stores valid records in a SQLite database.
- Supports append, replace, and upsert loading modes.
- Stores rejected records separately for further analysis.
- Maintains audit information for pipeline executions.
- Generates synthetic customer and order datasets with 100,000 records each.
- Includes a Streamlit dashboard to monitor pipeline execution, data quality, and performance.

## Technologies I Used

- **Python:** For developing the complete data pipeline.
- **Pandas:** For reading and processing datasets.
- **PyYAML:** For loading and handling YAML configurations.
- **SQLite:** For storing processed records.
- **Streamlit:** For creating the project dashboard.
- **Pytest:** For testing different pipeline scenarios.

## Project Folder Structure

```text
yottaflex-ai-hackathon/
│
├── config/
│   ├── customers.yaml
│   └── orders.yaml
│
├── data/
│   ├── generated/
│   └── sample/
│
├── src/
│   ├── audit.py
│   ├── config_loader.py
│   ├── ingestion.py
│   ├── loader.py
│   ├── performance.py
│   ├── pipeline.py
│   ├── quarantine.py
│   ├── transformation.py
│   ├── validation.py
│   └── generators/
│
├── tests/
│   └── test_pipeline.py
│
├── app.py
├── check_db.py
├── idempotency_check.py
├── performance_report.py
├── reconciliation.py
├── requirements.txt
├── DATA_DICTIONARY.md
├── DESIGN_NOTES.md
├── .gitignore
└── README.md
```

## How to Run the Project

Follow these steps to run the project on your system.

### Step 1: Clone the repository

```bash
git clone https://github.com/LeenasriReddy2004/yottaflex-ai-hackathon.git
cd yottaflex-ai-hackathon
```

### Step 2: Create a virtual environment

```bash
python -m venv .venv
```

### Step 3: Activate the virtual environment

For Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

### Step 4: Install the required packages

```bash
python -m pip install -r requirements.txt
```

## Running the Pipeline

I configured separate YAML files for customers and orders. The pipeline can be executed using the following commands.

**Customer Pipeline**

```bash
python -c "from src.pipeline import run_pipeline; print(run_pipeline('config/customers.yaml'))"
```

**Orders Pipeline**

```bash
python -c "from src.pipeline import run_pipeline; print(run_pipeline('config/orders.yaml'))"
```

## Running the Dashboard

I also created a Streamlit dashboard to make it easier to monitor the pipeline.

Run the following command:

```bash
python -m streamlit run app.py
```

Open the local URL displayed in your terminal. Usually:

`http://localhost:8501`

The dashboard includes sections for:

- Dashboard overview
- Running pipelines
- Data quality
- Performance
- Audit logs
- Warehouse information

## Running the Tests

I used Pytest to check how the pipeline handles different situations.

Run:

```bash
python -m pytest -v
```

Currently, all seven automated tests are passing.

The tests cover:

1. Empty CSV files.
2. Malformed CSV files.
3. Duplicate primary keys.
4. Missing required values.
5. Invalid foreign key records.
6. Repeated upsert loading without duplicate records.
7. Delete-event handling.

## Testing with Large Datasets

To check how the pipeline performs with larger datasets, I generated synthetic customer and order data containing 100,000 records each.

This helped me test data ingestion, validation, transformation, database loading, and processing performance with larger inputs.

I also included separate scripts to check database records, test idempotency, perform reconciliation, and generate performance reports.

## Database

I used SQLite to store the processed data.

The database file is created at:

`output/warehouse.db`

The pipeline also maintains audit information about its executions and stores rejected records separately.

## Additional Documentation

I have included two additional documents to explain the project in more detail:

- **DATA_DICTIONARY.md:** Contains information about the dataset columns and their purpose.
- **DESIGN_NOTES.md:** Explains the overall design and implementation approach.

## What I Learned

Building this project gave me practical experience in developing a data pipeline from the beginning.

I learned how to work with YAML configurations, process large CSV datasets, validate data, handle duplicates and rejected records, load data into a database, and monitor pipeline execution.

One of the main things I focused on was making the pipeline reusable and ensuring that repeated upsert runs do not unnecessarily create duplicate records.

**Developed by Leenasri Reddy as part of the YottaFlex.ai Hackathon.**