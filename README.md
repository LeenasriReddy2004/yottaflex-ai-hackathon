# YottaFlex AI – Configuration-Driven Data Loader

## About the Project

This project was developed as part of the YottaFlex.ai Hackathon.

The main idea behind this project is to make data loading easier and more reliable. Instead of writing separate code for every dataset, I built a system where the dataset details and rules are defined in YAML configuration files.

The pipeline reads the data, checks whether it is valid, applies the required transformations, and stores the processed records in a SQLite database.

It also keeps track of rejected records and pipeline execution details, making it easier to understand what happened during each run.

## What Does This Project Do?

The project includes the following features:

- Reads dataset details from YAML configuration files.
- Loads data from CSV files.
- Checks column names, data types, and required values.
- Identifies duplicate records and invalid data.
- Checks foreign key relationships between datasets.
- Applies transformations such as changing text to lowercase or title case.
- Stores valid records in a SQLite database.
- Supports append, replace, and upsert loading modes.
- Keeps rejected records separately for further checking.
- Maintains audit information for pipeline runs.
- Generates sample datasets for testing with 100,000 records.
- Includes a dashboard to monitor pipeline results and data quality.

## Technologies Used

- Python – Main programming language.
- Pandas – For handling and processing datasets.
- PyYAML – For reading YAML configuration files.
- SQLite – For storing processed data.
- Streamlit – For building the dashboard.
- Pytest – For testing the pipeline.

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
├── output/
├── outputs/
├── reports/
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
└── README.md
```

## How to Set Up the Project

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

## Running the Project

The pipeline can be executed for each dataset using its YAML configuration.

**For customers:**

```bash
python -c "from src.pipeline import run_pipeline; print(run_pipeline('config/customers.yaml'))"
```

**For orders:**

```bash
python -c "from src.pipeline import run_pipeline; print(run_pipeline('config/orders.yaml'))"
```

## Running the Dashboard

To start the dashboard, run:

```bash
python -m streamlit run app.py
```

After running the command, open the local URL shown in your terminal. Usually, it is:

`http://localhost:8501`

The dashboard helps view pipeline execution, data quality information, performance details, and audit logs.

## Running the Tests

To check whether the pipeline is working correctly, run:

```bash
python -m pytest -v
```

The current test suite contains seven tests. They cover empty files, malformed files, duplicate records, missing required values, invalid foreign keys, repeated upsert loading, and delete-event handling.

## Testing with Large Datasets

To check how the pipeline handles larger amounts of data, I generated sample customer and order datasets containing 100,000 records each.

This helps evaluate data processing, validation, database loading, and performance.

The project also includes scripts for checking database records, testing idempotency, reconciling data, and generating performance reports.

## Database

The processed data is stored in a SQLite database:

`output/warehouse.db`

The project also maintains audit information about pipeline runs and stores rejected records separately.

## Additional Documentation

- **DATA_DICTIONARY.md:** Explains the dataset columns and their purpose.
- **DESIGN_NOTES.md:** Describes the design and implementation of the project.

## Final Note

While building this project, I focused on making the data loading process reusable, handling invalid records properly, and making sure that running the pipeline again does not unnecessarily create duplicate records.

This project helped me understand how data ingestion, validation, transformation, database loading, testing, and monitoring work together in a real-world data pipeline.

**Developed as part of the YottaFlex.ai Hackathon.**