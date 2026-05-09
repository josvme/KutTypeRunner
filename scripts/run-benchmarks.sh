#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TIMESTAMP="${1:-$(date +%Y%m%d-%H%M%S)}"
RESULTS_DIR="${ROOT_DIR}/results/${TIMESTAMP}"
RAW_DIR="${RESULTS_DIR}/raw"

BENCH_ITERATIONS="${BENCH_ITERATIONS:-10000}"
BENCH_REPETITIONS="${BENCH_REPETITIONS:-5}"
SYMFONY_REPETITIONS="${SYMFONY_REPETITIONS:-3}"
SYMFONY_DURATION_SECONDS="${SYMFONY_DURATION_SECONDS:-30}"
SYMFONY_CONCURRENCY="${SYMFONY_CONCURRENCY:-1 20}"
SYMFONY_ENDPOINTS="${SYMFONY_ENDPOINTS:-/}"
SYMFONY_DIR="${SYMFONY_DIR:-${ROOT_DIR}/demo}"

BASELINE_PHP_BIN="${BASELINE_PHP_BIN:-php}"
BASELINE_PHP_ARGS_RAW="${BASELINE_PHP_ARGS:--n}"
WITH_EXT_PHP_BIN="${WITH_EXT_PHP_BIN:-php}"
WITH_EXT_PHP_ARGS_RAW="${WITH_EXT_PHP_ARGS:--n -d extension=${ROOT_DIR}/target/release/libkut_type_runner.so}"

MICRO_SCRIPTS=(
  "control_loop.php"
  "no_arg_user_function.php"
  "scalar_args.php"
  "object_args.php"
  "method_calls.php"
  "mixed_argument_shapes.php"
)

BASELINE_PHP_ARGS=()
WITH_EXT_PHP_ARGS=()

log() {
  printf '%s\n' "$*"
}

init_dirs() {
  mkdir -p "${RAW_DIR}"
  echo "benchmark,variant,iterations,total_ns,ns_per_op,repetition" > "${RAW_DIR}/micro.csv"
}

parse_php_args() {
  IFS=' ' read -r -a BASELINE_PHP_ARGS <<< "${BASELINE_PHP_ARGS_RAW}"
  IFS=' ' read -r -a WITH_EXT_PHP_ARGS <<< "${WITH_EXT_PHP_ARGS_RAW}"
}

build_extension() {
  log "Building release extension..."
  (cd "${ROOT_DIR}" && cargo build --release)
}

append_micro_record() {
  local csv_line="$1"
  local repetition="$2"

  printf '%s,%s\n' "${csv_line}" "${repetition}" >> "${RAW_DIR}/micro.csv"
}

run_micro_variant() {
  local variant="$1"
  local php_bin="$2"
  shift 2
  local -a php_args=("$@")

  local script
  for script in "${MICRO_SCRIPTS[@]}"; do
    local repetition
    for repetition in $(seq 1 "${BENCH_REPETITIONS}"); do
      local output
      output=$(BENCH_VARIANT="${variant}" BENCH_ITERATIONS="${BENCH_ITERATIONS}" "${php_bin}" "${php_args[@]}" "${ROOT_DIR}/bench/${script}" 2>/dev/null)

      while IFS= read -r line; do
        [ -z "${line}" ] && continue
        append_micro_record "${line}" "${repetition}"
      done <<< "${output}"
    done
  done
}

symfony_csv_header() {
  echo "endpoint,concurrency,variant,repetition,rps,latency_median_ms,latency_p95_ms,latency_max_ms,error_rate" > "${RAW_DIR}/symfony.csv"
}

append_symfony_record() {
  local endpoint="$1"
  local concurrency="$2"
  local variant="$3"
  local repetition="$4"
  local rps="$5"
  local p50="$6"
  local p95="$7"
  local pmax="$8"
  local error_rate="$9"

  printf '%s,%s,%s,%s,%s,%s,%s,%s,%s\n' \
    "${endpoint}" "${concurrency}" "${variant}" "${repetition}" \
    "${rps}" "${p50}" "${p95}" "${pmax}" "${error_rate}" >> "${RAW_DIR}/symfony.csv"
}

run_symfony_variant() {
  local variant="$1"
  local php_bin="$2"
  shift 2
  local -a php_args=("$@")

  local server_log="${RAW_DIR}/server-${variant}.log"
  "${php_bin}" "${php_args[@]}" -S 127.0.0.1:8000 -t "${SYMFONY_DIR}/public" > "${server_log}" 2>/dev/null &
  local server_pid=$!

  cleanup_server() {
    if kill -0 "${server_pid}" 2>/dev/null; then
      kill "${server_pid}" || true
      wait "${server_pid}" 2>/dev/null || true
    fi
  }

  trap cleanup_server RETURN
  sleep 2

  local endpoint
  for endpoint in ${SYMFONY_ENDPOINTS}; do
    local concurrency
    for concurrency in ${SYMFONY_CONCURRENCY}; do
      local repetition
      for repetition in $(seq 1 "${SYMFONY_REPETITIONS}"); do
        local k6_script
        local k6_summary
        k6_script="${RAW_DIR}/k6-script-${variant}-${concurrency}-${repetition}.js"
        k6_summary="${RAW_DIR}/k6-summary-${variant}-${concurrency}-${repetition}.json"

        cat > "${k6_script}" <<'JS'
import http from 'k6/http';

export default function () {
  http.get(__ENV.TARGET_URL);
}
JS

        TARGET_URL="http://127.0.0.1:8000${endpoint}" \
          k6 run \
            --quiet \
            --vus "${concurrency}" \
            --duration "${SYMFONY_DURATION_SECONDS}s" \
            --summary-export "${k6_summary}" \
            "${k6_script}" >/dev/null 2>/dev/null

        local parsed
        parsed=$(python3 "${ROOT_DIR}/scripts/parse_k6_summary.py" "${k6_summary}")

        local rps
        local p50
        local p95
        local pmax
        local error_rate
        IFS=',' read -r rps p50 p95 pmax error_rate <<< "${parsed}"

        append_symfony_record \
          "${endpoint}" "${concurrency}" "${variant}" "${repetition}" \
          "${rps:-0}" "${p50:-0}" "${p95:-0}" "${pmax:-0}" "${error_rate}"
      done
    done
  done

  cleanup_server
  trap - RETURN
}

run_symfony_benchmark_if_possible() {
  if ! command -v k6 >/dev/null 2>&1; then
    log "k6 not found; skipping Symfony benchmark"
    echo "k6 not found" > "${RAW_DIR}/symfony.skip.txt"
    return
  fi

  if [ ! -d "${SYMFONY_DIR}" ]; then
    if command -v composer >/dev/null 2>&1; then
      log "Creating Symfony demo app in ${SYMFONY_DIR}..."
      (cd "${ROOT_DIR}" && composer create-project symfony/symfony-demo demo)
    else
      log "Symfony demo directory missing and composer unavailable; skipping Symfony benchmark"
      echo "demo missing and composer unavailable" > "${RAW_DIR}/symfony.skip.txt"
      return
    fi
  fi

  symfony_csv_header

  log "Running Symfony benchmark (baseline)..."
  run_symfony_variant "baseline" "${BASELINE_PHP_BIN}" "${BASELINE_PHP_ARGS[@]}"

  log "Running Symfony benchmark (with extension)..."
  run_symfony_variant "with_ext" "${WITH_EXT_PHP_BIN}" "${WITH_EXT_PHP_ARGS[@]}"
}

write_summary() {
  python3 "${ROOT_DIR}/scripts/summarize_results.py" "${RESULTS_DIR}"
}

main() {
  init_dirs
  parse_php_args
  build_extension

  log "Running micro-benchmarks (baseline)..."
  run_micro_variant "baseline" "${BASELINE_PHP_BIN}" "${BASELINE_PHP_ARGS[@]}"

  log "Running micro-benchmarks (with extension)..."
  run_micro_variant "with_ext" "${WITH_EXT_PHP_BIN}" "${WITH_EXT_PHP_ARGS[@]}"

  run_symfony_benchmark_if_possible
  write_summary

  log "Benchmark run complete: ${RESULTS_DIR}"
}

main "$@"
