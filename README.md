# QFw-IQM

QFw-IQM contains IQM-specific characterization workflows. The preferred path
runs through the Quantum Framework, where QFw owns service startup, placement,
and the reusable IQM QPM integration. The same Python workflows can also run
directly through `iqm-client` for standalone characterization without QFw.

## Requirements

For QFw-backed execution:

- A configured QFw tree with the IQM QPM service available.
- An activated QFw environment:

```bash
source /path/to/QFw/setup/qfw_activate
```

- IQM endpoint credentials exported in the shell that starts QFw:

```bash
export QFW_QC_URL="https://<iqm-endpoint>"
export QFW_API_KEY="<api-key>"
```

Optional IQM settings:

```bash
export QFW_IQM_QUANTUM_COMPUTER="<machine-name>"
export QFW_IQM_REQUEST_TIMEOUT=30
export QFW_IQM_JOB_TIMEOUT=300
```

For direct execution without QFw:

- The `iqm-client` Python package and its IQM dependencies.
- `QFW_QC_URL` and `QFW_API_KEY` exported in the shell.

## Workflows

Each workflow supports `--backend auto|qfw|direct`. The default is `auto`.
When QFw is activated, `auto` uses QFw. Otherwise, `auto` uses direct
`iqm-client` access.

In QFw mode, each wrapper starts QFw with `config/qfw_iqm_services.yaml`, runs
one Python script through `qfw_srun.sh`, and tears QFw down.

```bash
./qfw_iqm_env_check.sh --json
./qfw_iqm_discover.sh --json
./qfw_iqm_submit_smoke.sh --shots 100 --json
./qfw_iqm_timing_overhead.sh --shots-sweep 1,10,100 --batch-sweep 1,2 --json
./qfw_iqm_timing_1q.sh --qubits QB1,QB2 --gates rx,ry --depths 1,2,4 --json
```

To force direct mode:

```bash
./qfw_iqm_env_check.sh --backend direct --json
./qfw_iqm_discover.sh --backend direct --json
./qfw_iqm_submit_smoke.sh --backend direct --shots 100 --json
./qfw_iqm_timing_overhead.sh --backend direct --shots-sweep 1,10,100 --json
./qfw_iqm_timing_1q.sh --backend direct --qubits QB1 --gates rx --json
```

To run the current suite in one QFw session:

```bash
./qfw_iqm_run_all.sh
```

`qfw_iqm_run_all.sh` includes the environment check, discovery capture, smoke
submission, and a short single-qubit timing sanity sweep. The timing sweep is
kept intentionally small so that `run_all` remains safe for routine validation.
The default 1Q timing settings can be changed with:

```bash
export QFW_IQM_RUN_ALL_1Q_QUBITS=QB1
export QFW_IQM_RUN_ALL_1Q_GATES=rx
export QFW_IQM_RUN_ALL_1Q_DEPTHS=1,2
export QFW_IQM_RUN_ALL_1Q_SHOTS=100
export QFW_IQM_RUN_ALL_1Q_REPETITIONS=1
```

Larger timing campaigns should still be run explicitly with the desired shot
sweep, batch sweep, depth sweep, qubit list, and repetition count.

Output is written under:

```text
data/raw/<YYYYMMDD>/<script-name>/<HHMMSS>/
```

Each workflow writes its terminal summary to the run's `results/` directory.
With `--json`, the summary is stored in `results/stdout.json`. Without
`--json`, the text summary is stored in `results/stdout.txt`. The terminal only
prints the path to that saved output file.

The `data/` directory is intentionally ignored by git.

## Script Reference

The top-level Python files under `scripts/` are the workflow entry points.
They all support `--backend auto|qfw|direct`, `--output-dir`, `--run-id`,
and `--json`. Scripts that contact the machine also support
`--system-up-timeout`; scripts that query or submit against a specific
calibration can use `--calibration-set-id`.

### `scripts/iqm_env_check.py`

`iqm_env_check.py` is the first connectivity and metadata check. It selects
the requested backend, asks the backend for static and dynamic device
information, and writes a single `env_check.json` file. The output includes
the backend mode that was used, static architecture data, dynamic architecture
data, active qubits, the selected calibration set, and a compact summary for
quick terminal inspection.

Use this script before running characterization jobs. A successful run shows
that the local test environment can reach the IQM backend and that the backend
can return basic machine metadata. It does not submit a quantum job.

Typical use:

```bash
./qfw_iqm_env_check.sh --json
./qfw_iqm_env_check.sh --backend direct --json
```

### `scripts/iqm_discover.py`

`iqm_discover.py` captures the machine description needed for later
characterization and reporting. It collects backend metadata, dynamic
architecture metadata, the calibration snapshot, the quality metric snapshot,
and the coupling graph. The script writes `device_snapshot.json`,
`calibration_snapshot.json`, and `coupling_graph.json`.

The coupling graph is derived from the device architecture and dynamic gate
loci. This makes the output useful even when the provider API does not expose a
single direct `couplers` field. The script intentionally does not submit a
quantum job, and it no longer writes a qSchedSim skeleton file. Its job is to
record the raw discovery artifacts that other tools or reports can consume.

Typical use:

```bash
./qfw_iqm_discover.sh --json
./qfw_iqm_discover.sh --calibration-set-id <uuid> --json
```

### `scripts/iqm_submit_smoke.py`

`iqm_submit_smoke.py` is the preferred operational smoke test. It builds a
one-qubit Qiskit circuit, optionally applies an `X` gate with `--flip`, measures
the qubit, submits the circuit through the selected backend, and records the
result. The script writes the input description, a QASM artifact generated from
the Qiskit circuit, the backend result payload, and a timing summary when timing
metadata is available.

The default circuit measures the initial `|0>` state. With `--flip`, it
measures a prepared `|1>` state instead. This provides a minimal end-to-end
check that circuit construction, submission, execution, result retrieval, count
parsing, and timing propagation are working. It is not a fidelity benchmark.

Typical use:

```bash
./qfw_iqm_submit_smoke.sh --shots 100 --json
./qfw_iqm_submit_smoke.sh --shots 100 --flip --json
```

### `scripts/iqm_timing_overhead.py`

`iqm_timing_overhead.py` measures job-submission and execution timing using
Qiskit-authored measurement circuits. It runs two experiment families. The
shot sweep submits single circuits at different shot counts, while the batch
sweep submits multiple circuits in one backend call to expose batching behavior.
The script can repeat each case with `--repetitions` and can vary circuit width
with `--widths`.

For each record, the script writes the generated QASM artifact, the raw result
payload, and per-record timing metrics. It also writes
`timing_records.jsonl` and a `timing_summary.json` file with basic linear fits
for shot scaling and batch scaling where enough successful points exist. Use
`--dry-run` to verify the planned record set and output layout without
submitting jobs.

Typical use:

```bash
./qfw_iqm_timing_overhead.sh \
    --shots-sweep 1,10,100 \
    --batch-sweep 1,2 \
    --repetitions 3 \
    --json
```

### `scripts/iqm_timing_1q.py`

`iqm_timing_1q.py` implements the single-qubit gate duration test from the
characterization plan. It uses Qiskit to author one-qubit circuits, repeats a
selected gate at each requested depth, maps logical qubit 0 to the requested
physical IQM qubit, submits the serialized circuit through the common backend
path, and records timing data for each run.

The supported gate probes are `x`, `rx`, and `ry`. On IQM hardware these probe
the native PRX family through different Qiskit source gates and phases. The
default gate set is `rx,ry`, the default depth sweep is
`1,2,4,8,16,32,64,128`, and the default qubit set is `all` active qubits
reported by the backend. Use `--angle` to change the RX/RY angle, `--shots` to
set the shot count, and `--repetitions` to repeat each qubit/gate/depth point.

For each point, the script writes the generated QASM artifact, the raw result
payload, and a JSON-lines timing record. The summary file includes linear fits
against depth for each gate/qubit pair and for each gate across all selected
qubits. The most useful fit for a hardware timing model is usually
`execution_per_shot_seconds`, because it divides the reported execution time by
the shot count before fitting depth.

Typical use:

```bash
./qfw_iqm_timing_1q.sh \
    --qubits QB1,QB2 \
    --gates rx,ry \
    --depths 1,2,4,8,16 \
    --shots 100 \
    --repetitions 3 \
    --json
```

### `scripts/iqm_submit_smoke_qasm.py`

`iqm_submit_smoke_qasm.py` is a lower-level version of the smoke test that
constructs OpenQASM directly instead of authoring the circuit with Qiskit. It
submits a one-qubit measurement circuit through the selected backend using the
backend `sync_run` path. It supports `--flip`, `--shots`, `--qubit`,
`--calibration-set-id`, `--timeout`, and `--use-timeslot`.

This script is kept as an explicit OpenQASM example and as a debugging path for
the native request format. New characterization tests should usually prefer
`iqm_submit_smoke.py` so that circuit construction goes through Qiskit.

Typical use:

```bash
python3 scripts/iqm_submit_smoke_qasm.py --backend direct --shots 100 --json
```

### `scripts/iqm_timing_overhead_qasm.py`

`iqm_timing_overhead_qasm.py` is the direct-OpenQASM counterpart to
`iqm_timing_overhead.py`. It builds measurement circuits as QASM strings,
submits them through `sync_run` or `sync_run_many`, and records the same style
of per-job timing output and summary fits. It supports the same timing sweep
controls as the Qiskit timing script, plus `--qubit` for one-qubit mapped runs.

This script is useful when the native OpenQASM request path itself needs to be
debugged or compared against the Qiskit-authored workflow. For general timing
campaigns, use `iqm_timing_overhead.py`.

Typical use:

```bash
python3 scripts/iqm_timing_overhead_qasm.py \
    --backend direct \
    --shots-sweep 1,10,100 \
    --batch-sweep 1,2 \
    --json
```

## Helper Modules

The `scripts/qfw_iqm_util/` package contains shared implementation code used
by the workflow scripts. These files are not meant to be run directly.

| Module | Role |
| --- | --- |
| `backend.py` | Parses the common `--backend` option and selects QFw or direct IQM execution. |
| `backend_direct.py` | Implements direct `iqm-client` access, metadata queries, direct circuit submission, timing extraction, and coupling graph construction. |
| `backend_qfw.py` | Adapts the workflows to the QFw IQM service and QFw Qiskit backend. |
| `output.py` | Creates the `data/raw/<date>/<script>/<run>/` directory layout and writes JSON artifacts. |
| `qfw.py` | Reserves the IQM QPM service and exits the QFw application cleanly. |
| `qiskit_exec.py` | Contains shared Qiskit execution helpers, QASM artifact writing, count extraction, and timing summary propagation. |
| `timing.py` | Converts IQM job timeline events into duration fields used by smoke and timing reports. |

## QFw Execution Model

The shell wrappers assume QFw is responsible for startup, service placement,
and teardown when `--backend qfw` is selected or `--backend auto` detects an
activated QFw shell. The Python scripts run as QFw applications and use
`api_qpm` to reserve the IQM QPM service.

The default service config starts one IQM QPM on group 1:

```bash
qfw_setup.sh --services-config config/qfw_iqm_services.yaml
qfw_srun.sh scripts/iqm_submit_smoke.py
qfw_teardown.sh
```

For a heterogeneous allocation, the application runs on group 0 and the IQM
QPM service runs on the group 1 head node. For local or single-node operation,
QFw's allocation abstraction can map both groups to the same node.

## Direct Execution Model

In direct mode, the shell wrappers do not call `qfw_setup.sh`, `qfw_srun.sh`,
or `qfw_teardown.sh`. They execute the Python workflow locally and use
`iqm-client` with `QFW_QC_URL` and `QFW_API_KEY`. This mode is useful for
early machine characterization and for sharing the scripts with users who do
not have QFw installed.

## Adding Workflows

New shell wrappers should source `qfw_iqm_common.sh` rather than reimplement
backend parsing or QFw startup. A minimal wrapper looks like:

```bash
#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${repo_dir}/qfw_iqm_common.sh"

qfw_iqm_init "$@"
qfw_iqm_run_single "scripts/new_workflow.py" "$@"
```

The Python script should add the common backend option with
`add_backend_argument(parser)` and construct the backend with
`get_backend(args.backend, args.system_up_timeout)`.

The `_qasm.py` scripts are retained as lower-level examples that build
OpenQASM directly. Characterization workflows should prefer Qiskit-authored
circuits unless they are explicitly testing OpenQASM handling.
