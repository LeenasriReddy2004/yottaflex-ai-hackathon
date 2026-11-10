import time
from src.pipeline import run_pipeline


def benchmark_pipeline(config_path, reference_data=None):
    start_time = time.perf_counter()

    result = run_pipeline(
        config_path,
        reference_data=reference_data
    )

    end_time = time.perf_counter()

    duration = end_time - start_time

    input_count = result["input_count"]

    throughput = (
        input_count / duration if duration > 0 else 0
    )

    return {
        "dataset": result["dataset"],
        "status": result["status"],
        "input_count": input_count,
        "accepted_count": result["accepted_count"],
        "rejected_count": result["rejected_count"],
        "duration_seconds": round(duration, 4),
        "records_per_second": round(throughput, 2)
    }