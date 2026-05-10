from __future__ import annotations

import argparse
import csv
import logging
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from altair_bench import EXPORTS as ALTAIR_EXPORTS
from matplotlib_bench import EXPORTS as MATPLOTLIB_EXPORTS
from plotly_bench import EXPORTS as PLOTLY_EXPORTS

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "outputs"
CSV_PATH = BASE_DIR / "benchmark_runs.csv"
BENCHMARK_TIMEOUT_SECONDS = 30
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

LIBRARIES = {
    "altair": ALTAIR_EXPORTS,
    "matplotlib": MATPLOTLIB_EXPORTS,
    "plotly": PLOTLY_EXPORTS,
}

EXPECTED_DATASETS = tuple(MATPLOTLIB_EXPORTS)
for library_name, exports in LIBRARIES.items():
    if tuple(exports) != EXPECTED_DATASETS:
        raise ValueError(f"{library_name} benchmark datasets are out of sync")

DATASETS = list(MATPLOTLIB_EXPORTS)


def append_result(row: dict[str, str | float]) -> None:
    should_write_header = not CSV_PATH.exists()
    with CSV_PATH.open("a", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=CSV_FIELDS)
        if should_write_header:
            writer.writeheader()
        writer.writerow(row)


def start_result_row(
    run_id: str,
    started_at_utc: str,
    library: str,
    dataset: str,
    output_path: Path,
) -> dict[str, str]:
    return {
        "run_id": run_id,
        "started_at_utc": started_at_utc,
        "library": library,
        "dataset": dataset,
        "elapsed_seconds": "",
        "status": "started",
        "output_path": str(output_path),
        "error": "",
    }


def _worker_command(library: str, dataset: str, output_path: Path) -> list[str]:
    return [
        sys.executable,
        str(BASE_DIR / "main.py"),
        "--worker-library",
        library,
        "--worker-dataset",
        dataset,
        "--worker-output-path",
        str(output_path),
    ]


def run_export_subprocess(
    library: str,
    dataset: str,
    output_path: Path,
    timeout_seconds: int,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        _worker_command(library, dataset, output_path),
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
    )


def _format_subprocess_error(completed: subprocess.CompletedProcess[str]) -> str:
    stderr = completed.stderr.strip()
    stdout = completed.stdout.strip()
    if stderr:
        return stderr
    if stdout:
        return stdout
    return f"worker exited with code {completed.returncode}"


def run_export(library: str, dataset: str, output_path: Path) -> None:
    export_fn = LIBRARIES[library][dataset]
    export_fn(output_path)


def benchmark_export(
    run_id: str,
    started_at_utc: str,
    library: str,
    dataset: str,
) -> None:
    output_path = OUTPUT_DIR / f"{library}_{dataset}.png"
    append_result(start_result_row(run_id, started_at_utc, library, dataset, output_path))
    logger.info("%s %s started", library, dataset)
    started = time.perf_counter()

    try:
        completed = run_export_subprocess(
            library,
            dataset,
            output_path,
            BENCHMARK_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        elapsed_seconds = time.perf_counter() - started
        logger.error("%s %s timed out after %.3fs", library, dataset, elapsed_seconds)
        append_result(
            {
                "run_id": run_id,
                "started_at_utc": started_at_utc,
                "library": library,
                "dataset": dataset,
                "elapsed_seconds": f"{elapsed_seconds:.6f}",
                "status": "timeout",
                "output_path": str(output_path),
                "error": f"timed out after {BENCHMARK_TIMEOUT_SECONDS}s",
            }
        )
        return

    elapsed_seconds = time.perf_counter() - started
    if completed.returncode != 0:
        logger.error(
            "%s %s failed after %.3fs with exit code %s",
            library,
            dataset,
            elapsed_seconds,
            completed.returncode,
        )
        append_result(
            {
                "run_id": run_id,
                "started_at_utc": started_at_utc,
                "library": library,
                "dataset": dataset,
                "elapsed_seconds": f"{elapsed_seconds:.6f}",
                "status": "error",
                "output_path": str(output_path),
                "error": _format_subprocess_error(completed),
            }
        )
        return

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


def warmup_export(library: str, dataset: str) -> None:
    output_path = OUTPUT_DIR / f"{library}_{dataset}.png"
    started = time.perf_counter()

    try:
        completed = run_export_subprocess(
            library,
            dataset,
            output_path,
            BENCHMARK_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        elapsed_seconds = time.perf_counter() - started
        logger.error("%s %s warm-up timed out after %.3fs", library, dataset, elapsed_seconds)
        return

    elapsed_seconds = time.perf_counter() - started
    if completed.returncode != 0:
        logger.error(
            "%s %s warm-up failed after %.3fs with exit code %s",
            library,
            dataset,
            elapsed_seconds,
            completed.returncode,
        )
        if completed.stderr.strip():
            logger.error("%s %s warm-up stderr: %s", library, dataset, completed.stderr.strip())
        return

    logger.info("%s %s warm-up completed in %.3fs", library, dataset, elapsed_seconds)


def run_benchmarks(*, libraries: list[str], runs: int, datasets: list[str] | None = None) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    OUTPUT_DIR.mkdir(exist_ok=True)

    selected_datasets = DATASETS if datasets is None else datasets

    logger.info("starting warm-up pass")
    for library in libraries:
        for dataset in selected_datasets:
            warmup_export(library, dataset)
    logger.info("finished warm-up pass")

    for _ in range(runs):
        run_id = uuid.uuid4().hex
        started_at_utc = datetime.now(timezone.utc).isoformat()

        logger.info("starting benchmark run %s", run_id)
        for library in libraries:
            for dataset in selected_datasets:
                benchmark_export(run_id, started_at_utc, library, dataset)
        logger.info("finished benchmark run %s", run_id)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--library",
        choices=("all", "altair", "matplotlib", "plotly"),
        default="all",
        help="Select which benchmark library to run.",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=4,
        help="Number of benchmark repetitions.",
    )
    parser.add_argument(
        "--dataset",
        action="append",
        choices=DATASETS,
        help="Limit execution to one or more benchmark cases.",
    )
    parser.add_argument("--worker-library", choices=LIBRARIES, help=argparse.SUPPRESS)
    parser.add_argument("--worker-dataset", choices=DATASETS, help=argparse.SUPPRESS)
    parser.add_argument("--worker-output-path", help=argparse.SUPPRESS)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.worker_library is not None:
        if args.worker_dataset is None or args.worker_output_path is None:
            raise ValueError("worker invocation requires dataset and output path")
        run_export(
            args.worker_library,
            args.worker_dataset,
            Path(args.worker_output_path),
        )
        return

    libraries = list(LIBRARIES) if args.library == "all" else [args.library]
    run_benchmarks(libraries=libraries, runs=args.runs, datasets=args.dataset)


def run_plotly() -> None:
    run_benchmarks(libraries=["plotly"], runs=4)


def run_matplotlib() -> None:
    run_benchmarks(libraries=["matplotlib"], runs=4)


def run_all() -> None:
    run_benchmarks(libraries=["altair", "matplotlib", "plotly"], runs=4)


def run_altair() -> None:
    run_benchmarks(libraries=["altair"], runs=4)


if __name__ == "__main__":
    main()
