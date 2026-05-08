from __future__ import annotations

import csv
import logging
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from matplotlib_bench import EXPORTS as MATPLOTLIB_EXPORTS
from plotly_bench import EXPORTS as PLOTLY_EXPORTS

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "outputs"
CSV_PATH = BASE_DIR / "benchmark_runs.csv"
CSV_FIELDS = [
    "run_id",
    "started_at_utc",
    "library",
    "dataset",
    "elapsed_seconds",
    "status",
    "output_path",
    "error",
]


def append_result(row: dict[str, str | float]) -> None:
    should_write_header = not CSV_PATH.exists()
    with CSV_PATH.open("a", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=CSV_FIELDS)
        if should_write_header:
            writer.writeheader()
        writer.writerow(row)


def benchmark_export(
    run_id: str,
    started_at_utc: str,
    library: str,
    dataset: str,
    export_fn,
) -> None:
    output_path = OUTPUT_DIR / f"{library}_{dataset}.png"
    started = time.perf_counter()

    try:
        export_fn(output_path)
    except Exception as exc:
        elapsed_seconds = time.perf_counter() - started
        logger.exception("%s %s failed after %.3fs", library, dataset, elapsed_seconds)
        append_result(
            {
                "run_id": run_id,
                "started_at_utc": started_at_utc,
                "library": library,
                "dataset": dataset,
                "elapsed_seconds": f"{elapsed_seconds:.6f}",
                "status": "error",
                "output_path": str(output_path),
                "error": repr(exc),
            }
        )
        return

    elapsed_seconds = time.perf_counter() - started
    logger.info("%s %s completed in %.3fs", library, dataset, elapsed_seconds)
    append_result(
        {
            "run_id": run_id,
            "started_at_utc": started_at_utc,
            "library": library,
            "dataset": dataset,
            "elapsed_seconds": f"{elapsed_seconds:.6f}",
            "status": "ok",
            "output_path": str(output_path),
            "error": "",
        }
    )


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    OUTPUT_DIR.mkdir(exist_ok=True)

    for i in range(4):
        run_id = uuid.uuid4().hex
        started_at_utc = datetime.now(timezone.utc).isoformat()
        benchmarks = [
            ("matplotlib", MATPLOTLIB_EXPORTS),
            ("plotly", PLOTLY_EXPORTS),
        ]

        logger.info("starting benchmark run %s", run_id)
        for library, exports in benchmarks:
            for dataset, export_fn in exports.items():
                benchmark_export(run_id, started_at_utc, library, dataset, export_fn)
        logger.info("finished benchmark run %s", run_id)


if __name__ == "__main__":
    main()
