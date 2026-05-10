#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

ITERATIONS="${ITERATIONS:-10}"
RUN_ID="${RUN_ID:-$(date -u +%Y%m%dT%H%M%SZ)}"
CSV_PATH="${CSV_PATH:-benchmark_results.csv}"
BINS=(charton kuva plotters)

mkdir -p output

echo "building release binaries"
cargo build --release --bins

if [[ ! -f "$CSV_PATH" || ! -s "$CSV_PATH" ]]; then
  printf 'run_id,timestamp,library,benchmark,status,elapsed_s,error\n' > "$CSV_PATH"
fi

echo "warmup run_id=$RUN_ID"
for bin in "${BINS[@]}"; do
  RUN_ID="$RUN_ID" "./target/release/$bin" >/dev/null
done

for run in $(seq 1 "$ITERATIONS"); do
  echo "iteration $run/$ITERATIONS run_id=$RUN_ID"
  for bin in "${BINS[@]}"; do
    RUN_ID="$RUN_ID" "./target/release/$bin"
  done
done
